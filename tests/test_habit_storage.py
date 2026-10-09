import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from services.firebase import db_state
from services.firebase.habits import HabitError, create_habit, save_checkin


class HabitFirestoreTests(unittest.TestCase):
    def setUp(self):
        self.transaction = Mock()
        self.user_ref, self.state_ref, self.checkins = Mock(), Mock(), Mock()
        self.user = {'account_id': 'generation-a'}
        self.user_ref.get.return_value = SimpleNamespace(exists=True, to_dict=lambda: self.user)
        state_collection = Mock()
        state_collection.document.return_value = self.state_ref
        self.user_ref.collection.side_effect = lambda name: state_collection if name == 'aether' else self.checkins
        self.state_ref.get.return_value = SimpleNamespace(exists=False)
        db_state.users_collection_ref = Mock()
        db_state.users_collection_ref.document.return_value = self.user_ref
        db_state.db = Mock()
        db_state.db.transaction.return_value = self.transaction
        self.wrap = patch('services.firebase.habits.firestore.transactional', side_effect=lambda function: function)
        self.wrap.start()
        self.clock = patch('services.firebase.habits.habit_today', return_value=date(2026, 10, 9))
        self.clock.start()

    def tearDown(self):
        self.clock.stop()
        self.wrap.stop()
        db_state.users_collection_ref = None
        db_state.db = None

    def test_creation_is_transactional_and_scoped_to_current_user(self):
        result = create_habit('user@example.com', 'generation-a', {'name': 'Read', 'description': '', 'icon': 'book', 'colour': '#d9c5a3', 'days': [4], 'category_id': None, 'group_id': None, 'start_date': '2026-10-09'})
        db_state.users_collection_ref.document.assert_called_with('user@example.com')
        self.user_ref.get.assert_called_once_with(transaction=self.transaction)
        self.state_ref.get.assert_called_once_with(transaction=self.transaction)
        saved_ref, saved = self.transaction.set.call_args.args
        self.assertIs(saved_ref, self.state_ref)
        self.assertEqual(saved['account_id'], 'generation-a')
        self.assertEqual(saved['habits'][0]['id'], result['habit']['id'])

    def test_stale_generation_and_deleting_account_cannot_write(self):
        for user in [{'account_id': 'generation-b'}, {'account_id': 'generation-a', 'account_deletion_in_progress': True}]:
            self.user = user
            with self.assertRaises(HabitError):
                save_checkin('user@example.com', 'generation-a', 'read', '2026-10-09', {'completed': True, 'note': ''})
            self.transaction.set.assert_not_called()
            self.transaction.delete.assert_not_called()

    def test_checkin_reads_current_schedule_before_writing(self):
        state = {'account_id': 'generation-a', 'habits': [{'id': 'read', 'start_date': '2026-10-09', 'schedule_history': [{'effective_from': '2026-10-09', 'days': [4], 'archived': False}]}], 'categories': [], 'groups': [], 'timezone': 'Europe/Dublin'}
        self.state_ref.get.return_value = SimpleNamespace(exists=True, to_dict=lambda: state)
        result = save_checkin('user@example.com', 'generation-a', 'read', '2026-10-09', {'completed': True, 'note': 'Done'})
        self.checkins.document.assert_called_with('read_2026-10-09')
        self.assertTrue(result['checkin']['completed'])
        self.assertEqual(self.transaction.set.call_args.args[1]['note'], 'Done')

    def test_configured_database_failure_never_uses_memory_fallback(self):
        self.user_ref.get.side_effect = RuntimeError('database offline')
        with self.assertRaises(HabitError) as failure:
            save_checkin('user@example.com', 'generation-a', 'read', '2026-10-09', {'completed': True, 'note': ''})
        self.assertEqual(failure.exception.status, 503)
        self.assertNotIn('user@example.com', db_state.habit_checkins_memory)
