"""Deterministic finance calculations over a synced ledger snapshot.

All money math uses Decimal; JSON serialization emits decimal strings with a
documented currency (EUR) and timezone (Europe/Dublin). Periods are whole
calendar months. Missing months are gaps, never zeros. Rule-adjusted results
are always reported next to the unmodified sheet baseline (reconciliation bridge).
"""

import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from .finance_rules import active_executable_rules, rule_matches


DUBLIN = ZoneInfo("Europe/Dublin")
CENT = Decimal("0.01")
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

PERIOD_PRESETS = ("this_month", "last_month", "last_3", "last_6", "last_12", "ytd", "all")
BUDGET_TYPES = ("Income", "Expense", "Refund")

TRANSFER_EVENTS = {"internal_transfer", "food_pot_transfer", "savings_transfer",
                   "sinking_contribution_receiving", "sinking_payment_transfer"}
INVESTMENT_EVENTS = {"investment_principal_transfer"}
SINKING_PURPOSES = {"apartment_management_fee", "local_property_tax"}
# Integrity safeguards enforced in code regardless of editable rules.
ALWAYS_EXCLUDED_EVENTS = {"confirmed_duplicate", "reverted", "failed"}


def today_dublin():
    return datetime.now(DUBLIN).date()


def _month(today, offset):
    first = today.replace(day=1)
    month = first.month - offset
    year = first.year
    while month <= 0:
        month += 12
        year -= 1
    return f"{year:04d}-{month:02d}"


def month_list(start, end):
    """Inclusive list of YYYY-MM months between two month strings (or None = unbounded)."""
    if start is None and end is None:
        return None
    first = date(int(start[:4]), int(start[5:7]), 1)
    last = date(int(end[:4]), int(end[5:7]), 1)
    months = []
    cursor = first
    while cursor <= last:
        months.append(f"{cursor.year:04d}-{cursor.month:02d}")
        cursor = date(cursor.year + (1 if cursor.month == 12 else 0), 1 if cursor.month == 12 else cursor.month + 1, 1)
    return months


def resolve_period(preset=None, start=None, end=None, today=None):
    """Resolve a preset or explicit whole-month range. Returns (start, end); (None, None) = all time."""
    today = today or today_dublin()
    if preset is None and start is None and end is None:
        preset = "this_month"
    if preset is not None:
        if preset not in PERIOD_PRESETS:
            raise ValueError(f"period must be one of {', '.join(PERIOD_PRESETS)} or start/end months")
        if start is not None or end is not None:
            raise ValueError("use either a period preset or start/end, not both")
        current = f"{today.year:04d}-{today.month:02d}"
        if preset == "this_month":
            return current, current
        if preset == "last_month":
            previous = _month(today, 1)
            return previous, previous
        if preset == "last_3":
            return _month(today, 2), current
        if preset == "last_6":
            return _month(today, 5), current
        if preset == "last_12":
            return _month(today, 11), current
        if preset == "ytd":
            return f"{today.year:04d}-01", current
        return None, None
    if start is None or end is None:
        raise ValueError("supply both start and end months (YYYY-MM)")
    if not MONTH_RE.match(start) or not MONTH_RE.match(end):
        raise ValueError("start and end must be whole months in YYYY-MM format")
    if start > end:
        raise ValueError("start must not be after end")
    return start, end


def _dec(value):
    return Decimal(str(value)) if value is not None else Decimal("0")


def _money(value):
    return format(value.quantize(CENT), "f")


def apply_rules(rules, row):
    """First matching active executable janus rule wins (priority desc, rule_id asc)."""
    for rule in active_executable_rules(rules):
        if rule_matches(rule, row):
            return rule
    return None


def derive_rows(rules, rows):
    """Attach a derived interpretation to each row. Source fields are never rewritten."""
    derived = []
    for row in rows:
        outcome = apply_rules(rules, row)
        excluded = outcome is not None and outcome["action"] == "exclude"
        if row.get("include_provisional_totals") == "NO":
            excluded = True
        base_type = row.get("type")
        if outcome is not None and outcome["action"] == "classify":
            base_type = outcome["action_value"].split(":")[0] or row.get("type")
        category = row.get("category")
        if outcome is not None and outcome["action"] == "set_category":
            category = outcome["action_value"]
        derived.append({
            **row,
            "derived": {
                "rule_id": outcome["rule_id"] if outcome else None,
                "action": outcome["action"] if outcome else None,
                "action_value": outcome["action_value"] if outcome else "",
                "excluded": excluded,
                "review": outcome is not None and outcome["action"] == "flag",
                "type": base_type,
                "category": category,
            },
        })
    return derived


def _receipt_groups(rows):
    """Within a receipt group, count the economic total once: if one row equals the
    group's signed total (the full receipt), the allocation rows are duplicates."""
    groups = {}
    for row in rows:
        group = row.get("receipt_group_id")
        if group:
            groups.setdefault(group, []).append(row)
    duplicates = set()
    conflicts = []
    for group, members in groups.items():
        if len(members) < 2:
            continue
        total = sum(_dec(r.get("amount_eur")) for r in members)
        for candidate in members:
            others = sum(_dec(r.get("amount_eur")) for r in members if r is not candidate)
            if len(members) > 1 and _dec(candidate.get("amount_eur")) == others:
                duplicates.update(id(r) for r in members if r is not candidate)
                conflicts.append(f"receipt group {group}: full receipt counted once; {len(members) - 1} allocation row(s) not double counted")
                break
        else:
            if len({(1 if _dec(r.get("amount_eur")) > 0 else -1) for r in members}) > 1:
                conflicts.append(f"receipt group {group}: conflicting allocations held for review")
    return duplicates, conflicts


def _sinking_walk(rows):
    """One chronological pass over sinking events: contributions build the recognised
    balance, covered bills consume it (unfunded portion stays an expense), releases
    reverse it once. Returns (covered_by_row_id, ending_balance, per_month, opening_verified)."""
    sinking_events = {"sinking_contribution_outgoing", "sinking_contribution_receiving",
                      "sinking_payment_transfer", "covered_sinking_bill", "sinking_release"}
    events = sorted(
        (r for r in rows if r.get("event_type") in sinking_events),
        key=lambda r: (r.get("month") or "", r.get("date") or "", r.get("row") or 0),
    )
    balance = Decimal("0")
    opening_verified = any(r.get("recognition_status") == "verified" for r in rows)
    covered_by_row = {}
    months = {}
    for row in events:
        month = row.get("month") or "unknown"
        event = row["event_type"]
        amount = _dec(row.get("amount_eur"))
        entry = months.setdefault(month, {"contributions": Decimal("0"), "covered": Decimal("0"),
                                          "released": Decimal("0"), "bills": Decimal("0")})
        if event == "sinking_contribution_outgoing" and row.get("fund_purpose") in SINKING_PURPOSES:
            contribution = abs(amount)
            entry["contributions"] += contribution
            balance += contribution
        elif event == "covered_sinking_bill":
            bill = abs(amount)
            covered = min(bill, balance)
            covered_by_row[id(row)] = covered
            entry["bills"] += bill
            entry["covered"] += covered
            balance -= covered
        elif event == "sinking_release":
            reversal = min(abs(amount), balance)
            entry["released"] += reversal
            balance -= reversal
    return covered_by_row, balance, months, opening_verified


def sinking_ledger(rows):
    """Stateful recognised-balance ledger for the sinking fund across all history.

    Only apartment management fee and LPT purposes qualify. The opening recognised
    balance is not verifiable from the ledger alone, so results are provisional:
    covered-bill exclusions are flagged, never silently applied.
    """
    _covered, balance, months, opening_verified = _sinking_walk(rows)
    return {
        "opening_verified": opening_verified,
        "provisional": not opening_verified,
        "current_recognised_balance": _money(balance),
        "months": {m: {k: _money(v) for k, v in e.items()} for m, e in sorted(months.items())},
    }


def budget_view(derived_rows, start, end):
    """Sheet baseline vs rule-adjusted budget totals over whole months."""
    months = None if start is None else set(month_list(start, end))
    in_scope = [r for r in derived_rows if months is None or r.get("month") in months]
    ledger = sinking_ledger(derived_rows)
    covered_by_row, _balance, _months, _verified = _sinking_walk(derived_rows)

    duplicates, receipt_conflicts = _receipt_groups(in_scope)

    def totals(rows, use_rules):
        income = spending = refunds = transfers = investment = Decimal("0")
        count = 0
        for row in rows:
            amount = _dec(row.get("amount_eur"))
            if amount == 0 and row.get("amount_eur") is None:
                continue
            derived = row.get("derived", {})
            if use_rules and derived.get("excluded"):
                continue
            if not use_rules and row.get("include_provisional_totals") == "NO":
                continue
            if id(row) in duplicates:
                continue
            event = row.get("event_type")
            if use_rules and event in ALWAYS_EXCLUDED_EVENTS:
                continue
            if use_rules and event in TRANSFER_EVENTS:
                transfers += amount
                continue
            if use_rules and event in INVESTMENT_EVENTS:
                investment += amount
                continue
            if use_rules and event == "sinking_contribution_outgoing" and row.get("fund_purpose") in SINKING_PURPOSES:
                spending += amount
                count += 1
                continue
            type_eff = derived.get("type") if use_rules else row.get("type")
            if event == "covered_sinking_bill" and use_rules:
                spending += -(abs(amount) - covered_by_row.get(id(row), Decimal("0")))
                count += 1
                continue
            if type_eff == "Income":
                income += amount
            elif type_eff == "Expense":
                spending += amount
            elif type_eff == "Refund":
                refunds += amount
            else:
                continue
            count += 1
        return {"income": income, "spending": spending, "refunds": refunds,
                "transfers": transfers, "investment": investment, "rows": count}

    sheet = totals(in_scope, use_rules=False)
    adjusted = totals(in_scope, use_rules=True)

    def signed(t):
        return {"income": _money(t["income"]), "spending": _money(t["spending"]),
                "refunds": _money(t["refunds"]), "net": _money(t["income"] + t["spending"] + t["refunds"]),
                "transfers": _money(t["transfers"]), "investment": _money(t["investment"]),
                "rows": t["rows"]}

    sheet_signed, adj_signed = signed(sheet), signed(adjusted)
    bridge = {key: _money(Decimal(adj_signed[key]) - Decimal(sheet_signed[key]))
              for key in ("income", "spending", "refunds", "net")}
    available_months = sorted({r.get("month") for r in derived_rows if r.get("month")})
    gaps = [m for m in (month_list(start, end) or []) if m not in available_months]
    return {
        "period": {"start": start, "end": end},
        "sheet_totals": sheet_signed,
        "adjusted_totals": adj_signed,
        "reconciliation_bridge": bridge,
        "receipt_conflicts": receipt_conflicts,
        "gaps": gaps,
        "available_months": available_months,
        "provisional": ledger["provisional"],
        "currency": "EUR",
    }


def cashflow(derived_rows, start, end, by="month"):
    months = month_list(start, end)
    scope = [r for r in derived_rows if months is None or r.get("month") in months]
    scope = [r for r in scope if not r.get("derived", {}).get("excluded")
             and r.get("include_provisional_totals") != "NO"]
    scope = [r for r in scope if r.get("derived", {}).get("type") in BUDGET_TYPES
             or r.get("event_type") == "covered_sinking_bill"]
    if by == "category":
        steps = {}
        for row in scope:
            month = row.get("month") or "unknown"
            category = row.get("derived", {}).get("category") or "Uncategorised"
            amount = _dec(row.get("amount_eur"))
            if row.get("event_type") == "covered_sinking_bill":
                continue
            entry = steps.setdefault(month, {}).setdefault(category, Decimal("0"))
            steps[month][category] = entry + amount
        return [{"month": m, "categories": {c: _money(v) for c, v in sorted(cats.items())}}
                for m, cats in sorted(steps.items())]
    monthly = {}
    for row in scope:
        month = row.get("month") or "unknown"
        amount = _dec(row.get("amount_eur"))
        monthly[month] = monthly.get(month, Decimal("0")) + amount
    return [{"month": m, "net": _money(v)} for m, v in sorted(monthly.items())]


def aggregates(derived_rows, start, end, field):
    months = month_list(start, end)
    scope = [r for r in derived_rows if (months is None or r.get("month") in months)
             and not r.get("derived", {}).get("excluded")
             and r.get("include_provisional_totals") != "NO"
             and r.get("derived", {}).get("type") in ("Expense", "Refund", "Income")]
    totals = {}
    for row in scope:
        key = row.get(field) or "Unknown"
        totals[key] = totals.get(key, Decimal("0")) + _dec(row.get("amount_eur"))
    return [{"name": k, "total": _money(v), "count": sum(1 for r in scope if (r.get(field) or "Unknown") == k)}
            for k, v in sorted(totals.items(), key=lambda item: item[1])]


def trends(derived_rows, start, end):
    months = month_list(start, end)
    scope = [r for r in derived_rows if (months is None or r.get("month") in months)
             and not r.get("derived", {}).get("excluded")
             and r.get("include_provisional_totals") != "NO"
             and r.get("derived", {}).get("type") in BUDGET_TYPES]
    per_month = {}
    for row in scope:
        month = row.get("month") or "unknown"
        amount = _dec(row.get("amount_eur"))
        type_eff = row["derived"]["type"]
        entry = per_month.setdefault(month, {"income": Decimal("0"), "spending": Decimal("0"), "refunds": Decimal("0")})
        if type_eff == "Income":
            entry["income"] += amount
        elif type_eff == "Expense":
            entry["spending"] += amount
        elif type_eff == "Refund":
            entry["refunds"] += amount
    result = []
    for month in sorted(per_month):
        entry = per_month[month]
        result.append({"month": month, "income": _money(entry["income"]), "spending": _money(entry["spending"]),
                       "refunds": _money(entry["refunds"]), "net": _money(entry["income"] + entry["spending"] + entry["refunds"])})
    return result


def parse_net_worth(snapshot_grid):
    """Parse the `snapshot` tab. Returns available=False when the schema is not recognized;
    subtotal rows are never added to individual holdings (no double counting)."""
    if not snapshot_grid:
        return {"available": False, "reason": "no snapshot tab"}
    header = [str(c).strip().lower() if c is not None else "" for c in snapshot_grid[0]]
    def col(*names):
        for name in names:
            if name in header:
                return header.index(name)
        return None
    date_col, amount_col = col("date"), col("amount eur", "balance eur", "amount", "balance")
    type_col, label_col = col("type"), col("item", "holding", "account", "description", "name")
    subtotal_col = col("subtotal", "is subtotal")
    if date_col is None or amount_col is None:
        return {"available": False, "reason": "snapshot tab missing Date or amount column"}
    from .finance_sheets import parse_date, parse_money
    per_date = {}
    for row in snapshot_grid[1:]:
        cells = list(row) + [""] * (len(header) - len(row))
        day = parse_date(cells[date_col])
        amount = parse_money(cells[amount_col])
        if day is None or amount is None:
            continue
        label = str(cells[label_col]).strip().lower() if label_col is not None and cells[label_col] else ""
        is_subtotal = subtotal_col is not None and str(cells[subtotal_col]).strip().upper() == "YES" or label.startswith("total")
        kind = str(cells[type_col]).strip().lower() if type_col is not None and cells[type_col] else ""
        entry = per_date.setdefault(day, {"assets": Decimal("0"), "liabilities": Decimal("0")})
        if is_subtotal:
            continue
        if "liab" in kind:
            entry["liabilities"] += abs(amount)
        else:
            entry["assets"] += amount
    if not per_date:
        return {"available": False, "reason": "no dated balances parsed"}
    history = [{"date": d, "assets": _money(e["assets"]), "liabilities": _money(-e["liabilities"]),
                "net": _money(e["assets"] - e["liabilities"])} for d, e in sorted(per_date.items())]
    latest = history[-1]
    return {"available": True, "latest": latest, "history": history, "currency": "EUR"}
