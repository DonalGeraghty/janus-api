"""Account-scoped finance rule storage with atomic rule-set versions and history.

Firestore is the runtime authority; the in-memory stores are the local fallback.
Every committed mutation bumps rule_set_version exactly once and appends one
history entry holding the full resulting snapshot, so any version can be restored.
"""

import copy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from firebase_admin import firestore

from core.finance_rules import ROW_FIELDS, evaluate_rows, find_conflicts, validate_fields
from core.finance_rules_csv import parse_rules_csv, rules_to_csv, rules_to_json_payload
from . import db_state
from .account_state import ACCOUNT_DELETION_FIELD, ACCOUNT_DELETION_TOKEN_FIELD, account_id_matches
from .core import normalize_user_email
from ..logging_service import logger


class FinanceError(Exception):
    def __init__(self, message, status=400, details=None):
        super().__init__(message)
        self.status = status
        self.details = details


RULES_COLLECTION = "finance_rules"
HISTORY_COLLECTION = "finance_rule_history"
SETTINGS_COLLECTION = "finance_settings"
SETTINGS_DOC = "settings"

RULE_FIELDS = ("scope", "name", "type", "field", "operator", "value", "action",
               "action_value", "priority", "status", "source_section", "description")

PUBLIC_FIELDS = ("rule_id", *RULE_FIELDS, "revision", "created_at", "updated_at", "review_reason")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _guard(user, account_id, deletion_token=None):
    if not user or not account_id_matches(account_id, user):
        raise FinanceError("Account is unavailable", 401)
    if deletion_token:
        if not user.get(ACCOUNT_DELETION_FIELD) or user.get(ACCOUNT_DELETION_TOKEN_FIELD) != deletion_token:
            raise FinanceError("Account deletion changed", 409)
    elif user.get(ACCOUNT_DELETION_FIELD):
        raise FinanceError("Account deletion is in progress", 409)


def _public(rule):
    return {key: rule[key] for key in PUBLIC_FIELDS if key in rule}


def _history_entry(version, actor, summary, changed_rule_ids, rules):
    return {
        "version": version,
        "created_at": _now(),
        "actor": actor,
        "summary": summary,
        "changed_rule_ids": sorted(changed_rule_ids),
        "rule_count": len(rules),
        "rules": [dict(rule) for rule in rules],
    }


def _operate(email, account_id, operation, deletion_token=None):
    """Read every required document before writing; guard deletion and generation.

    operation(rules, settings) returns (result, writes, deletes, history).
    """
    email = normalize_user_email(email)
    if not email:
        raise FinanceError("Invalid account", 401)
    if db_state.users_collection_ref is not None:
        if db_state.db is None:
            raise FinanceError("Finance storage is unavailable", 503)
        user_ref = db_state.users_collection_ref.document(email)
        rules_ref = user_ref.collection(RULES_COLLECTION)
        settings_ref = user_ref.collection(SETTINGS_COLLECTION).document(SETTINGS_DOC)
        history_ref = user_ref.collection(HISTORY_COLLECTION)

        @firestore.transactional
        def execute(transaction):
            user = user_ref.get(transaction=transaction)
            _guard(user.to_dict() if user.exists else None, account_id, deletion_token)
            rules = {document.id: dict(document.to_dict(), rule_id=document.id)
                     for document in rules_ref.stream(transaction=transaction)}
            settings_document = settings_ref.get(transaction=transaction)
            settings = settings_document.to_dict() if settings_document.exists else {"rule_set_version": 0}
            result, writes, deletes, history = operation(rules, settings)
            for rule_id, rule in writes.items():
                transaction.set(rules_ref.document(rule_id), rule)
            for rule_id in deletes:
                transaction.delete(rules_ref.document(rule_id))
            if history is not None:
                settings["rule_set_version"] = history["version"]
                transaction.set(history_ref.document(str(history["version"])), history)
            settings["updated_at"] = _now()
            transaction.set(settings_ref, settings)
            return result

        try:
            return execute(db_state.db.transaction())
        except FinanceError:
            raise
        except Exception as error:
            logger.error("Finance rule storage failed: %s: %s", type(error).__name__, str(error)[:200])
            raise FinanceError("Finance storage is unavailable", 503) from error

    with db_state.memory_lock:
        _guard(db_state.auth_users_memory.get(email), account_id, deletion_token)
        rules = copy.deepcopy(db_state.finance_rules_memory.get(email, {}))
        settings = copy.deepcopy(db_state.finance_settings_memory.get(email, {"rule_set_version": 0}))
        result, writes, deletes, history = operation(rules, settings)
        for rule_id in deletes:
            rules.pop(rule_id, None)
        rules.update(copy.deepcopy(writes))
        db_state.finance_rules_memory[email] = rules
        if history is not None:
            settings["rule_set_version"] = history["version"]
            db_state.finance_rule_history_memory.setdefault(email, {})[str(history["version"])] = copy.deepcopy(history)
        settings["updated_at"] = _now()
        db_state.finance_settings_memory[email] = settings
        return copy.deepcopy(result)


def _sorted_public(rules):
    return [_public(rule) for rule in sorted(rules.values(), key=lambda rule: rule["rule_id"])]


def list_rules(email, account_id, include_deleted=False, scope=None, status=None):
    def read(rules, settings):
        visible = {rule["rule_id"]: rule for rule in rules.values()
                   if (include_deleted or rule.get("status") != "deleted")
                   and (scope is None or rule.get("scope") == scope)
                   and (status is None or rule.get("status") == status)}
        return {"rules": _sorted_public(visible),
                "rule_set_version": settings.get("rule_set_version", 0)}, {}, [], None
    return _operate(email, account_id, read)


def create_rule(email, account_id, data, actor):
    def create(rules, settings):
        rule_id = data["rule_id"]
        if rule_id in rules:
            raise FinanceError("A rule with this ID already exists", 409)
        now = _now()
        rule = {"rule_id": rule_id, "revision": 1, "created_at": now, "updated_at": now, **data}
        version = settings.get("rule_set_version", 0) + 1
        snapshot = {**rules, rule_id: rule}
        history = _history_entry(version, actor, f"Created rule {rule_id}", [rule_id], list(snapshot.values()))
        return {"rule": _public(rule), "rule_set_version": version}, {rule_id: rule}, [], history
    return _operate(email, account_id, create)


def update_rule(email, account_id, rule_id, data, actor):
    def update(rules, settings):
        existing = rules.get(rule_id)
        if existing is None or existing.get("status") == "deleted":
            raise FinanceError("Rule not found", 404)
        if existing.get("revision", 0) != data.get("revision"):
            raise FinanceError("Rule was changed by someone else; reload and retry", 409)
        updates = {key: value for key, value in data.items() if key != "revision" and value is not None}
        rule = dict(existing)
        rule.update(updates)
        _clean, errors, _review = validate_fields(rule)
        if errors:
            raise FinanceError("Rule validation failed", 400, details=errors)
        rule["revision"] = existing.get("revision", 0) + 1
        rule["updated_at"] = _now()
        if "action" in updates or "status" in updates:
            rule.pop("review_reason", None)
        version = settings.get("rule_set_version", 0) + 1
        snapshot = {**rules, rule_id: rule}
        history = _history_entry(version, actor, f"Updated rule {rule_id}", [rule_id], list(snapshot.values()))
        return {"rule": _public(rule), "rule_set_version": version}, {rule_id: rule}, [], history
    return _operate(email, account_id, update)


def delete_rule(email, account_id, rule_id, revision, actor):
    def delete(rules, settings):
        existing = rules.get(rule_id)
        if existing is None:
            raise FinanceError("Rule not found", 404)
        if existing.get("status") == "deleted":
            return {"rule": _public(existing), "rule_set_version": settings.get("rule_set_version", 0),
                    "deleted": False}, {}, [], None
        if revision is not None and existing.get("revision", 0) != revision:
            raise FinanceError("Rule was changed by someone else; reload and retry", 409)
        rule = dict(existing, status="deleted", revision=existing.get("revision", 0) + 1, updated_at=_now())
        version = settings.get("rule_set_version", 0) + 1
        snapshot = {**rules, rule_id: rule}
        history = _history_entry(version, actor, f"Deleted rule {rule_id}", [rule_id], list(snapshot.values()))
        return {"rule": _public(rule), "rule_set_version": version, "deleted": True}, {rule_id: rule}, [], history
    return _operate(email, account_id, delete)


def _classify_changes(existing_rules, rows):
    changes, held = [], []
    for row in rows:
        rule_id = row["rule_id"]
        current = existing_rules.get(rule_id)
        entry = {"rule_id": rule_id, "status": row.get("status", "active")}
        if current is None:
            entry["change"] = "create"
        elif any(current.get(field) != row.get(field, "") for field in RULE_FIELDS):
            entry["change"] = "update"
        else:
            entry["change"] = "unchanged"
        if row.get("review_reason"):
            entry["action"] = "held_for_review"
            entry["reason"] = row["review_reason"]
            held.append(dict(entry, change=entry["change"]))
        changes.append(entry)
    return changes, held


def import_rules(email, account_id, csv_text, mode, actor):
    rows, errors = parse_rules_csv(csv_text)
    if errors:
        raise FinanceError("CSV validation failed", 400, details=errors)
    if mode not in ("preview", "commit"):
        raise FinanceError("mode must be 'preview' or 'commit'", 400)

    def plan(rules, settings):
        merged = {rule["rule_id"]: dict(rule) for rule in rules.values()}
        for row in rows:
            rule_id = row["rule_id"]
            base = merged.get(rule_id, {"rule_id": rule_id, "revision": 0})
            merged[rule_id] = {**base, **{key: row.get(key, "") for key in RULE_FIELDS}}
        conflicts = find_conflicts(list(merged.values()))
        conflicting_ids = {rule_id for conflict in conflicts for rule_id in conflict["rule_ids"]}
        for row in rows:
            if row["rule_id"] in conflicting_ids and row.get("status") == "active":
                row["status"] = "review"
                row["review_reason"] = "Conflicting rule assignment; held for review"
        changes, held = _classify_changes(rules, rows)
        base = {
            "valid": True,
            "mode": mode,
            "changes": changes,
            "held": held,
            "conflicts": conflicts,
            "rule_set_version": settings.get("rule_set_version", 0),
        }
        if mode == "preview":
            return {**base, "would_be_version": base["rule_set_version"] + (1 if changes else 0)}, {}, [], None

        now = _now()
        writes, changed = {}, []
        for row in rows:
            rule_id = row["rule_id"]
            existing = rules.get(rule_id)
            data = {key: row.get(key, "") for key in RULE_FIELDS}
            if existing is not None and not row.get("review_reason") \
                    and all(existing.get(field) == data.get(field) for field in RULE_FIELDS):
                continue
            if existing is None:
                rule = {"rule_id": rule_id, "revision": 1, "created_at": now, "updated_at": now, **data}
            else:
                rule = dict(existing)
                rule.update(data)
                rule["revision"] = existing.get("revision", 0) + 1
                rule["updated_at"] = now
            if row.get("review_reason"):
                rule["review_reason"] = row["review_reason"]
            else:
                rule.pop("review_reason", None)
            writes[rule_id] = rule
            changed.append(rule_id)
        version = settings.get("rule_set_version", 0) + (1 if writes else 0)
        history = None
        if writes:
            snapshot = {**rules, **writes}
            created = len([c for c in changes if c["change"] == "create"])
            updated = len([c for c in changes if c["change"] == "update"])
            history = _history_entry(
                version, actor,
                f"Imported rules: {created} created, {updated} updated, {len(held)} held for review",
                changed, list(snapshot.values()))
        return {**base, "rule_set_version": version, "committed": bool(writes)}, writes, [], history

    return _operate(email, account_id, plan)


def export_rules(email, account_id, fmt, include_deleted=False):
    def read(rules, settings):
        visible = [rule for rule in rules.values() if include_deleted or rule.get("status") != "deleted"]
        if fmt == "csv":
            return {"format": "csv", "csv": rules_to_csv(visible),
                    "rule_set_version": settings.get("rule_set_version", 0)}, {}, [], None
        if fmt == "json":
            return {"format": "json", **rules_to_json_payload(visible, settings.get("rule_set_version", 0))}, {}, [], None
        raise FinanceError("format must be 'csv' or 'json'", 400)
    return _operate(email, account_id, read)


def test_rules(email, account_id, rows, rule_ids=None):
    if not isinstance(rows, list) or not rows or len(rows) > 100:
        raise FinanceError("rows must be a non-empty list of at most 100 sample rows", 400)
    for row in rows:
        if not isinstance(row, dict) or len(row) > 32 or any(not isinstance(key, str) or len(key) > 64 for key in row):
            raise FinanceError("each row must be an object of at most 32 named fields", 400)
        for field, value in row.items():
            if value is None:
                continue
            if field in ("amount_eur", "fee_eur"):
                try:
                    number = Decimal(str(value))
                    if not number.is_finite():
                        raise ValueError
                    number.quantize(Decimal("0.01"))
                except (InvalidOperation, ValueError):
                    raise FinanceError(f"{field} must be a finite number", 400) from None
            elif field in ROW_FIELDS and not isinstance(value, str):
                raise FinanceError(f"{field} must be text", 400)
            elif field == "row" and (not isinstance(value, int) or isinstance(value, bool)):
                raise FinanceError("row must be an integer", 400)
            elif not isinstance(value, (str, int, float, bool)):
                raise FinanceError("sample row values must be text, numbers, booleans or null", 400)
    if rule_ids is not None and (not isinstance(rule_ids, list) or any(not isinstance(item, str) for item in rule_ids)):
        raise FinanceError("rule_ids must be a list of rule IDs", 400)

    def read(rules, settings):
        selected = list(rules.values())
        if rule_ids is not None:
            selected = [rule for rule in selected if rule["rule_id"] in set(rule_ids)]
        results, conflicts = evaluate_rows(selected, rows)
        return {"results": results, "conflicts": conflicts,
                "rule_set_version": settings.get("rule_set_version", 0)}, {}, [], None
    return _operate(email, account_id, read)


def _read_history(email, account_id):
    email = normalize_user_email(email)
    if not email:
        raise FinanceError("Invalid account", 401)
    if db_state.users_collection_ref is not None:
        if db_state.db is None:
            raise FinanceError("Finance storage is unavailable", 503)
        user_ref = db_state.users_collection_ref.document(email)
        try:
            user = user_ref.get()
            _guard(user.to_dict() if user.exists else None, account_id)
            entries = [dict(document.to_dict(), version=int(document.id))
                       for document in user_ref.collection(HISTORY_COLLECTION).stream()]
            settings = user_ref.collection(SETTINGS_COLLECTION).document(SETTINGS_DOC).get()
            version = settings.to_dict().get("rule_set_version", 0) if settings.exists else 0
        except FinanceError:
            raise
        except Exception as error:
            logger.error("Finance history read failed: %s: %s", type(error).__name__, str(error)[:200])
            raise FinanceError("Finance storage is unavailable", 503) from error
    else:
        with db_state.memory_lock:
            _guard(db_state.auth_users_memory.get(email), account_id)
            entries = [dict(entry, version=int(version))
                       for version, entry in db_state.finance_rule_history_memory.get(email, {}).items()]
            version = db_state.finance_settings_memory.get(email, {}).get("rule_set_version", 0)
    entries.sort(key=lambda entry: entry["version"], reverse=True)
    summaries = [{key: entry.get(key) for key in ("version", "created_at", "actor", "summary", "changed_rule_ids", "rule_count")}
                 for entry in entries]
    return {"history": summaries, "rule_set_version": version}


def list_history(email, account_id):
    return _read_history(email, account_id)


def _load_snapshot(email, account_id, version):
    email = normalize_user_email(email)
    if db_state.users_collection_ref is not None:
        if db_state.db is None:
            raise FinanceError("Finance storage is unavailable", 503)
        document = db_state.users_collection_ref.document(email).collection(HISTORY_COLLECTION).document(str(version)).get()
        if not document.exists:
            raise FinanceError("History version not found", 404)
        return document.to_dict().get("rules")
    with db_state.memory_lock:
        _guard(db_state.auth_users_memory.get(email), account_id)
        entry = db_state.finance_rule_history_memory.get(email, {}).get(str(version))
        if not entry:
            raise FinanceError("History version not found", 404)
        return entry.get("rules")


def restore_version(email, account_id, version, actor):
    try:
        target = int(version)
    except (TypeError, ValueError):
        raise FinanceError("Invalid history version", 400)
    snapshot = _load_snapshot(email, account_id, target)
    if not isinstance(snapshot, list):
        raise FinanceError("History version not found", 404)

    def restore(rules, settings):
        now = _now()
        writes, changed = {}, []
        restored_ids = set()
        for saved in snapshot:
            rule_id = saved.get("rule_id")
            if not rule_id:
                continue
            restored_ids.add(rule_id)
            existing = rules.get(rule_id)
            data = {key: saved.get(key, "") for key in RULE_FIELDS}
            if existing is not None and all(existing.get(field) == data.get(field) for field in RULE_FIELDS):
                continue
            if existing is None:
                rule = {"rule_id": rule_id, "created_at": now, **data}
            else:
                rule = dict(existing)
                rule.update(data)
            rule["revision"] = (existing.get("revision", 0) if existing else 0) + 1
            rule["updated_at"] = now
            rule.pop("review_reason", None)
            writes[rule_id] = rule
            changed.append(rule_id)
        for rule_id, existing in rules.items():
            if rule_id not in restored_ids and existing.get("status") != "deleted":
                rule = dict(existing, status="deleted", revision=existing.get("revision", 0) + 1, updated_at=now)
                writes[rule_id] = rule
                changed.append(rule_id)
        new_version = settings.get("rule_set_version", 0) + (1 if writes else 0)
        history = None
        if writes:
            merged = {**rules, **writes}
            history = _history_entry(new_version, actor, f"Restored rule set from version {target}", changed, list(merged.values()))
        return {"rule_set_version": new_version, "restored_from": target, "changed_rule_ids": sorted(changed)}, writes, [], history

    return _operate(email, account_id, restore)


def delete_finance_account_data(email, account_id, deletion_token):
    """Delete finance rules, history and settings only under the owning tombstoned account."""
    if db_state.users_collection_ref is None:
        return True
    if db_state.db is None:
        return False
    user_ref = db_state.users_collection_ref.document(normalize_user_email(email))

    def remove(transaction, target):
        document = user_ref.get(transaction=transaction)
        if not document.exists:
            return
        data = document.to_dict() or {}
        if (not account_id_matches(account_id, data) or not data.get(ACCOUNT_DELETION_FIELD)
                or data.get(ACCOUNT_DELETION_TOKEN_FIELD) != deletion_token):
            raise FinanceError("Account deletion state changed", 409)
        transaction.delete(target)

    try:
        # The tombstone prevents concurrent integration writes during traversal.
        for name in (RULES_COLLECTION, HISTORY_COLLECTION, SETTINGS_COLLECTION):
            for document in user_ref.collection(name).stream():
                firestore.transactional(remove)(db_state.db.transaction(), document.reference)
        firestore.transactional(remove)(db_state.db.transaction(), user_ref.collection("private").document("finance"))
        return True
    except Exception:
        return False
