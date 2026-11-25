"""Rule CRUD, CSV interchange, dry runs and version history."""

from flask import Response, g, jsonify, request

from core.finance.rule_engine import RuleInput, RuleUpdate
from services.firebase.finance.rules import (
    create_rule, delete_rule, export_rules, import_rules,
    list_history, list_rules, restore_version, test_rules, update_rule,
)
from .shared import actor, blueprint, payload


@blueprint.get("/rules")
def rules_list():
    identity = g.finance_identity
    return jsonify(status="success", **list_rules(
        identity["email"], identity["account_id"],
        include_deleted=request.args.get("include_deleted") == "true",
        scope=request.args.get("scope") or None,
        status=request.args.get("status") or None,
    ))


@blueprint.post("/rules")
def rules_create():
    identity = g.finance_identity
    data = payload(RuleInput)
    return jsonify(status="success", **create_rule(
        identity["email"], identity["account_id"], data, actor(identity))), 201


@blueprint.put("/rules/<rule_id>")
def rules_update(rule_id):
    identity = g.finance_identity
    data = payload(RuleUpdate, True)
    return jsonify(status="success", **update_rule(
        identity["email"], identity["account_id"], rule_id, data, actor(identity)))


@blueprint.delete("/rules/<rule_id>")
def rules_delete(rule_id):
    identity = g.finance_identity
    revision = request.args.get("revision", type=int)
    if revision is None:
        body = request.get_json(silent=True) or {}
        revision = body.get("revision")
        if not isinstance(revision, int):
            revision = None
    return jsonify(status="success", **delete_rule(
        identity["email"], identity["account_id"], rule_id, revision, actor(identity)))


@blueprint.post("/rules/import")
def rules_import():
    identity = g.finance_identity
    body = request.get_json(silent=True) or {}
    csv_text = body.get("csv")
    mode = body.get("mode", "preview")
    if not isinstance(csv_text, str):
        return jsonify(status="error", error="Supply the rules CSV text in the 'csv' field"), 400
    result = import_rules(identity["email"], identity["account_id"], csv_text, mode, actor(identity))
    status_code = 201 if mode == "commit" and result.get("committed") else 200
    return jsonify(status="success", **result), status_code


@blueprint.get("/rules/export")
def rules_export():
    identity = g.finance_identity
    fmt = request.args.get("format", "csv")
    result = export_rules(identity["email"], identity["account_id"], fmt,
                          include_deleted=request.args.get("include_deleted") == "true")
    if fmt == "csv":
        return Response(result["csv"], mimetype="text/csv", headers={
            "Content-Disposition": "attachment; filename=financial_rules.csv",
            "Cache-Control": "no-store",
        })
    return jsonify(status="success", **result)


@blueprint.post("/rules/test")
def rules_test():
    identity = g.finance_identity
    body = request.get_json(silent=True) or {}
    rows = body.get("rows")
    rule_ids = body.get("rule_ids")
    return jsonify(status="success", **test_rules(
        identity["email"], identity["account_id"], rows, rule_ids))


@blueprint.get("/rules/history")
def rules_history():
    identity = g.finance_identity
    return jsonify(status="success", **list_history(identity["email"], identity["account_id"]))


@blueprint.post("/rules/restore/<version>")
def rules_restore(version):
    identity = g.finance_identity
    return jsonify(status="success", **restore_version(
        identity["email"], identity["account_id"], version, actor(identity)))
