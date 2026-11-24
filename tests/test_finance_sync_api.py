"""Finance sync: read-only Sheets pull, validation, atomic snapshot publish, stale fallback."""
import unittest
from datetime import date
from unittest.mock import patch

from app import app
from core.finance_sheets import SHEETS_EPOCH, parse_date, parse_money, rows_to_transactions
from services import google_sheets
from services.firebase import db_state


TOKEN = "ya29.synthetic-google-token-0123456789abcdef"
WORKBOOK = "1RUiRPyU2DnoXe5Tbhd6BZXMCdJtxg7FP3UQwCd2i_e0"


HEADER = ["Transaction ID", "Date", "Month", "Account", "Description", "Merchant", "Amount EUR",
          "Fee EUR", "Type", "Category", "Spending class", "Source references", "Review status",
          "Notes", "Balance EUR", "Include provisional totals", "Receipt group ID"]


def serial(y, m, d):
    return (date(y, m, d) - SHEETS_EPOCH).days + 1

SNAPSHOT_GRID = [
    ["Date", "Item", "Type", "Amount EUR", "Subtotal"],
    [serial(2026, 10, 31), "BOI current", "asset", 5200.50, "NO"],
    [serial(2026, 10, 31), "DeGiro", "asset", 12000, "NO"],
    [serial(2026, 10, 31), "Total assets", "asset", 17200.50, "YES"],
    [serial(2026, 10, 31), "Mortgage", "liability", -180000, "NO"],
    [serial(2026, 11, 30), "BOI current", "asset", 6100, "NO"],
    [serial(2026, 11, 30), "Mortgage", "liability", -179000, "NO"],
]


def grid_for(ledger, snapshot):
    def _fetch(workbook_id, range_name, token, **kwargs):
        if "combined" in range_name:
            if isinstance(ledger, Exception):
                raise ledger
            return ledger
        if isinstance(snapshot, Exception):
            raise snapshot
        return snapshot
    return _fetch


GRID = [
    HEADER,
    ["T-001", serial(2026, 11, 3), "2026-11", "BOI", "Salary", "Employer", 4000, 0, "Income", "Salary", "Income", "payslip", "Imported", "", 5200.50, "YES", ""],
    ["T-002", serial(2026, 11, 5), "2026-11", "Revolut", "Groceries", "Spar", -82.34, 0, "Expense", "Groceries", "Variable Essential", "receipt", "Matched exports", "", None, "YES", "R-1"],
    ["T-003", "2026-10-31", "2026-10", "Monzo", "Rent", "Landlord", "-950.00", 0, "Expense", "Housing", "Fixed Essential", "", "Manual only", "", None, "NO", ""],
]


class FinanceSyncApiTests(unittest.TestCase):
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
        self.fetch = patch("services.google_sheets.fetch_values", side_effect=grid_for(GRID, SNAPSHOT_GRID))
        self.fetch_mock = self.fetch.start()
        self.client = app.test_client()
        self.headers = self.register("owner@example.com")
        self.client.put("/api/finance/connection", headers=self.headers,
                        json={"access_token": TOKEN, "workbook_id": WORKBOOK})
        self.other = self.register("other@example.com")

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

    def test_sync_requires_authentication_and_connection(self):
        self.assertEqual(self.client.post("/api/finance/sync").status_code, 401)
        self.assertEqual(self.client.get("/api/finance/sync/status").status_code, 401)
        fresh = self.register("fresh@example.com")
        result = self.client.post("/api/finance/sync", headers=fresh)
        self.assertEqual(result.status_code, 403)
        self.assertEqual(result.get_json()["error"], "finance_not_connected")
        result = self.client.get("/api/finance/sync/status", headers=fresh)
        self.assertEqual(result.status_code, 403)

    def test_sync_publishes_validated_snapshot_and_status(self):
        result = self.client.post("/api/finance/sync", headers=self.headers)
        self.assertEqual(result.status_code, 201, result.get_json())
        sync = result.get_json()["sync"]
        self.assertEqual(sync["row_count"], 3)
        self.assertEqual(sync["source"], "google_sheets")
        self.assertEqual(sync["workbook_id"], WORKBOOK)
        self.assertEqual(sync["coverage"]["months"], ["2026-10", "2026-11"])
        self.assertEqual(sync["coverage"]["currency"], "EUR")
        self.assertTrue(sync["snapshot_id"])
        self.assertFalse(sync["stale"])
        self.assertEqual(google_sheets.fetch_values.call_args[0][0], WORKBOOK)

        status = self.client.get("/api/finance/sync/status", headers=self.headers).get_json()["sync"]
        self.assertEqual(status["snapshot_id"], sync["snapshot_id"])
        self.assertFalse(status["stale"])
        self.assertIsNone(status["error"])
        self.assertFalse(status["sync_required"])
        self.assertEqual(status["row_count"], 3)
        self.assertEqual(self.client.get("/api/finance/sync/status", headers=self.headers).headers["Cache-Control"], "no-store")

    def test_snapshot_tab_is_stored_and_missing_tab_warns_but_succeeds(self):
        sync = self.client.post("/api/finance/sync", headers=self.headers).get_json()["sync"]
        snapshot = db_state.finance_snapshots_memory["owner@example.com"]
        self.assertIsNotNone(snapshot["snapshot_grid"])
        self.assertEqual(sync["row_count"], 3)
        self.fetch_mock.side_effect = grid_for(GRID, google_sheets.SheetsError("workbook_not_found", 404))
        sync = self.client.post("/api/finance/sync", headers=self.headers).get_json()["sync"]
        self.assertIsNone(db_state.finance_snapshots_memory["owner@example.com"]["snapshot_grid"])
        self.assertTrue(any("snapshot tab unavailable" in w for w in sync["warnings"]))

    def test_failed_sync_retains_last_good_snapshot_with_stale_flag(self):
        first = self.client.post("/api/finance/sync", headers=self.headers).get_json()["sync"]
        self.fetch_mock.side_effect = grid_for(google_sheets.SheetsError("sheets_unreachable", 502), SNAPSHOT_GRID)
        result = self.client.post("/api/finance/sync", headers=self.headers)
        self.assertEqual(result.status_code, 502)
        self.assertEqual(result.get_json()["details"]["code"], "sheets_unreachable")
        status = self.client.get("/api/finance/sync/status", headers=self.headers).get_json()["sync"]
        self.assertTrue(status["stale"])
        self.assertEqual(status["snapshot_id"], first["snapshot_id"])
        self.assertEqual(status["error"], "sheets_unreachable")
        self.assertIsNotNone(status["last_attempt_at"])
        self.fetch_mock.side_effect = grid_for(GRID, SNAPSHOT_GRID)
        recovered = self.client.post("/api/finance/sync", headers=self.headers).get_json()["sync"]
        self.assertNotEqual(recovered["snapshot_id"], first["snapshot_id"])
        status = self.client.get("/api/finance/sync/status", headers=self.headers).get_json()["sync"]
        self.assertFalse(status["stale"])
        self.assertIsNone(status["error"])

    def test_rejected_token_maps_to_reconnect_and_workbook_404(self):
        self.client.post("/api/finance/sync", headers=self.headers)
        self.fetch_mock.side_effect = grid_for(google_sheets.SheetsError("sheets_reconnect_required", 409), SNAPSHOT_GRID)
        result = self.client.post("/api/finance/sync", headers=self.headers)
        self.assertEqual(result.status_code, 409)
        self.assertIn("Replace it in Account", result.get_json()["error"])
        self.fetch_mock.side_effect = grid_for(google_sheets.SheetsError("workbook_not_found", 404), SNAPSHOT_GRID)
        self.assertEqual(self.client.post("/api/finance/sync", headers=self.headers).status_code, 404)

    def test_validation_failure_rejects_sync_without_touching_snapshot(self):
        self.client.post("/api/finance/sync", headers=self.headers)
        self.fetch_mock.side_effect = grid_for([["Transaction ID", "Date"], ["T-1", 46000]], SNAPSHOT_GRID)
        result = self.client.post("/api/finance/sync", headers=self.headers)
        self.assertEqual(result.status_code, 422)
        self.assertIn("Missing required columns", result.get_json()["details"][0])
        status = self.client.get("/api/finance/sync/status", headers=self.headers).get_json()["sync"]
        self.assertEqual(status["error"], "validation_failed")
        self.assertTrue(status["stale"])

    def test_disconnect_clears_snapshot_and_blocks_sync(self):
        self.client.post("/api/finance/sync", headers=self.headers)
        self.assertIn("owner@example.com", db_state.finance_snapshots_memory)
        self.client.delete("/api/finance/connection", headers=self.headers)
        self.assertNotIn("owner@example.com", db_state.finance_snapshots_memory)
        self.assertNotIn("owner@example.com", db_state.finance_sync_status_memory)
        self.assertEqual(self.client.post("/api/finance/sync", headers=self.headers).status_code, 403)

    def test_account_deletion_clears_sync_state(self):
        self.client.post("/api/finance/sync", headers=self.headers)
        result = self.client.delete("/api/auth/account", headers=self.headers, json={"password": "password123"})
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertNotIn("owner@example.com", db_state.finance_snapshots_memory)
        self.assertNotIn("owner@example.com", db_state.finance_sync_status_memory)

    def test_status_before_any_sync_requests_sync(self):
        status = self.client.get("/api/finance/sync/status", headers=self.headers).get_json()["sync"]
        self.assertTrue(status["sync_required"])
        self.assertIsNone(status["snapshot_id"])
        self.assertFalse(status["stale"])


class FinanceSheetsParsingTests(unittest.TestCase):
    def test_serial_and_iso_dates_and_money(self):
        self.assertEqual(parse_date(serial(2026, 11, 24)), "2026-11-24")
        self.assertEqual(parse_date("2026-11-24"), "2026-11-24")
        self.assertIsNone(parse_date("24/11/2026"))
        self.assertIsNone(parse_date(0))
        self.assertEqual(parse_money(4000), 4000)
        self.assertEqual(parse_money("€1,234.50"), parse_money("1234.50"))
        self.assertIsNone(parse_money("abc"))

    def test_rows_map_by_header_not_position_and_flag_unknowns(self):
        shuffled = [HEADER[::-1]] + [[row[::-1] for row in GRID[1:]]][0]
        transactions, warnings, errors = rows_to_transactions(shuffled)
        self.assertEqual(errors, [])
        self.assertEqual(transactions[0]["transaction_id"], "T-001")
        self.assertEqual(transactions[0]["amount_eur"], "4000")
        self.assertEqual(transactions[0]["date"], "2026-11-03")
        self.assertEqual(transactions[2]["include_provisional_totals"], "NO")
        bad = [HEADER, ["T-9", "not-a-date", "2026-13", "BOI", "x", None, "oops", None, "Expense", None, None, None, None, None, None, "MAYBE", None]]
        transactions, warnings, errors = rows_to_transactions(bad)
        self.assertEqual(errors, [])
        self.assertIsNone(transactions[0]["date"])
        self.assertIsNone(transactions[0]["month"])
        self.assertIsNone(transactions[0]["amount_eur"])
        self.assertIsNone(transactions[0]["include_provisional_totals"])
        self.assertEqual(len(warnings), 4)
        empty, _w, errors = rows_to_transactions([[]])
        self.assertEqual(errors, ["The 'combined data' tab has no header row"])


if __name__ == "__main__":
    unittest.main()
