"""Keyless, read-only Sheets credentials for the dedicated reader identity."""

import os
import re
import threading

import google.auth
from google.auth import impersonated_credentials
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request

READ_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"
CLOUD_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
_lock = threading.Lock()
_credentials = None
_target = None


class SheetsIdentityError(Exception):
    pass


def reader_email():
    value = os.environ.get("FINANCE_SHEETS_SERVICE_ACCOUNT", "").strip()
    return value if re.fullmatch(r"[a-z0-9-]+@[a-z0-9-]+\.iam\.gserviceaccount\.com", value) else None


def access_token():
    """Refresh on demand. The runtime/user ADC needs Token Creator on this reader."""
    global _credentials, _target
    target = reader_email()
    if not target:
        raise SheetsIdentityError("The Google Sheets reader has not been configured.")
    with _lock:
        try:
            if _credentials is None or _target != target:
                source, _project = google.auth.default(scopes=[CLOUD_SCOPE])
                _credentials = impersonated_credentials.Credentials(
                    source_credentials=source, target_principal=target,
                    target_scopes=[READ_SCOPE], lifetime=3600,
                )
                _target = target
            if not _credentials.valid:
                _credentials.refresh(Request())
            if not _credentials.token:
                raise SheetsIdentityError("The Google Sheets reader could not authenticate.")
            return _credentials.token
        except GoogleAuthError:
            _credentials, _target = None, None
            # SDK messages can contain credential details; return a fixed safe message.
            raise SheetsIdentityError("The Google Sheets reader could not authenticate. Check its cloud permissions.") from None
