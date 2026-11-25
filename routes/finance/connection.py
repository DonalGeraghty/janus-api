"""Connect or disconnect the account's read-only Google Sheets workbook."""

from flask import g, jsonify, request

from services.finance import connection as finance_connection_setup
from services.finance.connection import WORKBOOK_PATTERN as WORKBOOK_ID_PATTERN
from services.credential_service import (
    CredentialConfigurationError,
    CredentialEncryptionError,
    encrypt_api_key,
)
from services.firebase.finance.connections import (
    delete_finance_connection,
    get_finance_connection_status,
    save_finance_connection,
)
from .shared import blueprint


@blueprint.get("/connection")
def connection_status():
    identity = g.finance_identity
    return jsonify(status="success", connection=get_finance_connection_status(identity["email"], identity["account_id"]))


@blueprint.put("/connection")
def connection_save():
    identity = g.finance_identity
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify(status="error", error="Supply a connection object."), 400
    mode = data.get("mode", "access_token" if "access_token" in data else "service_account")
    if mode == "service_account":
        status = finance_connection_setup.connect(identity["email"], identity["account_id"], data.get("workbook_id"))
        return jsonify(status="success", connection=status)
    if mode != "access_token":
        return jsonify(status="error", error="Unsupported connection mode."), 400
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
