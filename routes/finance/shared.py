"""Finance blueprint, account gate, safe errors and request helpers."""

from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError

from core.request_auth import authenticated_identity
from services.firebase.finance.connections import FinanceConnectionError, has_finance_connection
from services.firebase.finance.rules import FinanceError

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
        code = error.details.get("code") if isinstance(error.details, dict) else None
        if code:
            body["error"] = code
            body["message"] = str(error)
    return jsonify(**body), error.status


@blueprint.errorhandler(ValidationError)
def invalid_rule(error):
    return jsonify(status="error", error="Invalid rule data",
                   message="; ".join(str(item) for item in error.errors()[:3])), 400


@blueprint.errorhandler(FinanceConnectionError)
def connection_error(error):
    return jsonify(status="error", error=str(error)), error.status


def payload(model, partial=False):
    return model.model_validate(request.get_json(silent=True) or {}).model_dump(mode="json", exclude_unset=partial)


def actor(identity):
    return identity["email"]
