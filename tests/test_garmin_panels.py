"""Synthetic health-panel, preference ownership, and activity-detail regressions."""

import unittest
from unittest.mock import patch

from tests import test_garmin_api as fixture
from tests.test_garmin_api import EMAIL, ACCOUNT, DAY, TOKEN
from services import garmin_resources, garmin_client
from services.garmin_catalog import HEALTH_RESOURCES, PANEL_IDS
from services.firebase import garmin as storage
from services.firebase.account_state import ACCOUNT_DELETION_FIELD
from services.garmin_errors import GarminError


class GarminPanelIntegrationTests(unittest.TestCase):
    setUp = fixture.GarminIntegrationTests.setUp
    connect = fixture.GarminIntegrationTests.connect
    allow_refresh = fixture.GarminIntegrationTests.allow_refresh
    connection = fixture.GarminIntegrationTests.connection
    steps = fixture.GarminIntegrationTests.steps

    def test_all_new_routes_require_current_janus_account(self):
        for method, path in (("get", "/data/hrv"), ("get", "/preferences"), ("put", "/preferences"),
                             ("get", "/activities/123"), ("post", "/activities/123"),
                             ("get", "/activities/123/workouts")):
            result = getattr(self.client, method)("/api/garmin" + path)
            self.assertEqual(result.status_code, 401)
            self.assertEqual(result.headers["Cache-Control"], "no-store")

    def test_each_health_resource_caches_and_refreshes_independently(self):
        self.connect()
        with patch.object(garmin_resources, "fetch_health", side_effect=lambda resource, *args: {"resource": resource}) as fetch:
            for resource in sorted(HEALTH_RESOURCES):
                path = f"/api/garmin/data/{resource}?start={DAY}&end={DAY}"
                first = self.client.get(path, headers=self.headers)
                self.assertEqual(first.status_code, 200, first.json)
                self.assertEqual(first.json["data"], {"resource": resource})
                self.assertEqual(self.client.get(path, headers=self.headers).json["meta"]["source"], "cache")
                self.allow_refresh(resource)
                refreshed = self.client.post('/api/garmin/refresh', headers=self.headers,
                                             json={"resources": [resource], "start": DAY, "end": DAY})
                self.assertEqual(refreshed.status_code, 200, refreshed.json)
            self.assertEqual(fetch.call_count, len(HEALTH_RESOURCES) * 2)

    def test_panel_failure_preserves_saved_data_without_blocking_steps(self):
        self.connect()
        path = f"/api/garmin/data/weight?start={DAY}&end={DAY}"
        with patch.object(garmin_resources, "fetch_health", return_value={"dailyWeightSummaries": []}):
            original = self.client.get(path, headers=self.headers).json
        self.allow_refresh("weight")
        with patch.object(garmin_resources, "fetch_health", side_effect=GarminError("garmin_unavailable", "Unavailable")):
            result = self.client.post('/api/garmin/refresh', headers=self.headers,
                                      json={"resources": ["weight"], "start": DAY, "end": DAY})
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json["meta"]["stale"])
        self.assertEqual(result.json["meta"]["fetched_at"], original["meta"]["fetched_at"])
        self.assertEqual(self.steps().status_code, 200)

    def test_preferences_survive_disconnect_but_are_account_generation_owned(self):
        initial = self.client.get('/api/garmin/preferences', headers=self.headers)
        self.assertEqual(initial.json['preferences']['visible_panels'], list(PANEL_IDS))
        saved = self.client.put('/api/garmin/preferences', headers=self.headers, json={"visible_panels": ["sleep", "hrv"]})
        self.assertEqual(saved.status_code, 200)
        self.connect()
        self.client.delete('/api/garmin/connection', headers=self.headers)
        self.assertEqual(self.client.get('/api/garmin/preferences', headers=self.headers).json['preferences']['visible_panels'], ["sleep", "hrv"])
        self.records[f"users/{EMAIL}"]['account_id'] = 'replacement-account'
        with self.assertRaises(GarminError):
            storage.preferences(EMAIL, ACCOUNT, ['weight'])
        self.assertEqual(storage.preferences(EMAIL, 'replacement-account')['visible_panels'], list(PANEL_IDS))
        self.records[f"users/{EMAIL}"][ACCOUNT_DELETION_FIELD] = True
        with self.assertRaises(GarminError):
            storage.preferences(EMAIL, 'replacement-account', [])

    def test_preferences_validate_unknown_duplicate_and_non_string_values(self):
        for panels in (["unknown"], ["steps", "steps"], [{}], None, "steps"):
            result = self.client.put('/api/garmin/preferences', headers=self.headers, json={"visible_panels": panels})
            self.assertEqual(result.status_code, 400)
        self.assertEqual(self.client.put('/api/garmin/preferences', headers=self.headers, json={"visible_panels": []}).status_code, 200)

    def test_retired_resources_reject_reads_refreshes_and_preferences(self):
        self.connect()
        for resource in ('body-battery', 'heart-rate', 'fitness-age'):
            with self.subTest(resource=resource), patch.object(garmin_resources, 'fetch_health') as fetch:
                self.assertNotIn(resource, PANEL_IDS)
                self.assertEqual(self.client.get(f'/api/garmin/data/{resource}?start={DAY}&end={DAY}', headers=self.headers).status_code, 404)
                self.assertEqual(self.client.post('/api/garmin/refresh', headers=self.headers, json={'resources': [resource], 'start': DAY, 'end': DAY}).status_code, 400)
                self.assertEqual(self.client.put('/api/garmin/preferences', headers=self.headers, json={'visible_panels': [resource]}).status_code, 400)
                fetch.assert_not_called()

    def test_saved_preferences_drop_retired_panels_and_preserve_remaining_choices(self):
        path = f'users/{EMAIL}/garmin_settings/dashboard'
        for original, expected in [(['sleep', 'heart-rate', 'hrv', 'body-battery', 'fitness-age'], ['sleep', 'hrv']), ([], []), (['body-battery'], [])]:
            self.records[path] = {'account_id': ACCOUNT, 'visible_panels': original}
            result = self.client.get('/api/garmin/preferences', headers=self.headers)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json['preferences']['visible_panels'], expected)

    def test_activity_cache_is_separate_for_each_id_and_workouts(self):
        self.connect()
        with patch.object(garmin_resources, 'fetch_activity', side_effect=lambda token, activity_id, workouts: [] if workouts else {"activityId": activity_id}) as fetch:
            for path in ('/activities/123', '/activities/456', '/activities/123/workouts'):
                first = self.client.get('/api/garmin' + path, headers=self.headers)
                self.assertEqual(first.status_code, 200, first.json)
                self.assertEqual(self.client.get('/api/garmin' + path, headers=self.headers).json['meta']['source'], 'cache')
            self.allow_refresh('activity-summary:123')
            self.assertEqual(self.client.post('/api/garmin/activities/123', headers=self.headers).status_code, 200)
            self.assertEqual(fetch.call_count, 4)

    def test_new_inputs_cannot_select_upstream_urls_or_unbounded_ranges(self):
        self.connect()
        for path in (f'/data/hrv?start={DAY}&end={DAY}&url=https://example.com',
                     f'/data/hrv?start={DAY}&start={DAY}&end={DAY}', '/data/hrv?start=bad&end=bad',
                     '/data/hrv?start=2026-01-01&end=2026-03-01',
                     '/activities/0', '/activities/9223372036854775808', '/activities/123?url=https://example.com'):
            self.assertEqual(self.client.get('/api/garmin' + path, headers=self.headers).status_code, 400, path)
        self.assertEqual(self.client.get(f'/api/garmin/data/unknown?start={DAY}&end={DAY}', headers=self.headers).status_code, 404)
        self.assertEqual(self.client.post('/api/garmin/refresh', headers=self.headers, json={"resources": [{}], "start": DAY, "end": DAY}).status_code, 400)


class GarminPanelClientTests(unittest.TestCase):
    def test_documented_paths_and_shapes(self):
        fixtures = {
            'stress': ({"data": [{"calendarDate": DAY, "stress": {"avgLevel": 25}}]}, 'v2/dailysummaries'),
            'movement': ({"data": [{"calendarDate": DAY, "movement": {"steps": {"value": 100}}}]}, 'v2/dailysummaries'),
            'hrv': ({"hrvSummaries": [{"calendarDate": DAY, "lastNightAvg": 60}]}, 'hrv/daily/'),
            'hydration': ([{"calendarDate": DAY, "valueInML": 1500}], 'stats/hydration/daily/'),
            'weight': ({"dailyWeightSummaries": [{"summaryDate": DAY, "latestWeight": {"weight": 70}}]}, 'weight/range/'),
        }
        for resource, (data, path) in fixtures.items():
            with self.subTest(resource=resource), patch.object(garmin_resources, '_json_response', return_value=data) as upstream:
                result = garmin_resources.fetch_health(resource, TOKEN, DAY, DAY)
                self.assertIn(path, upstream.call_args_list[0].args[0])
                self.assertIsNotNone(result)

    def test_missing_data_is_successful_and_invalid_data_is_not_cached_as_empty(self):
        for resource in HEALTH_RESOURCES:
            with self.subTest(resource=resource), patch.object(garmin_resources, '_json_response', return_value=None):
                garmin_resources.fetch_health(resource, TOKEN, DAY, DAY)
            with self.subTest(resource=resource), patch.object(garmin_resources, '_json_response', return_value='private-upstream-content'):
                with self.assertRaises(GarminError) as raised:
                    garmin_resources.fetch_health(resource, TOKEN, DAY, DAY)
                self.assertNotIn('private-upstream-content', str(raised.exception))
        with patch.object(garmin_client, '_request', return_value=''):
            self.assertIsNone(garmin_client._json_response('/hrv-service/hrv/day', TOKEN))

    def test_retired_resources_never_call_garmin(self):
        for resource in ('body-battery', 'heart-rate', 'fitness-age'):
            with self.subTest(resource=resource), patch.object(garmin_resources, '_json_response') as upstream:
                with self.assertRaises(GarminError) as raised:
                    garmin_resources.fetch_health(resource, TOKEN, DAY, DAY)
                self.assertEqual(raised.exception.code, 'invalid_resource')
                upstream.assert_not_called()

    def test_upstream_log_labels_remove_activity_ids_dates_and_query_parameters(self):
        self.assertEqual(garmin_client._endpoint_label('/activity-service/activity/123456789012/workouts?token=secret'), '/activity-service/activity/{id}/workouts')
        self.assertEqual(garmin_client._endpoint_label('/hrv-service/hrv/daily/2026-10-16/2026-10-22'), '/hrv-service/hrv/daily/{date}/{date}')

    def test_activity_mismatches_and_malformed_workouts_are_rejected(self):
        for data, workouts in [({'activityId': 456}, False), ([], False), ({}, True), ([None], True)]:
            with patch.object(garmin_resources, '_json_response', return_value=data), self.assertRaises(GarminError):
                garmin_resources.fetch_activity(TOKEN, 123, workouts)
