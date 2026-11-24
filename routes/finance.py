"""Finance connection plus rules management: individual CRUD, CSV import/export, dry-run.

A shared Janus login alone is not finance access: every /api/finance route except
the connection endpoints requires the account to have its own KMS-encrypted Google
Sheets credential stored (PUT /api/finance/connection), the same per-account model
as the AI provider keys. All responses are Cache-Control: no-store.
"""

import re

from flask import Blueprint, Response, g, jsonify, request
from pydantic import ValidationError

from core.finance_rules import RuleInput, RuleUpdate
from core.request_auth import authenticated_identity
from services.credential_service import (
    CredentialConfigurationError,
    CredentialEncryptionError,
    encrypt_api_key,
)
from services.firebase.finance_connection import (
    FinanceConnectionError,
    delete_finance_connection,
    get_finance_connection_status,
    has_finance_connection,
    save_finance_connection,
)
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
WORKBOOK_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{10,128}$")


@blueprint.before_request
def require_finance_account():
    request.max_content_length = MAX_BODY_BYTES
    if request.method == "OPTIONS":
        return None
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="unauthorized", message="Sign in to continue."), 401
    g.finance_identity = identity
    if request.path == "/api/finance/connection":
        return None
    if not has_finance_connection(identity["email"], identity["account_id"]):
        return jsonify(status="error", error="finance_not_connected",
                       message="Connect your own Google Sheets workbook first (Account, Finance connection)."), 403
    return None


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


@blueprint.errorhandler(FinanceConnectionError)
def connection_error(error):
    return jsonify(status="error", error=str(error)), error.status


@blueprint.get("/connection")
def connection_status():
    identity = g.finance_identity
    return jsonify(status="success", connection=get_finance_connection_status(identity["email"], identity["account_id"]))


@blueprint.put("/connection")
def connection_save():
    identity = g.finance_identity
    data = request.get_json(silent=True) or {}
    token = data.get("access_token")
    workbook_id = data.get("workbook_id")
    if not isinstance(token, str) or not token.strip() or len(token) < 20 or len(token) > 2048 or any(c.isspace() for c in token):
        return jsonify(status="error", error="invalid_access_token",
                       message="Supply a Google OAuth access token (no spaces, 20-2048 characters)."), 400
    if not isinstance(workbook_id, str) or not WORKBOOK_ID_PATTERN.fullmatch(workbook_id.strip()):
        return jsonify(status="error", error="invalid_workbook_id",
                       message="Supply the Google Sheets workbook ID of your finance workbook."), 400
    email = identity["email"]
    try:
        ciphertext = encrypt_api_key(token.strip(), email, provider="google", aad_version=2)
    except (CredentialConfigurationError, CredentialEncryptionError):
        return jsonify(status="error", error="credential_service_unavailable",
                       message="Secure credential storage is unavailable."), 503
    status = save_finance_connection(email, identity["account_id"], ciphertext, token.strip()[-4:], workbook_id.strip())
    return jsonify(status="success", connection=status)


@blueprint.delete("/connection")
def connection_delete():
    identity = g.finance_identity
    return jsonify(status="success", connection=delete_finance_connection(identity["email"], identity["account_id"]))


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
