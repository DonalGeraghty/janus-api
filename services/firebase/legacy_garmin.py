"""Guarded cleanup of historical Garmin records during shared-account deletion.

The Garmin integration itself is removed; this module remains only so explicit
account deletion still removes stored Garmin credentials, caches and settings
with account-generation and deletion-token checks.
"""

from firebase_admin import firestore

from . import db_state
from .account_state import ACCOUNT_DELETION_FIELD, ACCOUNT_DELETION_TOKEN_FIELD, account_id_matches
from .core import normalize_user_email


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
            raise ValueError("account_unavailable")
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
