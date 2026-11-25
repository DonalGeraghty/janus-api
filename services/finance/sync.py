"""Sync orchestration: pull the ledger from Sheets, validate, atomically publish.

The snapshot is a derived, replaceable in-memory document scoped to the account
and snapshot ID; it is never treated as durable or shared across instances. A
failed sync retains the last good snapshot with a stale flag. Restarting with an
empty cache is surfaced as sync_required, never as zero data.
"""

import threading
from datetime import datetime, timezone
from uuid import uuid4

from core.finance.sheets import LEDGER_RANGE, SNAPSHOT_RANGE, build_coverage, rows_to_transactions
from services.finance import sheets as google_sheets
from services.finance import identity as sheets_identity
from services.credential_service import (
    CredentialConfigurationError,
    CredentialEncryptionError,
    decrypt_api_key,
)
from services.firebase import db_state
from services.firebase.finance.connections import (
    FinanceConnectionError,
    get_finance_connection_status,
    load_finance_credential,
)
from services.firebase.finance.rules import FinanceError, list_rules


_locks_guard = threading.Lock()
_locks = {}

_SHEETS_MESSAGES = {
    "sheets_reconnect_required": "Google Sheets access was rejected. Check workbook sharing in Account, or reconnect a legacy token connection.",
    "workbook_not_found": "The finance workbook was not found or is not shared with the token's account.",
    "sheets_upstream_error": "Google Sheets returned an error. Last good data is retained.",
    "sheets_unreachable": "Google Sheets is unreachable. Last good data is retained.",
    "sheets_bad_response": "Google Sheets returned an unexpected response. Last good data is retained.",
    "sheets_not_configured": "Connect your Google Sheets workbook in Account first.",
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _lock_for(email):
    with _locks_guard:
        return _locks.setdefault(email, threading.Lock())


def _load_token(email, account_id):
    credential = load_finance_credential(email, account_id)
    if credential and credential.get("mode") == "service_account":
        if credential.get("account_id") != account_id:
            raise FinanceError("Account is unavailable", 401)
        try:
            return sheets_identity.access_token()
        except sheets_identity.SheetsIdentityError as error:
            raise FinanceError(str(error), 503) from None
    if not credential or not credential.get("ciphertext"):
        raise FinanceError("Connect your Google Sheets workbook in Account first.", 403)
    try:
        return decrypt_api_key(
            credential["ciphertext"], email,
            provider=credential.get("provider", "google"),
            aad_version=credential.get("aad_version", 2),
        )
    except (CredentialConfigurationError, CredentialEncryptionError) as error:
        raise FinanceError("Secure credential storage is unavailable.", 503) from error


def _empty_status():
    return {
        "last_success_at": None,
        "last_attempt_at": None,
        "snapshot_id": None,
        "stale": False,
        "error": None,
        "row_count": 0,
        "coverage": None,
    }


def _binding(connection):
    return (connection.get("account_id"), connection.get("workbook_id"),
            connection.get("connection_id"), connection.get("mode"),
            connection.get("service_account_email") if connection.get("mode") == "service_account" else None)


def sync_now(email, account_id):
    """Pull, validate and atomically publish the ledger snapshot. Returns a bounded summary."""
    from services.firebase.core import normalize_user_email
    email = normalize_user_email(email)
    if not email:
        raise FinanceError("Invalid account", 401)
    with _lock_for(email):
        connection = get_finance_connection_status(email, account_id)
        if not connection.get("connected") or not connection.get("workbook_id"):
            raise FinanceError("Connect your Google Sheets workbook in Account first.", 403)
        binding = _binding(connection)
        with db_state.memory_lock:
            status = db_state.finance_sync_status_memory.get(email)
            if not status or status.get("binding") != binding:
                status = {**_empty_status(), "binding": binding}
                db_state.finance_sync_status_memory[email] = status
            status["last_attempt_at"] = _now()
        try:
            token = _load_token(email, account_id)
            values = google_sheets.fetch_values(connection["workbook_id"], LEDGER_RANGE, token)
        except FinanceError:
            status["error"] = "sheets_authentication_failed"
            status["stale"] = get_snapshot(email, account_id) is not None
            raise
        except google_sheets.SheetsError as error:
            status["error"] = error.code
            status["stale"] = email in db_state.finance_snapshots_memory
            raise FinanceError(_SHEETS_MESSAGES.get(error.code, "Google Sheets sync failed."), error.status, details={"code": error.code}) from error
        transactions, warnings, errors = rows_to_transactions(values)
        if errors:
            status["error"] = "validation_failed"
            status["stale"] = email in db_state.finance_snapshots_memory
            raise FinanceError("Ledger validation failed; last good data is retained.", 422, details=errors)
        snapshot_grid = None
        try:
            snapshot_grid = google_sheets.fetch_values(connection["workbook_id"], SNAPSHOT_RANGE, token)
        except google_sheets.SheetsError:
            warnings.append("snapshot tab unavailable; net worth will report an explicit unavailable state")
        fetched_at = _now()
        snapshot = {
            "snapshot_id": uuid4().hex,
            "fetched_at": fetched_at,
            "source": "google_sheets",
            "workbook_id": connection["workbook_id"],
            "account_id": account_id,
            "binding": binding,
            "rule_set_version": list_rules(email, account_id)["rule_set_version"],
            "rows": transactions,
            "snapshot_grid": snapshot_grid,
            "warnings": warnings,
            "coverage": build_coverage(transactions, fetched_at),
        }
        with db_state.memory_lock:
            current = get_finance_connection_status(email, account_id)
            if not current.get("connected") or _binding(current) != binding:
                raise FinanceError("The workbook connection changed during import. Try again.", 409,
                                   details={"code": "finance_connection_changed"})
            db_state.finance_snapshots_memory[email] = snapshot
            status.update({
                "last_success_at": fetched_at,
                "snapshot_id": snapshot["snapshot_id"],
                "stale": False,
                "error": None,
                "row_count": len(transactions),
                "coverage": snapshot["coverage"],
            })
        return summarize(snapshot, status)


def sync_status(email, account_id):
    from services.firebase.core import normalize_user_email
    email = normalize_user_email(email)
    if not email:
        raise FinanceError("Invalid account", 401)
    connection = get_finance_connection_status(email, account_id)
    snapshot = get_snapshot(email, account_id)
    with db_state.memory_lock:
        status = dict(db_state.finance_sync_status_memory.get(email) or _empty_status())
        if status.get("binding") != _binding(connection):
            status = _empty_status()
        status.pop("binding", None)
        status["sync_required"] = snapshot is None
        status["rule_set_version"] = list_rules(email, account_id)["rule_set_version"]
        return status


def get_snapshot(email, account_id=None):
    """Return only a snapshot belonging to the current account and connection."""
    with db_state.memory_lock:
        snapshot = db_state.finance_snapshots_memory.get(email)
        if snapshot is None:
            return None
        expected = account_id or snapshot.get("account_id")
        if not expected or snapshot.get("account_id") != expected:
            return None
        try:
            connection = get_finance_connection_status(email, expected)
        except FinanceConnectionError as error:
            if error.status in (401, 409):
                return None
            raise
        if not connection.get("connected") or snapshot.get("binding") != _binding(connection):
            db_state.finance_snapshots_memory.pop(email, None)
            db_state.finance_sync_status_memory.pop(email, None)
            return None
        return snapshot


def summarize(snapshot, status):
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "fetched_at": snapshot["fetched_at"],
        "source": snapshot["source"],
        "workbook_id": snapshot["workbook_id"],
        "rule_set_version": snapshot["rule_set_version"],
        "row_count": len(snapshot["rows"]),
        "coverage": snapshot["coverage"],
        "warnings": snapshot["warnings"][:50],
        "warning_count": len(snapshot["warnings"]),
        "stale": status.get("stale", False),
    }
