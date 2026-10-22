"""Registration, login, profile, and shared-account deletion endpoints."""

from flask import Blueprint, jsonify, request

from core.auth_service import (
    decode_access_token,
    login_user,
    register_user,
    verify_password,
)
from services.firebase_service import delete_user_account, get_user_record_for_account_deletion
from services.firebase.account_state import account_id_matches
from core.request_auth import authenticated_identity, bearer_token
from services.logging_service import get_flask_app_logger


logger = get_flask_app_logger()
blueprint = Blueprint("auth", __name__)


@blueprint.post("/api/auth/register")
def auth_register():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify(status="error", error="Invalid request"), 400
    payload, error, _ = register_user(data.get("email"), data.get("password"))

    if error == "invalid_email":
        return jsonify(status="error", error="Invalid email"), 400
    if error == "weak_password":
        return jsonify(status="error", error="Password must be at least 8 characters"), 400
    if error == "exists":
        return jsonify(status="error", error="An account with this email already exists"), 409
    if error:
        return jsonify(status="error", error="Registration failed"), 500

    return jsonify(
        status="success",
        token=payload["token"],
        user={
            "email": payload["email"],
            "account_id": payload["account_id"],
        },
    ), 201


@blueprint.post("/api/auth/login")
def auth_login():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify(status="error", error="Invalid email or password"), 401
    payload, error, _ = login_user(data.get("email"), data.get("password"))
    if error:
        return jsonify(status="error", error="Invalid email or password"), 401

    return jsonify(
        status="success",
        token=payload["token"],
        user={
            "email": payload["email"],
            "account_id": payload["account_id"],
        },
    )


@blueprint.get("/api/auth/me")
def auth_me():
    identity = authenticated_identity()
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    return jsonify(
        status="success",
        user={
            "email": identity["email"],
            "account_id": identity["account_id"],
        },
    )


@blueprint.delete("/api/auth/account")
def auth_delete_account():
    # Deletion must remain resumable while the account is tombstoned, so use
    # the deletion-aware lookup rather than the normal request identity helper.
    identity = decode_access_token(bearer_token())
    if not identity:
        return jsonify(status="error", error="Unauthorized"), 401
    email = identity["email"]
    user = get_user_record_for_account_deletion(email)
    if (
        not user
        or not account_id_matches(identity["account_id"], user)
    ):
        return jsonify(status="error", error="Unauthorized"), 401

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify(status="error", error="Invalid request"), 400
    password = data.get("password")
    if not isinstance(password, str) or not password:
        return jsonify(status="error", error="Password is required"), 400

    if not verify_password(password, user.get("password_hash")):
        return jsonify(status="error", error="Invalid password"), 401

    deleted, error = delete_user_account(email, identity["account_id"])
    if not deleted:
        logger.error("Could not delete account %s: %s", email, error)
        return jsonify(status="error", error="Could not delete account"), 500

    return jsonify(status="success")
