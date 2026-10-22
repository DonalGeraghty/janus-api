"""Garmin connection lifecycle and independent cached dashboard resources."""

import hashlib
import logging
import time
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from . import garmin_client
from .credential_service import encrypt_api_key, decrypt_api_key, CredentialConfigurationError, CredentialEncryptionError
from .firebase.garmin import execute
from .garmin_errors import GarminError

logger = logging.getLogger("janus-api.garmin")


def _log_failure(resource, error, cached, stage):
    # Error messages are Janus-authored; upstream response bodies never enter them.
    logger.warning("Garmin resource failure resource=%s stage=%s code=%s cached_fallback=%s retry_after=%s reason=%s",
                   resource, stage, error.code, cached, error.retry_after, error.message)


def _crypt(function, value, email, account_id, generation, purpose):
    try:
        return function(value, email, provider=f"garmin:{account_id}:{generation}:{purpose}", aad_version=2)
    except (CredentialConfigurationError, CredentialEncryptionError):
        raise GarminError("garmin_storage_unavailable", "Secure Garmin credential storage is unavailable.", 503) from None


def connection_status(connection):
    return {key: connection.get(key) for key in ("configured", "last_four", "verified_at", "reconnect_required")} | {"configured": bool(connection.get("configured"))}


def get_connection(email, account_id):
    connection, _ = execute(email, account_id)
    return connection_status(connection)


def save_connection(email, account_id, api_key):
    if not isinstance(api_key, str) or not 1 <= len(api_key.strip()) <= 4096 or any(not 33 <= ord(c) <= 126 for c in api_key.strip()):
        raise GarminError("invalid_api_key", "Enter a valid Garmin personal API key.", 400)
    api_key = api_key.strip()
    previous, _ = execute(email, account_id)
    token, expires_at = garmin_client.obtain_token(api_key)
    generation = uuid4().hex
    connection = {
        "configured": True, "generation": generation, "account_id": account_id,
        "ciphertext": _crypt(encrypt_api_key, api_key, email, account_id, generation, "key"),
        "token_ciphertext": _crypt(encrypt_api_key, token, email, account_id, generation, "token"),
        "token_expires_at": expires_at, "last_four": api_key[-4:],
        "verified_at": datetime.now(timezone.utc).isoformat(), "reconnect_required": False,
    }
    execute(email, account_id, "replace", generation=previous.get("generation"), connection=connection)
    return connection_status(connection)


def disconnect(email, account_id):
    connection, _ = execute(email, account_id)
    execute(email, account_id, "disconnect", generation=connection.get("generation"))


def validate_range(start, end):
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
        if first.isoformat() != start or last.isoformat() != end or not 0 <= (last - first).days < 28:
            raise ValueError()
    except (ValueError, TypeError):
        raise GarminError("invalid_date_range", "Use YYYY-MM-DD dates spanning at most 28 days, inclusive.", 400) from None
    return first, last


def _envelope(cache, source, now, warning=None):
    return {"data": cache["data"], "meta": {
        "source": source, "fetched_at": cache["fetched_at"], "fresh_until": cache["fresh_until"],
        "stale": bool(warning) or now >= cache["fresh_until"], "last_attempt_at": now if warning or source == "garmin" else cache["fetched_at"],
        "warning": {"code": warning.code, "message": warning.message, "retry_after": warning.retry_after} if warning else None,
    }}


def get_steps(email, account_id, start, end, force=False):
    validate_range(start, end)
    return _get_resource(email, account_id, "steps", start, end,
                         lambda token: garmin_client.fetch_steps(token, start, end), force)


def get_sleep(email, account_id, day, force=False):
    validate_range(day, day)
    return _get_resource(email, account_id, "sleep", day, day,
                         lambda token: garmin_client.fetch_sleep(token, day), force)


def get_sleep_history(email, account_id, start, end, force=False):
    validate_range(start, end)
    return _get_resource(email, account_id, "sleep", start, end,
                         lambda token: garmin_client.fetch_sleep_history(token, start, end), force, ":history")


def get_activities(email, account_id, start, end, limit=5, force=False):
    validate_range(start, end)
    if type(limit) is not int or not 1 <= limit <= 20:
        raise GarminError("invalid_limit", "Activity limit must be an integer from 1 to 20.", 400)
    return _get_resource(email, account_id, "activities", start, end,
                         lambda token: garmin_client.fetch_activities(token, start, end, limit), force, f":{limit}")


def _get_resource(email, account_id, resource, start, end, fetch, force=False, variant=""):
    connection, _ = execute(email, account_id)
    if not connection.get("configured"):
        raise GarminError("garmin_connection_required", "Connect Garmin in Account to view your data.", 409)
    generation = connection["generation"]
    cache_id = hashlib.sha256(f"{resource}:v1:{generation}:{start}:{end}{variant}".encode()).hexdigest()
    current, cache = execute(email, account_id, cache_id=cache_id)
    if current.get("generation") != generation:
        raise GarminError("garmin_connection_changed", "The Garmin connection changed. Try again.", 409)
    now = time.time()
    if cache and not force and now < cache["fresh_until"] and not current.get("reconnect_required"):
        return _envelope(cache, "cache", now)
    lease_id = uuid4().hex
    try:
        execute(email, account_id, "claim", generation=generation, resource=resource, now=now, lease_id=lease_id)
    except GarminError as error:
        _log_failure(resource, error, bool(cache) and error.code in ("garmin_rate_limited", "garmin_reconnect_required"), "refresh_claim")
        if cache and error.code in ("garmin_rate_limited", "garmin_reconnect_required"):
            return _envelope(cache, "cache", now, error)
        raise
    updates = {}
    try:
        if current.get("token_expires_at", 0) <= now + 60:
            key = _crypt(decrypt_api_key, current["ciphertext"], email, account_id, generation, "key")
            token, expires_at = garmin_client.obtain_token(key)
            updates = {"token_ciphertext": _crypt(encrypt_api_key, token, email, account_id, generation, "token"), "token_expires_at": expires_at}
        else:
            token = _crypt(decrypt_api_key, current["token_ciphertext"], email, account_id, generation, "token")
        data = fetch(token)
    except GarminError as error:
        finished = time.time()
        error.retry_after = max(10, error.retry_after)
        _log_failure(resource, error, bool(cache), "fetch")
        if error.code == "garmin_rate_limited":
            updates["retry_at"] = finished + max(10, error.retry_after)
        if error.code == "garmin_reconnect_required":
            updates["reconnect_required"] = True
        execute(email, account_id, "finish", cache_id=cache_id, generation=generation, resource=resource,
                lease_id=lease_id, retry_at=finished + max(10, error.retry_after), updates=updates)
        if cache:
            return _envelope(cache, "cache", finished, error)
        raise
    finished = time.time()
    # Recent and current records are mutable; older ranges can be reused longer.
    seconds = 900 if date.fromisoformat(end) >= datetime.now(timezone.utc).date() - timedelta(days=4) else 86400
    saved = {"data": data, "fetched_at": finished, "fresh_until": finished + seconds, "account_id": account_id, "generation": generation, "resource": resource, "start": start, "end": end}
    execute(email, account_id, "finish", cache_id=cache_id, generation=generation, resource=resource,
            lease_id=lease_id, retry_at=finished + 10, updates=updates, cache=saved)
    return _envelope(saved, "garmin", finished)
