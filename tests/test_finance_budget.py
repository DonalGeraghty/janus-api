import copy
import json
import unittest
from importlib import import_module
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from app import app
from core.finance import budget
from services.finance import sync
from services.ai_errors import AIRateLimitError
from services import ai_service
import test_finance_chat_api as chat_fixture


def proposal():
    return {"explanation": "Recent salary covers groceries. Reserve the upcoming bill before flexible spending.",
            "assumptions": [
                {"id": "bill", "kind": "bill", "label": "Electricity", "category": "Groceries", "amount_eur": "50.00", "due_date": "2026-11-28", "status": "expected", "confidence": "medium", "evidence": "Illustrative expected bill", "basis": "history"},
                {"id": "bonus", "kind": "income", "label": "Bonus", "category": "Income", "amount_eur": "1000.00", "due_date": "2026-11-28", "status": "expected", "confidence": "low", "evidence": "An estimate rather than guaranteed income", "basis": "history"}],
            "categories": [{"category": "Groceries", "fixed": False, "expected_remaining_eur": "120.00", "remaining": {"save_more": "60.00", "balanced": "90.00", "breathing_room": "120.00"}, "confidence": "medium", "reason": "Protect the bill and adjust flexible spending."}]}


class FinanceBudgetTests(unittest.TestCase):
    def setUp(self):
        self.harness = chat_fixture.FinanceChatApiTests("test_gating")
        self.harness.setUp()
        self.addCleanup(self.harness.tearDown)
        self.client, self.headers = self.harness.client, self.harness.headers
        self.client.post("/api/finance/sync", headers=self.headers)
        self.harness.has_credential = True
        selection = patch("routes.finance.budget.selected_ai_credential", side_effect=lambda *args: (
            {"provider": "openai", "model": "gpt-5.6-sol"}, {"ciphertext": "fake"} if self.harness.has_credential else None, None))
        selection.start()
        self.addCleanup(selection.stop)
        decrypt = patch("routes.finance.budget.decrypt_api_key", return_value="test-only-key")
        decrypt.start()
        self.addCleanup(decrypt.stop)
        clock = patch("core.finance.budget.calc.today_dublin", return_value=date(2026, 11, 25))
        clock.start()
        self.addCleanup(clock.stop)
        provider = patch("routes.finance.budget.ai_service.finance_budget", return_value=json.dumps(proposal()))
        self.plan_mock = provider.start()
        self.addCleanup(provider.stop)

    def context(self):
        return self.client.get("/api/finance/budget/context", headers=self.headers).get_json()

    def plan(self, body=None):
        return self.client.post("/api/finance/budget/plan", headers=self.headers, json=body or {})

    def test_context_scope_metadata_and_unknown_cash(self):
        body = self.context()
        context = body["context"]
        self.assertEqual(context["history_start"], "2026-05")
        self.assertEqual(context["month"], "2026-11")
        self.assertEqual(len(context["missing_months"]), 6)
        self.assertEqual(context["actual"]["spent_eur"], "82.34")
        self.assertFalse(context["cash_snapshot"]["available"])
        self.assertEqual(body["meta"]["rule_set_version"], 0)
        self.assertEqual(self.client.get("/api/finance/budget/context").status_code, 401)
        self.assertEqual(self.client.get("/api/finance/budget/context", headers=self.harness.other).status_code, 403)

    def test_plans_reconcile_and_use_user_provider(self):
        response = self.plan({"notes": "Christmas gifts are already bought.", "cushion_eur": "100.00"})
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        body = response.get_json()
        plan = body["plan"]
        self.assertEqual(plan["approaches"]["balanced"]["projected_savings_eur"], "4827.66")
        self.assertEqual(plan["approaches"]["balanced"]["categories"][0]["limit_eur"], "172.34")
        self.assertEqual(plan["future_income_eur"], "1000.00")
        prompt = self.plan_mock.call_args.args[1][0]["content"]
        self.assertIn("Christmas gifts are already bought", prompt)
        self.assertIn("Ignore previous instructions", prompt)
        self.assertEqual(body["meta"]["provider"], "openai")
        self.assertIn("privacy", body["meta"])

    def test_missing_key_invalid_input_and_provider_error(self):
        self.harness.has_credential = False
        self.assertEqual(self.plan().status_code, 409)
        self.harness.has_credential = True
        self.assertEqual(self.plan({"cushion_eur": "NaN"}).status_code, 400)
        self.plan_mock.side_effect = AIRateLimitError("busy")
        self.assertEqual(self.plan().status_code, 502)

    def test_rejects_underfunded_bills_nonmonotonic_limits_and_missing_categories(self):
        for mutate in (
            lambda p: p["categories"][0]["remaining"].update(save_more="10.00"),
            lambda p: p["categories"][0]["remaining"].update(save_more="110.00"),
            lambda p: p.update(categories=[]),
            lambda p: p["categories"][0].update(fixed=True),
            lambda p: p["assumptions"][0].update(due_date="2026-12-01"),
        ):
            p = proposal()
            mutate(p)
            self.plan_mock.return_value = json.dumps(p)
            self.assertEqual(self.plan().status_code, 422)

    def test_paid_corrections_remove_future_income_and_must_be_honored(self):
        correction = proposal()["assumptions"][1]
        correction["status"] = "paid"
        body = {"corrections": [correction]}
        self.assertEqual(self.plan(body).status_code, 422)
        p = proposal()
        p["assumptions"][1] = correction
        self.plan_mock.return_value = json.dumps(p)
        self.assertEqual(self.plan(body).get_json()["plan"]["future_income_eur"], "0.00")

    def test_failed_sync_and_inflight_replacement_cannot_publish_plan(self):
        from services.firebase import db_state
        db_state.finance_sync_status_memory["owner@example.com"]["stale"] = True
        self.assertEqual(self.plan().status_code, 409)
        self.plan_mock.assert_not_called()
        db_state.finance_sync_status_memory["owner@example.com"]["stale"] = False
        def replace(*args):
            sync.get_snapshot("owner@example.com")["snapshot_id"] = "replacement"
            return json.dumps(proposal())
        self.plan_mock.side_effect = replace
        self.assertEqual(self.plan().status_code, 409)

    def test_funding_gap_is_explicit_and_no_cash_is_added(self):
        body = self.plan({"cushion_eur": "5000"}).get_json()
        self.assertEqual(body["plan"]["approaches"]["balanced"]["funding_gap_eur"], "172.34")

    def test_demo_is_explicit_and_never_calls_provider(self):
        with patch.dict(app.config, LOCAL_DEMO=True):
            response = self.plan()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["meta"]["demo"])
        self.plan_mock.assert_not_called()

    def test_history_and_future_rows_are_bounded_before_prompt(self):
        snapshot = copy.deepcopy(sync.get_snapshot("owner@example.com"))
        source = snapshot["rows"][1]
        snapshot["rows"] += [{**source, "transaction_id": "old", "month": "2026-04", "date": "2026-04-01", "merchant": "TOO OLD"},
                             {**source, "transaction_id": "future", "month": "2026-11", "date": "2026-11-30", "merchant": "FUTURE ROW"}]
        context = budget.build_context(snapshot, [], today=date(2026, 11, 25))
        self.assertNotIn("TOO OLD", json.dumps(context))
        self.assertNotIn("FUTURE ROW", json.dumps(context))
        self.assertEqual(Decimal(context["actual"]["spent_eur"]), Decimal("82.34"))


class BudgetProviderTests(unittest.TestCase):
    def test_budget_dispatch_reuses_each_provider_with_sufficient_output_room(self):
        models = {"openai": "gpt-5.6-sol", "mistral": "mistral-small-2603", "anthropic": "claude-sonnet-5"}
        for provider, model in models.items():
            adapter = import_module(f"services.{provider}_service")
            with self.subTest(provider=provider), patch.object(adapter, "finance_chat", return_value="{}") as call:
                self.assertEqual(ai_service.finance_budget("system", [], "user@example.com", "fake-key", provider, model), "{}")
                if provider == "anthropic":
                    self.assertEqual(call.call_args.kwargs["max_tokens"], 10000)


if __name__ == "__main__":
    unittest.main()
