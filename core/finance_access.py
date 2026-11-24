"""Server-side finance entitlement: only configured owner accounts may use /api/finance."""

import os


def normalize_email(email):
    return (email or "").strip().lower()


def finance_owner_emails():
    raw = os.getenv("FINANCE_OWNER_EMAILS", "")
    return {normalize_email(part) for part in raw.split(",") if normalize_email(part)}


def finance_authorized(identity):
    """A valid shared Janus login alone is insufficient; finance needs a listed owner."""
    if not identity:
        return False
    owners = finance_owner_emails()
    if not owners:
        return False
    return normalize_email(identity.get("email")) in owners
