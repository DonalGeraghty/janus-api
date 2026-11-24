"""Per-account Google Sheets finance connection.

The secret (a user-supplied Google OAuth access token with read-only Sheets
scope) is KMS-encrypted by the route layer and stored under
users/{email}/private/finance, exactly like the per-user AI provider keys.
Only non-secret metadata (workbook ID, last four, timestamps) is readable back;
the browser never receives the token. Having this connection is what makes an
authenticated account finance-enabled; a shared login alone is not enough.
"""

import copy
from datetime import datetime, timezone

from firebase_admin import firestore

from . import db_state
from .account_state import ACCOUNT_DELETION_FIELD, ACCOUNT_DELETION_TOKEN_FIELD, account_id_matches
from .core import normalize_user_email
from ..logging_service import logger


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


def _status(connected, settings):
    connection = (settings or {}).get("finance_connection") or {}
    if not connected:
        return {"connected": False, "workbook_id": connection.get("workbook_id"), "last_four": None, "updated_at": connection.get("updated_at")}
    return {
        "connected": True,
        "workbook_id": connection.get("workbook_id"),
        "last_four": connection.get("last_four"),
        "purpose": PURPOSE,
        "updated_at": connection.get("updated_at"),
    }


def _write_settings(transaction, settings_ref, settings, connected, workbook_id, last_four):
    connection = dict(settings.get("finance_connection") or {})
    connection.update({"connected": connected, "workbook_id": workbook_id, "last_four": last_four, "updated_at": _now()})
    settings["finance_connection"] = connection
    settings["updated_at"] = _now()
    transaction.set(settings_ref, settings)


def save_finance_connection(email, account_id, ciphertext, last_four, workbook_id):
    """Store the encrypted token and the non-secret connection metadata atomically."""
    email = normalize_user_email(email)
    if not email:
        raise FinanceConnectionError("Invalid account", 401)
    now = _now()
    credential = {
        "provider": PROVIDER,
        "purpose": PURPOSE,
        "ciphertext": ciphertext,
        "last_four": last_four,
        "encryption_version": 2,
        "aad_version": AAD_VERSION,
        "created_at": now,
        "updated_at": now,
    }
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
            transaction.set(credential_ref, credential)
            _write_settings(transaction, settings_ref, settings, True, workbook_id, last_four)
            return _status(True, settings)

        try:
            return execute(db_state.db.transaction())
        except FinanceConnectionError:
            raise
        except Exception as error:
            logger.error("Finance connection save failed: %s", type(error).__name__)
            raise FinanceConnectionError("Finance storage is unavailable", 503) from error

    with db_state.memory_lock:
        _guard(db_state.auth_users_memory.get(email), account_id)
        settings = copy.deepcopy(db_state.finance_settings_memory.get(email, {}))
        db_state.finance_connection_memory[email] = copy.deepcopy(credential)
        connection = dict(settings.get("finance_connection") or {})
        connection.update({"connected": True, "workbook_id": workbook_id, "last_four": last_four, "updated_at": now})
        settings["finance_connection"] = connection
        settings["updated_at"] = now
        db_state.finance_settings_memory[email] = settings
        return _status(True, settings)


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
            return _status(credential.exists, settings_data)
        except FinanceConnectionError:
            raise
        except Exception as error:
            logger.error("Finance connection read failed: %s", type(error).__name__)
            raise FinanceConnectionError("Finance storage is unavailable", 503) from error
    with db_state.memory_lock:
        _guard(db_state.auth_users_memory.get(email), account_id)
        connected = email in db_state.finance_connection_memory
        settings = db_state.finance_settings_memory.get(email, {})
        return _status(connected, settings)


def has_finance_connection(email, account_id):
    return bool(get_finance_connection_status(email, account_id).get("connected"))


def load_finance_credential(email, account_id):
    """Return the stored credential document for server-side decryption (never serialized)."""
    email = normalize_user_email(email)
    if db_state.users_collection_ref is not None:
        if db_state.db is None:
            raise FinanceConnectionError("Finance storage is unavailable", 503)
        document = db_state.users_collection_ref.document(email).collection("private").document("finance").get()
        return document.to_dict() if document.exists else None
    with db_state.memory_lock:
        return copy.deepcopy(db_state.finance_connection_memory.get(email))


def delete_finance_connection(email, account_id, deletion_token=None):
    """Remove the secret and mark the connection as disconnected; metadata (workbook ID) is retained."""
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
            transaction.delete(credential_ref)
            settings_document = settings_ref.get(transaction=transaction)
            settings = settings_document.to_dict() if settings_document.exists else {}
            connection = dict(settings.get("finance_connection") or {})
            workbook_id = connection.get("workbook_id")
            _write_settings(transaction, settings_ref, settings, False, workbook_id, None)
            return _status(False, settings)

        try:
            return execute(db_state.db.transaction())
        except FinanceConnectionError:
            raise
        except Exception as error:
            logger.error("Finance connection delete failed: %s", type(error).__name__)
            raise FinanceConnectionError("Finance storage is unavailable", 503) from error

    with db_state.memory_lock:
        _guard(db_state.auth_users_memory.get(email), account_id, deletion_token)
        db_state.finance_connection_memory.pop(email, None)
        settings = copy.deepcopy(db_state.finance_settings_memory.get(email, {}))
        connection = dict(settings.get("finance_connection") or {})
        workbook_id = connection.get("workbook_id")
        connection.update({"connected": False, "workbook_id": workbook_id, "last_four": None, "updated_at": _now()})
        settings["finance_connection"] = connection
        db_state.finance_settings_memory[email] = settings
        return _status(False, settings)
