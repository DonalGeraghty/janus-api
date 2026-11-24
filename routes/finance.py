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
from services import finance_sync
from services import ai_service
from core import finance_calc
from core import finance_chat as finance_chat_core
from core.finance_chat import PRIVACY_NOTE, SYSTEM_PROMPT, build_context_pack, build_user_content, sanitize_history, sanitize_message
from services.ai_credentials import selected_ai_credential, stored_credential_aad_version
from services.ai_errors import (AIAuthenticationError, AIAuthorizationError, AIBillingError,
                               AIRateLimitError, AIServiceError)
from services.credential_service import CredentialConfigurationError, CredentialEncryptionError, decrypt_api_key
from services.firebase.finance_rules import list_rules as list_rule_docs


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


@blueprint.post("/sync")
def ledger_sync():
    identity = g.finance_identity
    return jsonify(status="success", sync=finance_sync.sync_now(identity["email"], identity["account_id"])), 201


@blueprint.get("/sync/status")
def ledger_sync_status():
    identity = g.finance_identity
    return jsonify(status="success", sync=finance_sync.sync_status(identity["email"], identity["account_id"]))


def _snapshot_and_rules(identity):
    snapshot = finance_sync.get_snapshot(identity["email"])
    if snapshot is None:
        raise FinanceError("Sync the ledger first (POST /api/finance/sync).", 409, details={"code": "sync_required"})
    rules = list_rule_docs(identity["email"], identity["account_id"], scope="janus", status="active")["rules"]
    return snapshot, rules


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
    snapshot, rules = _snapshot_and_rules(identity)
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
    if by not in ("month", "category"):
        raise FinanceError("by must be 'month' or 'category'", 400)
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
    snapshot, _rules = _snapshot_and_rules(identity)
    return jsonify(status="success", meta=_meta(snapshot), net_worth=finance_calc.parse_net_worth(snapshot.get("snapshot_grid")))


@blueprint.get("/sinking-funds")
def sinking_funds():
    identity = g.finance_identity
    snapshot, rows = _rows(identity)
    return jsonify(status="success", meta=_meta(snapshot), sinking_funds=finance_calc.sinking_ledger(rows))


@blueprint.get("/budgets")
def budgets():
    identity = g.finance_identity
    snapshot, _rules = _snapshot_and_rules(identity)
    return jsonify(status="success", meta=_meta(snapshot),
                   budgets={"available": False, "reason": "No confirmed budget tab in the ledger; budget charts stay hidden until verified budget data exists."})


@blueprint.post("/chat")
def chat():
    """Answer a finance question from the pinned snapshot; the LLM never calculates."""
    identity = g.finance_identity
    email, account_id = identity["email"], identity["account_id"]
    body = request.get_json(silent=True) or {}
    try:
        message = sanitize_message(body.get("message"))
        history = sanitize_history(body.get("history"))
    except ValueError as error:
        return jsonify(status="error", error=str(error)), 400
    snapshot = finance_sync.get_snapshot(email)
    if snapshot is None:
        return jsonify(status="error", error="Sync the ledger first (POST /api/finance/sync).",
                       details={"code": "sync_required"}), 409
    selection, credential, error = selected_ai_credential(email, account_id)
    if error:
        return jsonify(status="error", error=error, message="Secure AI settings are unavailable."), 503
    provider = selection["provider"]
    if not credential:
        return jsonify(status="error", error="provider_key_required", provider=provider,
                       message="Connect your selected AI provider in Account to ask finance questions."), 409
    try:
        api_key = decrypt_api_key(credential.get("ciphertext", ""), email, provider=provider,
                                  aad_version=stored_credential_aad_version(provider, credential))
    except (CredentialConfigurationError, CredentialEncryptionError):
        return jsonify(status="error", error="credential_service_unavailable",
                       message="Secure credential storage is unavailable."), 503
    pack = build_context_pack(email, account_id)
    messages = history + [{"role": "user", "content": build_user_content(message, pack)}]
    try:
        answer = ai_service.finance_chat(SYSTEM_PROMPT, messages, email, api_key, provider, selection["model"])
    except (AIAuthenticationError, AIAuthorizationError, AIBillingError, AIRateLimitError, AIServiceError, ValidationError) as failure:
        mappings = [(AIAuthenticationError, "provider_key_invalid", "Your provider key is no longer valid.", 422),
                    (AIAuthorizationError, "provider_access_denied", "Your provider key does not allow this model.", 403),
                    (AIBillingError, "provider_billing_required", "Your provider account needs billing or credit.", 402),
                    (AIRateLimitError, "provider_rate_limited", "Your AI provider is busy. Try again shortly.", 429)]
        code, detail, status_code = "provider_unavailable", "Could not answer. Try again shortly.", 502
        for error_type, mapped_code, mapped_detail, mapped_status in mappings:
            if isinstance(failure, error_type):
                code, detail, status_code = mapped_code, mapped_detail, mapped_status
                break
        return jsonify(status="error", error=code, provider=provider, message=detail), status_code
    if len(answer) > 8000:
        answer = answer[:8000]
    status = finance_sync.sync_status(email, account_id)
    return jsonify(status="success", answer=answer, meta={
        "snapshot_id": snapshot["snapshot_id"],
        "rule_set_version": snapshot["rule_set_version"],
        "provider": provider,
        "model": selection["model"],
        "fetched_at": snapshot["fetched_at"],
        "stale": status.get("stale", False),
        "coverage": snapshot["coverage"],
        "privacy": PRIVACY_NOTE,
    })


@blueprint.get("/rules/history")
def rules_history():
    identity = g.finance_identity
    return jsonify(status="success", **list_history(identity["email"], identity["account_id"]))


@blueprint.post("/rules/restore/<version>")
def rules_restore(version):
    identity = g.finance_identity
    return jsonify(status="success", **restore_version(
        identity["email"], identity["account_id"], version, actor(identity)))
