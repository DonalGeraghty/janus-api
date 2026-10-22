"""Retired study endpoints stay absent; legacy records retain deletion guarantees."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app import app
from services.firebase import db_state
from services.firebase.account_state import ACCOUNT_DELETION_FIELD, ACCOUNT_DELETION_TOKEN_FIELD
from services.firebase.flashcards import _delete_batch_in_transaction, delete_flashcards


class RetiredFlashcardApiTests(unittest.TestCase):
    def setUp(self):
        db_state.users_collection_ref = None
        db_state.db = None
        self.stores = (db_state.auth_users_memory, db_state.flashcards_memory, db_state.flashcard_reviews_memory)
        for store in self.stores:
            store.clear()
        self.client = app.test_client()
        response = self.client.post('/api/auth/register', json={'email': 'legacy@example.com', 'password': 'password123'})
        self.assertEqual(response.status_code, 201)
        self.headers = {'Authorization': f"Bearer {response.json['token']}"}

    def tearDown(self):
        for store in self.stores:
            store.clear()

    def test_retired_routes_and_api_index_are_absent(self):
        routes = [('post', '/api/minerva/respond'), ('get', '/api/user/minerva-settings'),
                  ('put', '/api/user/minerva-settings'), ('get', '/api/flashcards'),
                  ('post', '/api/flashcards'), ('get', '/api/flashcards/due'),
                  ('put', '/api/flashcards/old'), ('delete', '/api/flashcards/old'),
                  ('post', '/api/flashcards/old/reviews')]
        for headers in ({}, self.headers):
            for method, route in routes:
                self.assertEqual(getattr(self.client, method)(route, headers=headers, json={}).status_code, 404, route)
        index = self.client.get('/').get_data(as_text=True)
        for route in ('/api/flashcards', '/api/minerva/respond', '/api/user/minerva-settings'):
            self.assertNotIn(route, index)

    def test_legacy_data_is_preserved_until_explicit_account_deletion(self):
        db_state.flashcards_memory['legacy@example.com'] = {'old': {'front': 'Keep'}}
        db_state.flashcard_reviews_memory['legacy@example.com'] = {'review': {'card_id': 'old'}}
        self.assertEqual(self.client.get('/api/garmin/connection', headers=self.headers).status_code, 503)
        self.assertIn('old', db_state.flashcards_memory['legacy@example.com'])
        result = self.client.delete('/api/auth/account', headers=self.headers, json={'password': 'password123'})
        self.assertEqual(result.status_code, 200)
        self.assertNotIn('legacy@example.com', db_state.flashcards_memory)
        self.assertNotIn('legacy@example.com', db_state.flashcard_reviews_memory)


class LegacyFlashcardCleanupTests(unittest.TestCase):
    def setUp(self):
        db_state.users_collection_ref = None
        db_state.db = None
        db_state.auth_users_memory.clear()
        db_state.flashcards_memory.clear()
        db_state.flashcard_reviews_memory.clear()

    def tearDown(self):
        self.setUp()

    def owner(self, **changes):
        return {'account_id': 'account-1', ACCOUNT_DELETION_FIELD: True, ACCOUNT_DELETION_TOKEN_FIELD: 'delete-1', **changes}

    def test_firestore_cleanup_requires_generation_and_deletion_marker(self):
        for changes in ({'account_id': 'new'}, {ACCOUNT_DELETION_FIELD: False}, {ACCOUNT_DELETION_TOKEN_FIELD: 'other'}):
            user_ref, transaction = Mock(), Mock()
            user_ref.get.return_value = SimpleNamespace(exists=True, to_dict=lambda: self.owner(**changes))
            ok, error = _delete_batch_in_transaction(transaction, user_ref, [Mock()], 'account-1', 'delete-1')
            self.assertFalse(ok)
            self.assertEqual(error, 'account_mismatch')
            transaction.delete.assert_not_called()

    def test_matching_firestore_cleanup_removes_requested_documents(self):
        user_ref, transaction = Mock(), Mock()
        user_ref.get.return_value = SimpleNamespace(exists=True, to_dict=self.owner)
        ok, _ = _delete_batch_in_transaction(transaction, user_ref, [Mock(), Mock()], 'account-1', 'delete-1')
        self.assertTrue(ok)
        self.assertEqual(transaction.delete.call_count, 2)

    def test_missing_account_does_not_touch_subcollections(self):
        user_ref, transaction = Mock(), Mock()
        user_ref.get.return_value = SimpleNamespace(exists=False)
        self.assertTrue(_delete_batch_in_transaction(transaction, user_ref, [Mock()], 'account-1', 'delete-1')[0])
        transaction.delete.assert_not_called()

    def test_memory_cleanup_preserves_other_generations_and_removes_both_collections(self):
        db_state.flashcards_memory['user@example.com'] = {'old': {}}
        db_state.flashcard_reviews_memory['user@example.com'] = {'review': {}}
        db_state.auth_users_memory['user@example.com'] = self.owner(account_id='new')
        self.assertFalse(delete_flashcards('user@example.com', 'account-1', 'delete-1'))
        self.assertIn('user@example.com', db_state.flashcards_memory)
        db_state.auth_users_memory['user@example.com'] = self.owner()
        self.assertTrue(delete_flashcards('user@example.com', 'account-1', 'delete-1'))
        self.assertNotIn('user@example.com', db_state.flashcards_memory)
        self.assertNotIn('user@example.com', db_state.flashcard_reviews_memory)

    def test_configured_firestore_failure_does_not_fall_back_to_memory(self):
        db_state.users_collection_ref = Mock()
        db_state.flashcards_memory['user@example.com'] = {'old': {}}
        self.assertFalse(delete_flashcards('user@example.com', 'account-1', 'delete-1'))
        self.assertIn('user@example.com', db_state.flashcards_memory)
        db_state.users_collection_ref = None


if __name__ == '__main__':
    unittest.main()
