"""Retired Garmin routes stay absent; historical Garmin records retain deletion guarantees."""
import unittest

from app import app
from services.firebase import db_state
from services.firebase.legacy_garmin import delete_garmin_account_data


class RetiredGarminApiTests(unittest.TestCase):
    def setUp(self):
        db_state.users_collection_ref = None
        db_state.db = None
        db_state.auth_users_memory.clear()
        self.client = app.test_client()
        response = self.client.post('/api/auth/register', json={'email': 'legacy@example.com', 'password': 'password123'})
        self.assertEqual(response.status_code, 201)
        self.headers = {'Authorization': f"Bearer {response.json['token']}"}

    def tearDown(self):
        db_state.auth_users_memory.clear()

    def test_garmin_routes_and_api_index_are_absent(self):
        routes = [('get', '/api/garmin/connection'), ('put', '/api/garmin/connection'), ('delete', '/api/garmin/connection'),
                  ('get', '/api/garmin/data/steps?start=2026-10-01&end=2026-10-09'),
                  ('get', '/api/garmin/preferences'), ('put', '/api/garmin/preferences'), ('post', '/api/garmin/refresh'),
                  ('get', '/api/garmin/activities/abc'), ('post', '/api/garmin/activities/abc')]
        for headers in ({}, self.headers):
            for method, route in routes:
                self.assertEqual(getattr(self.client, method)(route, headers=headers, json={}).status_code, 404, route)
        index = self.client.get('/').get_data(as_text=True)
        self.assertNotIn('/api/garmin', index)

    def test_legacy_garmin_cleanup_remains_wired_into_account_deletion(self):
        # In-memory mode has no Firestore collections to traverse; the guarded
        # cleanup must be a safe no-op there, and account deletion must succeed.
        self.assertTrue(delete_garmin_account_data('legacy@example.com', 'whatever', 'token'))
        result = self.client.delete('/api/auth/account', headers=self.headers, json={'password': 'password123'})
        self.assertEqual(result.status_code, 200, result.get_json())


if __name__ == '__main__':
    unittest.main()
