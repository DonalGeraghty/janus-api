import copy
import json
import unittest
from datetime import date
from types import SimpleNamespace
from decimal import Decimal
from unittest.mock import patch

from app import app
from core.finance import budget
from services.finance import sync
from services.ai_errors import AIRateLimitError
from services import ai_service
import test_finance_chat_api as chat_fixture


def proposal():
    return {"analysis": {"save_more": "Keep flexible spending tight while protecting the expected bill.", "balanced": "Allow moderate flexible spending, but treat the expected bonus as uncertain.", "breathing_room": "Leave more flexibility for groceries while protecting the expected bill."}, "assumptions": [
                {"id": "bill", "kind": "bill", "label": "Electricity", "category": "Groceries", "amount_eur": "50.00", "due_date": "2026-11-28", "status": "expected", "confidence": "medium", "evidence": "Illustrative expected bill", "basis": "history"},
                {"id": "bonus", "kind": "income", "label": "Bonus", "category": "Income", "amount_eur": "1000.00", "due_date": "2026-11-28", "status": "expected", "confidence": "low", "evidence": "An estimate rather than guaranteed income", "basis": "history"}],
            "categories": [{"category": "Groceries", "fixed": False, "remaining": {"save_more": "60.00", "balanced": "90.00", "breathing_room": "120.00"}, "confidence": "medium", "reason": "Protect the bill and adjust flexible spending."}]}


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
        response = self.plan()
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        body = response.get_json()
        plan = body["plan"]
        self.assertEqual(plan["approaches"]["balanced"]["categories"][0]["limit_eur"], "172.34")
        self.assertEqual(plan["future_income_eur"], "1000.00")
        for mode in budget.MODES:
            self.assertEqual(plan["approaches"][mode]["analysis"], proposal()["analysis"][mode])
        prompt = self.plan_mock.call_args.args[1][0]["content"]
        self.assertNotIn("user_context", json.loads(prompt))
        self.assertNotIn("forecast_eur", plan["approaches"]["balanced"]["categories"][0])
        self.assertIn("Ignore previous instructions", prompt)
        self.assertEqual(body["meta"]["provider"], "openai")
        self.assertIn("privacy", body["meta"])

    def test_analysis_is_bounded_required_and_normalized_to_one_paragraph(self):
        raw = proposal()
        raw['analysis']['balanced'] = 'One sentence.\n\nAnother sentence.'
        context = self.context()['context']
        plan = budget.validate_plan(json.dumps(raw), context)
        self.assertEqual(plan['approaches']['balanced']['analysis'], 'One sentence. Another sentence.')
        for invalid in ('', ' ' * 10, 'x' * 401):
            raw['analysis']['balanced'] = invalid
            with self.assertRaises(ValueError):
                budget.validate_plan(json.dumps(raw), context)
        del raw['analysis']['balanced']
        with self.assertRaises(ValueError):
            budget.validate_plan(json.dumps(raw), context)

    def test_missing_key_invalid_input_and_provider_error(self):
        self.harness.has_credential = False
        self.assertEqual(self.plan().status_code, 409)
        self.harness.has_credential = True
        self.assertEqual(self.plan({"cushion_eur": "NaN"}).status_code, 400)
        self.plan_mock.side_effect = AIRateLimitError("busy")
        self.assertEqual(self.plan().status_code, 502)

    def test_rejects_underfunded_bills_nonmonotonic_limits_and_missing_bill_categories(self):
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

    def test_retired_planner_inputs_are_rejected_before_provider_call(self):
        for body in ({"notes": "A trip"}, {"cushion_eur": "100"}, {"corrections": []}):
            self.assertEqual(self.plan(body).status_code, 400)
        self.plan_mock.assert_not_called()

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

    def test_retries_once_with_actionable_feedback_then_succeeds(self):
        broken = proposal()
        broken['categories'][0]['remaining']['save_more'] = '110.00'
        self.plan_mock.side_effect = [json.dumps(broken), json.dumps(proposal())]
        response = self.plan()
        self.assertEqual(response.status_code, 200, response.json)
        self.assertTrue(response.json['meta']['repair_attempted'])
        self.assertEqual(self.plan_mock.call_count, 2)
        self.assertIn('save_more <= balanced', self.plan_mock.call_args.args[1][-1]['content'])

    def test_spent_only_category_and_numeric_money_do_not_discard_plan(self):
        raw = proposal()
        raw['assumptions'] = []
        raw['categories'] = []
        self.plan_mock.return_value = json.dumps(raw)
        response = self.plan()
        self.assertEqual(response.status_code, 200)
        row = response.json['plan']['approaches']['balanced']['categories'][0]
        self.assertEqual(row['limit_eur'], '82.34')
        self.assertEqual(row['remaining_at_creation_eur'], '0.00')
        self.assertIn('no further allowance', row['reason'])
        raw = proposal()
        raw['categories'][0]['category'] = 'groceries'
        raw['categories'][0]['remaining']['balanced'] = 90.0
        self.plan_mock.return_value = json.dumps(raw)
        response = self.plan()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['plan']['approaches']['balanced']['categories'][0]['limit_eur'], '172.34')

    def test_exhausted_repair_returns_reason_without_raw_response_or_unbounded_calls(self):
        self.plan_mock.return_value = json.dumps({'private_financial_value': 'SECRET-SYNTHETIC'})
        response = self.plan()
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.plan_mock.call_count, 2)
        self.assertIn('validation_reason', response.json)
        self.assertNotIn('SECRET-SYNTHETIC', json.dumps(response.json))

    def test_import_change_during_invalid_response_prevents_repair_call(self):
        def replace(*args):
            sync.get_snapshot('owner@example.com')['snapshot_id'] = 'replacement'
            return '{}'
        self.plan_mock.side_effect = replace
        self.assertEqual(self.plan().status_code, 409)
        self.assertEqual(self.plan_mock.call_count, 1)

    def test_schema_failure_can_be_repaired_but_provider_outage_is_not_retried(self):
        from services.ai_errors import AIResponseValidationError
        self.plan_mock.side_effect = [AIResponseValidationError('Invalid budget structure.'), json.dumps(proposal())]
        self.assertEqual(self.plan().status_code, 200)
        self.plan_mock.reset_mock()
        self.plan_mock.side_effect = AIRateLimitError('busy')
        self.assertEqual(self.plan().status_code, 502)
        self.assertEqual(self.plan_mock.call_count, 1)


class BudgetProviderTests(unittest.TestCase):
    def test_budget_dispatch_requests_structured_output_from_every_provider(self):
        parsed = budget.Proposal.model_validate(proposal())
        with patch('services.openai_service.OpenAI') as sdk:
            call = sdk.return_value.responses.parse
            call.return_value = SimpleNamespace(output_parsed=parsed)
            raw = ai_service.finance_budget('system', [], 'user@example.com', 'fake-key', 'openai', 'gpt-5.6-sol')
            self.assertEqual(json.loads(raw)['categories'][0]['category'], 'Groceries')
            self.assertIs(call.call_args.kwargs['text_format'], budget.Proposal)
            self.assertFalse(call.call_args.kwargs['store'])
        with patch('services.mistral_service.Mistral') as sdk:
            call = sdk.return_value.__enter__.return_value.chat.parse
            call.return_value = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))])
            ai_service.finance_budget('system', [], 'user@example.com', 'fake-key', 'mistral', 'mistral-small-2603')
            self.assertIs(call.call_args.kwargs['response_format'], budget.Proposal)
        with patch('services.anthropic_service.Anthropic') as sdk:
            call = sdk.return_value.__enter__.return_value.messages.parse
            call.return_value = SimpleNamespace(parsed_output=parsed, stop_reason='end_turn')
            ai_service.finance_budget('system', [], 'user@example.com', 'fake-key', 'anthropic', 'claude-sonnet-5')
            self.assertIs(call.call_args.kwargs['output_format'], budget.Proposal)
            self.assertEqual(call.call_args.kwargs['max_tokens'], 10000)


if __name__ == '__main__':
    unittest.main()
