"""Finance rules management: individual CRUD, CSV import/export and dry-run tests.

Finance access requires a current Janus bearer token for an account listed in
FINANCE_OWNER_EMAILS; a shared login alone is not enough. All responses are
Cache-Control: no-store and never mix snapshot/rule-set versions.
"""

from functools import wraps

from flask import Blueprint, Response, g, jsonify, request
from pydantic import ValidationError

from core.finance_access import finance_authorized
from core.finance_rules import RuleInput, RuleUpdate
from core.request_auth import authenticated_identity
from services.firebase.finance_rules import (
    FinanceError,
    create_rule,
    delete_rule,
    export_rules,
    import_rules,
    list_history,
    list_rules,
    restore_version,
    test_rules,
    update_rule,
)


blueprint = Blueprint("finance", __name__, url_prefix="/api/finance")

MAX_BODY_BYTES = 256 * 1024


@blueprint.before_request
def require_finance_account():
    request.max_content_length = MAX_BODY_BYTES
    if request.method == "OPTIONS":
        return None
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="unauthorized", message="Sign in to continue."), 401
    if not finance_authorized(identity):
        return jsonify(status="error", error="forbidden",
                       message="Finance access is not enabled for this account."), 403
    g.finance_identity = identity


@blueprint.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@blueprint.errorhandler(FinanceError)
def finance_error(error):
    body = {"status": "error", "error": str(error)}
    if error.details:
        body["details"] = error.details
    return jsonify(**body), error.status


@blueprint.errorhandler(ValidationError)
def invalid_rule(error):
    return jsonify(status="error", error="Invalid rule data",
                   message="; ".join(str(item) for item in error.errors()[:3])), 400


def payload(model, partial=False):
    return model.model_validate(request.get_json(silent=True) or {}).model_dump(mode="json", exclude_unset=partial)


def actor(identity):
    return identity["email"]


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
