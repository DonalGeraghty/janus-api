"""Shared owner-scoped snapshot and current-rule evidence for finance reports."""
from services.finance import sync as finance_sync
from services.firebase.finance.rules import FinanceError, list_rules as list_rule_docs


def snapshot_and_rules(identity):
    snapshot = finance_sync.get_snapshot(identity["email"], identity["account_id"])
    if snapshot is None:
        raise FinanceError("Sync the ledger first (POST /api/finance/sync).", 409, details={"code": "sync_required"})
    rule_set = list_rule_docs(identity["email"], identity["account_id"], scope="janus", status="active")
    # Reports apply the current imported rules, independently of the Sheets import.
    # Describe that exact rule set without mutating the cached source snapshot.
    return {**snapshot, "rule_set_version": rule_set["rule_set_version"]}, rule_set["rules"]
