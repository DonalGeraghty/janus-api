"""Shared cleanup retains deletion guarantees for historical integration data."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from services.firebase import db_state
from services.firebase.legacy_data import delete_legacy_account_data
from services.firebase.account_state import ACCOUNT_DELETION_FIELD, ACCOUNT_DELETION_TOKEN_FIELD


class LegacyAccountCleanupTests(unittest.TestCase):
    def setUp(self):
        db_state.users_collection_ref = None
        db_state.db = None
        db_state.auth_users_memory.clear()

    def tearDown(self):
        db_state.auth_users_memory.clear()
        db_state.users_collection_ref = None
        db_state.db = None

    def test_shared_cleanup_removes_historical_documents_and_credentials(self):
        db_state.auth_users_memory.clear()
        db_state.db = Mock()
        db_state.users_collection_ref = Mock()
        user_ref = db_state.users_collection_ref.document.return_value
        user_ref.get.return_value = SimpleNamespace(exists=True, to_dict=lambda: {
            'account_id': 'account-1', ACCOUNT_DELETION_FIELD: True,
            ACCOUNT_DELETION_TOKEN_FIELD: 'delete-1',
        })
        collections = {name: Mock() for name in ('flashcards', 'flashcard_reviews', 'garmin_cache', 'garmin_settings', 'private')}
        document_refs = []
        for name in ('flashcards', 'flashcard_reviews', 'garmin_cache', 'garmin_settings'):
            reference = Mock(name=name)
            document_refs.append(reference)
            collections[name].stream.return_value = [SimpleNamespace(reference=reference)]
        user_ref.collection.side_effect = collections.__getitem__
        document_refs.append(collections['private'].document.return_value)
        with patch('services.firebase.legacy_data.firestore.transactional', side_effect=lambda fn: fn):
            self.assertTrue(delete_legacy_account_data('legacy@example.com', 'account-1', 'delete-1'))
        transaction = db_state.db.transaction.return_value
        transaction.delete.assert_has_calls([call(ref) for ref in document_refs], any_order=True)
        self.assertEqual(transaction.delete.call_count, len(document_refs))
        collections['private'].document.assert_called_once_with('garmin')


if __name__ == '__main__':
    unittest.main()
