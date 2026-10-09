"""Legacy workout cleanup during account deletion; no active workout API."""

from firebase_admin import firestore

from . import db_state
from .account_state import (
    ACCOUNT_DELETION_FIELD,
    ACCOUNT_DELETION_TOKEN_FIELD,
    account_id_matches,
)
from .core import normalize_user_email
from ..logging_service import logger


def _history_collection(email_key):
    return db_state.users_collection_ref.document(email_key).collection(
        "workout_history"
    )


def _delete_workout_batch_in_transaction(
    transaction,
    user_ref,
    document_refs,
    expected_account_id,
    deletion_token,
):
    user_document = user_ref.get(transaction=transaction)
    if not user_document.exists:
        return True, None
    user_data = user_document.to_dict() or {}
    if (
        not user_data.get(ACCOUNT_DELETION_FIELD)
        or not account_id_matches(expected_account_id, user_data)
        or user_data.get(ACCOUNT_DELETION_TOKEN_FIELD) != deletion_token
    ):
        return False, "account_mismatch"
    for document_ref in document_refs:
        transaction.delete(document_ref)
    return True, None


def delete_workout_entries(email, expected_account_id, deletion_token):
    """Delete all workout history before removing the parent user document."""
    email_key = normalize_user_email(email)
    if not email_key:
        return False

    if db_state.users_collection_ref:
        if db_state.db is None:
            return False
        try:
            user_ref = db_state.users_collection_ref.document(email_key)
            documents = list(_history_collection(email_key).stream())
            for offset in range(0, len(documents), 400):
                document_refs = [
                    document.reference
                    for document in documents[offset:offset + 400]
                ]
                transaction = db_state.db.transaction()
                deleted, _ = firestore.transactional(
                    _delete_workout_batch_in_transaction
                )(
                    transaction,
                    user_ref,
                    document_refs,
                    expected_account_id,
                    deletion_token,
                )
                if not deleted:
                    return False
        except Exception as error:
            logger.error("Firestore workout cleanup failed", extra={
                "operation": "delete_workout_entries",
                "error": type(error).__name__,
            })
            return False

    with db_state.memory_lock:
        user = db_state.auth_users_memory.get(email_key)
        if user:
            if (
                not user.get(ACCOUNT_DELETION_FIELD)
                or not account_id_matches(expected_account_id, user)
                or user.get(ACCOUNT_DELETION_TOKEN_FIELD) != deletion_token
            ):
                return False
            db_state.workout_history_memory.pop(email_key, None)
    return True
