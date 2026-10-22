"""Transactional Garmin storage. No plaintext or process-memory fallback."""

from uuid import uuid4

from firebase_admin import firestore

from . import db_state
from .core import normalize_user_email
from .account_state import ACCOUNT_DELETION_FIELD, ACCOUNT_DELETION_TOKEN_FIELD, account_id_matches
from ..garmin_errors import GarminError


def _validate_account(data, account_id):
    if not data or not account_id_matches(account_id, data) or data.get(ACCOUNT_DELETION_FIELD):
        raise GarminError("account_unavailable", "This account is no longer available.", 409)


def _apply(transaction, user_ref, connection_ref, cache_ref, account_id, action, values):
    user = user_ref.get(transaction=transaction)
    _validate_account(user.to_dict() if user.exists else None, account_id)
    snapshot = connection_ref.get(transaction=transaction)
    connection = (snapshot.to_dict() or {}) if snapshot.exists else {}
    cached = cache_ref.get(transaction=transaction) if cache_ref else None
    cache = (cached.to_dict() or {}) if cached and cached.exists else None
    if action == "read":
        return connection, cache
    if connection.get("generation") != values.get("generation"):
        raise GarminError("garmin_connection_changed", "The Garmin connection changed. Reload and try again.", 409)
    if action == "replace":
        transaction.set(connection_ref, values["connection"])
        return values["connection"]
    if action == "disconnect":
        transaction.set(connection_ref, {"generation": uuid4().hex, "configured": False})
        return None
    if not connection.get("configured"):
        raise GarminError("garmin_connection_required", "Connect Garmin in Account to view your data.", 409)
    if action == "claim":
        now = values["now"]
        if connection.get("reconnect_required"):
            raise GarminError("garmin_reconnect_required", "Replace your Garmin personal API key in Account.", 409)
        wait = max(connection.get("lease_until", 0), connection.get("retry_at", 0)) - now
        if wait > 0:
            raise GarminError("garmin_rate_limited", "A refresh is running or cooling down. Try again shortly.", 429, int(wait) + 1)
        transaction.update(connection_ref, {"lease_id": values["lease_id"], "lease_until": now + 60})
        return None
    if action == "finish":
        if connection.get("lease_id") != values["lease_id"]:
            raise GarminError("garmin_connection_changed", "A newer Garmin refresh has started. Try again.", 409)
        updates = {"lease_id": None, "lease_until": 0, **values["updates"]}
        transaction.update(connection_ref, updates)
        if values.get("cache") is not None:
            transaction.set(cache_ref, values["cache"])
        return None
    raise ValueError("Unknown Garmin storage action")


def execute(email, account_id, action="read", cache_id=None, **values):
    if db_state.db is None or db_state.users_collection_ref is None:
        raise GarminError("garmin_storage_unavailable", "Secure Garmin storage is unavailable.", 503)
    user_ref = db_state.users_collection_ref.document(normalize_user_email(email))
    connection_ref = user_ref.collection("private").document("garmin")
    cache_ref = user_ref.collection("garmin_cache").document(cache_id) if cache_id else None
    try:
        return firestore.transactional(_apply)(db_state.db.transaction(), user_ref, connection_ref, cache_ref, account_id, action, values)
    except GarminError:
        raise
    except Exception:
        raise GarminError("garmin_storage_unavailable", "Secure Garmin storage is unavailable.", 503) from None


def delete_garmin_account_data(email, account_id, deletion_token):
    """Delete only under the owning tombstoned account; safe to retry."""
    if db_state.users_collection_ref is None:
        return True
    if db_state.db is None:
        return False
    user_ref = db_state.users_collection_ref.document(normalize_user_email(email))

    def remove(transaction, target):
        document = user_ref.get(transaction=transaction)
        if not document.exists:
            return
        data = document.to_dict() or {}
        if (not account_id_matches(account_id, data) or not data.get(ACCOUNT_DELETION_FIELD)
                or data.get(ACCOUNT_DELETION_TOKEN_FIELD) != deletion_token):
            raise GarminError("account_unavailable", "Account deletion state changed.", 409)
        transaction.delete(target)

    try:
        # The tombstone prevents concurrent integration writes during traversal.
        for name in ("garmin_cache", "garmin_settings"):
            for document in user_ref.collection(name).stream():
                firestore.transactional(remove)(db_state.db.transaction(), document.reference)
        firestore.transactional(remove)(db_state.db.transaction(), user_ref.collection("private").document("garmin"))
        return True
    except Exception:
        return False
