"""Finance rules API: owner-only access, CRUD, CSV import/export, dry-run, history."""
import os
import unittest
from unittest.mock import patch

from app import app
from services.firebase import db_state


CSV_SEED = (
    "rule_id,scope,name,type,field,operator,value,action,action_value,priority,status,source_section,description\r\n"
    "A01,janus,Exclude flagged rows,accounting,include_provisional_totals,equals,NO,exclude,all_budget_totals,1000,active,4.1,Never override exclusions\r\n"
    "A05,janus,Owned account transfer,accounting,event_type,equals,internal_transfer,exclude,budget_cashflow,300,active,5,Both legs excluded\r\n"
    "C01,janus,Spar,categorisation,merchant,contains,Spar,set_category,Groceries,50,review,ledger sample,Suggested fallback\r\n"
)

RULE = {
    "rule_id": "T01", "scope": "janus", "name": "Ordinary spending", "type": "accounting",
    "field": "event_type", "operator": "equals", "value": "ordinary_expense",
    "action": "classify", "action_value": "Expense", "priority": 200,
    "status": "active", "source_section": "5", "description": "Negative actual spending",
}


class FinanceRulesApiTests(unittest.TestCase):
    def setUp(self):
        db_state.users_collection_ref = None
        db_state.db = None
        self.stores = (db_state.auth_users_memory, db_state.finance_rules_memory,
                       db_state.finance_rule_history_memory, db_state.finance_settings_memory)
        for store in self.stores:
            store.clear()
        self.env = patch.dict(os.environ, {"FINANCE_OWNER_EMAILS": "owner@example.com"})
        self.env.start()
        self.client = app.test_client()
        self.headers = self.register("owner@example.com")
        self.other = self.register("other@example.com")

    def tearDown(self):
        self.env.stop()
        for store in self.stores:
            store.clear()

    def register(self, email):
        result = self.client.post("/api/auth/register", json={"email": email, "password": "password123"})
        self.assertEqual(result.status_code, 201)
        return {"Authorization": f"Bearer {result.get_json()['token']}"}

    def create(self, **overrides):
        data = {**RULE, **overrides}
        result = self.client.post("/api/finance/rules", headers=self.headers, json=data)
        self.assertEqual(result.status_code, 201, result.get_json())
        return result.get_json()

    def test_all_routes_require_authentication_and_owner_entitlement(self):
        routes = [("get", "/api/finance/rules"), ("post", "/api/finance/rules"),
                  ("put", "/api/finance/rules/T01"), ("delete", "/api/finance/rules/T01"),
                  ("post", "/api/finance/rules/import"), ("get", "/api/finance/rules/export"),
                  ("post", "/api/finance/rules/test"), ("get", "/api/finance/rules/history"),
                  ("post", "/api/finance/rules/restore/1")]
        for method, path in routes:
            self.assertEqual(getattr(self.client, method)(path).status_code, 401, path)
            result = getattr(self.client, method)(path, headers=self.other, json={"csv": CSV_SEED, "mode": "preview", "rows": [{}]})
            self.assertEqual(result.status_code, 403, path)
            self.assertEqual(result.get_json()["error"], "forbidden")

    def test_responses_are_never_cached(self):
        result = self.client.get("/api/finance/rules", headers=self.headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["Cache-Control"], "no-store")

    def test_crud_with_version_checks_and_soft_delete(self):
        created = self.create()
        self.assertEqual(created["rule"]["revision"], 1)
        self.assertEqual(created["rule_set_version"], 1)
        duplicate = self.client.post("/api/finance/rules", headers=self.headers, json=RULE)
        self.assertEqual(duplicate.status_code, 409)
        listed = self.client.get("/api/finance/rules", headers=self.headers).get_json()
        self.assertEqual([rule["rule_id"] for rule in listed["rules"]], ["T01"])
        self.assertEqual(listed["rule_set_version"], 1)

        stale = self.client.put("/api/finance/rules/T01", headers=self.headers, json={"revision": 99, "name": "Stale"})
        self.assertEqual(stale.status_code, 409)
        updated = self.client.put("/api/finance/rules/T01", headers=self.headers, json={"revision": 1, "name": "Renamed", "status": "disabled"})
        self.assertEqual(updated.status_code, 200, updated.get_json())
        self.assertEqual(updated.get_json()["rule"]["revision"], 2)
        self.assertEqual(updated.get_json()["rule"]["name"], "Renamed")
        self.assertEqual(updated.get_json()["rule_set_version"], 2)

        deleted = self.client.delete("/api/finance/rules/T01?revision=2", headers=self.headers)
        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.get_json()["deleted"])
        self.assertEqual(deleted.get_json()["rule"]["status"], "deleted")
        self.assertEqual(self.client.get("/api/finance/rules", headers=self.headers).get_json()["rules"], [])
        with_deleted = self.client.get("/api/finance/rules?include_deleted=true", headers=self.headers).get_json()
        self.assertEqual(with_deleted["rules"][0]["status"], "deleted")
        again = self.client.delete("/api/finance/rules/T01", headers=self.headers)
        self.assertEqual(again.status_code, 200)
        self.assertFalse(again.get_json()["deleted"])
        self.assertEqual(self.client.put("/api/finance/rules/T01", headers=self.headers, json={"revision": 3, "name": "X"}).status_code, 404)
        self.assertEqual(self.client.delete("/api/finance/rules/MISSING", headers=self.headers).status_code, 404)

    def test_rule_payload_validation(self):
        for bad in [{**RULE, "action": "eval"}, {**RULE, "operator": "regex"},
                    {**RULE, "priority": 10**9}, {**RULE, "rule_id": "bad id!"},
                    {**RULE, "extra": 1}, {**RULE, "status": "deleted"}]:
            result = self.client.post("/api/finance/rules", headers=self.headers, json=bad)
            self.assertEqual(result.status_code, 400, bad)
        self.assertEqual(self.client.put("/api/finance/rules/T01", headers=self.headers, json={"name": "No revision"}).status_code, 400)

    def test_csv_import_preview_then_commit_is_atomic_and_versioned(self):
        preview = self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": CSV_SEED, "mode": "preview"}).get_json()
        self.assertTrue(preview["valid"])
        self.assertEqual([c["change"] for c in preview["changes"]], ["create", "create", "create"])
        self.assertEqual(preview["would_be_version"], 1)
        commit = self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": CSV_SEED, "mode": "commit"})
        self.assertEqual(commit.status_code, 201)
        self.assertEqual(commit.get_json()["rule_set_version"], 1)
        listed = self.client.get("/api/finance/rules", headers=self.headers).get_json()
        self.assertEqual([rule["rule_id"] for rule in listed["rules"]], ["A01", "A05", "C01"])
        self.assertEqual(listed["rules"][2]["status"], "review")
        repeat = self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": CSV_SEED, "mode": "commit"})
        self.assertEqual(repeat.status_code, 200)
        self.assertFalse(repeat.get_json()["committed"])
        self.assertEqual(repeat.get_json()["rule_set_version"], 1)
        changed = CSV_SEED.replace("Never override exclusions", "Never override exclusions without review")
        update = self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": changed, "mode": "commit"}).get_json()
        self.assertEqual(update["rule_set_version"], 2)
        self.assertEqual(update["changes"][0]["change"], "update")
        self.assertEqual(self.client.get("/api/finance/rules", headers=self.headers).get_json()["rules"][0]["description"],
                         "Never override exclusions without review")

    def test_csv_import_rejects_hard_errors_and_holds_unsupported_actions(self):
        duplicate = CSV_SEED + "A01,janus,Duplicate,accounting,event_type,equals,x,exclude,y,1,active,,dup\r\n"
        result = self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": duplicate, "mode": "commit"})
        self.assertEqual(result.status_code, 400)
        self.assertIn("duplicate rule_id", result.get_json()["details"][0])
        bad_header = "rule_id,scope,wrong\r\nA01,janus,x\r\n"
        self.assertEqual(self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": bad_header}).status_code, 400)

        unsupported = ("rule_id,scope,name,type,field,operator,value,action,action_value,priority,status,source_section,description\r\n"
                       "X01,janus,Unknown,accounting,event_type,equals,x,drop_everything,,10,active,,unknown action\r\n")
        preview = self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": unsupported, "mode": "preview"}).get_json()
        self.assertEqual(len(preview["held"]), 1)
        commit = self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": unsupported, "mode": "commit"}).get_json()
        rule = self.client.get("/api/finance/rules", headers=self.headers).get_json()["rules"][0]
        self.assertEqual(rule["status"], "review")
        self.assertIn("unsupported action", rule["review_reason"])
        self.assertEqual(commit["rule_set_version"], 1)

    def test_conflicting_active_rules_are_held_for_review_on_commit(self):
        conflicting = (
            "rule_id,scope,name,type,field,operator,value,action,action_value,priority,status,source_section,description\r\n"
            "K01,janus,One,accounting,event_type,equals,ambiguous,classify,Expense,500,active,,first\r\n"
            "K02,janus,Two,accounting,event_type,equals,ambiguous,exclude,budget_cashflow,500,active,,second\r\n"
        )
        preview = self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": conflicting, "mode": "preview"}).get_json()
        self.assertEqual(len(preview["conflicts"]), 1)
        self.assertEqual(sorted(preview["conflicts"][0]["rule_ids"]), ["K01", "K02"])
        self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": conflicting, "mode": "commit"})
        rules = self.client.get("/api/finance/rules", headers=self.headers).get_json()["rules"]
        self.assertTrue(all(rule["status"] == "review" for rule in rules))

    def test_export_csv_escapes_formulas_and_json_is_lossless(self):
        evil = {**RULE, "rule_id": "E01", "name": "=HYPERLINK(\"https://example.com\")"}
        self.create(**evil)
        response = self.client.get("/api/finance/rules/export?format=csv", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        text = response.get_data(as_text=True)
        self.assertIn("rule_id,scope,name", text.split("\r\n")[0])
        self.assertIn("'=HYPERLINK", text)
        self.assertNotIn("\r\n=HYPERLINK", text)
        payload = self.client.get("/api/finance/rules/export?format=json", headers=self.headers).get_json()
        self.assertEqual(payload["rules"][0]["name"], evil["name"])
        self.assertEqual(payload["rule_set_version"], 1)
        self.assertEqual(self.client.get("/api/finance/rules/export?format=xml", headers=self.headers).status_code, 400)

    def test_dry_run_applies_active_rules_deterministically(self):
        self.create()
        self.create(rule_id="T02", name="Transfers", field="event_type", operator="equals",
                    value="internal_transfer", action="exclude", action_value="budget_cashflow", priority=300)
        body = {"rows": [{"event_type": "ordinary_expense", "amount_eur": "-10"},
                         {"event_type": "internal_transfer", "amount_eur": "-500"},
                         {"event_type": "external_income", "amount_eur": "4000"}]}
        result = self.client.post("/api/finance/rules/test", headers=self.headers, json=body).get_json()
        self.assertEqual(result["results"][0]["outcome"], {"rule_id": "T01", "action": "classify", "action_value": "Expense"})
        self.assertEqual(result["results"][1]["outcome"]["action"], "exclude")
        self.assertIsNone(result["results"][2]["outcome"])
        self.assertEqual(result["results"][1]["matches"][0]["rule_id"], "T02")
        self.assertEqual(self.client.post("/api/finance/rules/test", headers=self.headers, json={"rows": []}).status_code, 400)
        self.assertEqual(self.client.post("/api/finance/rules/test", headers=self.headers, json={"rows": [{"event_type": "x"}] * 101}).status_code, 400)

    def test_history_lists_versions_and_restore_reverts_the_rule_set(self):
        self.create()
        self.client.put("/api/finance/rules/T01", headers=self.headers, json={"revision": 1, "name": "Changed"})
        history = self.client.get("/api/finance/rules/history", headers=self.headers).get_json()
        self.assertEqual([entry["version"] for entry in history["history"]], [2, 1])
        self.assertEqual(history["rule_set_version"], 2)
        restored = self.client.post("/api/finance/rules/restore/1", headers=self.headers)
        self.assertEqual(restored.status_code, 200)
        self.assertEqual(restored.get_json()["rule_set_version"], 3)
        rule = self.client.get("/api/finance/rules", headers=self.headers).get_json()["rules"][0]
        self.assertEqual(rule["name"], RULE["name"])
        self.assertEqual(rule["revision"], 3)
        self.assertEqual(self.client.post("/api/finance/rules/restore/99", headers=self.headers).status_code, 404)

    def test_list_filters_by_scope_and_status(self):
        self.create()
        self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": CSV_SEED, "mode": "commit"})
        self.assertEqual(len(self.client.get("/api/finance/rules?scope=janus", headers=self.headers).get_json()["rules"]), 4)
        self.assertEqual(len(self.client.get("/api/finance/rules?status=review", headers=self.headers).get_json()["rules"]), 1)
        self.assertEqual(self.client.get("/api/finance/rules?status=bogus", headers=self.headers).get_json()["rules"], [])

    def test_account_deletion_removes_finance_data(self):
        self.create()
        self.assertIn("owner@example.com", db_state.finance_rules_memory)
        result = self.client.delete("/api/auth/account", headers=self.headers, json={"password": "password123"})
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertNotIn("owner@example.com", db_state.finance_rules_memory)
        self.assertNotIn("owner@example.com", db_state.finance_rule_history_memory)
        self.assertNotIn("owner@example.com", db_state.finance_settings_memory)


if __name__ == "__main__":
    unittest.main()
