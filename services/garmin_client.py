"""Bounded HTTPS access to Garmin Personal API; no credential files or redirects."""

import json
import math
import time
from http.client import HTTPException
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

import jwt

from .garmin_errors import GarminError

BASE_URL = "https://personal.connectapi.garmin.com"
TOKEN_PATH = "/personalapitoken-service/personal-api/personal-api-key/token"
MAX_RESPONSE_BYTES = 256 * 1024


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _retry_delay(value):
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        try:
            seconds = math.ceil((parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            seconds = 60
    return min(86400, max(1, seconds))


def _request(path, authorization, method="GET"):
    request = Request(BASE_URL + path, headers={"Authorization": authorization, "Accept": "*/*"}, method=method)
    try:
        with build_opener(_NoRedirect()).open(request, timeout=12) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise GarminError("garmin_invalid_response", "Garmin returned too much data.")
        return body.decode("utf-8")
    except HTTPError as error:
        if error.code in (401, 403):
            raise GarminError("garmin_reconnect_required", "Garmin rejected this connection. Replace your personal API key.", 409) from None
        if error.code == 429:
            raise GarminError("garmin_rate_limited", "Garmin is rate limiting requests. Try again later.", 429, _retry_delay(error.headers.get("Retry-After"))) from None
        raise GarminError("garmin_unavailable", "Garmin is temporarily unavailable.") from None
    except (URLError, OSError, UnicodeError, ValueError, HTTPException):
        raise GarminError("garmin_unavailable", "Could not reach Garmin. Try again later.") from None


def obtain_token(api_key):
    token = _request(TOKEN_PATH, f"ApiKey {api_key}", "POST").strip()
    try:
        # TLS authenticates the token endpoint. Decode exp only for scheduling;
        # these claims never authenticate a Janus user.
        expires_at = float(jwt.decode(token, options={"verify_signature": False})["exp"])
        if not math.isfinite(expires_at) or expires_at <= time.time():
            raise ValueError("expired")
    except (jwt.PyJWTError, KeyError, TypeError, ValueError, OverflowError):
        raise GarminError("garmin_invalid_response", "Garmin returned an invalid access token.") from None
    return token, expires_at


def fetch_steps(token, start, end):
    body = _request(f"/usersummary-service/stats/steps/daily/{start}/{end}", f"Bearer {token}")
    try:
        data = json.loads(body)
        if not isinstance(data, list) or len(data) > 28:
            raise ValueError("shape")
        seen = set()
        for row in data:
            day = row["calendarDate"]
            if not isinstance(day, str) or not start <= day <= end or day in seen:
                raise ValueError("date")
            if datetime.strptime(day, "%Y-%m-%d").date().isoformat() != day:
                raise ValueError("date format")
            seen.add(day)
            for field in ("totalSteps", "totalDistance", "stepGoal"):
                value = row.get(field)
                if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                    raise ValueError("measurement")
        return data
    except (ValueError, TypeError, KeyError):
        raise GarminError("garmin_invalid_response", "Garmin returned unexpected steps data.") from None
