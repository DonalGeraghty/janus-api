"""Snapshot imports and ledger reports using one canonical interpretation."""

from flask import g, jsonify, request

from core.finance import calculations as finance_calc
from services.finance import sync as finance_sync
from services.firebase.finance.rules import FinanceError
from services.finance.evidence import snapshot_and_rules
from .shared import blueprint


@blueprint.post("/sync")
def ledger_sync():
    identity = g.finance_identity
    return jsonify(status="success", sync=finance_sync.sync_now(identity["email"], identity["account_id"])), 201


@blueprint.get("/sync/status")
def ledger_sync_status():
    identity = g.finance_identity
    return jsonify(status="success", sync=finance_sync.sync_status(identity["email"], identity["account_id"]))


def _period():
    try:
        return finance_calc.resolve_period(
            preset=request.args.get("period"),
            start=request.args.get("start"),
            end=request.args.get("end"),
        )
    except ValueError as error:
        raise FinanceError(str(error), 400)


def _meta(snapshot):
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "rule_set_version": snapshot["rule_set_version"],
        "source": snapshot["source"],
        "fetched_at": snapshot["fetched_at"],
        "coverage": snapshot["coverage"],
        "warnings": snapshot["warnings"][:50],
    }


def _rows(identity):
    snapshot, rules = snapshot_and_rules(identity)
    return snapshot, finance_calc.derive_rows(rules, snapshot["rows"])


@blueprint.get("/transactions")
def transactions():
    identity = g.finance_identity
    snapshot, rows = _rows(identity)
    start, end = _period()
    months = None if start is None else set(finance_calc.month_list(start, end))
    query = request.args.get("search", "").strip().lower()
    def matches(row):
        if months is not None and row.get("month") not in months:
            return False
        if request.args.get("month") and row.get("month") != request.args.get("month"):
            return False
        for field in ("type", "category", "merchant", "account"):
            wanted = request.args.get(field)
            if wanted and (row.get("derived", {}).get(field) or row.get(field) or "") != wanted:
                return False
        if query and query not in f"{row.get('description') or ''} {row.get('merchant') or ''} {row.get('transaction_id') or ''}".lower():
            return False
        return True

    result = [row for row in rows if matches(row)]
    sort_key = request.args.get("sort", "date")
    reverse = request.args.get("order", "asc") == "desc"
    if sort_key not in ("date", "amount_eur", "row", "month"):
        raise FinanceError("sort must be one of date, amount_eur, row, month", 400)
    result.sort(key=lambda r: (r.get(sort_key) or "", r.get("row") or 0), reverse=reverse)
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    if not 1 <= limit <= 200 or offset < 0:
        raise FinanceError("limit must be 1-200 and offset at least 0", 400)
    page = result[offset:offset + limit]
    return jsonify(status="success", meta=_meta(snapshot), period={"start": start, "end": end},
                   total=len(result), transactions=page)


@blueprint.get("/summary")
def summary():
    identity = g.finance_identity
    snapshot, rows = _rows(identity)
    start, end = _period()
    return jsonify(status="success", meta=_meta(snapshot), summary=finance_calc.budget_view(rows, start, end))


@blueprint.get("/cashflow")
def cashflow():
    identity = g.finance_identity
    snapshot, rows = _rows(identity)
    start, end = _period()
    by = request.args.get("by", "month")
    if by not in ("month", "category", "breakdown"):
        raise FinanceError("by must be 'month', 'category' or 'breakdown'", 400)
    return jsonify(status="success", meta=_meta(snapshot), period={"start": start, "end": end},
                   cashflow=finance_calc.cashflow(rows, start, end, by))


@blueprint.get("/categories")
def categories():
    identity = g.finance_identity
    snapshot, rows = _rows(identity)
    start, end = _period()
    return jsonify(status="success", meta=_meta(snapshot), categories=finance_calc.aggregates(rows, start, end, "category"))


@blueprint.get("/merchants")
def merchants():
    identity = g.finance_identity
    snapshot, rows = _rows(identity)
    start, end = _period()
    return jsonify(status="success", meta=_meta(snapshot), merchants=finance_calc.aggregates(rows, start, end, "merchant"))


@blueprint.get("/trends")
def trends():
    identity = g.finance_identity
    snapshot, rows = _rows(identity)
    start, end = _period()
    return jsonify(status="success", meta=_meta(snapshot), trends=finance_calc.trends(rows, start, end))


@blueprint.get("/net-worth")
def net_worth():
    identity = g.finance_identity
    snapshot, _rules = snapshot_and_rules(identity)
    return jsonify(status="success", meta=_meta(snapshot), net_worth=finance_calc.parse_net_worth(snapshot.get("snapshot_grid")))


@blueprint.get("/sinking-funds")
def sinking_funds():
    identity = g.finance_identity
    snapshot, rows = _rows(identity)
    return jsonify(status="success", meta=_meta(snapshot), sinking_funds=finance_calc.sinking_ledger(rows))


@blueprint.get("/budgets")
def budgets():
    identity = g.finance_identity
    snapshot, _rules = snapshot_and_rules(identity)
    return jsonify(status="success", meta=_meta(snapshot),
                   budgets={"available": False, "reason": "No confirmed budget tab in the ledger; budget charts stay hidden until verified budget data exists."})
