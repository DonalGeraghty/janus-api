"""Read-only finance questions answered from server-computed context."""

from flask import g, jsonify, request
from pydantic import ValidationError

from core.finance.chat import (
    PRIVACY_NOTE, SYSTEM_PROMPT, build_context_pack, build_user_content,
    sanitize_history, sanitize_message,
)
from services import ai_service
from services.finance import sync as finance_sync
from services.ai_credentials import selected_ai_credential, stored_credential_aad_version
from services.ai_errors import (
    AIAuthenticationError, AIAuthorizationError, AIBillingError,
    AIRateLimitError, AIServiceError,
)
from services.credential_service import (
    CredentialConfigurationError,
    CredentialEncryptionError,
    decrypt_api_key,
)
from .shared import blueprint


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
    snapshot = finance_sync.get_snapshot(email, account_id)
    if snapshot is None:
        return jsonify(status="error", error="sync_required",
                       message="Sync the ledger first (POST /api/finance/sync)."), 409
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
