"""Nutrition HTTP endpoints."""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from core.nutrition_service import MealRecommendationInput, NutritionEntryInput
from services.firebase_service import (
    create_nutrition_entry,
    delete_nutrition_entry,
    list_nutrition_entries,
    update_nutrition_entry,
)
from services.credential_service import (
    CredentialConfigurationError,
    CredentialEncryptionError,
    decrypt_api_key,
)
from services.ai_catalog import provider_name
from services.ai_errors import (
    AIAuthenticationError,
    AIAuthorizationError,
    AIBillingError,
    AIRateLimitError,
    AIServiceError,
)
from services.ai_service import analyze_meal, recommend_meals
from services.ai_contract import MAX_MEAL_MESSAGE_LENGTH
from core.request_auth import authenticated_identity
from services.ai_credentials import (
    provider_billing_message,
    selected_ai_credential,
    stored_credential_aad_version,
)
from services.logging_service import get_flask_app_logger


logger = get_flask_app_logger()
blueprint = Blueprint("nutrition", __name__)


@blueprint.post("/api/nutrition/analyze")
def nutrition_analyze():
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    email = identity["email"]

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify(status="error", error="Message is required"), 400
    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        return jsonify(status="error", error="Message is required"), 400
    if len(message.strip()) > MAX_MEAL_MESSAGE_LENGTH:
        return jsonify(status="error", error="Message must be 2000 characters or fewer"), 400

    selection, credential, error = selected_ai_credential(
        email,
        identity["account_id"],
    )
    if error:
        logger.error("Credential read failed for %s: %s", email, error)
        return jsonify(
            status="error",
            error=error,
            message=(
                "AI settings are unavailable"
                if error == "settings_service_unavailable"
                else "Secure credential storage is unavailable"
            ),
        ), 503
    if not credential:
        provider = selection["provider"]
        return jsonify(
            status="error",
            error="provider_key_required",
            provider=provider,
            message=(
                f"Add your {provider_name(provider)} API key before analyzing meals"
            ),
        ), 409

    provider = selection["provider"]
    model = selection["model"]
    try:
        api_key = decrypt_api_key(
            credential.get("ciphertext", ""),
            email,
            provider=provider,
            aad_version=stored_credential_aad_version(provider, credential),
        )
        analysis = analyze_meal(message, email, api_key, provider, model)
    except ValueError as error:
        message = (
            "Message must be 2000 characters or fewer"
            if str(error) == "message_too_long"
            else "Message is required"
        )
        return jsonify(status="error", error=message), 400
    except (CredentialConfigurationError, CredentialEncryptionError) as error:
        logger.error("Credential decryption unavailable: %s", type(error).__name__)
        return jsonify(
            status="error",
            error="credential_service_unavailable",
            message="Secure credential storage is unavailable",
        ), 503
    except AIAuthenticationError:
        return jsonify(
            status="error",
            error="provider_key_invalid",
            provider=provider,
            message=f"Your {provider_name(provider)} API key is no longer valid",
        ), 422
    except AIAuthorizationError:
        return jsonify(
            status="error",
            error="provider_access_denied",
            provider=provider,
            message=(
                f"Your {provider_name(provider)} API key does not have the "
                "required API access"
            ),
        ), 403
    except AIBillingError:
        return jsonify(
            status="error",
            error="provider_billing_required",
            provider=provider,
            message=provider_billing_message(provider),
        ), 402
    except AIRateLimitError:
        return jsonify(
            status="error",
            error="provider_rate_limited",
            provider=provider,
            message="Meal analysis is temporarily busy",
        ), 429
    except AIServiceError as error:
        logger.error("Meal analysis failed: %s", error)
        return jsonify(
            status="error",
            error="provider_unavailable",
            provider=provider,
            message="Meal analysis failed",
        ), 502

    return jsonify(status="success", analysis=analysis)


@blueprint.post("/api/nutrition/recommend")
def nutrition_recommend():
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    email = identity["email"]

    try:
        recommendation_input = MealRecommendationInput.model_validate(
            request.get_json(silent=True) or {}
        )
    except ValidationError:
        return jsonify(
            status="error",
            error="invalid_recommendation_request",
            message="Enter valid nutrition targets and choose one to three meals",
        ), 400

    selection, credential, error = selected_ai_credential(
        email,
        identity["account_id"],
    )
    if error:
        logger.error("Credential read failed for %s: %s", email, error)
        return jsonify(
            status="error",
            error=error,
            message=(
                "AI settings are unavailable"
                if error == "settings_service_unavailable"
                else "Secure credential storage is unavailable"
            ),
        ), 503
    if not credential:
        provider = selection["provider"]
        return jsonify(
            status="error",
            error="provider_key_required",
            provider=provider,
            message=(
                f"Add your {provider_name(provider)} API key before requesting "
                "meal recommendations"
            ),
        ), 409

    provider = selection["provider"]
    model = selection["model"]
    try:
        api_key = decrypt_api_key(
            credential.get("ciphertext", ""),
            email,
            provider=provider,
            aad_version=stored_credential_aad_version(provider, credential),
        )
        recommendation = recommend_meals(
            recommendation_input, email, api_key, provider, model
        )
    except (CredentialConfigurationError, CredentialEncryptionError) as error:
        logger.error("Credential decryption unavailable: %s", type(error).__name__)
        return jsonify(
            status="error",
            error="credential_service_unavailable",
            message="Secure credential storage is unavailable",
        ), 503
    except AIAuthenticationError:
        return jsonify(
            status="error",
            error="provider_key_invalid",
            provider=provider,
            message=f"Your {provider_name(provider)} API key is no longer valid",
        ), 422
    except AIAuthorizationError:
        return jsonify(
            status="error",
            error="provider_access_denied",
            provider=provider,
            message=(
                f"Your {provider_name(provider)} API key does not have the "
                "required API access"
            ),
        ), 403
    except AIBillingError:
        return jsonify(
            status="error",
            error="provider_billing_required",
            provider=provider,
            message=provider_billing_message(provider),
        ), 402
    except AIRateLimitError:
        return jsonify(
            status="error",
            error="provider_rate_limited",
            provider=provider,
            message="Meal recommendations are temporarily busy",
        ), 429
    except AIServiceError as error:
        logger.error("Meal recommendation failed: %s", error)
        return jsonify(
            status="error",
            error="provider_unavailable",
            provider=provider,
            message="Meal recommendation failed",
        ), 502

    return jsonify(status="success", recommendation=recommendation)


@blueprint.post("/api/nutrition/entries")
def nutrition_entries_create():
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    email = identity["email"]

    try:
        entry_input = NutritionEntryInput.model_validate(request.get_json(silent=True) or {})
    except ValidationError:
        return jsonify(status="error", error="Invalid nutrition entry"), 400

    items = [item.model_dump() for item in entry_input.items]
    created, error, entry = create_nutrition_entry(
        email,
        items,
        entry_input.eaten_at,
        entry_input.source_message,
        identity["account_id"],
        (
            str(entry_input.client_request_id)
            if entry_input.client_request_id
            else None
        ),
    )
    if not created:
        logger.error("Nutrition entry create failed for %s: %s", email, error)
        return jsonify(status="error", error="Could not save nutrition entry"), 500
    return jsonify(status="success", entry=entry), 201


@blueprint.get("/api/nutrition/entries")
def nutrition_entries_list():
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    email = identity["email"]

    date_value = None
    date_text = request.args.get("date")
    all_text = request.args.get("all")
    if all_text not in (None, "true"):
        return jsonify(
            status="error",
            error="All must be true when supplied",
        ), 400
    all_entries_requested = all_text == "true"
    if date_text:
        try:
            date_value = datetime.strptime(date_text, "%Y-%m-%d").date()
        except ValueError:
            return jsonify(status="error", error="Date must use YYYY-MM-DD"), 400

    start_value = None
    end_value = None
    start_text = request.args.get("start")
    end_text = request.args.get("end")
    if all_entries_requested and (
        date_text
        or start_text
        or end_text
        or request.args.get("limit") is not None
    ):
        return jsonify(
            status="error",
            error="All cannot be combined with date, start/end, or limit",
        ), 400
    if bool(start_text) != bool(end_text):
        return jsonify(
            status="error",
            error="Start and end must be supplied together",
        ), 400
    if date_text and start_text:
        return jsonify(
            status="error",
            error="Use either date or start/end, not both",
        ), 400
    if start_text and end_text:
        try:
            start_value = datetime.fromisoformat(
                start_text.replace("Z", "+00:00")
            )
            end_value = datetime.fromisoformat(
                end_text.replace("Z", "+00:00")
            )
            if (
                start_value.tzinfo is None
                or start_value.utcoffset() is None
                or end_value.tzinfo is None
                or end_value.utcoffset() is None
            ):
                raise ValueError
            start_value = start_value.astimezone(timezone.utc)
            end_value = end_value.astimezone(timezone.utc)
        except ValueError:
            return jsonify(
                status="error",
                error="Start and end must be timezone-aware ISO-8601 datetimes",
            ), 400
        if end_value <= start_value:
            return jsonify(
                status="error",
                error="End must be later than start",
            ), 400
        if end_value - start_value > timedelta(days=8):
            return jsonify(
                status="error",
                error="Date range cannot exceed eight days",
            ), 400

    if all_entries_requested:
        limit = None
    else:
        range_requested = start_value is not None
        default_limit = "500" if range_requested else "50"
        maximum_limit = 500 if range_requested else 100
        try:
            limit = min(
                max(int(request.args.get("limit", default_limit)), 1),
                maximum_limit,
            )
        except ValueError:
            return jsonify(status="error", error="Limit must be a number"), 400

    ok, error, entries = list_nutrition_entries(
        email=email,
        date_value=date_value,
        limit=None if all_entries_requested else limit + 1,
        account_id=identity["account_id"],
        start_value=start_value,
        end_value=end_value,
    )
    if not ok:
        logger.error("Nutrition entry list failed for %s: %s", email, error)
        return jsonify(status="error", error="Could not load nutrition entries"), 500
    truncated = False if all_entries_requested else len(entries) > limit
    response_entries = entries if all_entries_requested else entries[:limit]
    return jsonify(
        status="success",
        entries=response_entries,
        pagination={
            "start": start_value.isoformat() if start_value else None,
            "end": end_value.isoformat() if end_value else None,
            "limit": limit,
            "truncated": truncated,
        },
    )


@blueprint.delete("/api/nutrition/entries/<entry_id>")
def nutrition_entry_delete(entry_id):
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    email = identity["email"]

    deleted, error = delete_nutrition_entry(
        email,
        entry_id,
        identity["account_id"],
    )
    if error == "invalid_entry_id":
        return jsonify(status="error", error="Invalid nutrition entry ID"), 400
    if error == "not_found":
        return jsonify(status="error", error="Nutrition entry not found"), 404
    if not deleted:
        logger.error("Nutrition entry delete failed for %s: %s", email, error)
        return jsonify(status="error", error="Could not delete nutrition entry"), 500
    return jsonify(status="success")


@blueprint.put("/api/nutrition/entries/<entry_id>")
def nutrition_entry_update(entry_id):
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    email = identity["email"]

    try:
        entry_input = NutritionEntryInput.model_validate(request.get_json(silent=True) or {})
    except ValidationError:
        return jsonify(status="error", error="Invalid nutrition entry"), 400

    updated, error, entry = update_nutrition_entry(
        email,
        entry_id,
        [item.model_dump() for item in entry_input.items],
        entry_input.eaten_at,
        entry_input.source_message,
        identity["account_id"],
    )
    if error == "invalid_entry_id":
        return jsonify(status="error", error="Invalid nutrition entry ID"), 400
    if error == "not_found":
        return jsonify(status="error", error="Nutrition entry not found"), 404
    if not updated:
        logger.error("Nutrition entry update failed for %s: %s", email, error)
        return jsonify(status="error", error="Could not update nutrition entry"), 500
    return jsonify(status="success", entry=entry)
