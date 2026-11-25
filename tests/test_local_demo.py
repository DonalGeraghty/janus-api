"""Exercise the isolated demo through real auth, ingestion and finance routes."""

from datetime import date
import unittest
from unittest.mock import patch

from run_demo import DEMO_EMAIL, DEMO_PASSWORD, demo_application


class LocalDemoTests(unittest.TestCase):
    def setUp(self):
        self.context = demo_application(date(2026, 11, 24))
        self.app = self.context.__enter__()
        self.addCleanup(self.context.__exit__, None, None, None)
        self.client = self.app.test_client()
        result = self.client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json["user"]["is_demo"])
        self.headers = {"Authorization": "Bearer " + result.json["token"]}

    def test_real_auth_and_synthetic_reports(self):
        self.assertEqual(self.client.get("/api/auth/me", headers=self.headers).status_code, 200)
        self.assertEqual(self.client.get("/api/finance/summary").status_code, 401)
        result = self.client.get("/api/finance/summary?start=2026-11&end=2026-11", headers=self.headers)
        self.assertEqual(result.status_code, 200, result.json)
        summary = result.json
        self.assertEqual(summary["meta"]["source"], "local_demo")
        self.assertEqual(summary["summary"]["adjusted_totals"]["net"], "1354.50")
        worth = self.client.get("/api/finance/net-worth", headers=self.headers).json
        self.assertEqual(worth["net_worth"]["latest"]["net"], "232000.00")
        for endpoint in ("transactions", "cashflow", "trends", "categories", "merchants", "rules", "sinking-funds", "budgets"):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.client.get("/api/finance/" + endpoint, headers=self.headers).status_code, 200)

    def test_sync_is_local_and_other_accounts_cannot_read_demo(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("Unexpected network")):
            result = self.client.post("/api/finance/sync", headers=self.headers)
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.json["sync"]["source"], "local_demo")
        other = self.client.post("/api/auth/register", json={"email": "other@example.test", "password": "password123"})
        result = self.client.get("/api/finance/summary", headers={"Authorization": "Bearer " + other.json["token"]})
        self.assertEqual(result.status_code, 403)

    def test_wrong_password_and_cloud_operations_are_rejected(self):
        self.assertEqual(self.client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": "wrong"}).status_code, 401)
        for path in ("/api/finance/chat", "/api/nutrition/analyze", "/api/habits/draft"):
            self.assertEqual(self.client.post(path, headers=self.headers, json={}).status_code, 403)
        for path in ("/api/finance/connection", "/api/user/ai-credentials/openai"):
            self.assertEqual(self.client.put(path, headers=self.headers, json={}).status_code, 403)

    def test_csv_rules_apply_to_ledger_and_charts_without_reimporting_data(self):
        from services.finance_sync import get_snapshot
        before = get_snapshot(DEMO_EMAIL)
        snapshot_id = before["snapshot_id"]
        csv_text = (
            "rule_id,scope,name,type,field,operator,value,action,action_value,priority,status,source_section,description\n"
            "DEMO-CATEGORY,janus,Example category,categorisation,merchant,equals,Example Market,set_category,Food,100,active,,Synthetic example\n"
            "DEMO-CLASSIFY,janus,Example classification,accounting,merchant,equals,Example Market,classify,Expense,200,active,,Synthetic example\n"
            "DEMO-FLAG,janus,Example review,reporting,merchant,equals,Example Market,flag,review,300,active,,Synthetic example\n"
            "DEMO-EXCLUDE,janus,Example exclusion,accounting,merchant,equals,Example Energy,exclude,budget_cashflow,100,active,,Synthetic example\n"
        )
        preview = self.client.post("/api/finance/rules/import", headers=self.headers,
                                   json={"csv": csv_text, "mode": "preview"})
        self.assertEqual(preview.status_code, 200, preview.json)
        self.assertEqual(get_snapshot(DEMO_EMAIL)["rule_set_version"], 0)
        result = self.client.post("/api/finance/rules/import", headers=self.headers,
                                  json={"csv": csv_text, "mode": "commit"})
        self.assertEqual(result.status_code, 201, result.json)
        version = result.json["rule_set_version"]
        for endpoint in ("transactions", "summary", "categories", "cashflow", "trends"):
            response = self.client.get(f"/api/finance/{endpoint}?period=all", headers=self.headers)
            self.assertEqual(response.status_code, 200, response.json)
            self.assertEqual(response.json["meta"]["snapshot_id"], snapshot_id)
            self.assertEqual(response.json["meta"]["rule_set_version"], version)
        rows = self.client.get("/api/finance/transactions?period=all&merchant=Example%20Market", headers=self.headers).json["transactions"]
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["category"] == "Groceries" and row["derived"]["category"] == "Food" for row in rows))
        self.assertTrue(all(row["derived"]["review"] for row in rows))
        dry_run = self.client.post("/api/finance/rules/test", headers=self.headers,
                                    json={"rows": [{k: v for k, v in row.items() if k != "derived"} for row in rows]})
        self.assertEqual(dry_run.status_code, 200, dry_run.json)
        self.assertEqual([r["derived"] for r in dry_run.json["results"]], [r["derived"] for r in rows])
        categories = self.client.get("/api/finance/categories?period=all", headers=self.headers).json["categories"]
        self.assertIn({"name": "Food", "total": "-2846.80", "count": 6}, categories)
        from decimal import Decimal
        summary = self.client.get("/api/finance/summary?period=all", headers=self.headers).json["summary"]
        self.assertEqual(summary["adjusted_totals"]["net"], "4952.70")
        self.assertEqual(summary["sheet_totals"]["net"], "4031.30")
        for endpoint, key in (("cashflow", "cashflow"), ("trends", "trends")):
            points = self.client.get(f"/api/finance/{endpoint}?period=all", headers=self.headers).json[key]
            self.assertEqual(sum(Decimal(point["net"]) for point in points), Decimal("4952.70"))
        self.assertEqual(get_snapshot(DEMO_EMAIL)["rule_set_version"], 0)  # source snapshot untouched

    def test_demo_has_realistic_positive_and_negative_months(self):
        result = self.client.get("/api/finance/cashflow?period=all", headers=self.headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual([row["net"] for row in result.json["cashflow"]],
                         ["1371.50", "-677.70", "446.00", "2305.25", "-768.25", "1354.50"])
