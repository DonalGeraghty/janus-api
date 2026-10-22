"""Bounded, documented Garmin dashboard reads and conservative shape validation."""

from urllib.parse import urlencode
from datetime import date

from .garmin_client import _json_response, _measurement
from .garmin_errors import GarminError


def _rows(data, start, end, day_key="calendarDate"):
    if data is None:
        return []
    if not isinstance(data, list) or len(data) > 28:
        raise ValueError("records array")
    seen, result = set(), []
    for row in data:
        if not isinstance(row, dict):
            raise ValueError("record object")
        day = row.get(day_key)
        if day is None or day == "":
            continue
        if (not isinstance(day, str) or date.fromisoformat(day).isoformat() != day
                or not start <= day <= end or day in seen):
            raise ValueError("record date")
        seen.add(day)
        result.append(row)
    return sorted(result, key=lambda row: row[day_key])


def _object(data):
    if not isinstance(data, dict):
        raise ValueError("response object")
    return data


def fetch_health(resource, token, start, end):
    """Retain all fields; validate the envelope and displayed numeric measurements."""
    query = urlencode({"startDate": start, "endDate": end})
    try:
        if resource in ("stress", "movement"):
            raw = _json_response("/usersummary-service/v2/dailysummaries?" + query, token)
            data = _rows(_object(raw).get("data") if raw is not None else None, start, end)
        elif resource == "hrv":
            raw = _json_response(f"/hrv-service/hrv/daily/{start}/{end}", token)
            data = _rows(_object(raw).get("hrvSummaries") if raw is not None else None, start, end)
            for row in data:
                for key in ("weeklyAvg", "lastNightAvg", "lastNight5MinHigh"):
                    _measurement(row.get(key))
        elif resource == "hydration":
            data = _rows(_json_response(f"/usersummary-service/stats/hydration/daily/{start}/{end}", token), start, end)
            for row in data:
                for key in ("valueInML", "goalInML", "sweatLossInML", "activityIntakeInML"):
                    _measurement(row.get(key))
        elif resource == "weight":
            raw = _json_response(f"/weight-service/weight/range/{start}/{end}?includeAll=false", token)
            data = _object(raw) if raw is not None else {"dailyWeightSummaries": []}
            data["dailyWeightSummaries"] = _rows(data.get("dailyWeightSummaries"), start, end, "summaryDate")
            for row in data["dailyWeightSummaries"]:
                latest = row.get("latestWeight")
                if latest is not None:
                    _object(latest)
                    for key in ("weight", "bmi", "bodyFat", "bodyWater", "muscleMass", "boneMass"):
                        _measurement(latest.get(key))
        else:
            raise GarminError("invalid_resource", "Unknown Garmin resource.", 400)
        return data
    except (ValueError, TypeError, KeyError):
        # Never include response values or upstream exception text in errors/logs.
        raise GarminError("garmin_invalid_response", f"Garmin returned unexpected {resource} data.") from None


def fetch_activity(token, activity_id, workouts=False):
    path = f"/activity-service/activity/{activity_id}" + ("/workouts" if workouts else "")
    data = _json_response(path, token)
    if workouts:
        if data is None:
            return []
        if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
            raise GarminError("garmin_invalid_response", "Garmin returned unexpected activity workouts.")
    elif data is not None:
        if not isinstance(data, dict) or data.get("activityId", activity_id) != activity_id:
            raise GarminError("garmin_invalid_response", "Garmin returned unexpected activity details.")
    return data
