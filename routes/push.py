"""Push HTTP endpoints."""

import hmac
import os

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from core.push_service import (
    PushSettingsInput,
    PushSubscriptionDeleteInput,
    PushSubscriptionInput,
)
from services.firebase_service import (
    delete_push_subscription,
    get_push_settings,
    save_push_settings,
    save_push_subscription,
)
from services.web_push_service import dispatch_due_reminders, public_push_configuration
from core.request_auth import authenticated_identity
from services.logging_service import get_flask_app_logger


logger = get_flask_app_logger()
blueprint = Blueprint("push", __name__)


@blueprint.get("/api/user/push-settings")
def push_settings_get():
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    ok, error, settings = get_push_settings(
        identity["email"],
        identity["account_id"],
    )
    if not ok:
        logger.error("Push settings read failed: %s", error)
        return jsonify(status="error", error="Could not load push settings"), 500
    return jsonify(
        status="success",
        settings=settings,
        push=public_push_configuration(),
    )


@blueprint.put("/api/user/push-settings")
def push_settings_put():
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    try:
        settings_input = PushSettingsInput.model_validate(
            request.get_json(silent=True) or {}
        )
    except ValidationError:
        return jsonify(status="error", error="Invalid push settings"), 400
    configuration = public_push_configuration()
    if settings_input.enabled and not configuration["configured"]:
        return jsonify(
            status="error",
            error="push_not_configured",
            message="Push reminders are not configured on the server",
        ), 503
    settings = settings_input.model_dump()
    saved, error = save_push_settings(
        identity["email"],
        identity["account_id"],
        settings,
    )
    if not saved:
        logger.error("Push settings write failed: %s", error)
        return jsonify(status="error", error="Could not save push settings"), 500
    return jsonify(status="success", settings=settings)


@blueprint.post("/api/user/push-subscriptions")
def push_subscription_post():
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    try:
        subscription_input = PushSubscriptionInput.model_validate(
            request.get_json(silent=True) or {}
        )
    except ValidationError:
        return jsonify(status="error", error="Invalid push subscription"), 400
    if not public_push_configuration()["configured"]:
        return jsonify(
            status="error",
            error="push_not_configured",
            message="Push reminders are not configured on the server",
        ), 503
    saved, error = save_push_subscription(
        identity["email"],
        identity["account_id"],
        subscription_input.model_dump(),
    )
    if not saved:
        logger.error("Push subscription write failed: %s", error)
        return jsonify(status="error", error="Could not save push subscription"), 500
    return jsonify(status="success"), 201


@blueprint.delete("/api/user/push-subscriptions")
def push_subscription_delete():
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    try:
        subscription_input = PushSubscriptionDeleteInput.model_validate(
            request.get_json(silent=True) or {}
        )
    except ValidationError:
        return jsonify(status="error", error="Invalid push subscription"), 400
    deleted, error = delete_push_subscription(
        identity["email"],
        identity["account_id"],
        subscription_input.endpoint,
    )
    if not deleted:
        logger.error("Push subscription delete failed: %s", error)
        return jsonify(status="error", error="Could not delete push subscription"), 500
    return jsonify(status="success")


@blueprint.post("/api/internal/push/reminders")
def push_reminders_dispatch():
    expected_secret = os.environ.get("PUSH_CRON_SECRET", "")
    provided_secret = request.headers.get("X-Cron-Secret", "")
    if not expected_secret:
        return jsonify(status="error", error="Push scheduler is not configured"), 503
    if not provided_secret or not hmac.compare_digest(
        provided_secret,
        expected_secret,
    ):
        return jsonify(status="error", error="Unauthorized"), 401
    return jsonify(dispatch_due_reminders())
