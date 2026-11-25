"""Synthetic acceptance checks for keyless access, tenant isolation and cache races."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app import app
from core.finance.sheets import HEADER_TO_FIELD, LEDGER_RANGE
from services.finance import identity as sheets_identity
from services.firebase import db_state
from services.firebase.finance.connections import delete_finance_connection, save_finance_connection
from services.finance.sheets import SheetsError

READER = "reader@synthetic-project.iam.gserviceaccount.com"
WORKBOOK = "synthetic_finance_workbook_0123456789"
RECORD = {"Transaction ID": "synthetic-1", "Date": "2026-11-24", "Month": "2026-11",
          "Amount EUR": -10, "Type": "Expense", "Include provisional totals": "YES"}
GRID = [list(HEADER_TO_FIELD), [RECORD.get(key, "") for key in HEADER_TO_FIELD]]


class SheetsServiceAccountTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"FINANCE_SHEETS_SERVICE_ACCOUNT": READER})
        self.env.start()
        self.addCleanup(self.env.stop)
        db_state.db = db_state.users_collection_ref = None
        self.stores = [value for name, value in vars(db_state).items() if name.endswith("_memory") and isinstance(value, dict)]
        for store in self.stores:
            store.clear()
        self.addCleanup(lambda: [store.clear() for store in self.stores])
        self.client = app.test_client()
        result = self.client.post("/api/auth/register", json={"email": "reader-owner@example.com", "password": "password123"})
        self.headers = {"Authorization": "Bearer " + result.json["token"]}
        self.account_id = db_state.auth_users_memory["reader-owner@example.com"]["account_id"]
        self.approve()
        self.token = patch("services.finance.identity.access_token", return_value="synthetic-short-lived-token")
        self.token_mock = self.token.start()
        self.addCleanup(self.token.stop)
        self.fetch = patch("services.finance.sheets.fetch_values", side_effect=self.grid)
        self.fetch_mock = self.fetch.start()
        self.addCleanup(self.fetch.stop)

    def approve(self):
        db_state.finance_settings_memory.setdefault("reader-owner@example.com", {})["finance_service_account_approval"] = {
            "account_id": self.account_id, "workbook_id": WORKBOOK,
        }

    @staticmethod
    def grid(_workbook, range_name, _token, **_kwargs):
        return GRID if range_name == LEDGER_RANGE else GRID[:1] if range_name.endswith("A1:Q1") else []

    def connect(self, workbook=WORKBOOK):
        return self.client.put("/api/finance/connection", headers=self.headers,
                               json={"mode": "service_account", "workbook_id": workbook})

    def test_connection_migrates_only_after_validation_and_never_returns_credentials(self):
        save_finance_connection("reader-owner@example.com", self.account_id, "synthetic-old-ciphertext", "old4", WORKBOOK)
        self.fetch_mock.side_effect = SheetsError("workbook_not_found", 404)
        self.assertEqual(self.connect().status_code, 403)
        self.assertEqual(db_state.finance_connection_memory["reader-owner@example.com"]["ciphertext"], "synthetic-old-ciphertext")
        self.fetch_mock.side_effect = self.grid
        result = self.connect(f"https://docs.google.com/spreadsheets/d/{WORKBOOK}/edit#gid=0")
        self.assertEqual(result.status_code, 200, result.json)
        self.assertEqual(result.json["connection"]["mode"], "service_account")
        self.assertNotIn("ciphertext", db_state.finance_connection_memory["reader-owner@example.com"])
        self.assertNotIn("synthetic-short-lived-token", result.get_data(as_text=True))
        imported = self.client.post("/api/finance/sync", headers=self.headers)
        self.assertEqual(imported.status_code, 201, imported.json)
        self.assertEqual(imported.json["sync"]["row_count"], 1)
        self.assertEqual(self.client.get("/api/finance/summary?period=all", headers=self.headers).json["summary"]["adjusted_totals"]["net"], "-10.00")
        # Changing the binding invalidates an already cached snapshot, even on another worker.
        db_state.finance_settings_memory["reader-owner@example.com"]["finance_service_account_approval"]["workbook_id"] = "different-approved-workbook"
        self.assertEqual(self.client.get("/api/finance/transactions?period=all", headers=self.headers).status_code, 403)

    def test_unapproved_accounts_workbooks_and_generations_never_reach_google(self):
        for workbook in ("different_workbook_12345", "https://untrusted.example/spreadsheets/d/anything"):
            self.assertIn(self.connect(workbook).status_code, (400, 403))
        db_state.finance_settings_memory["reader-owner@example.com"]["finance_service_account_approval"]["account_id"] = "old-generation"
        self.assertEqual(self.connect().status_code, 403)
        other = self.client.post("/api/auth/register", json={"email": "different@example.com", "password": "password123"})
        response = self.client.put("/api/finance/connection", headers={"Authorization": "Bearer " + other.json["token"]},
                                   json={"workbook_id": WORKBOOK})
        self.assertEqual(response.status_code, 403)
        self.token_mock.assert_not_called()
        self.fetch_mock.assert_not_called()

    def test_inflight_import_cannot_publish_after_connection_or_account_changes(self):
        for change in ("disconnect", "replace", "recreate", "unapprove"):
            with self.subTest(change=change):
                db_state.auth_users_memory["reader-owner@example.com"]["account_id"] = self.account_id
                self.approve()
                self.fetch_mock.side_effect = self.grid
                self.assertEqual(self.connect().status_code, 200)

                def changed(workbook, range_name, token, **kwargs):
                    if range_name == LEDGER_RANGE:
                        if change == "disconnect":
                            delete_finance_connection("reader-owner@example.com", self.account_id)
                        elif change == "replace":
                            save_finance_connection("reader-owner@example.com", self.account_id, None, None, WORKBOOK, mode="service_account")
                        elif change == "recreate":
                            db_state.auth_users_memory["reader-owner@example.com"]["account_id"] = "new-account-generation"
                        else:
                            db_state.finance_settings_memory["reader-owner@example.com"].pop("finance_service_account_approval")
                    return self.grid(workbook, range_name, token, **kwargs)

                self.fetch_mock.side_effect = changed
                result = self.client.post("/api/finance/sync", headers=self.headers)
                self.assertIn(result.status_code, (401, 409), result.json)
                self.assertNotIn("reader-owner@example.com", db_state.finance_snapshots_memory)


class SheetsIdentityTests(unittest.TestCase):
    def test_credentials_refresh_with_read_only_scope_and_auth_errors_stay_private(self):
        from google.auth.exceptions import RefreshError

        credentials = SimpleNamespace(valid=False, token=None)

        def refresh(_request):
            credentials.valid, credentials.token = True, "synthetic-refreshed-token"

        credentials.refresh = Mock(side_effect=refresh)
        with (patch.dict(os.environ, {"FINANCE_SHEETS_SERVICE_ACCOUNT": READER}),
              patch.object(sheets_identity, "_credentials", None), patch.object(sheets_identity, "_target", None),
              patch("services.finance.identity.google.auth.default", return_value=(Mock(), "synthetic-project")),
              patch("services.finance.identity.impersonated_credentials.Credentials", return_value=credentials) as factory):
            self.assertEqual(sheets_identity.access_token(), "synthetic-refreshed-token")
            self.assertEqual(sheets_identity.access_token(), "synthetic-refreshed-token")
            self.assertEqual(credentials.refresh.call_count, 1)
            self.assertEqual(factory.call_args.kwargs["target_scopes"], [sheets_identity.READ_SCOPE])
            credentials.valid = False
            self.assertEqual(sheets_identity.access_token(), "synthetic-refreshed-token")
            self.assertEqual(credentials.refresh.call_count, 2)
            credentials.valid = False
            credentials.refresh.side_effect = RefreshError("synthetic-private-credential-detail")
            with self.assertRaises(sheets_identity.SheetsIdentityError) as caught:
                sheets_identity.access_token()
            self.assertNotIn("synthetic-private-credential-detail", str(caught.exception))
