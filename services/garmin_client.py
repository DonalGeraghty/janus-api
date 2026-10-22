"""Bounded HTTPS access to Garmin Personal API; no credential files or redirects."""

import json
import math
import logging
import re
import time
from http.client import HTTPException
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.parse import urlencode

import jwt

from .garmin_errors import GarminError

BASE_URL = "https://personal.connectapi.garmin.com"
TOKEN_PATH = "/personalapitoken-service/personal-api/personal-api-key/token"
MAX_RESPONSE_BYTES = 256 * 1024
logger = logging.getLogger("janus-api.garmin.client")


def _endpoint_label(path):
    path = re.sub(r"/\d{4}-\d{2}-\d{2}(?=/|$)", "/{date}", path.split("?", 1)[0])
    return re.sub(r"/[0-9]+(?=/|$)", "/{id}", path)


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
    started = time.monotonic()
    request = Request(BASE_URL + path, headers={"Authorization": authorization, "Accept": "*/*"}, method=method)
    try:
        with build_opener(_NoRedirect()).open(request, timeout=12) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise GarminError("garmin_invalid_response", "Garmin returned too much data.")
        return body.decode("utf-8")
    except HTTPError as error:
        logger.warning("Garmin upstream failure endpoint=%s status=%s duration_ms=%.0f",
                       _endpoint_label(path), error.code, (time.monotonic() - started) * 1000)
        if error.code in (401, 403):
            raise GarminError("garmin_reconnect_required", "Garmin rejected this connection. Replace your personal API key.", 409) from None
        if error.code == 429:
            raise GarminError("garmin_rate_limited", "Garmin is rate limiting requests. Try again later.", 429, _retry_delay(error.headers.get("Retry-After"))) from None
        if error.code == 404 and path.startswith("/activity-service/activity/"):
            raise GarminError("garmin_not_found", "This Garmin activity is no longer available.", 404) from None
        raise GarminError("garmin_unavailable", "Garmin is temporarily unavailable.") from None
    except (URLError, OSError, UnicodeError, ValueError, HTTPException):
        logger.warning("Garmin upstream transport failure endpoint=%s duration_ms=%.0f",
                       _endpoint_label(path), (time.monotonic() - started) * 1000)
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


def _json_response(path, token):
    try:
        body = _request(path, f"Bearer {token}")
        return json.loads(body) if body.strip() else None
    except ValueError:
        raise GarminError("garmin_invalid_response", "Garmin returned unexpected data.") from None


def _measurement(value):
    if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
        raise ValueError("measurement")


def fetch_sleep(token, day):
    data = _json_response("/sleep-service/sleep/dailySleep?" + urlencode({"date": day}), token)
    return _validate_sleep(data, day)


def fetch_sleep_history(token, start, end):
    query = urlencode({"startDate": start, "endDate": end})
    data = _json_response("/sleep-service/sleep/dailySleepSummariesByDate?" + query, token)
    if data is None:
        return []
    if not isinstance(data, list) or len(data) > 28:
        raise GarminError("garmin_invalid_response", "Garmin returned unexpected sleep history: response array.")
    records, seen = [], set()
    for row in data:
        if not isinstance(row, dict):
            raise GarminError("garmin_invalid_response", "Garmin returned unexpected sleep history: record object.")
        day = row.get("calendarDate")
        if day is None or day == "":
            # Validate an empty record using the same rules as single-day sleep.
            _validate_sleep(row, start)
            continue
        if not isinstance(day, str) or not start <= day <= end or day in seen:
            raise GarminError("garmin_invalid_response", "Garmin returned unexpected sleep history: calendarDate range or duplicate.")
        validated = _validate_sleep(row, day)
        if validated is not None:
            seen.add(day)
            records.append(validated)
    return sorted(records, key=lambda row: row["calendarDate"])


def _validate_sleep(data, day):
    # Diagnostics contain only fixed field names, never response values or keys.
    invalid_field = "response object"
    try:
        if data is None:
            return None
        if not isinstance(data, dict):
            raise ValueError("shape")
        # Support a wrapped DTO as well as the flat shape in the Personal API spec.
        sleep = data.get("dailySleepDTO", data)
        if sleep is None:
            return None
        invalid_field = "dailySleepDTO object"
        if not isinstance(sleep, dict):
            raise ValueError("shape")
        if not sleep:
            return None
        invalid_field = "calendarDate (must be a YYYY-MM-DD date)"
        recorded_day = sleep.get("calendarDate", day)
        # An empty record, or a valid record for another day, does not supply
        # sleep for the requested date. Never display it under the wrong date.
        if recorded_day is None or recorded_day == "":
            logger.info("Garmin sleep unavailable reason=empty_calendar_date")
            return None
        if (not isinstance(recorded_day, str)
                or datetime.strptime(recorded_day, "%Y-%m-%d").date().isoformat() != recorded_day):
            raise ValueError("date")
        if recorded_day != day:
            logger.info("Garmin sleep unavailable reason=different_calendar_date")
            return None
        for field in ("sleepTimeSeconds", "deepSleepSeconds", "lightSleepSeconds", "remSleepSeconds", "awakeSleepSeconds"):
            invalid_field = field + " (must be a number or null)"
            _measurement(sleep.get(field))
        scores = sleep.get("sleepScores")
        if scores is not None:
            invalid_field = "sleepScores object"
            if not isinstance(scores, dict):
                raise ValueError("scores")
            for score in scores.values():
                if score is None:
                    continue
                invalid_field = "sleepScores entry (must be an object or null)"
                if not isinstance(score, dict):
                    raise ValueError("score")
                invalid_field = "sleepScores entry value (must be a number or null)"
                _measurement(score.get("value"))
        return data
    except (ValueError, TypeError):
        raise GarminError("garmin_invalid_response", f"Garmin returned unexpected sleep data: {invalid_field}.") from None


def fetch_activities(token, start, end, limit):
    query = urlencode({"start": 0, "limit": limit, "startDate": start, "endDate": end,
                       "sortBy": "startLocal", "sortOrder": "desc", "excludeChildren": "true"})
    data = _json_response("/activitylist-service/activities/search/activities?" + query, token)
    try:
        if not isinstance(data, list) or len(data) > limit:
            raise ValueError("shape")
        seen = set()
        for row in data:
            if not isinstance(row, dict):
                raise ValueError("activity")
            activity_id = row.get("activityId")
            if type(activity_id) is not int or activity_id < 0 or activity_id in seen:
                raise ValueError("id")
            seen.add(activity_id)
            for field in ("activityName", "startTimeLocal"):
                if row.get(field) is not None and not isinstance(row[field], str):
                    raise ValueError("text")
            local = row.get("startTimeLocal")
            if local and not start <= datetime.fromisoformat(local).date().isoformat() <= end:
                raise ValueError("date")
            if row.get("activityType") is not None and not isinstance(row["activityType"], dict):
                raise ValueError("type")
            for field in ("distance", "duration"):
                _measurement(row.get(field))
        return sorted(data, key=lambda item: (item.get("startTimeLocal") or "").replace("T", " "), reverse=True)
    except (ValueError, TypeError):
        raise GarminError("garmin_invalid_response", "Garmin returned unexpected activity data.") from None
