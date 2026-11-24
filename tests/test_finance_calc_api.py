"""Finance calculations and read API: acceptance cases, endpoints, pinning, auth."""
import unittest
from datetime import date
from unittest.mock import patch

from app import app
from core import finance_calc
from core.finance_sheets import SHEETS_EPOCH
from services import google_sheets
from services.firebase import db_state


TOKEN = "ya29.synthetic-google-token-0123456789abcdef"
WORKBOOK = "1RUiRPyU2DnoXe5Tbhd6BZXMCdJtxg7FP3UQwCd2i_e0"
HEADER = ["Transaction ID", "Date", "Month", "Account", "Description", "Merchant", "Amount EUR",
          "Fee EUR", "Type", "Category", "Spending class", "Source references", "Review status",
          "Notes", "Balance EUR", "Include provisional totals", "Receipt group ID"]


def serial(y, m, d):
    return (date(y, m, d) - SHEETS_EPOCH).days + 1


def row(**kwargs):
    base = {"row": kwargs.pop("row", 1), "transaction_id": kwargs.pop("transaction_id", "T-1"),
            "date": kwargs.pop("date", "2026-11-05"), "month": kwargs.pop("month", "2026-11"),
            "account": "BOI", "description": "x", "merchant": None, "amount_eur": "0",
            "fee_eur": None, "type": "Expense", "category": "General", "spending_class": None,
            "source_references": None, "review_status": "Imported", "notes": None, "balance_eur": None,
            "include_provisional_totals": "YES", "receipt_group_id": None}
    base.update(kwargs)
    return base


def derived(rows, rules=()):
    return finance_calc.derive_rows(list(rules), rows)


def totals(rows, start=None, end=None):
    return finance_calc.budget_view(derived(rows), start, end)["adjusted_totals"]


class AcceptanceCaseTests(unittest.TestCase):
    def test_salary_and_ordinary_purchase(self):
        t = totals([row(transaction_id="a", type="Income", amount_eur="4000"),
                    row(transaction_id="b", type="Expense", amount_eur="-10", merchant="Shop")])
        self.assertEqual(t["income"], "4000.00")
        self.assertEqual(t["spending"], "-10.00")
        self.assertEqual(t["net"], "3990.00")

    def test_owned_transfer_both_legs_zero_budget(self):
        t = totals([row(transaction_id="a", type="Transfer", amount_eur="-500", event_type="internal_transfer"),
                    row(transaction_id="b", type="Transfer", amount_eur="500", event_type="internal_transfer")])
        self.assertEqual(t["income"], "0.00")
        self.assertEqual(t["spending"], "0.00")
        self.assertEqual(t["net"], "0.00")

    def test_food_pot_contribution_excluded_purchase_counts(self):
        t = totals([row(transaction_id="a", type="Transfer", amount_eur="-100", event_type="food_pot_transfer"),
                    row(transaction_id="b", type="Expense", amount_eur="-20", merchant="Spar")])
        self.assertEqual(t["spending"], "-20.00")

    def test_sinking_contribution_counted_once(self):
        t = totals([row(transaction_id="a", type="Transfer", amount_eur="-220", event_type="sinking_contribution_outgoing", fund_purpose="local_property_tax"),
                    row(transaction_id="b", type="Transfer", amount_eur="220", event_type="sinking_contribution_receiving", fund_purpose="local_property_tax")])
        self.assertEqual(t["spending"], "-220.00")

    def test_covered_bill_fully_and_partially_funded(self):
        rows = [row(transaction_id="c", type="Transfer", amount_eur="-2000", event_type="sinking_contribution_outgoing", fund_purpose="apartment_management_fee", month="2026-10", date="2026-10-01"),
                row(transaction_id="b1", type="Expense", amount_eur="-2000", event_type="covered_sinking_bill", fund_purpose="apartment_management_fee", month="2026-11", date="2026-11-01")]
        self.assertEqual(totals(rows)["spending"], "-2000.00")  # only the contribution; bill fully covered
        rows[0]["amount_eur"] = "-1800"
        self.assertEqual(totals(rows)["spending"], "-2000.00")  # -1800 contribution + -200 unfunded

    def test_sinking_opening_balance_unknown_is_provisional(self):
        ledger = finance_calc.sinking_ledger(derived([row(event_type="covered_sinking_bill", amount_eur="-2000", fund_purpose="apartment_management_fee")]))
        self.assertTrue(ledger["provisional"])
        self.assertFalse(ledger["opening_verified"])

    def test_release_reverses_once(self):
        rows = [row(transaction_id="c", type="Transfer", amount_eur="-100", event_type="sinking_contribution_outgoing", fund_purpose="local_property_tax"),
                row(transaction_id="r", type="Transfer", amount_eur="100", event_type="sinking_release", fund_purpose="local_property_tax")]
        self.assertEqual(totals(rows)["spending"], "-100.00")
        ledger = finance_calc.sinking_ledger(derived(rows))
        self.assertEqual(ledger["current_recognised_balance"], "0.00")

    def test_investment_principal_is_not_consumption_or_income(self):
        t = totals([row(type="Transfer", amount_eur="-1000", event_type="investment_principal_transfer", merchant="DeGiro")])
        self.assertEqual(t["spending"], "0.00")
        self.assertEqual(t["investment"], "-1000.00")

    def test_refund_offsets_spending_and_mortgage_is_full_outflow(self):
        t = totals([row(type="Expense", amount_eur="-50", merchant="Shop"),
                    row(type="Refund", amount_eur="50"),
                    row(type="Expense", amount_eur="-1200", category="Housing")])
        self.assertEqual(t["spending"], "-1250.00")
        self.assertEqual(t["refunds"], "50.00")
        self.assertEqual(t["net"], "-1200.00")

    def test_excluded_flag_and_confirmed_duplicate(self):
        t = totals([row(amount_eur="-10", include_provisional_totals="NO"),
                    row(amount_eur="-10", event_type="confirmed_duplicate")])
        self.assertEqual(t["spending"], "0.00")

    def test_identical_legitimate_purchases_not_deduplicated(self):
        t = totals([row(transaction_id="a", amount_eur="-10", merchant="Shop", date="2026-11-05"),
                    row(transaction_id="b", amount_eur="-10", merchant="Shop", date="2026-11-06")])
        self.assertEqual(t["spending"], "-20.00")

    def test_receipt_group_counted_once(self):
        t = totals([row(transaction_id="full", amount_eur="-30", receipt_group_id="R-9", type="Expense"),
                    row(transaction_id="i1", amount_eur="-10", receipt_group_id="R-9", type="Expense", review_status="Allocation"),
                    row(transaction_id="i2", amount_eur="-20", receipt_group_id="R-9", type="Expense", review_status="Allocation")])
        self.assertEqual(t["spending"], "-30.00")

    def test_fee_not_subtracted_twice(self):
        t = totals([row(amount_eur="-10", fee_eur="2")])
        self.assertEqual(t["spending"], "-10.00")

    def test_missing_month_is_a_gap_not_zero(self):
        view = finance_calc.budget_view(derived([row(month="2026-11", amount_eur="-5")]), "2026-10", "2026-11")
        self.assertEqual(view["gaps"], ["2026-10"])

    def test_period_presets_and_validation(self):
        today = date(2026, 11, 24)
        self.assertEqual(finance_calc.resolve_period("this_month", today=today), ("2026-11", "2026-11"))
        self.assertEqual(finance_calc.resolve_period("last_month", today=today), ("2026-10", "2026-10"))
        self.assertEqual(finance_calc.resolve_period("last_3", today=today), ("2026-09", "2026-11"))
        self.assertEqual(finance_calc.resolve_period("ytd", today=today), ("2026-01", "2026-11"))
        self.assertEqual(finance_calc.resolve_period("all", today=today), (None, None))
        self.assertEqual(finance_calc.resolve_period(start="2026-01", end="2026-03", today=today), ("2026-01", "2026-03"))
        for bad in ({"preset": "nope"}, {"start": "2026-13", "end": "2026-12"}, {"start": "2026-05", "end": "2026-01"}, {"preset": "all", "start": "2026-01"}):
            with self.assertRaises(ValueError):
                finance_calc.resolve_period(today=today, **bad)

    def test_net_worth_avoids_subtotal_double_count(self):
        grid = [["Date", "Item", "Type", "Amount EUR", "Subtotal"],
                [serial(2026, 10, 31), "BOI", "asset", 5000, "NO"],
                [serial(2026, 10, 31), "DeGiro", "asset", 12000, "NO"],
                [serial(2026, 10, 31), "Total assets", "asset", 17000, "YES"],
                [serial(2026, 10, 31), "Mortgage", "liability", -180000, "NO"]]
        result = finance_calc.parse_net_worth(grid)
        self.assertTrue(result["available"])
        self.assertEqual(result["latest"]["assets"], "17000.00")
        self.assertEqual(result["latest"]["net"], "-163000.00")
        self.assertEqual(finance_calc.parse_net_worth([["A", "B"]])["available"], False)
        self.assertEqual(finance_calc.parse_net_worth(None)["available"], False)


GRID = [
    HEADER,
    ["T-001", serial(2026, 11, 3), "2026-11", "BOI", "Salary", "Employer", 4000, 0, "Income", "Salary", "Income", "payslip", "Imported", "", 5200.50, "YES", ""],
    ["T-002", serial(2026, 11, 5), "2026-11", "Revolut", "Groceries", "Spar", -82.34, 0, "Expense", "Groceries", "Variable Essential", "receipt", "Matched exports", "", None, "YES", "R-1"],
    ["T-003", "2026-10-31", "2026-10", "Monzo", "Rent", "Landlord", "-950.00", 0, "Expense", "Housing", "Fixed Essential", "", "Manual only", "", None, "YES", ""],
]
SNAPSHOT_GRID = [["Date", "Item", "Type", "Amount EUR", "Subtotal"],
                 [serial(2026, 11, 30), "BOI", "asset", 6100, "NO"],
                 [serial(2026, 11, 30), "Total assets", "asset", 6100, "YES"],
                 [serial(2026, 11, 30), "Mortgage", "liability", -179000, "NO"]]


def grid_for(ledger, snapshot=SNAPSHOT_GRID):
    def _fetch(workbook_id, range_name, token, **kwargs):
        return ledger if "combined" in range_name else snapshot
    return _fetch


class FinanceReadApiTests(unittest.TestCase):
    def setUp(self):
        db_state.users_collection_ref = None
        db_state.db = None
        self.stores = (db_state.auth_users_memory, db_state.finance_rules_memory,
                       db_state.finance_rule_history_memory, db_state.finance_settings_memory,
                       db_state.finance_connection_memory, db_state.finance_snapshots_memory,
                       db_state.finance_sync_status_memory)
        for store in self.stores:
            store.clear()
        self.encrypt = patch("routes.finance.encrypt_api_key", return_value="fake-kms-ciphertext")
        self.encrypt.start()
        self.token = patch("services.finance_sync._load_token", return_value=TOKEN)
        self.token.start()
        self.fetch = patch("services.google_sheets.fetch_values", side_effect=grid_for(GRID))
        self.fetch_mock = self.fetch.start()
        self.client = app.test_client()
        self.headers = self.register("owner@example.com")
        self.client.put("/api/finance/connection", headers=self.headers,
                        json={"access_token": TOKEN, "workbook_id": WORKBOOK})
        self.other = self.register("other@example.com")
        self.client.post("/api/finance/sync", headers=self.headers)

    def tearDown(self):
        self.fetch.stop()
        self.token.stop()
        self.encrypt.stop()
        for store in self.stores:
            store.clear()

    def register(self, email):
        result = self.client.post("/api/auth/register", json={"email": email, "password": "password123"})
        self.assertEqual(result.status_code, 201)
        return {"Authorization": f"Bearer {result.get_json()['token']}"}

    def test_read_endpoints_require_auth_connection_and_sync(self):
        for path in ("/api/finance/transactions", "/api/finance/summary", "/api/finance/cashflow",
                     "/api/finance/categories", "/api/finance/merchants", "/api/finance/trends",
                     "/api/finance/net-worth", "/api/finance/sinking-funds", "/api/finance/budgets"):
            self.assertEqual(self.client.get(path).status_code, 401, path)
            self.assertEqual(self.client.get(path, headers=self.other).status_code, 403, path)
        fresh = self.register("fresh@example.com")
        self.client.put("/api/finance/connection", headers=fresh, json={"access_token": TOKEN, "workbook_id": WORKBOOK})
        result = self.client.get("/api/finance/summary", headers=fresh)
        self.assertEqual(result.status_code, 409, result.get_json())
        self.assertEqual(result.get_json()["details"]["code"], "sync_required")

    def test_transactions_filter_paginate_and_pin_versions(self):
        result = self.client.get("/api/finance/transactions?period=all&limit=2", headers=self.headers)
        self.assertEqual(result.status_code, 200)
        body = result.get_json()
        self.assertEqual(body["total"], 3)
        self.assertEqual(len(body["transactions"]), 2)
        self.assertEqual(body["meta"]["snapshot_id"], db_state.finance_snapshots_memory["owner@example.com"]["snapshot_id"])
        self.assertIn("rule_set_version", body["meta"])
        self.assertEqual(result.headers["Cache-Control"], "no-store")
        page2 = self.client.get("/api/finance/transactions?period=all&limit=2&offset=2", headers=self.headers).get_json()
        self.assertEqual(len(page2["transactions"]), 1)
        filtered = self.client.get("/api/finance/transactions?period=all&merchant=Spar", headers=self.headers).get_json()
        self.assertEqual(filtered["total"], 1)
        by_month = self.client.get("/api/finance/transactions?period=all&month=2026-10", headers=self.headers).get_json()
        self.assertEqual(by_month["total"], 1)
        self.assertEqual(self.client.get("/api/finance/transactions?limit=500", headers=self.headers).status_code, 400)
        self.assertEqual(self.client.get("/api/finance/transactions?period=bogus", headers=self.headers).status_code, 400)

    def test_summary_cashflow_categories_merchants_trends(self):
        summary = self.client.get("/api/finance/summary?period=all", headers=self.headers).get_json()["summary"]
        self.assertEqual(summary["adjusted_totals"]["income"], "4000.00")
        self.assertEqual(summary["adjusted_totals"]["spending"], "-1032.34")
        self.assertEqual(summary["sheet_totals"]["spending"], "-1032.34")
        self.assertIn("reconciliation_bridge", summary)
        self.assertEqual(summary["gaps"], [])
        flow = self.client.get("/api/finance/cashflow?period=all", headers=self.headers).get_json()["cashflow"]
        self.assertEqual({f["month"]: f["net"] for f in flow}, {"2026-10": "-950.00", "2026-11": "3917.66"})
        cats = self.client.get("/api/finance/categories?period=all", headers=self.headers).get_json()["categories"]
        self.assertIn({"name": "Groceries", "total": "-82.34", "count": 1}, cats)
        merchants = self.client.get("/api/finance/merchants?period=all", headers=self.headers).get_json()["merchants"]
        self.assertTrue(any(m["name"] == "Spar" for m in merchants))
        trends = self.client.get("/api/finance/trends?period=all", headers=self.headers).get_json()["trends"]
        self.assertEqual(len(trends), 2)
        self.assertEqual(self.client.get("/api/finance/cashflow?by=bogus", headers=self.headers).status_code, 400)

    def test_net_worth_sinking_and_budgets_states(self):
        worth = self.client.get("/api/finance/net-worth", headers=self.headers).get_json()["net_worth"]
        self.assertTrue(worth["available"])
        self.assertEqual(worth["latest"]["assets"], "6100.00")
        self.assertEqual(worth["latest"]["net"], "-172900.00")
        sinking = self.client.get("/api/finance/sinking-funds", headers=self.headers).get_json()["sinking_funds"]
        self.assertTrue(sinking["provisional"])
        budgets = self.client.get("/api/finance/budgets", headers=self.headers).get_json()["budgets"]
        self.assertFalse(budgets["available"])

    def test_rules_apply_to_summary_with_reason_per_row(self):
        rule = {"rule_id": "A05", "scope": "janus", "name": "Transfers", "type": "accounting",
                "field": "type", "operator": "equals", "value": "Transfer",
                "action": "exclude", "action_value": "budget_cashflow", "priority": 300,
                "status": "active", "source_section": "5", "description": ""}
        self.client.post("/api/finance/rules", headers=self.headers, json=rule)
        self.client.post("/api/finance/sync", headers=self.headers)
        self.fetch_mock.side_effect = grid_for(GRID + [["T-004", serial(2026, 11, 6), "2026-11", "BOI", "Transfer out", "BOI savings", "-500", 0, "Transfer", "", "", "", "Manual only", "", None, "YES", ""]])
        self.client.post("/api/finance/sync", headers=self.headers)
        rows = self.client.get("/api/finance/transactions?period=all&type=Transfer", headers=self.headers).get_json()["transactions"]
        self.assertEqual(rows[0]["derived"]["rule_id"], "A05")
        self.assertTrue(rows[0]["derived"]["excluded"])
        summary = self.client.get("/api/finance/summary?period=all", headers=self.headers).get_json()["summary"]
        self.assertEqual(summary["adjusted_totals"]["spending"], "-1032.34")
        self.assertEqual(summary["sheet_totals"]["spending"], "-1032.34")


if __name__ == "__main__":
    unittest.main()
