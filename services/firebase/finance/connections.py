"""Account-bound Sheets connections, administrator approvals and legacy tokens.

Service-account connections contain metadata only. Legacy OAuth tokens remain
encrypted until a validated migration replaces them. Approval is bound to the
account generation and workbook, independently of the reader's Google access.
"""

import copy
from datetime import datetime, timezone
from uuid import uuid4

from firebase_admin import firestore

from .. import db_state
from ..account_state import ACCOUNT_DELETION_FIELD, ACCOUNT_DELETION_TOKEN_FIELD, account_id_matches
from ..core import normalize_user_email
from ...logging_service import logger
from services.finance.identity import reader_email


PROVIDER = "google"
PURPOSE = "google_sheets_read_only"
AAD_VERSION = 2
FINANCE_SETTINGS_DOC = "settings"


class FinanceConnectionError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _now():
    return datetime.now(timezone.utc).isoformat()


def _guard(user, account_id, deletion_token=None):
    if not user or not account_id_matches(account_id, user):
        raise FinanceConnectionError("Account is unavailable", 401)
    if deletion_token:
        if not user.get(ACCOUNT_DELETION_FIELD) or user.get(ACCOUNT_DELETION_TOKEN_FIELD) != deletion_token:
            raise FinanceConnectionError("Account deletion changed", 409)
    elif user.get(ACCOUNT_DELETION_FIELD):
        raise FinanceConnectionError("Account deletion is in progress", 409)


def _require_approval(settings, account_id, workbook_id):
    approval = (settings or {}).get("finance_service_account_approval") or {}
    if approval.get("account_id") != account_id or approval.get("workbook_id") != workbook_id:
        raise FinanceConnectionError("This workbook is not approved for your Janus account.", 403)


def _status(connected, settings, account_id=None):
    connection = (settings or {}).get("finance_connection") or {}
    approval = (settings or {}).get("finance_service_account_approval") or {}
    approved = approval.get("workbook_id") if approval.get("account_id") == account_id else None
    if connection.get("mode") == "service_account":
        connected = connected and bool(approved and approved == connection.get("workbook_id")
                                       and connection.get("account_id") == account_id and reader_email())
    return {
        "connected": bool(connected),
        "workbook_id": connection.get("workbook_id"),
        "last_four": connection.get("last_four") if connected else None,
        "mode": connection.get("mode", "access_token") if connected else connection.get("mode"),
        "connection_id": connection.get("connection_id") or connection.get("updated_at"),
        "account_id": account_id,
        "service_account_email": reader_email(),
        "approved_workbook_id": approved,
        "service_account_ready": bool(approved and reader_email()),
        "purpose": PURPOSE,
        "updated_at": connection.get("updated_at"),
    }


def _write_settings(transaction, settings_ref, settings, connected, workbook_id, last_four, **metadata):
    connection = dict(settings.get("finance_connection") or {})
    connection.update({"connected": connected, "workbook_id": workbook_id, "last_four": last_four, "updated_at": _now()})
    connection.update(metadata)
    settings["finance_connection"] = connection
    settings["updated_at"] = _now()
    transaction.set(settings_ref, settings)


def save_finance_connection(email, account_id, ciphertext, last_four, workbook_id, *, mode="access_token"):
    """Atomically replace a connection and invalidate the previous derived data."""
    email = normalize_user_email(email)
    if not email:
        raise FinanceConnectionError("Invalid account", 401)
    now = _now()
    credential = {
        "mode": mode,
        "provider": PROVIDER,
        "purpose": PURPOSE,
        "ciphertext": ciphertext,
        "last_four": last_four,
        "encryption_version": 2,
        "aad_version": AAD_VERSION,
        "created_at": now,
        "updated_at": now,
    }
    connection_id = uuid4().hex
    if mode == "service_account":
        credential = {"mode": mode, "account_id": account_id, "connection_id": connection_id,
                      "workbook_id": workbook_id, "updated_at": now}
    if db_state.users_collection_ref is not None:
        if db_state.db is None:
            raise FinanceConnectionError("Finance storage is unavailable", 503)
        user_ref = db_state.users_collection_ref.document(email)
        credential_ref = user_ref.collection("private").document("finance")
        settings_ref = user_ref.collection("finance_settings").document(FINANCE_SETTINGS_DOC)

        @firestore.transactional
        def execute(transaction):
            user = user_ref.get(transaction=transaction)
            _guard(user.to_dict() if user.exists else None, account_id)
            settings_document = settings_ref.get(transaction=transaction)
            settings = settings_document.to_dict() if settings_document.exists else {}
            if mode == "service_account":
                _require_approval(settings, account_id, workbook_id)
            transaction.set(credential_ref, credential)
            _write_settings(transaction, settings_ref, settings, True, workbook_id, last_four,
                            mode=mode, connection_id=connection_id, account_id=account_id)
            return _status(True, settings, account_id)

        try:
            result = execute(db_state.db.transaction())
            with db_state.memory_lock:
                db_state.finance_snapshots_memory.pop(email, None)
                db_state.finance_sync_status_memory.pop(email, None)
            return result
        except FinanceConnectionError:
            raise
        except Exception as error:
            logger.error("Finance connection save failed: %s: %s", type(error).__name__, str(error)[:200])
            raise FinanceConnectionError("Finance storage is unavailable", 503) from error

    with db_state.memory_lock:
        _guard(db_state.auth_users_memory.get(email), account_id)
        settings = copy.deepcopy(db_state.finance_settings_memory.get(email, {}))
        if mode == "service_account":
            _require_approval(settings, account_id, workbook_id)
        db_state.finance_connection_memory[email] = copy.deepcopy(credential)
        connection = dict(settings.get("finance_connection") or {})
        connection.update({"connected": True, "workbook_id": workbook_id, "last_four": last_four, "updated_at": now,
                           "mode": mode, "connection_id": connection_id, "account_id": account_id})
        settings["finance_connection"] = connection
        settings["updated_at"] = now
        db_state.finance_settings_memory[email] = settings
        db_state.finance_snapshots_memory.pop(email, None)
        db_state.finance_sync_status_memory.pop(email, None)
        return _status(True, settings, account_id)


def get_finance_connection_status(email, account_id):
    email = normalize_user_email(email)
    if not email:
        raise FinanceConnectionError("Invalid account", 401)
    if db_state.users_collection_ref is not None:
        if db_state.db is None:
            raise FinanceConnectionError("Finance storage is unavailable", 503)
        user_ref = db_state.users_collection_ref.document(email)
        try:
            user = user_ref.get()
            _guard(user.to_dict() if user.exists else None, account_id)
            credential = user_ref.collection("private").document("finance").get()
            settings = user_ref.collection("finance_settings").document(FINANCE_SETTINGS_DOC).get()
            settings_data = settings.to_dict() if settings.exists else {}
            return _status(credential.exists, settings_data, account_id)
        except FinanceConnectionError:
            raise
        except Exception as error:
            logger.error("Finance connection read failed: %s: %s", type(error).__name__, str(error)[:200])
            raise FinanceConnectionError("Finance storage is unavailable", 503) from error
    with db_state.memory_lock:
        _guard(db_state.auth_users_memory.get(email), account_id)
        connected = email in db_state.finance_connection_memory
        settings = db_state.finance_settings_memory.get(email, {})
        return _status(connected, settings, account_id)


def has_finance_connection(email, account_id):
    return bool(get_finance_connection_status(email, account_id).get("connected"))


def load_finance_credential(email, account_id):
    """Return the stored credential document for server-side decryption (never serialized)."""
    email = normalize_user_email(email)
    if db_state.users_collection_ref is not None:
        if db_state.db is None:
            raise FinanceConnectionError("Finance storage is unavailable", 503)
        user_ref = db_state.users_collection_ref.document(email)
        user = user_ref.get()
        _guard(user.to_dict() if user.exists else None, account_id)
        document = user_ref.collection("private").document("finance").get()
        return document.to_dict() if document.exists else None
    with db_state.memory_lock:
        _guard(db_state.auth_users_memory.get(email), account_id)
        return copy.deepcopy(db_state.finance_connection_memory.get(email))


def delete_finance_connection(email, account_id, deletion_token=None):
    """Disconnect and clear derived data; retain rules, workbook metadata and approval."""
    email = normalize_user_email(email)
    if not email:
        raise FinanceConnectionError("Invalid account", 401)
    if db_state.users_collection_ref is not None:
        if db_state.db is None:
            raise FinanceConnectionError("Finance storage is unavailable", 503)
        user_ref = db_state.users_collection_ref.document(email)
        credential_ref = user_ref.collection("private").document("finance")
        settings_ref = user_ref.collection("finance_settings").document(FINANCE_SETTINGS_DOC)

        @firestore.transactional
        def execute(transaction):
            user = user_ref.get(transaction=transaction)
            _guard(user.to_dict() if user.exists else None, account_id, deletion_token)
            # All reads must precede writes inside a Firestore transaction.
            settings_document = settings_ref.get(transaction=transaction)
            settings = settings_document.to_dict() if settings_document.exists else {}
            connection = dict(settings.get("finance_connection") or {})
            workbook_id = connection.get("workbook_id")
            transaction.delete(credential_ref)
            _write_settings(transaction, settings_ref, settings, False, workbook_id, None)
            return _status(False, settings, account_id)

        try:
            result = execute(db_state.db.transaction())
            with db_state.memory_lock:
                db_state.finance_snapshots_memory.pop(email, None)
                db_state.finance_sync_status_memory.pop(email, None)
            return result
        except FinanceConnectionError:
            raise
        except Exception as error:
            logger.error("Finance connection delete failed: %s: %s", type(error).__name__, str(error)[:200])
            raise FinanceConnectionError("Finance storage is unavailable", 503) from error

    with db_state.memory_lock:
        _guard(db_state.auth_users_memory.get(email), account_id, deletion_token)
        db_state.finance_connection_memory.pop(email, None)
        db_state.finance_snapshots_memory.pop(email, None)
        db_state.finance_sync_status_memory.pop(email, None)
        settings = copy.deepcopy(db_state.finance_settings_memory.get(email, {}))
        connection = dict(settings.get("finance_connection") or {})
        workbook_id = connection.get("workbook_id")
        connection.update({"connected": False, "workbook_id": workbook_id, "last_four": None, "updated_at": _now()})
        settings["finance_connection"] = connection
        db_state.finance_settings_memory[email] = settings
        return _status(False, settings, account_id)
