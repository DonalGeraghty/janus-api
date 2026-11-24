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
    for original in rows:
        row = classify_event(original)
        outcome = apply_rules(rules, row)
        excluded = outcome is not None and outcome["action"] == "exclude"
        # Generic transfer rules must not suppress an explicitly identified contribution or release.
        if excluded and outcome.get("field") == "type" and row.get("type") == "Transfer" and row.get("event_type") in ("sinking_contribution_outgoing", "sinking_release"):
            excluded = False
        if row.get("include_provisional_totals") != "YES":
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
                "exclusion_reason": ("sheet_inclusion_not_yes" if row.get("include_provisional_totals") != "YES" else "rule_exclusion") if excluded else None,
                "review": outcome is not None and outcome["action"] == "flag",
                "type": base_type,
                "category": category,
            },
        })
    return canonicalize(derived)


def _receipt_groups(rows):
    """Within a receipt group, count the economic total once: if one row equals the
    group's signed total (the full receipt), the allocation rows are duplicates."""
    groups = {}
    for row in rows:
        group = row.get("receipt_group_id")
        if group and not row["derived"]["excluded"]:
            groups.setdefault(group, []).append(row)
    duplicates = set()
    conflicts = []
    for group, members in groups.items():
        if len(members) < 2:
            continue
        total = sum(_dec(r.get("amount_eur")) for r in members)
        for candidate in members:
            others = sum(_dec(r.get("amount_eur")) for r in members if r is not candidate)
            if candidate.get("review_status") != "Allocation" and all(r.get("review_status") == "Allocation" for r in members if r is not candidate) and _dec(candidate.get("amount_eur")) == others:
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
        (r for r in rows if r.get("event_type") in sinking_events and not r.get("derived", {}).get("excluded") and r.get("event_type") not in ALWAYS_EXCLUDED_EVENTS),
        key=lambda r: (r.get("month") or "", r.get("date") or "", r.get("row") or 0),
    )
    balance = Decimal("0")
    opening_verified = False  # No verified opening-balance field in the production ledger.
    covered_by_row = {}
    months = {}
    for row in events:
        month = row.get("month") or "unknown"
        event = row["event_type"]
        amount = _dec(row.get("amount_eur"))
        entry = months.setdefault(month, {"contributions": Decimal("0"), "covered": Decimal("0"),
                                          "released": Decimal("0"), "bills": Decimal("0")})
        if event == "sinking_contribution_outgoing" and row.get("fund_purpose") in SINKING_PURPOSES | {"shared_sinking_fund"} and amount < 0:
            contribution = abs(amount)
            entry["contributions"] += contribution
            balance += contribution
        elif event == "covered_sinking_bill" and row.get("fund_purpose") in SINKING_PURPOSES and amount < 0:
            bill = abs(amount)
            covered = min(bill, balance)
            covered_by_row[id(row)] = covered
            entry["bills"] += bill
            entry["covered"] += covered
            balance -= covered
        elif event == "sinking_release" and amount > 0:
            reversal = min(abs(amount), balance)
            covered_by_row[id(row)] = reversal
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


def classify_event(original):
    """Recognise explicit ledger evidence; ambiguous funding never assumes coverage."""
    row = dict(original)
    if row.get("event_type"):
        return row
    text = " ".join(str(row.get(k) or "") for k in ("description", "merchant", "category", "notes", "source_references")).lower()
    status = str(row.get("review_status") or "").lower()
    amount = _dec(row.get("amount_eur"))
    kind = row.get("type")
    event = None
    purpose = None
    if status == "confirmed duplicate" or (status == "resolved duplicate" and row.get("include_provisional_totals") != "YES"):
        event = "confirmed_duplicate"
    elif status in ("reverted", "failed"):
        event = status
    elif "sinking fund" in text:
        if "release" in text and amount > 0 and kind in ("Transfer", "Refund"):
            event = "sinking_release"
        elif ("management fee" in text or "local property tax" in text or re.search(r"\blpt\b", text)) and kind == "Expense" and ("paid from sinking fund" in text or "funded by sinking fund" in text or "funded from sinking fund" in text) and "unfunded" not in text:
            event = "covered_sinking_bill"
            purpose = "apartment_management_fee" if "management fee" in text else "local_property_tax"
        elif kind in ("Transfer", "Expense") and ("contribution" in text or "allocation" in text or "transfer to sinking fund" in text or row.get("category") == "Sinking Fund" and kind == "Expense"):
            event = "sinking_contribution_outgoing" if amount < 0 else "sinking_contribution_receiving"
            purpose = "shared_sinking_fund"
        elif kind == "Transfer":
            event = "sinking_payment_transfer"
    elif kind == "Transfer":
        event = "investment_principal_transfer" if "degiro" in text or "dejiro" in text else "internal_transfer"
    if event:
        row["event_type"] = event
    if purpose:
        row["fund_purpose"] = purpose
    return row


def canonicalize(rows):
    """Compute a single effective budget amount for all downstream consumers."""
    # Conflicting eligible IDs are not resolved by arbitrary sheet order.
    ids = {}
    for row in rows:
        if row.get("transaction_id") and not row["derived"]["excluded"]:
            ids.setdefault(row["transaction_id"], []).append(row)
    seen = set()
    for row in rows:
        d = row["derived"]
        tid = row.get("transaction_id")
        if tid and len(ids.get(tid, [])) > 1:
            signatures = {tuple(r.get(k) for k in ("date", "month", "amount_eur", "type", "account", "description", "category")) for r in ids[tid]}
            if len(signatures) > 1:
                d.update(excluded=True, review=True, exclusion_reason="conflicting_transaction_id")
        if tid and tid in seen:
            d.update(excluded=True, review=True, exclusion_reason="duplicate_transaction_id")
        if row.get("event_type") in ALWAYS_EXCLUDED_EVENTS or row.get("amount_eur") is None or not row.get("date") or not row.get("month") or not tid:
            d.update(excluded=True, review=True, exclusion_reason="invalid_or_excluded_event")
        if tid and not d["excluded"]:
            seen.add(tid)
    duplicates, conflicts = _receipt_groups(rows)
    for row in rows:
        if id(row) in duplicates:
            row["derived"].update(excluded=True, exclusion_reason="receipt_allocation_duplicate")
    covered, _, _, _ = _sinking_walk(rows)
    for row in rows:
        d = row["derived"]
        event = row.get("event_type")
        amount = _dec(row.get("amount_eur"))
        effective = Decimal("0")
        investment = transfer = Decimal("0")
        if not d["excluded"]:
            if event in TRANSFER_EVENTS:
                d["type"] = "Transfer"
                transfer = amount
            elif event in INVESTMENT_EVENTS:
                d["type"] = "Transfer"
                investment = amount
            elif event == "sinking_contribution_outgoing" and row.get("fund_purpose") in SINKING_PURPOSES | {"shared_sinking_fund"} and amount < 0:
                d.update(type="Expense", category="Sinking Fund")
                effective = amount
            elif event == "covered_sinking_bill":
                d["type"] = "Expense"
                effective = amount + covered.get(id(row), Decimal("0"))
            elif event == "sinking_release":
                d.update(type="Expense", category="Sinking Fund")
                effective = covered.get(id(row), Decimal("0"))
            elif d["type"] in BUDGET_TYPES:
                effective = amount
        d.update(effective_budget_amount_eur=_money(effective), investment_amount_eur=_money(investment),
                 transfer_amount_eur=_money(transfer))
    return rows


def _scope(rows, start, end):
    months = None if start is None else set(month_list(start, end))
    return [r for r in rows if months is None or r.get("month") in months]


def _totals(rows, adjusted=True):
    totals = dict.fromkeys(("income", "spending", "refunds", "transfers", "investment"), Decimal("0"))
    count = 0
    for row in rows:
        d = row["derived"]
        if adjusted:
            totals["transfers"] += _dec(d["transfer_amount_eur"])
            totals["investment"] += _dec(d["investment_amount_eur"])
            if d["excluded"]:
                continue
            amount, kind = _dec(d["effective_budget_amount_eur"]), d["type"]
        else:
            if row.get("include_provisional_totals") != "YES" or row.get("amount_eur") is None:
                continue
            amount, kind = _dec(row["amount_eur"]), row.get("type")
        key = {"Income": "income", "Expense": "spending", "Refund": "refunds"}.get(kind)
        if key:
            totals[key] += amount
            count += 1
    totals["net"] = totals["income"] + totals["spending"] + totals["refunds"]
    return {k: _money(v) for k,v in totals.items()} | {"rows": count}


def budget_view(derived_rows, start, end):
    scope = _scope(derived_rows, start, end)
    sheet, adjusted = _totals(scope, False), _totals(scope)
    months = sorted({r["month"] for r in derived_rows if r.get("month")})
    _, conflicts = _receipt_groups(scope)
    return {"period": {"start": start, "end": end}, "sheet_totals": sheet, "adjusted_totals": adjusted,
            "reconciliation_bridge": {k: _money(_dec(adjusted[k]) - _dec(sheet[k])) for k in ("income", "spending", "refunds", "net")},
            "receipt_conflicts": conflicts, "gaps": [m for m in month_list(start, end) or [] if m not in months],
            "available_months": months, "provisional": sinking_ledger(derived_rows)["provisional"], "currency": "EUR"}


def _budget_rows(rows, start, end):
    return [r for r in _scope(rows, start, end) if not r["derived"]["excluded"] and r["derived"]["type"] in BUDGET_TYPES]


def cashflow(derived_rows, start, end, by="month"):
    if by == "month":
        return [{"month": r["month"], "net": r["net"]} for r in trends(derived_rows, start, end)]
    groups = {}
    for row in _budget_rows(derived_rows, start, end):
        d = row["derived"]
        group = groups.setdefault(row.get("month") or "unknown", {})
        key = d.get("category") or "Uncategorised"
        group[key] = group.get(key, Decimal("0")) + _dec(d["effective_budget_amount_eur"])
    return [{"month": m, "categories": {k: _money(v) for k,v in sorted(g.items())}} for m,g in sorted(groups.items())]


def aggregates(derived_rows, start, end, field):
    totals = {}
    for row in _budget_rows(derived_rows, start, end):
        d = row["derived"]
        key = (d.get(field) if field == "category" else row.get(field)) or "Unknown"
        amount, count = totals.get(key, (Decimal("0"), 0))
        totals[key] = (amount + _dec(d["effective_budget_amount_eur"]), count + 1)
    return [{"name": k, "total": _money(v), "count": n} for k,(v,n) in sorted(totals.items(), key=lambda item: item[1][0])]


def trends(derived_rows, start, end):
    groups = {}
    for row in _budget_rows(derived_rows, start, end):
        groups.setdefault(row.get("month") or "unknown", []).append(row)
    return [{"month": m, **{k: v for k,v in _totals(rows).items() if k in ("income","spending","refunds","net")}} for m,rows in sorted(groups.items())]


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
    # The production snapshot has one row per date and holdings in columns.
    asset_names = ("supersaver", "boi goalsaver", "boi current account", "revolut", "monzo",
                   "pension mercer workday", "pension efx new ireland", "pension sie zurich",
                   "dejiro", "apartment value")
    if "mortgage (owed)" in header and "date" in header:
        from .finance_sheets import parse_date, parse_money
        history, warnings = [], []
        seen_dates = set()
        for index, row in enumerate(snapshot_grid[1:], 2):
            cells = list(row) + [None] * max(0, len(header) - len(row))
            day = parse_date(cells[header.index("date")])
            if not day:
                continue
            if day in seen_dates:
                warnings.append(f"row {index}: duplicate snapshot date {day}")
                history = [h for h in history if h["date"] != day]
                continue
            seen_dates.add(day)
            def value(name):
                amount = parse_money(cells[header.index(name)]) if name in header else None
                return amount if amount is not None and amount.is_finite() else None
            holdings = {name: value(name) for name in asset_names}
            mortgage = value("mortgage (owed)")
            missing = [name for name, amount in holdings.items() if amount is None]
            if mortgage is None:
                missing.append("mortgage (owed)")
            for subtotal, names in (("cash totals", asset_names[:5]), ("pension totals", asset_names[5:8])):
                total = value(subtotal)
                if total is not None and all(holdings[n] is not None for n in names):
                    if abs(total - sum(holdings[n] for n in names)) > CENT:
                        warnings.append(f"row {index}: {subtotal} does not match holdings")
            if missing:
                warnings.append(f"row {index}: incomplete snapshot: {', '.join(missing)}")
                continue
            assets = sum(holdings.values(), Decimal("0"))
            history.append({"date": day, "assets": _money(assets), "liabilities": _money(-abs(mortgage)),
                            "net": _money(assets - abs(mortgage))})
        history.sort(key=lambda h: h["date"])
        if not history:
            return {"available": False, "reason": "no complete dated balances", "warnings": warnings}
        return {"available": True, "latest": history[-1], "history": history, "currency": "EUR",
                "warnings": warnings, "provisional": bool(warnings)}
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
