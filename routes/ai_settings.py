"""Shared AI provider settings and encrypted credential endpoints."""

from flask import Blueprint, jsonify, request

from services.firebase_service import (
    delete_ai_credential,
    get_ai_credential_status,
    get_ai_selection,
    save_ai_credential,
    save_ai_selection,
)
from services.credential_service import (
    CredentialConfigurationError,
    CredentialEncryptionError,
    encrypt_api_key,
)
from services.ai_catalog import (
    SUPPORTED_PROVIDERS,
    is_supported_model,
    is_supported_provider,
    provider_name,
    public_provider_catalog,
)
from services.ai_errors import (
    AIAuthenticationError,
    AIAuthorizationError,
    AIBillingError,
    AIRateLimitError,
    AIServiceError,
)
from services.ai_service import validate_provider_api_key as validate_api_key
from core.request_auth import authenticated_identity
from services.ai_credentials import provider_billing_message
from services.logging_service import get_flask_app_logger


logger = get_flask_app_logger()
blueprint = Blueprint("ai_settings", __name__)


def _credential_error(provider, error, message, status_code, compatibility=False):
    if compatibility:
        error = {
            "provider_key_invalid": "openai_key_invalid",
            "provider_access_denied": "openai_access_denied",
            "provider_billing_required": "openai_billing_required",
            "provider_rate_limited": "openai_rate_limited",
            "provider_unavailable": "openai_unavailable",
        }.get(error, error)
    payload = {
        "status": "error",
        "error": error,
        "message": message,
    }
    if not compatibility:
        payload["provider"] = provider
    return jsonify(payload), status_code


def _put_ai_credential(provider, compatibility=False):
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="unauthorized"), 401
    email = identity["email"]
    if not is_supported_provider(provider):
        return jsonify(status="error", error="invalid_provider"), 400

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify(status="error", error="invalid_request"), 400
    try:
        validation = validate_api_key(provider, data.get("api_key"), email)
        if isinstance(validation, str):
            # Preserve compatibility with custom provider adapters using the
            # original string-only validation contract.
            api_key = validation
            validation_warning = None
        else:
            api_key = validation.api_key
            validation_warning = validation.warning
        ciphertext = encrypt_api_key(
            api_key, email, provider=provider, aad_version=2
        )
    except ValueError:
        display_name = provider_name(provider)
        return _credential_error(
            provider,
            "invalid_api_key",
            f"A valid {display_name} API key is required",
            400,
            compatibility,
        )
    except AIAuthenticationError:
        display_name = provider_name(provider)
        return _credential_error(
            provider,
            "provider_key_invalid",
            f"{display_name} rejected this API key",
            422,
            compatibility,
        )
    except AIAuthorizationError:
        display_name = provider_name(provider)
        return _credential_error(
            provider,
            "provider_access_denied",
            f"{display_name} accepted the key but denied the required API access",
            403,
            compatibility,
        )
    except AIBillingError:
        return _credential_error(
            provider,
            "provider_billing_required",
            provider_billing_message(provider),
            402,
            compatibility,
        )
    except AIRateLimitError:
        return _credential_error(
            provider,
            "provider_rate_limited",
            "The provider could not verify the key because it is rate limited",
            429,
            compatibility,
        )
    except AIServiceError:
        return _credential_error(
            provider,
            "provider_unavailable",
            "The provider could not verify the key",
            502,
            compatibility,
        )
    except (CredentialConfigurationError, CredentialEncryptionError) as error:
        logger.error("Credential encryption unavailable: %s", type(error).__name__)
        return jsonify(
            status="error",
            error="credential_service_unavailable",
            message="Secure credential storage is unavailable",
        ), 503

    saved, error, credential_status = save_ai_credential(
        email,
        provider,
        ciphertext,
        api_key[-4:],
        aad_version=2,
        account_id=identity["account_id"],
    )
    if not saved:
        logger.error(
            "Credential save failed for %s (%s): %s", email, provider, error
        )
        return jsonify(
            status="error",
            error="credential_service_unavailable",
            message="Secure credential storage is unavailable",
        ), 503
    payload = {"status": "success", "credential": credential_status}
    if not compatibility:
        payload["provider"] = provider
    if validation_warning == "provider_billing_required":
        payload["warning"] = {
            "code": validation_warning,
            "message": (
                f"The key was saved, but your {provider_name(provider)} API account "
                "needs available credit or a higher spending limit "
                "before AI features can run"
            ),
        }
    return jsonify(payload)


def _get_ai_credential_status_response(provider, compatibility=False):
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="unauthorized"), 401
    email = identity["email"]
    if not is_supported_provider(provider):
        return jsonify(status="error", error="invalid_provider"), 400

    ok, error, credential_status = get_ai_credential_status(
        email,
        provider,
        identity["account_id"],
    )
    if not ok:
        logger.error(
            "Credential status failed for %s (%s): %s", email, provider, error
        )
        return jsonify(
            status="error",
            error="credential_service_unavailable",
            message="Secure credential storage is unavailable",
        ), 503
    payload = {
        "status": "success",
        "credential": credential_status or {"configured": False},
    }
    if not compatibility:
        payload["provider"] = provider
    return jsonify(payload)


def _delete_ai_credential_response(provider, compatibility=False):
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="unauthorized"), 401
    email = identity["email"]
    if not is_supported_provider(provider):
        return jsonify(status="error", error="invalid_provider"), 400

    deleted, error = delete_ai_credential(
        email,
        provider,
        identity["account_id"],
    )
    if not deleted:
        logger.error(
            "Credential delete failed for %s (%s): %s", email, provider, error
        )
        return jsonify(
            status="error",
            error="credential_service_unavailable",
            message="Secure credential storage is unavailable",
        ), 503
    payload = {"status": "success"}
    if not compatibility:
        payload["provider"] = provider
    return jsonify(payload)


@blueprint.put("/api/user/ai-credentials/<provider>")
def ai_credential_put(provider):
    return _put_ai_credential(provider)


@blueprint.get("/api/user/ai-credentials/<provider>")
def ai_credential_get(provider):
    return _get_ai_credential_status_response(provider)


@blueprint.delete("/api/user/ai-credentials/<provider>")
def ai_credential_delete(provider):
    return _delete_ai_credential_response(provider)


@blueprint.put("/api/user/openai-key")
def openai_key_put():
    return _put_ai_credential("openai", compatibility=True)


@blueprint.get("/api/user/openai-key")
def openai_key_get():
    return _get_ai_credential_status_response("openai", compatibility=True)


@blueprint.delete("/api/user/openai-key")
def openai_key_delete():
    return _delete_ai_credential_response("openai", compatibility=True)


@blueprint.get("/api/user/ai-settings")
def ai_settings_get():
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="unauthorized"), 401
    email = identity["email"]

    ok, error, selection = get_ai_selection(
        email,
        identity["account_id"],
    )
    if not ok:
        logger.error("AI settings read failed for %s: %s", email, error)
        return jsonify(
            status="error",
            error="settings_service_unavailable",
            message="AI settings are unavailable",
        ), 503

    credential_statuses = {}
    for provider in SUPPORTED_PROVIDERS:
        credential_ok, credential_error, credential = get_ai_credential_status(
            email,
            provider,
            identity["account_id"],
        )
        if not credential_ok:
            logger.error(
                "Credential status failed for %s (%s): %s",
                email,
                provider,
                credential_error,
            )
            return jsonify(
                status="error",
                error="credential_service_unavailable",
                message="Secure credential storage is unavailable",
            ), 503
        credential_statuses[provider] = credential or {"configured": False}

    providers = public_provider_catalog()
    for provider in providers:
        provider["credential"] = credential_statuses[provider["id"]]

    return jsonify(
        status="success",
        selection=selection,
        providers=providers,
    )


@blueprint.put("/api/user/ai-settings")
def ai_settings_put():
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="unauthorized"), 401
    email = identity["email"]

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify(status="error", error="invalid_request"), 400
    provider = data.get("provider")
    model = data.get("model")
    if not is_supported_provider(provider):
        return jsonify(status="error", error="invalid_provider"), 400
    if not is_supported_model(provider, model):
        return jsonify(status="error", error="invalid_model"), 400

    saved, error, selection = save_ai_selection(
        email,
        provider,
        model,
        identity["account_id"],
    )
    if not saved:
        logger.error("AI settings save failed for %s: %s", email, error)
        return jsonify(
            status="error",
            error="settings_service_unavailable",
            message="AI settings could not be saved",
        ), 503
    return jsonify(status="success", selection=selection)
