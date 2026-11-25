"""Portable CSV interchange for finance rule sets.

CSV is the human-editable interchange format; Firestore is the runtime authority.
Exports are protected against spreadsheet formula injection while JSON export
stays lossless for machine round-trips.
"""

import csv
import io

from .rule_engine import validate_fields

CSV_HEADERS = [
    "rule_id", "scope", "name", "type", "field", "operator", "value", "action",
    "action_value", "priority", "status", "source_section", "description",
]

MAX_CSV_BYTES = 256 * 1024


def parse_rules_csv(text):
    """Parse and validate a rules CSV.

    Returns (rows, errors). Hard errors (bad headers, malformed rows, duplicate
    IDs) reject the whole import; rows with unsupported actions are returned
    with status forced to "review" so they are never silently activated.
    """
    if not isinstance(text, str) or not text.strip():
        return [], ["CSV is empty"]
    if len(text.encode("utf-8")) > MAX_CSV_BYTES:
        return [], ["CSV exceeds the 256 KiB limit"]
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return [], ["CSV has no header row"]
    missing = [header for header in CSV_HEADERS if header not in reader.fieldnames]
    unknown = [header for header in reader.fieldnames if header not in CSV_HEADERS]
    if missing or unknown:
        problems = []
        if missing:
            problems.append(f"missing headers: {', '.join(missing)}")
        if unknown:
            problems.append(f"unknown headers: {', '.join(unknown)}")
        return [], problems
    rows, errors, seen = [], [], set()
    for line_number, raw in enumerate(reader, start=2):
        if None in raw:
            errors.append(f"line {line_number}: more fields than headers")
            continue
        rule, rule_errors, _review = validate_fields(raw, strict=False)
        if rule_errors:
            errors.extend(f"line {line_number}: {error}" for error in rule_errors)
            continue
        rule_id = rule["rule_id"]
        if rule_id in seen:
            errors.append(f"line {line_number}: duplicate rule_id {rule_id!r}")
            continue
        seen.add(rule_id)
        for header in CSV_HEADERS:
            rule.setdefault(header, "")
        rows.append(rule)
    return rows, errors


def _csv_safe(cell):
    text = "" if cell is None else str(cell)
    if text[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


def rules_to_csv(rules):
    """Serialize rules to CSV, neutralizing cells that spreadsheets would evaluate."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(CSV_HEADERS)
    for rule in sorted(rules, key=lambda item: item["rule_id"]):
        writer.writerow([_csv_safe(rule.get(header, "")) for header in CSV_HEADERS])
    return buffer.getvalue()


def rules_to_json_payload(rules, rule_set_version):
    return {
        "rule_set_version": rule_set_version,
        "rules": [dict(rule) for rule in sorted(rules, key=lambda item: item["rule_id"])],
    }
