"""Resolve a request's JWT against the current shared account generation."""

from flask import request
from core.auth_service import decode_access_token
from services.firebase_service import get_user_record
from services.firebase.account_state import account_id_matches


def bearer_token():
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        return token.strip()
    return None


def authenticated_identity():
    identity = decode_access_token(bearer_token())
    if not identity:
        return None
    user = get_user_record(identity["email"])
    if not user or not account_id_matches(identity["account_id"], user):
        return None
    return identity
