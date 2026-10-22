"""Retirement coverage and retained account-deletion guarantees for old data."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app import app
from services.firebase import db_state
from services.firebase.account_state import ACCOUNT_DELETION_FIELD, ACCOUNT_DELETION_TOKEN_FIELD
from services.firebase.workouts import _delete_workout_batch_in_transaction, delete_workout_entries


class RetiredWorkoutApiTests(unittest.TestCase):
    def setUp(self):
        db_state.users_collection_ref = None
        db_state.db = None
        for store in (db_state.auth_users_memory, db_state.workout_history_memory, db_state.habits_memory, db_state.habit_checkins_memory):
            store.clear()
        self.client = app.test_client()
        response = self.client.post('/api/auth/register', json={'email': 'legacy@example.com', 'password': 'password123'})
        self.assertEqual(response.status_code, 201)
        self.headers = {'Authorization': f"Bearer {response.get_json()['token']}"}

    def tearDown(self):
        for store in (db_state.auth_users_memory, db_state.workout_history_memory, db_state.habits_memory, db_state.habit_checkins_memory):
            store.clear()

    def test_retired_routes_are_absent_for_signed_in_and_anonymous_clients(self):
        for headers in ({}, self.headers):
            for method, path in [('get', '/api/workouts'), ('post', '/api/workouts/analyze'),
                                 ('put', '/api/workouts/old-entry'), ('delete', '/api/workouts/old-entry')]:
                response = getattr(self.client, method)(path, headers=headers, json={})
                self.assertEqual(response.status_code, 404, (method, path))
        self.assertNotIn('/api/workouts', self.client.get('/').get_data(as_text=True))

    def test_historical_records_remain_until_explicit_account_deletion(self):
        records = {'old-entry': {'title': 'Historical workout'}}
        db_state.workout_history_memory['legacy@example.com'] = records.copy()
        self.assertEqual(self.client.get('/api/habits', headers=self.headers).status_code, 200)
        self.assertEqual(db_state.workout_history_memory['legacy@example.com'], records)
        response = self.client.delete('/api/auth/account', headers=self.headers, json={'password': 'password123'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('legacy@example.com', db_state.workout_history_memory)


class LegacyWorkoutCleanupTests(unittest.TestCase):
    def setUp(self):
        db_state.users_collection_ref = None
        db_state.db = None
        db_state.auth_users_memory.clear()
        db_state.workout_history_memory.clear()

    def tearDown(self):
        db_state.users_collection_ref = None
        db_state.db = None
        db_state.auth_users_memory.clear()
        db_state.workout_history_memory.clear()

    def _user(self, **changes):
        return {'account_id': 'account-1', ACCOUNT_DELETION_FIELD: True,
                ACCOUNT_DELETION_TOKEN_FIELD: 'deletion-1', **changes}

    def test_firestore_cleanup_requires_matching_generation_token_and_marker(self):
        for changes in [{'account_id': 'new-account'}, {ACCOUNT_DELETION_TOKEN_FIELD: 'different-token'}, {ACCOUNT_DELETION_FIELD: False}]:
            user_ref, transaction = Mock(), Mock()
            user_ref.get.return_value = SimpleNamespace(exists=True, to_dict=lambda: self._user(**changes))
            deleted, error = _delete_workout_batch_in_transaction(transaction, user_ref, [Mock()], 'account-1', 'deletion-1')
            self.assertFalse(deleted)
            self.assertEqual(error, 'account_mismatch')
            transaction.delete.assert_not_called()

    def test_matching_firestore_cleanup_deletes_the_batch(self):
        user_ref, transaction = Mock(), Mock()
        user_ref.get.return_value = SimpleNamespace(exists=True, to_dict=self._user)
        document_refs = [Mock(), Mock()]
        deleted, error = _delete_workout_batch_in_transaction(transaction, user_ref, document_refs, 'account-1', 'deletion-1')
        self.assertTrue(deleted)
        self.assertIsNone(error)
        self.assertEqual(transaction.delete.call_count, 2)

    def test_missing_account_cannot_delete_a_recreated_accounts_documents(self):
        user_ref, transaction = Mock(), Mock()
        user_ref.get.return_value = SimpleNamespace(exists=False)
        deleted, error = _delete_workout_batch_in_transaction(transaction, user_ref, [Mock()], 'account-1', 'deletion-1')
        self.assertTrue(deleted)
        self.assertIsNone(error)
        transaction.delete.assert_not_called()

    def test_memory_cleanup_rejects_stale_account_or_token(self):
        db_state.workout_history_memory['user@example.com'] = {'old-entry': {}}
        for changes in [{'account_id': 'new-account'}, {ACCOUNT_DELETION_TOKEN_FIELD: 'different-token'}, {ACCOUNT_DELETION_FIELD: False}]:
            db_state.auth_users_memory['user@example.com'] = self._user(**changes)
            self.assertFalse(delete_workout_entries('user@example.com', 'account-1', 'deletion-1'))
            self.assertIn('old-entry', db_state.workout_history_memory['user@example.com'])
        db_state.auth_users_memory['user@example.com'] = self._user()
        self.assertTrue(delete_workout_entries('user@example.com', 'account-1', 'deletion-1'))
        self.assertNotIn('user@example.com', db_state.workout_history_memory)

    def test_configured_firestore_failure_preserves_memory_data(self):
        db_state.users_collection_ref = Mock()
        db_state.workout_history_memory['user@example.com'] = {'old-entry': {}}
        self.assertFalse(delete_workout_entries('user@example.com', 'account-1', 'deletion-1'))
        self.assertIn('old-entry', db_state.workout_history_memory['user@example.com'])
