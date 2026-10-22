import unittest
from datetime import date
from unittest.mock import patch

from app import app
from core.habit_service import habit_stats, is_due
from services.ai_errors import AIBillingError
from services.firebase import db_state
from services.firebase.habits import HabitError, _guard, _operate
from services.firebase.account_state import ACCOUNT_DELETION_FIELD


class HabitApiTests(unittest.TestCase):
    def setUp(self):
        db_state.users_collection_ref = None
        db_state.db = None
        for store in [db_state.auth_users_memory, db_state.habits_memory, db_state.habit_checkins_memory]:
            store.clear()
        self.client = app.test_client()
        self.today = date(2026, 10, 9)
        self.clock = patch('services.firebase.habits.habit_today', return_value=self.today)
        self.clock.start()
        self.headers = self.register('habits@example.com')

    def tearDown(self):
        self.clock.stop()
        for store in [db_state.auth_users_memory, db_state.habits_memory, db_state.habit_checkins_memory]:
            store.clear()

    def register(self, email):
        result = self.client.post('/api/auth/register', json={'email': email, 'password': 'password123'})
        self.assertEqual(result.status_code, 201)
        return {'Authorization': f"Bearer {result.get_json()['token']}"}

    def create(self, **overrides):
        data = {'name': 'Read', 'days': [0, 1, 2, 3, 4, 5, 6], 'start_date': self.today.isoformat()}
        data.update(overrides)
        result = self.client.post('/api/habits', headers=self.headers, json=data)
        self.assertEqual(result.status_code, 201, result.get_json())
        return result.get_json()['habit']

    def test_all_mutations_require_authentication(self):
        for method, path in [('get', '/api/habits'), ('post', '/api/habits'), ('put', '/api/habits/x'),
                             ('delete', '/api/habits/x'), ('put', '/api/habits/x/checkins/2026-10-09'),
                             ('get', '/api/habit-checkins'), ('post', '/api/habit-groups'),
                             ('put', '/api/habit-categories/x'), ('put', '/api/habits/settings'), ('post', '/api/habits/draft')]:
            self.assertEqual(getattr(self.client, method)(path).status_code, 401)

    def test_crud_ownership_and_label_cleanup(self):
        group = self.client.post('/api/habit-groups', headers=self.headers, json={'name': 'Evening'}).get_json()['item']
        category = self.client.post('/api/habit-categories', headers=self.headers, json={'name': 'Learning'}).get_json()['item']
        habit = self.create(group_id=group['id'], category_id=category['id'])
        other = self.register('other@example.com')
        self.assertEqual(self.client.get('/api/habits', headers=other).get_json()['habits'], [])
        self.assertEqual(self.client.put(f"/api/habits/{habit['id']}", headers=other, json={'name': 'Other'}).status_code, 404)
        self.assertEqual(self.client.post('/api/habits', headers=other, json={'name': 'Walk', 'days': [4], 'start_date': '2026-10-09', 'group_id': group['id']}).status_code, 400)
        self.client.delete(f"/api/habit-groups/{group['id']}", headers=self.headers)
        self.client.delete(f"/api/habit-categories/{category['id']}", headers=self.headers)
        result = self.client.get('/api/habits', headers=self.headers).get_json()['habits'][0]
        self.assertIsNone(result['group_id'])
        self.assertIsNone(result['category_id'])

    def test_checkins_are_idempotent_correctable_and_removed_with_habit(self):
        habit = self.create()
        path = f"/api/habits/{habit['id']}/checkins/2026-10-09"
        for _ in range(2):
            self.assertEqual(self.client.put(path, headers=self.headers, json={'completed': True, 'note': 'After dinner'}).status_code, 200)
        state = self.client.get('/api/habits', headers=self.headers).get_json()
        self.assertEqual(state['stats'][habit['id']]['current'], 1)
        self.assertEqual(len(state['today_checkins']), 1)
        result = self.client.get('/api/habit-checkins?start=2026-10-01&end=2026-10-31', headers=self.headers).get_json()
        self.assertEqual(result['checkins'][0]['note'], 'After dinner')
        self.assertEqual(len(result['checkins']), 1)
        self.client.put(path, headers=self.headers, json={'completed': False, 'note': 'Corrected'})
        self.assertEqual(self.client.get('/api/habits', headers=self.headers).get_json()['stats'][habit['id']]['current'], 0)
        self.assertEqual(self.client.delete(f"/api/habits/{habit['id']}", headers=self.headers).status_code, 200)
        self.assertEqual(db_state.habit_checkins_memory['habits@example.com'], {})
        self.assertEqual(self.client.put(path, headers=self.headers, json={'completed': True}).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/habits/{habit['id']}", headers=self.headers).status_code, 200)

    def test_schedule_edits_coalesce_from_tomorrow_and_preserve_today(self):
        habit = self.create(days=[4])
        path = f"/api/habits/{habit['id']}"
        self.assertEqual(self.client.put(path, headers=self.headers, json={'days': [0]}).status_code, 200)
        self.assertEqual(self.client.put(path, headers=self.headers, json={'days': [1]}).status_code, 200)
        updated = self.client.get('/api/habits', headers=self.headers).get_json()['habits'][0]
        self.assertEqual(len(updated['schedule_history']), 2)
        self.assertTrue(is_due(updated, '2026-10-09'))
        self.assertFalse(is_due(updated, '2026-10-12'))
        self.assertTrue(is_due(updated, '2026-10-13'))
        self.client.put(path, headers=self.headers, json={'archived': True})
        updated = self.client.get('/api/habits', headers=self.headers).get_json()['habits'][0]
        self.assertTrue(is_due(updated, '2026-10-09'))
        self.assertFalse(is_due(updated, '2026-10-13'))

    def test_validation_rejects_invalid_dates_days_colours_and_future_checkins(self):
        for fields in [{'days': []}, {'days': [7]}, {'days': [True]}, {'days': [1, 1]}, {'colour': 'red'},
                       {'name': ' '}, {'start_date': '2026-02-30'}, {'start_date': '2026-10-08'}, {'unknown': 'field'}]:
            data = {'name': 'Read', 'days': [4], 'start_date': '2026-10-09', **fields}
            self.assertEqual(self.client.post('/api/habits', headers=self.headers, json=data).status_code, 400, fields)
        habit = self.create(days=[4])
        for day in ['2026-10-10', '2026-10-08', '2026-02-30', '20261009']:
            self.assertEqual(self.client.put(f"/api/habits/{habit['id']}/checkins/{day}", headers=self.headers, json={'completed': True}).status_code, 400)
        self.assertEqual(self.client.put(f"/api/habits/{habit['id']}", headers=self.headers, json={'name': None}).status_code, 400)
        self.assertEqual(self.client.put('/api/habits/settings', headers=self.headers, json={'timezone': 'Mars/Olympus'}).status_code, 400)
        self.assertEqual(self.client.get('/api/habit-checkins?start=2020-01-01&end=2026-10-09', headers=self.headers).status_code, 400)
        self.assertEqual(self.client.get('/api/habit-checkins?start=bad&end=2026-10-09', headers=self.headers).status_code, 400)

    def test_reordering_renaming_and_archive_restore(self):
        first, second = self.create(), self.create(name='Walk')
        self.client.put(f"/api/habits/{second['id']}", headers=self.headers, json={'order': 0, 'name': 'Walk outside', 'colour': '#123456'})
        result = self.client.get('/api/habits', headers=self.headers).get_json()['habits']
        self.assertEqual([item['id'] for item in result], [second['id'], first['id']])
        self.assertEqual([item['order'] for item in result], [0, 1])
        self.assertEqual(result[0]['name'], 'Walk outside')
        self.client.put(f"/api/habits/{first['id']}", headers=self.headers, json={'archived': True})
        self.client.put(f"/api/habits/{first['id']}", headers=self.headers, json={'archived': False})
        result = self.client.get('/api/habits', headers=self.headers).get_json()['habits'][1]
        self.assertFalse(result['archived'])
        self.assertFalse(result['schedule_history'][-1]['archived'])

    def test_ai_drafts_use_account_context_without_saving(self):
        self.create()
        with patch('app._selected_ai_credential', return_value=({'provider': 'openai', 'model': 'gpt-5.6-sol'}, None, None)):
            self.assertEqual(self.client.post('/api/habits/draft', headers=self.headers, json={'message': 'Help me read'}).status_code, 409)
        draft = {'summary': 'A simple evening routine.', 'habits': [{'name': 'Stretch', 'description': 'Stretch briefly before bed.', 'icon': 'leaf', 'colour': '#a5c9ad', 'days': [0, 2, 4], 'category': 'Health', 'group': 'Evening'}]}
        with patch('app._selected_ai_credential', return_value=({'provider': 'mistral', 'model': 'mistral-small-2603'}, {'ciphertext': 'encrypted', 'aad_version': 2}, None)), patch('app.decrypt_api_key', return_value='key'), patch('habit_routes.draft_habits', return_value=draft) as generate:
            result = self.client.post('/api/habits/draft', headers=self.headers, json={'message': 'Build an evening routine'})
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertEqual(generate.call_args.args[1]['habits'][0]['name'], 'Read')
        self.assertEqual(generate.call_args.args[-2:], ('mistral', 'mistral-small-2603'))
        self.assertEqual(len(self.client.get('/api/habits', headers=self.headers).get_json()['habits']), 1)
        with patch('app._selected_ai_credential', return_value=({'provider': 'openai', 'model': 'gpt-5.6-sol'}, {'ciphertext': 'encrypted'}, None)), patch('app.decrypt_api_key', return_value='key'), patch('habit_routes.draft_habits', side_effect=AIBillingError('credit')):
            result = self.client.post('/api/habits/draft', headers=self.headers, json={'message': 'Read'})
        self.assertEqual(result.status_code, 402)

    def test_account_deletion_cleans_habits_and_rejects_old_token(self):
        habit = self.create()
        self.client.put(f"/api/habits/{habit['id']}/checkins/2026-10-09", headers=self.headers, json={'completed': True})
        result = self.client.delete('/api/auth/account', headers=self.headers, json={'password': 'password123'})
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertNotIn('habits@example.com', db_state.habits_memory)
        self.assertNotIn('habits@example.com', db_state.habit_checkins_memory)
        new_headers = self.register('habits@example.com')
        self.assertEqual(self.client.get('/api/habits', headers=self.headers).status_code, 401)
        self.assertEqual(self.client.get('/api/habits', headers=new_headers).get_json()['habits'], [])

    def test_generation_and_deletion_guards_fail_closed(self):
        user = db_state.auth_users_memory['habits@example.com']
        with self.assertRaises(HabitError):
            _guard(user, 'stale-account-id')
        user[ACCOUNT_DELETION_FIELD] = True
        self.assertEqual(self.client.get('/api/habits', headers=self.headers).status_code, 401)
        with self.assertRaises(HabitError):
            _operate('habits@example.com', user['account_id'], lambda state, entries: ({}, [], []))


class HabitStatisticsTests(unittest.TestCase):
    def test_streaks_skip_unscheduled_days_and_pending_today(self):
        habit = {'id': 'read', 'start_date': '2026-10-05', 'schedule_history': [{'effective_from': '2026-10-05', 'days': [0, 2, 4], 'archived': False}]}
        checkins = [{'habit_id': 'read', 'date': day, 'completed': True} for day in ['2026-10-05', '2026-10-07']]
        self.assertEqual(habit_stats(habit, checkins, date(2026, 10, 9)), {'current': 2, 'best': 2, 'rate': 100})
        self.assertEqual(habit_stats(habit, checkins, date(2026, 10, 10)), {'current': 0, 'best': 2, 'rate': 67})
        habit['schedule_history'].append({'effective_from': '2026-10-09', 'days': [0, 2, 4], 'archived': True})
        self.assertEqual(habit_stats(habit, checkins, date(2026, 10, 15))['current'], 2)


if __name__ == '__main__':
    unittest.main()
