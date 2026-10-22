"""Ensure route extraction preserves the public API and app-level behaviour."""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from app import app, create_app


CONTRACT = json.loads((Path(__file__).parent / "fixtures/api_contract.json").read_text(encoding="utf-8"))


def route_inventory(application):
    return sorted(
        [{"path": rule.rule, "methods": sorted(rule.methods - {"HEAD", "OPTIONS"})}
         for rule in application.url_map.iter_rules()],
        key=lambda item: (item["path"], item["methods"]),
    )


class ApplicationFactoryTests(unittest.TestCase):
    def test_exported_app_and_fresh_apps_preserve_every_url_and_method(self):
        for application in (app, create_app(), create_app({"TESTING": True})):
            self.assertEqual(route_inventory(application), CONTRACT["routes"])
            self.assertEqual(application.test_client().get("/").get_json(), CONTRACT["index"])

    def test_instances_have_independent_configuration_and_single_registration(self):
        first = create_app({"TESTING": True, "INSTANCE_LABEL": "first"})
        second = create_app({"TESTING": True, "INSTANCE_LABEL": "second"})
        self.assertIsNot(first, second)
        first.config["INSTANCE_LABEL"] = "changed"
        self.assertEqual(second.config["INSTANCE_LABEL"], "second")
        expected = {"auth", "ai_settings", "nutrition", "push", "aether_habits", "garmin", "health"}
        self.assertEqual(set(first.blueprints), expected)
        self.assertEqual(set(second.blueprints), expected)
        self.assertEqual(len(first.before_request_funcs[None]), 1)
        self.assertEqual(len(second.before_request_funcs[None]), 1)

    def test_health_response_and_request_logging_remain_unchanged(self):
        application = create_app({"TESTING": True})
        with patch("routes.health.get_database_status", return_value={"firestore_available": True}):
            with self.assertLogs("flask_app", level="INFO") as logs:
                result = application.test_client().get("/health")
        self.assertEqual(result.get_json(), {"status": "healthy", "database": {"firestore_available": True}})
        self.assertEqual(len(logs.records), 1)
        self.assertRegex(logs.records[0].getMessage(), r"GET /health 200 \d+\.\d+ms")

    def test_protected_endpoints_still_require_authentication(self):
        client = create_app({"TESTING": True}).test_client()
        for path in ("/api/auth/me", "/api/user/ai-settings", "/api/user/push-settings",
                     "/api/nutrition/entries", "/api/habits", "/api/garmin/connection"):
            response = client.get(path)
            self.assertEqual(response.status_code, 401, path)
            self.assertEqual(response.get_json()["status"], "error", path)
        self.assertEqual(client.get("/api/garmin/connection").headers["Cache-Control"], "no-store")

    def test_cors_preflight_still_allows_authenticated_json_requests(self):
        client = create_app({"TESTING": True}).test_client()
        for path, method in (("/api/garmin/connection", "PUT"), ("/api/user/ai-settings", "PUT"), ("/api/habits", "POST")):
            response = client.options(path, headers={
                "Origin": "https://minerva.example",
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "Authorization, Content-Type",
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["Access-Control-Allow-Origin"], "https://minerva.example")
            self.assertIn(method, response.headers["Access-Control-Allow-Methods"])
            self.assertIn("Authorization", response.headers["Access-Control-Allow-Headers"])
            self.assertIn("Content-Type", response.headers["Access-Control-Allow-Headers"])

    def test_global_json_error_handlers_apply_to_fresh_apps(self):
        application = create_app({"PROPAGATE_EXCEPTIONS": False})

        @application.get("/__synthetic_failure")
        def failure():
            raise RuntimeError("synthetic-private-detail")

        client = application.test_client()
        missing = client.get("/__missing")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.get_json(), {"status": "error", "error": "Not found"})
        with patch.object(application.logger, "error"), patch("app.logger"):
            failed = client.get("/__synthetic_failure")
        self.assertEqual(failed.status_code, 500)
        self.assertEqual(failed.get_json(), {"status": "error", "error": "Internal server error"})
        self.assertNotIn("synthetic-private-detail", failed.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
