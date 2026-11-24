"""Exercise the Firestore-backed finance code paths with a fake Firestore client.

The in-memory fallback is covered elsewhere; these tests drive the
users_collection_ref / db branches so Firestore-only bugs surface.
"""
import copy
import unittest
from unittest.mock import patch

import firebase_admin.firestore as real_firestore

from app import app
from core.auth_service import create_access_token
from services.firebase import db_state


STORE = {}


class FakeSnapshot:
    def __init__(self, ref, data):
        self.reference = ref
        self.id = ref.id
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return copy.deepcopy(self._data) if self._data is not None else None


class FakeDocRef:
    def __init__(self, path):
        self.path = path
        self.id = path.split("/")[-1]

    def collection(self, name):
        return FakeColRef(f"{self.path}/{name}")

    def get(self, transaction=None):
        return FakeSnapshot(self, STORE.get(self.path))


class FakeColRef:
    def __init__(self, path):
        self.path = path

    def document(self, doc_id):
        return FakeDocRef(f"{self.path}/{doc_id}")

    def stream(self, transaction=None):
        prefix = self.path + "/"
        return [FakeSnapshot(FakeDocRef(p), d) for p, d in sorted(STORE.items())
                if p.startswith(prefix) and "/" not in p[len(prefix):]]


class FakeTransaction:
    def get(self, ref):
        return ref.get()

    def set(self, ref, data):
        STORE[ref.path] = copy.deepcopy(data)

    def delete(self, ref):
        STORE.pop(ref.path, None)


class FakeDB:
    def transaction(self):
        return FakeTransaction()


def fake_transactional(fn):
    def wrapper(transaction, *args, **kwargs):
        return fn(transaction, *args, **kwargs)
    return wrapper


CSV_SEED = (
    "rule_id,scope,name,type,field,operator,value,action,action_value,priority,status,source_section,description\r\n"
    "A01,janus,Exclude flagged rows,accounting,include_provisional_totals,equals,NO,exclude,all_budget_totals,1000,active,4.1,Never override\r\n"
    "A05,janus,Owned account transfer,accounting,event_type,equals,internal_transfer,exclude,budget_cashflow,300,active,5,Both legs excluded\r\n"
)


class FinanceFirestoreModeTests(unittest.TestCase):
    def setUp(self):
        STORE.clear()
        db_state.users_collection_ref = FakeColRef("users")
        db_state.db = FakeDB()
        STORE["users/owner@example.com"] = {"account_id": "acc-1", "password_hash": "x"}
        for store in (db_state.auth_users_memory, db_state.finance_rules_memory,
                      db_state.finance_rule_history_memory, db_state.finance_settings_memory,
                      db_state.finance_connection_memory, db_state.finance_snapshots_memory,
                      db_state.finance_sync_status_memory):
            store.clear()
        self.transactional = patch.object(real_firestore, "transactional", fake_transactional)
        self.transactional.start()
        self.encrypt = patch("routes.finance.encrypt_api_key", return_value="fake-kms-ciphertext")
        self.encrypt.start()
        self.client = app.test_client()
        token = create_access_token("owner@example.com", "acc-1")
        self.headers = {"Authorization": f"Bearer {token}"}

    def tearDown(self):
        self.encrypt.stop()
        self.transactional.stop()
        db_state.users_collection_ref = None
        db_state.db = None
        STORE.clear()

    def test_full_finance_flow_over_firestore_path(self):
        # connect
        result = self.client.put("/api/finance/connection", headers=self.headers,
                                 json={"access_token": "ya29.synthetic-token-abcdef1234", "workbook_id": "1RUiRPyU2DnoXe5Tbhd6BZXMCdJtxg7FP3UQwCd2i_e0"})
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertTrue(result.get_json()["connection"]["connected"])
        # status readable
        self.assertEqual(self.client.get("/api/finance/connection", headers=self.headers).status_code, 200)
        # rules list (empty)
        result = self.client.get("/api/finance/rules", headers=self.headers)
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertEqual(result.get_json()["rules"], [])
        # create
        rule = {"rule_id": "T01", "scope": "janus", "name": "Ordinary spending", "type": "accounting",
                "field": "event_type", "operator": "equals", "value": "ordinary_expense",
                "action": "classify", "action_value": "Expense", "priority": 200, "status": "active",
                "source_section": "5", "description": ""}
        result = self.client.post("/api/finance/rules", headers=self.headers, json=rule)
        self.assertEqual(result.status_code, 201, result.get_json())
        # import commit
        result = self.client.post("/api/finance/rules/import", headers=self.headers, json={"csv": CSV_SEED, "mode": "commit"})
        self.assertEqual(result.status_code, 201, result.get_json())
        self.assertEqual(result.get_json()["rule_set_version"], 2)
        # list + filters
        listed = self.client.get("/api/finance/rules", headers=self.headers).get_json()
        self.assertEqual([r["rule_id"] for r in listed["rules"]], ["A01", "A05", "T01"])
        # history
        history = self.client.get("/api/finance/rules/history", headers=self.headers)
        self.assertEqual(history.status_code, 200, history.get_json())
        self.assertEqual([h["version"] for h in history.get_json()["history"]], [2, 1])
        # export
        self.assertEqual(self.client.get("/api/finance/rules/export?format=csv", headers=self.headers).status_code, 200)
        self.assertEqual(self.client.get("/api/finance/rules/export?format=json", headers=self.headers).status_code, 200)
        # dry run
        result = self.client.post("/api/finance/rules/test", headers=self.headers,
                                  json={"rows": [{"event_type": "internal_transfer"}, {"event_type": "ordinary_expense"}]})
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertEqual(result.get_json()["results"][0]["outcome"]["action"], "exclude")
        # update with revision
        result = self.client.put("/api/finance/rules/T01", headers=self.headers, json={"revision": 1, "name": "Renamed"})
        self.assertEqual(result.status_code, 200, result.get_json())
        # restore version 1 (only T01 existed then; A01/A05 become soft-deleted)
        result = self.client.post("/api/finance/rules/restore/1", headers=self.headers)
        self.assertEqual(result.status_code, 200, result.get_json())
        rules = self.client.get("/api/finance/rules", headers=self.headers).get_json()["rules"]
        self.assertEqual([r["rule_id"] for r in rules], ["T01"])
        with_deleted = self.client.get("/api/finance/rules?include_deleted=true", headers=self.headers).get_json()["rules"]
        self.assertEqual({r["rule_id"]: r["status"] for r in with_deleted if r["rule_id"] in ("A01", "A05")},
                         {"A01": "deleted", "A05": "deleted"})
        # delete + disconnect
        self.assertEqual(self.client.delete("/api/finance/rules/A05?revision=1", headers=self.headers).status_code, 200)
        result = self.client.delete("/api/finance/connection", headers=self.headers)
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertFalse(result.get_json()["connection"]["connected"])
        # after disconnect, rules are locked again
        result = self.client.get("/api/finance/rules", headers=self.headers)
        self.assertEqual(result.status_code, 403, result.get_json())


if __name__ == "__main__":
    unittest.main()
