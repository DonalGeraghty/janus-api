"""Typed finance rule model, allowlists, deterministic ordering and dry-run engine.

Rules are data, never code: every field, operator and action is checked against
the allowlists below, and only allowlisted row actions can affect calculations.
"""

from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict, Field, model_validator


RULE_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"

SCOPES = ("janus", "chatgpt_workflow")
RULE_TYPES = ("accounting", "reporting", "workflow", "categorisation")
STATUSES = ("active", "review", "disabled", "deleted")
CSV_STATUSES = ("active", "review", "disabled")

# Fields a row predicate may test against a transaction/ledger row.
ROW_FIELDS = (
    "transaction_id", "date", "month", "account", "description", "merchant",
    "amount_eur", "fee_eur", "type", "category", "spending_class",
    "review_status", "include_provisional_totals", "fund_purpose",
    "recognition_status", "asset_type", "receipt_group_id", "event_type",
)

OPERATORS = ("always", "equals", "not_equals", "in", "not_in", "contains", "gt", "gte", "lt", "lte")

# Row-executable actions change how a single ledger row is interpreted.
EXECUTABLE_ACTIONS = frozenset({
    "classify", "exclude", "flag", "set_category", "allocate", "reverse",
})

# Allowlisted policy/invariant/stateful-handler actions. They are stored and
# reported but never applied per row by the dry-run engine.
POLICY_ACTIONS = frozenset({
    "allow", "include",
    "read_combined_only", "use_eur", "use_dublin", "sum_eligible_signed", "avoid_double_fee",
    "monthly_net_waterfall", "calendar_month_filters", "label_provisional",
    "assets_minus_liabilities", "no_double_payroll", "explicit_ratio", "require_valid_budget",
    "count_once", "preserve_vocabulary", "show_snapshot_age", "same_financial_services",
    "no_ledger_writes", "exact_money", "distinguish_returns", "no_automatic_reclassification",
    "preserve_raw", "match_before_add", "verify_group_total", "five_exports", "flag_gap",
    "check_coverage", "match_multiset", "match_bank_id", "match_economic_event",
    "match_counterparties", "reconcile_anchors", "disclose_exceptions", "readback",
    "restrict_changes", "backup_before_restructure", "flag_known_limits", "require_evidence",
})

KNOWN_ACTIONS = EXECUTABLE_ACTIONS | POLICY_ACTIONS

# Accounting decisions compete; category assignment and review are independent.
ACTION_EFFECTS = {
    "classify": "accounting", "exclude": "accounting", "allocate": "accounting",
    "reverse": "accounting", "set_category": "category", "flag": "review",
}


def action_value_error(rule):
    action, value = rule.get("action"), rule.get("action_value") or ""
    if action == "classify":
        kind, separator, category = value.partition(":")
        if kind not in ("Income", "Expense", "Refund", "Transfer") or (separator and not category.strip()):
            return "classify requires Income, Expense, Refund or Transfer, optionally followed by :Category"
    if action == "set_category" and not value.strip():
        return "set_category requires a category"
    if action in ("allocate", "reverse"):
        expected = {"allocate": "unfunded_portion_only", "reverse": "previously_recognised_expense"}[action]
        if value != expected:
            return f"{action} requires action_value {expected!r}"
    return None


def is_executable(rule):
    return rule.get("scope") == "janus" and rule.get("action") in EXECUTABLE_ACTIONS


def validate_fields(data, strict=True):
    """Validate one rule mapping against the allowlists.

    Returns (clean_rule, errors, review_reason). In strict mode any problem is
    an error (JSON CRUD). In lenient mode (CSV import) an unknown action is not
    an error but forces status "review" so it can never activate silently.
    """
    errors, review_reason = [], None
    clean = {key: (value if value is None else str(value).strip()) for key, value in data.items()}

    rule_id = clean.get("rule_id") or ""
    if not rule_id or len(rule_id) > 64 or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for c in rule_id):
        errors.append(f"invalid rule_id {rule_id!r}")
    if clean.get("scope") not in SCOPES:
        errors.append(f"scope must be one of {', '.join(SCOPES)}")
    if not clean.get("name"):
        errors.append("name is required")
    elif len(clean["name"]) > 120:
        errors.append("name must be at most 120 characters")
    if clean.get("type") not in RULE_TYPES:
        errors.append(f"type must be one of {', '.join(RULE_TYPES)}")
    field, operator, action = clean.get("field"), clean.get("operator"), clean.get("action")
    if operator not in OPERATORS:
        errors.append(f"operator must be one of {', '.join(OPERATORS)}")
    elif operator == "always":
        if field != "*":
            errors.append("operator 'always' requires field '*'")
    elif field not in ROW_FIELDS:
        errors.append(f"field must be one of {', '.join(ROW_FIELDS)} or '*'")
    if action not in KNOWN_ACTIONS:
        message = f"unsupported action {action!r}"
        if strict:
            errors.append(message)
        else:
            review_reason = message
    elif message := action_value_error(clean):
        if strict:
            errors.append(message)
        else:
            review_reason = message
    status = clean.get("status", "active")
    if status not in (STATUSES if strict else CSV_STATUSES):
        errors.append(f"status must be one of {', '.join(STATUSES if strict else CSV_STATUSES)}")
    try:
        priority = int(clean.get("priority"))
        if not 0 <= priority <= 100000:
            raise ValueError
        clean["priority"] = priority
    except (TypeError, ValueError):
        errors.append("priority must be an integer between 0 and 100000")
    for key, limit in (("value", 500), ("action_value", 500), ("source_section", 200), ("description", 2000)):
        if len(clean.get(key) or "") > limit:
            errors.append(f"{key} must be at most {limit} characters")
    if review_reason and clean.get("status", "active") == "active":
        clean["status"] = "review"
    if review_reason:
        clean["review_reason"] = review_reason
    return clean, errors, review_reason


class RuleInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    rule_id: str = Field(pattern=RULE_ID_PATTERN)
    scope: str
    name: str = Field(min_length=1, max_length=120)
    type: str
    field: str = Field(min_length=1, max_length=64)
    operator: str
    value: str = Field(default="", max_length=500)
    action: str = Field(min_length=1, max_length=64)
    action_value: str = Field(default="", max_length=500)
    priority: int = Field(ge=0, le=100000)
    status: str = "active"
    source_section: str = Field(default="", max_length=200)
    description: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def check_allowlists(self):
        _clean, errors, _reason = validate_fields(self.model_dump(), strict=True)
        if errors:
            raise ValueError("; ".join(errors))
        if self.status not in ("active", "review", "disabled"):
            raise ValueError("status must be active, review or disabled")
        return self


class RuleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    revision: int = Field(ge=1)
    scope: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: str | None = None
    field: str | None = Field(default=None, min_length=1, max_length=64)
    operator: str | None = None
    value: str | None = Field(default=None, max_length=500)
    action: str | None = Field(default=None, min_length=1, max_length=64)
    action_value: str | None = Field(default=None, max_length=500)
    priority: int | None = Field(default=None, ge=0, le=100000)
    status: str | None = None
    source_section: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def check_update(self):
        updates = {key: value for key, value in self.model_dump(exclude={"revision"}).items() if value is not None}
        if not updates:
            raise ValueError("Supply at least one rule field to update")
        errors = []
        if self.scope is not None and self.scope not in SCOPES:
            errors.append(f"scope must be one of {', '.join(SCOPES)}")
        if self.type is not None and self.type not in RULE_TYPES:
            errors.append(f"type must be one of {', '.join(RULE_TYPES)}")
        if self.field is not None and self.field != "*" and self.field not in ROW_FIELDS:
            errors.append(f"field must be one of {', '.join(ROW_FIELDS)} or '*'")
        if self.operator is not None and self.operator not in OPERATORS:
            errors.append(f"operator must be one of {', '.join(OPERATORS)}")
        if self.action is not None and self.action not in KNOWN_ACTIONS:
            errors.append(f"unsupported action {self.action!r}")
        if self.status is not None and self.status not in ("active", "review", "disabled"):
            errors.append("status must be active, review or disabled")
        if errors:
            raise ValueError("; ".join(errors))
        return self


def sort_rules(rules):
    """Deterministic execution order: higher priority first, then rule_id."""
    return sorted(rules, key=lambda rule: (-rule["priority"], rule["rule_id"]))


def active_executable_rules(rules):
    return sort_rules([rule for rule in rules if rule.get("status") == "active" and is_executable(rule)])


def _as_decimal(value):
    try:
        result = Decimal(str(value).strip())
        return result if result.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def rule_matches(rule, row):
    """Evaluate one row-predicate rule against a sample ledger row."""
    operator, field, expected = rule["operator"], rule["field"], rule.get("value") or ""
    if operator == "always":
        return True
    actual = row.get(field)
    if actual is None:
        return False
    if operator in ("gt", "gte", "lt", "lte"):
        left, right = _as_decimal(actual), _as_decimal(expected)
        if left is None or right is None:
            return False
        return {"gt": left > right, "gte": left >= right, "lt": left < right, "lte": left <= right}[operator]
    text = str(actual).strip().lower()
    wanted = expected.strip().lower()
    if operator == "equals":
        return text == wanted
    if operator == "not_equals":
        return text != wanted
    if operator in ("in", "not_in"):
        options = {part.strip().lower() for part in expected.split("|") if part.strip()}
        hit = text in options
        return hit if operator == "in" else not hit
    if operator == "contains":
        return wanted in text
    return False


def find_conflicts(rules):
    """Flag groups of active executable rules that compete on the same condition."""
    groups = {}
    for rule in active_executable_rules(rules):
        key = (rule["field"], rule["operator"], (rule.get("value") or "").strip().lower(),
               rule["priority"], ACTION_EFFECTS[rule["action"]])
        groups.setdefault(key, []).append(rule)
    conflicts = []
    for (field, operator, value, priority, _effect), members in groups.items():
        outcomes = {(member["action"], member.get("action_value") or "") for member in members}
        if len(outcomes) > 1:
            conflicts.append({
                "field": field, "operator": operator, "value": value, "priority": priority,
                "rule_ids": sorted(member["rule_id"] for member in members),
            })
    return sorted(conflicts, key=lambda item: item["rule_ids"])


def matching_rule_effects(active_rules, row):
    """Match the original interpreted row; first rule per effect wins. No chaining."""
    matches, selected, effects = [], [], set()
    for rule in active_rules:
        if rule_matches(rule, row):
            matches.append(rule)
            effect = ACTION_EFFECTS[rule["action"]]
            if effect not in effects:
                selected.append(rule)
                effects.add(effect)
    return matches, selected


def evaluate_rows(rules, rows):
    """Dry-run: apply active janus row rules to sample rows. Pure; never mutates."""
    # Import here to keep the calculation module's shared predicate dependency acyclic.
    from .finance_calc import derive_rows

    active = active_executable_rules(rules)
    results = []
    for index, row in enumerate(derive_rows(rules, rows)):
        matches, _selected = matching_rule_effects(active, row)
        interpretation = row["derived"]
        results.append({
            "index": index,
            "outcome": None if interpretation["rule_id"] is None else {
                key: interpretation[key] for key in ("rule_id", "action", "action_value")
            },
            "derived": interpretation,
            "matches": [
                {"rule_id": rule["rule_id"], "priority": rule["priority"],
                 "action": rule["action"], "action_value": rule.get("action_value") or ""}
                for rule in matches
            ],
        })
    return results, find_conflicts(rules)
