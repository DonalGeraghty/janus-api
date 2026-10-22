"""Shared AI credential selection, ciphertext versions, and billing messages."""

from services.firebase_service import get_ai_credential, get_ai_selection
from services.ai_catalog import provider_name


def provider_billing_message(provider):
    return (
        f"Your {provider_name(provider)} API account needs available credit "
        "or a higher spending limit"
    )


def selected_ai_credential(email, account_id):
    ok, error, selection = get_ai_selection(email, account_id)
    if not ok:
        return None, None, "settings_service_unavailable"

    provider = selection["provider"]
    ok, error, credential = get_ai_credential(
        email,
        provider,
        account_id,
    )
    if not ok:
        return selection, None, "credential_service_unavailable"
    return selection, credential, None


def stored_credential_aad_version(provider, credential):
    aad_version = credential.get("aad_version")
    if aad_version is None:
        return 1 if provider == "openai" else 2
    return aad_version
