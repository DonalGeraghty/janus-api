"""Garmin integration tests with synthetic data and transactional boundary doubles."""

import json
import time
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.error import HTTPError

import jwt

from app import app
from services import garmin_client, garmin_service
from services.firebase import db_state
from services.firebase import garmin as storage
from services.garmin_errors import GarminError

EMAIL = "garmin@example.com"
ACCOUNT = "account-one"
DAY = date.today().isoformat()
KEY = "synthetic-personal-key-1234"
TOKEN = jwt.encode({"exp": int(time.time()) + 86400}, "synthetic-test-signing-key-only")
STEPS = [{"calendarDate": DAY, "totalSteps": 4321, "stepGoal": 8000, "totalDistance": 3000}]
SLEEP = {"calendarDate": DAY, "sleepTimeSeconds": 27000, "deepSleepSeconds": 5400,
         "lightSleepSeconds": 16200, "remSleepSeconds": 5400, "awakeSleepSeconds": 600,
         "sleepScores": {"overall": {"value": 82}}}
ACTIVITIES = [{"activityId": 123, "activityName": "Morning run", "startTimeLocal": DAY + " 07:30:00",
               "activityType": {"typeKey": "running"}, "distance": 5100, "duration": 1800}]


class Reference:
    def __init__(self, records, path):
        self.records, self.path = records, path

    def collection(self, name):
        return Reference(self.records, f"{self.path}/{name}")

    def document(self, name):
        return Reference(self.records, f"{self.path}/{name}")

    def get(self, transaction=None):
        value = self.records.get(self.path)
        return SimpleNamespace(exists=value is not None, to_dict=lambda: dict(value) if value is not None else None, reference=self)

    def stream(self):
        return [Reference(self.records, key).get() for key in list(self.records) if key.startswith(self.path + "/")]


class Transaction:
    def __init__(self, records):
        self.records = records

    def set(self, ref, data):
        self.records[ref.path] = dict(data)

    def update(self, ref, data):
        self.records[ref.path].update(data)

    def delete(self, ref):
        self.records.pop(ref.path, None)


class GarminIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.records = {f"users/{EMAIL}": {"account_id": ACCOUNT}}
        self.patches = [
            patch.object(db_state, "users_collection_ref", Reference(self.records, "users")),
            patch.object(db_state, "db", SimpleNamespace(transaction=lambda: Transaction(self.records))),
            patch.object(storage.firestore, "transactional", lambda function: function),
            patch("services.garmin_service.encrypt_api_key", side_effect=lambda value, *args, **kwargs: "encrypted:" + value),
            patch("services.garmin_service.decrypt_api_key", side_effect=lambda value, *args, **kwargs: value.removeprefix("encrypted:")),
            patch("services.garmin_client.obtain_token", return_value=(TOKEN, time.time() + 86400)),
            patch("services.garmin_client.fetch_steps", return_value=STEPS),
            patch("core.request_auth.decode_access_token", side_effect=lambda token: {"email": EMAIL, "account_id": ACCOUNT} if token == "valid" else None),
            patch("core.request_auth.get_user_record", side_effect=lambda email: self.records.get(f"users/{email}")),
            patch("services.garmin_client.fetch_sleep", return_value=SLEEP),
            patch("services.garmin_client.fetch_activities", return_value=ACTIVITIES),
        ]
        self.mocks = [item.start() for item in self.patches]
        self.addCleanup(lambda: [item.stop() for item in reversed(self.patches)])
        self.client = app.test_client()
        self.headers = {"Authorization": "Bearer valid"}

    def connect(self):
        return self.client.put("/api/garmin/connection", headers=self.headers, json={"api_key": KEY})

    def steps(self, refresh=False):
        if refresh:
            return self.client.post("/api/garmin/refresh", headers=self.headers, json={"resources": ["steps"], "start": DAY, "end": DAY})
        return self.client.get(f"/api/garmin/data/steps?start={DAY}&end={DAY}", headers=self.headers)

    def sleep(self, refresh=False):
        if refresh:
            return self.client.post("/api/garmin/refresh", headers=self.headers, json={"resources": ["sleep"], "start": DAY, "end": DAY})
        return self.client.get(f"/api/garmin/data/sleep?date={DAY}", headers=self.headers)

    def activities(self, limit=5):
        return self.client.get(f"/api/garmin/data/activities?start={DAY}&end={DAY}&limit={limit}", headers=self.headers)

    def allow_refresh(self, resource="steps"):
        self.connection["retry_at"] = 0
        self.connection["resource_locks"][resource]["retry_at"] = 0

    @property
    def connection(self):
        return self.records[f"users/{EMAIL}/private/garmin"]

    def test_routes_require_janus_login_and_disable_browser_caching(self):
        for method, path in (("get", "/connection"), ("put", "/connection"), ("delete", "/connection"), ("get", "/data/steps"), ("get", "/data/sleep"), ("get", "/data/activities"), ("post", "/refresh")):
            result = getattr(self.client, method)("/api/garmin" + path)
            self.assertEqual(result.status_code, 401)
            self.assertEqual(result.headers["Cache-Control"], "no-store")

    def test_connect_encrypts_both_secrets_and_returns_safe_metadata(self):
        response = self.connect()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["connection"]["configured"])
        self.assertEqual(response.json["connection"]["last_four"], "1234")
        for secret in (KEY, TOKEN, "ciphertext", "generation"):
            self.assertNotIn(secret, response.get_data(as_text=True))
        encrypt = self.mocks[3]
        self.assertEqual(encrypt.call_count, 2)
        self.assertIn(ACCOUNT, encrypt.call_args.kwargs["provider"])
        self.assertIn(self.connection["generation"], encrypt.call_args.kwargs["provider"])

    def test_bad_replacement_preserves_working_connection(self):
        self.connect()
        previous = dict(self.connection)
        self.mocks[5].side_effect = GarminError("garmin_reconnect_required", "Invalid key", 409)
        self.assertEqual(self.connect().status_code, 409)
        self.assertEqual(self.connection, previous)

    def test_encryption_failure_never_persists_plaintext(self):
        from services.credential_service import CredentialEncryptionError
        self.mocks[3].side_effect = CredentialEncryptionError()
        self.assertEqual(self.connect().status_code, 503)
        self.assertNotIn(f"users/{EMAIL}/private/garmin", self.records)

    def test_first_fetch_persists_and_second_fetch_reuses_cache(self):
        self.connect()
        first, second = self.steps(), self.steps()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json["meta"]["source"], "garmin")
        self.assertEqual(second.json["meta"]["source"], "cache")
        self.assertEqual(second.json["data"], STEPS)
        self.mocks[6].assert_called_once()

    def test_manual_refresh_bypasses_fresh_cache_and_failed_refresh_keeps_timestamp(self):
        self.connect()
        original = self.steps().json
        self.allow_refresh()
        self.mocks[6].side_effect = GarminError("garmin_unavailable", "Unavailable")
        failed = self.steps(refresh=True)
        self.assertEqual(failed.status_code, 200)
        self.assertEqual(failed.json["data"], STEPS)
        self.assertTrue(failed.json["meta"]["stale"])
        self.assertEqual(failed.json["meta"]["fetched_at"], original["meta"]["fetched_at"])
        self.assertEqual(failed.json["meta"]["warning"]["code"], "garmin_unavailable")
        self.allow_refresh()
        self.mocks[6].side_effect = None
        self.assertEqual(self.steps(refresh=True).json["meta"]["source"], "garmin")

    def test_stale_cache_refreshes_automatically_and_empty_response_is_cached(self):
        self.connect()
        self.steps()
        cached = next(value for key, value in self.records.items() if "/garmin_cache/" in key)
        cached["fresh_until"] = 0
        self.allow_refresh()
        self.mocks[6].return_value = []
        result = self.steps()
        self.assertEqual(result.json["data"], [])
        self.assertFalse(result.json["meta"]["stale"])
        self.assertEqual(self.steps().json["data"], [])

    def test_rate_limits_suppress_repeat_upstream_requests(self):
        self.connect()
        self.mocks[6].side_effect = GarminError("garmin_rate_limited", "Wait", 429, 120)
        first = self.steps()
        self.assertEqual(first.status_code, 429)
        self.assertEqual(first.headers["Retry-After"], "120")
        self.assertEqual(self.steps().status_code, 429)
        self.mocks[6].assert_called_once()

    def test_expired_token_renews_and_revocation_does_not_log_out_janus(self):
        self.connect()
        self.connection["token_expires_at"] = 0
        self.mocks[6].side_effect = GarminError("garmin_reconnect_required", "Replace key", 409)
        result = self.steps()
        self.assertEqual(result.status_code, 409)
        self.assertEqual(self.mocks[5].call_count, 2)
        self.assertTrue(self.connection["reconnect_required"])
        self.assertEqual(self.client.get("/api/garmin/connection", headers=self.headers).status_code, 200)

    def test_disconnect_and_replacement_isolate_previous_cache(self):
        self.connect()
        self.steps()
        old_generation = self.connection["generation"]
        self.assertEqual(self.client.delete("/api/garmin/connection", headers=self.headers).status_code, 200)
        self.assertNotIn("ciphertext", self.connection)
        self.assertEqual(self.steps().status_code, 409)
        self.connect()
        self.assertNotEqual(self.connection["generation"], old_generation)
        self.assertEqual(self.steps().json["meta"]["source"], "garmin")

    def test_disconnected_or_recreated_accounts_reject_inflight_writes(self):
        self.connect()
        old = self.connection["generation"]
        garmin_service.disconnect(EMAIL, ACCOUNT)
        with self.assertRaises(GarminError):
            storage.execute(EMAIL, ACCOUNT, "finish", generation=old, lease_id="old", updates={}, cache={"data": STEPS})
        self.records[f"users/{EMAIL}"]["account_id"] = "new-account"
        with self.assertRaises(GarminError):
            storage.execute(EMAIL, ACCOUNT)

    def test_tombstone_blocks_writes_and_cleanup_removes_all_garmin_data(self):
        self.connect()
        self.steps()
        self.records[f"users/{EMAIL}/flashcards/retained"] = {"front": "Keep"}
        self.records[f"users/{EMAIL}"].update(account_deletion_in_progress=True, account_deletion_token="deleting")
        with self.assertRaises(GarminError):
            storage.execute(EMAIL, ACCOUNT)
        self.assertFalse(storage.delete_garmin_account_data(EMAIL, ACCOUNT, "wrong-token"))
        self.assertTrue(storage.delete_garmin_account_data(EMAIL, ACCOUNT, "deleting"))
        self.assertFalse(any("/garmin_cache/" in key or key.endswith("private/garmin") for key in self.records))
        self.assertIn(f"users/{EMAIL}/flashcards/retained", self.records)

    def test_storage_failure_has_no_memory_fallback(self):
        with patch.object(db_state, "db", None):
            self.assertEqual(self.connect().status_code, 503)

    def test_control_characters_and_non_ascii_keys_never_reach_garmin(self):
        for key in ("key\x00secret", "key\r\nInjected: secret", "key\u00e9"):
            result = self.client.put("/api/garmin/connection", headers=self.headers, json={"api_key": key})
            self.assertEqual(result.status_code, 400)
        self.mocks[5].assert_not_called()

    def test_another_account_cannot_read_this_connection(self):
        self.connect()
        with self.assertRaises(GarminError):
            storage.execute("other@example.com", ACCOUNT)

    def test_overlapping_refreshes_and_expired_lease_writes_are_rejected(self):
        self.connect()
        generation = self.connection["generation"]
        storage.execute(EMAIL, ACCOUNT, "claim", generation=generation, now=100, lease_id="first")
        with self.assertRaises(GarminError) as failure:
            storage.execute(EMAIL, ACCOUNT, "claim", generation=generation, now=110, lease_id="overlap")
        self.assertEqual(failure.exception.code, "garmin_rate_limited")
        storage.execute(EMAIL, ACCOUNT, "claim", generation=generation, now=170, lease_id="second")
        with self.assertRaises(GarminError):
            storage.execute(EMAIL, ACCOUNT, "finish", generation=generation, lease_id="first", updates={})

    def test_failed_cache_write_is_not_reported_as_success(self):
        self.connect()
        original = storage._apply

        def fail_save(*args):
            if args[-2] == "finish" and args[-1].get("cache") is not None:
                raise RuntimeError("database failed")
            return original(*args)

        with patch.object(storage, "_apply", side_effect=fail_save):
            self.assertEqual(self.steps().status_code, 503)
        self.assertFalse(any("/garmin_cache/" in key for key in self.records))

    def test_ranges_bodies_and_unknown_proxy_parameters_are_validated(self):
        self.assertEqual(self.client.put("/api/garmin/connection", headers=self.headers, json=[]).status_code, 400)
        for query in ("start=2026-01-01&end=2026-02-01", "start=bad&end=bad", "start=2026-01-01&end=2026-01-01&url=https://example.com"):
            self.assertEqual(self.client.get("/api/garmin/data/steps?" + query, headers=self.headers).status_code, 400)
        with self.assertRaises(GarminError):
            garmin_service.validate_range("2026-01-02", "2026-01-01")

    def test_all_three_resources_load_and_cache_independently(self):
        self.connect()
        for request, expected in ((self.steps, STEPS), (self.sleep, SLEEP), (self.activities, ACTIVITIES)):
            first, cached = request(), request()
            self.assertEqual(first.status_code, 200, first.json)
            self.assertEqual(first.json["data"], expected)
            self.assertEqual(cached.json["meta"]["source"], "cache")
        self.mocks[6].assert_called_once()
        self.mocks[9].assert_called_once()
        self.mocks[10].assert_called_once_with(TOKEN, DAY, DAY, 5)
        self.assertEqual({item["resource"] for key, item in self.records.items() if "/garmin_cache/" in key}, {"steps", "sleep", "activities"})

    def test_sleep_failure_and_cooldown_do_not_block_other_resources(self):
        self.connect()
        self.mocks[9].side_effect = GarminError("garmin_unavailable", "Sleep unavailable")
        self.assertEqual(self.sleep().status_code, 502)
        self.assertEqual(self.steps().status_code, 200)
        self.assertEqual(self.activities().status_code, 200)
        self.assertEqual(self.sleep().status_code, 429)
        self.mocks[9].assert_called_once()

    def test_failed_sleep_refresh_preserves_its_own_data_and_timestamp(self):
        self.connect()
        original = self.sleep().json
        self.allow_refresh("sleep")
        self.mocks[9].side_effect = GarminError("garmin_unavailable", "Sleep unavailable")
        saved = self.sleep(refresh=True)
        self.assertEqual(saved.json["data"], SLEEP)
        self.assertTrue(saved.json["meta"]["stale"])
        self.assertEqual(saved.json["meta"]["fetched_at"], original["meta"]["fetched_at"])
        self.assertEqual(self.activities().status_code, 200)

    def test_upstream_rate_limit_backoff_is_shared_but_fresh_cache_still_works(self):
        self.connect()
        self.steps()
        self.mocks[9].side_effect = GarminError("garmin_rate_limited", "Wait", 429, 120)
        self.assertEqual(self.sleep().status_code, 429)
        self.assertEqual(self.activities().status_code, 429)
        self.assertEqual(self.steps().json["meta"]["source"], "cache")
        self.mocks[10].assert_not_called()

    def test_resource_claims_can_overlap_and_preserve_each_others_locks(self):
        self.connect()
        generation = self.connection["generation"]
        for resource in ("steps", "sleep", "activities"):
            storage.execute(EMAIL, ACCOUNT, "claim", generation=generation, resource=resource, now=100, lease_id=resource)
        self.assertEqual(set(self.connection["resource_locks"]), {"steps", "sleep", "activities"})
        with self.assertRaises(GarminError):
            storage.execute(EMAIL, ACCOUNT, "claim", generation=generation, resource="sleep", now=101, lease_id="overlap")

    def test_successful_sibling_request_does_not_clear_authentication_failure(self):
        self.connect()
        def revoke_during_fetch(*args):
            self.connection["reconnect_required"] = True
            return ACTIVITIES
        self.mocks[10].side_effect = revoke_during_fetch
        self.assertEqual(self.activities().status_code, 200)
        self.assertTrue(self.connection["reconnect_required"])

    def test_null_sleep_and_empty_activities_are_cached_as_successes(self):
        self.connect()
        self.mocks[9].return_value = None
        self.mocks[10].return_value = []
        self.assertIsNone(self.sleep().json["data"])
        self.assertEqual(self.sleep().json["meta"]["source"], "cache")
        self.assertEqual(self.activities().json["data"], [])

    def test_activity_limits_have_separate_cache_entries(self):
        self.connect()
        self.assertEqual(self.activities(5).status_code, 200)
        self.allow_refresh("activities")
        self.assertEqual(self.activities(10).status_code, 200)
        self.assertEqual(self.activities(5).json["meta"]["source"], "cache")
        self.assertEqual(self.mocks[10].call_count, 2)

    def test_new_resource_inputs_are_bounded_and_cannot_proxy_arbitrary_urls(self):
        self.connect()
        for path in ("/data/sleep?date=bad", f"/data/sleep?date={DAY}&date={DAY}",
                     f"/data/sleep?date={DAY}&url=https://example.com", f"/data/activities?start={DAY}&end={DAY}&limit=21"):
            self.assertEqual(self.client.get('/api/garmin' + path, headers=self.headers).status_code, 400)
        for body in ({"resources": ["sleep"], "start": "2026-01-01", "end": "2026-01-02"},
                     {"resources": ["activities"], "start": DAY, "end": DAY, "limit": True},
                     {"resources": ["sleep", "steps"], "start": DAY, "end": DAY}):
            self.assertEqual(self.client.post('/api/garmin/refresh', headers=self.headers, json=body).status_code, 400)


class GarminClientTests(unittest.TestCase):
    def test_sleep_and_activity_paths_fields_and_recorded_local_dates(self):
        with patch.object(garmin_client, "_request", return_value=json.dumps(SLEEP)) as upstream:
            self.assertEqual(garmin_client.fetch_sleep(TOKEN, DAY), SLEEP)
            self.assertIn('date=' + DAY, upstream.call_args.args[0])
        with patch.object(garmin_client, "_request", return_value=json.dumps({"dailySleepDTO": SLEEP})):
            self.assertEqual(garmin_client.fetch_sleep(TOKEN, DAY)["dailySleepDTO"], SLEEP)
        with patch.object(garmin_client, "_request", return_value=json.dumps(ACTIVITIES)) as upstream:
            self.assertEqual(garmin_client.fetch_activities(TOKEN, DAY, DAY, 5), ACTIVITIES)
            self.assertIn('limit=5', upstream.call_args.args[0])
            self.assertIn('sortOrder=desc', upstream.call_args.args[0])
            self.assertIn('excludeChildren=true', upstream.call_args.args[0])

    def test_malformed_sleep_and_activities_are_rejected_without_becoming_empty_data(self):
        for body in ('[]', '{"sleepTimeSeconds":true}', '{"calendarDate":"wrong"}', '{"sleepScores":[]}'):
            with patch.object(garmin_client, "_request", return_value=body), self.assertRaises(GarminError):
                garmin_client.fetch_sleep(TOKEN, DAY)
        for data in ({}, [None], [{**ACTIVITIES[0], 'duration': True}], [ACTIVITIES[0], ACTIVITIES[0]]):
            with patch.object(garmin_client, "_request", return_value=json.dumps(data)), self.assertRaises(GarminError):
                garmin_client.fetch_activities(TOKEN, DAY, DAY, 5)

    def test_plain_text_jwt_and_steps_shape(self):
        with patch.object(garmin_client, "_request", return_value=TOKEN):
            token, expiry = garmin_client.obtain_token(KEY)
            self.assertEqual(token, TOKEN)
            self.assertGreater(expiry, time.time())
        with patch.object(garmin_client, "_request", return_value=json.dumps(STEPS)):
            self.assertEqual(garmin_client.fetch_steps(TOKEN, DAY, DAY), STEPS)

    def test_invalid_token_and_malformed_measurements_fail_safely(self):
        for body in ("not-a-token", jwt.encode({"exp": 1}, "test")):
            with patch.object(garmin_client, "_request", return_value=body), self.assertRaises(GarminError):
                garmin_client.obtain_token(KEY)
        for body in ('{}', '[null]', '[{"calendarDate":"bad"}]', json.dumps([{**STEPS[0], "totalSteps": True}])):
            with patch.object(garmin_client, "_request", return_value=body), self.assertRaises(GarminError):
                garmin_client.fetch_steps(TOKEN, DAY, DAY)

    def test_redirects_and_rate_limits_return_safe_errors_without_upstream_body(self):
        for code in (302, 401, 429, 500):
            opener = Mock()
            opener.open.side_effect = HTTPError("https://garmin", code, KEY, {"Retry-After": "90"}, None)
            with patch.object(garmin_client, "build_opener", return_value=opener), self.assertRaises(GarminError) as raised:
                garmin_client._request("/path", "Bearer " + TOKEN)
            self.assertNotIn(KEY, str(raised.exception))
            if code == 429:
                self.assertEqual(raised.exception.retry_after, 90)


if __name__ == "__main__":
    unittest.main()
