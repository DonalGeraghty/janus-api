"""Parsing and validation for the read-only Google Sheets finance ledger.

The `combined data` tab is read A:Q but mapped by header name, never by fixed
position. Sheets native values arrive with UNFORMATTED_VALUE: numbers as JSON
numbers and dates as 1900-system serial numbers. Money is kept as Decimal and
serialized as decimal strings; unknown values stay null, never zero.
"""

import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation


SHEETS_EPOCH = date(1899, 12, 30)  # Google Sheets 1900 date system
LEDGER_RANGE = "'combined data'!A:Q"
CURRENCY = "EUR"
TIMEZONE = "Europe/Dublin"
MAX_ROWS = 50_000

HEADER_TO_FIELD = {
    "Transaction ID": "transaction_id",
    "Date": "date",
    "Month": "month",
    "Account": "account",
    "Description": "description",
    "Merchant": "merchant",
    "Amount EUR": "amount_eur",
    "Fee EUR": "fee_eur",
    "Type": "type",
    "Category": "category",
    "Spending class": "spending_class",
    "Source references": "source_references",
    "Review status": "review_status",
    "Notes": "notes",
    "Balance EUR": "balance_eur",
    "Include provisional totals": "include_provisional_totals",
    "Receipt group ID": "receipt_group_id",
}
REQUIRED_HEADERS = {"Transaction ID", "Date", "Amount EUR", "Type", "Include provisional totals"}

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_serial_date(value):
    """Convert a Sheets 1900-system serial number to an ISO date."""
    try:
        serial = int(value)
    except (TypeError, ValueError):
        return None
    if serial < 1 or serial > 80000:
        return None
    return (SHEETS_EPOCH + timedelta(days=serial - 1)).isoformat()


def parse_date(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return parse_serial_date(value)
    text = str(value).strip()
    if ISO_DATE_RE.match(text):
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError:
            return None
    return None


def parse_month(value):
    if value is None:
        return None
    text = str(value).strip()
    return text if MONTH_RE.match(text) else None


def parse_money(value):
    """Parse a native numeric or currency-formatted string into a Decimal."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).strip().replace("€", "").replace(",", "").replace(" ", "")
    if not text or text in ("-", "—"):
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def parse_flag(value):
    if value is None:
        return None
    text = str(value).strip().upper()
    if text == "YES":
        return "YES"
    if text == "NO":
        return "NO"
    return None


def parse_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def rows_to_transactions(values):
    """Map a raw A:Q grid (first row = headers) to transaction dicts.

    Returns (transactions, warnings, errors). errors are hard failures that
    reject the sync; warnings are recorded on the snapshot.
    """
    errors, warnings = [], []
    if not values or not any(cell for cell in values[0] if str(cell).strip()):
        return [], [], ["The 'combined data' tab has no header row"]
    header = [str(cell).strip() if cell is not None else "" for cell in values[0]]
    unknown_headers = [h for h in header if h and h not in HEADER_TO_FIELD]
    if unknown_headers:
        warnings.append(f"Ignoring unknown columns: {', '.join(unknown_headers)}")
    missing = [h for h in REQUIRED_HEADERS if h not in header]
    if missing:
        return [], warnings, [f"Missing required columns: {', '.join(sorted(missing))}"]
    column_field = {index: HEADER_TO_FIELD[name] for index, name in enumerate(header) if name in HEADER_TO_FIELD}

    if len(values) - 1 > MAX_ROWS:
        return [], warnings, [f"Ledger exceeds the {MAX_ROWS} row limit"]

    transactions = []
    for offset, row in enumerate(values[1:], start=2):
        cells = list(row) + [""] * (len(header) - len(row))
        record = {"row": offset}
        for index, field in column_field.items():
            record[field] = cells[index] if index < len(cells) else ""
        transaction = {
            "row": offset,
            "transaction_id": parse_text(record.get("transaction_id")),
            "date": parse_date(record.get("date")),
            "month": parse_month(record.get("month")),
            "account": parse_text(record.get("account")),
            "description": parse_text(record.get("description")),
            "merchant": parse_text(record.get("merchant")),
            "amount_eur": _money_str(record.get("amount_eur"), offset, warnings),
            "fee_eur": _money_str(record.get("fee_eur"), offset, warnings),
            "type": parse_text(record.get("type")),
            "category": parse_text(record.get("category")),
            "spending_class": parse_text(record.get("spending_class")),
            "source_references": parse_text(record.get("source_references")),
            "review_status": parse_text(record.get("review_status")),
            "notes": parse_text(record.get("notes")),
            "balance_eur": _money_str(record.get("balance_eur"), offset, warnings),
            "include_provisional_totals": parse_flag(record.get("include_provisional_totals")),
            "receipt_group_id": parse_text(record.get("receipt_group_id")),
        }
        if transaction["transaction_id"] is None:
            warnings.append(f"row {offset}: missing Transaction ID; kept but flagged")
        if transaction["date"] is None and record.get("date") not in (None, ""):
            warnings.append(f"row {offset}: unparseable Date {record.get('date')!r}; stored as null")
        if transaction["month"] is None and record.get("month") not in (None, ""):
            warnings.append(f"row {offset}: Month must be YYYY-MM; stored as null")
        elif transaction["month"] and transaction["date"] and not transaction["month"].startswith(transaction["date"][:7]):
            warnings.append(f"row {offset}: Month {transaction['month']} does not match Date {transaction['date']}")
        if transaction["amount_eur"] is None and record.get("amount_eur") not in (None, ""):
            warnings.append(f"row {offset}: unparseable Amount EUR {record.get('amount_eur')!r}; stored as null")
        if transaction["include_provisional_totals"] is None and record.get("include_provisional_totals") not in (None, ""):
            warnings.append(f"row {offset}: Include provisional totals must be YES or NO; stored as null")
        transactions.append(transaction)
    return transactions, warnings, errors


def _money_str(value, row, warnings):
    amount = parse_money(value)
    return None if amount is None else format(amount, "f")


def build_coverage(transactions, fetched_at):
    months = sorted({t["month"] for t in transactions if t.get("month")})
    return {
        "row_count": len(transactions),
        "months": months,
        "first_month": months[0] if months else None,
        "last_month": months[-1] if months else None,
        "cutoff": fetched_at,
        "timezone": TIMEZONE,
        "currency": CURRENCY,
    }
