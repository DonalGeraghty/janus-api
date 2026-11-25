"""Provider-neutral results for API credential validation."""

from dataclasses import dataclass


BILLING_REQUIRED = "provider_billing_required"


@dataclass(frozen=True)
class AICredentialValidation:
    """A normalized key plus any non-fatal provider warning."""

    api_key: str
    warning: str | None = None


def normalize_api_key(api_key):
    if not isinstance(api_key, str):
        raise ValueError("invalid_api_key")
    api_key = api_key.strip()
    if (
        len(api_key) < 20
        or len(api_key) > 512
        or any(char.isspace() for char in api_key)
    ):
        raise ValueError("invalid_api_key")
    return api_key
