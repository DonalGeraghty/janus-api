"""Authenticated Garmin connection and cached data endpoints."""

from flask import Blueprint, g, jsonify, request
from services import garmin_service
from services.garmin_errors import GarminError
from core.request_auth import authenticated_identity


blueprint = Blueprint("garmin", __name__, url_prefix="/api/garmin")

@blueprint.before_request
def require_account():
    request.max_content_length = 8192
    if request.method == "OPTIONS":
        return None
    g.garmin_identity = authenticated_identity()
    if not g.garmin_identity:
        return jsonify(status="error", error="unauthorized", message="Sign in to continue."), 401

@blueprint.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    return response

@blueprint.errorhandler(GarminError)
def integration_error(error):
    response = jsonify(status="error", error=error.code, message=error.message, retry_after=error.retry_after)
    if error.retry_after:
        response.headers["Retry-After"] = str(error.retry_after)
    return response, error.status

def identity():
    return g.garmin_identity["email"], g.garmin_identity["account_id"]

@blueprint.route("/connection", methods=["GET", "PUT", "DELETE"])
def connection():
    email, account_id = identity()
    if request.method == "GET":
        result = garmin_service.get_connection(email, account_id)
    elif request.method == "PUT":
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) != {"api_key"}:
            raise GarminError("invalid_request", "Provide a Garmin personal API key.", 400)
        result = garmin_service.save_connection(email, account_id, body["api_key"])
    else:
        garmin_service.disconnect(email, account_id)
        result = {"configured": False}
    return jsonify(status="success", connection=result)

@blueprint.get("/data/steps")
def steps():
    if set(request.args) != {"start", "end"} or any(len(request.args.getlist(k)) != 1 for k in request.args):
        raise GarminError("invalid_request", "Provide start and end dates only.", 400)
    return jsonify(status="success", **garmin_service.get_steps(*identity(), request.args["start"], request.args["end"]))


@blueprint.get("/data/sleep")
def sleep():
    if set(request.args) != {"date"} or len(request.args.getlist("date")) != 1:
        raise GarminError("invalid_request", "Provide a single sleep date.", 400)
    return jsonify(status="success", **garmin_service.get_sleep(*identity(), request.args["date"]))


@blueprint.get("/data/activities")
def activities():
    if not {"start", "end"} <= set(request.args) <= {"start", "end", "limit"} or any(len(request.args.getlist(key)) != 1 for key in request.args):
        raise GarminError("invalid_request", "Provide start and end dates and an optional activity limit.", 400)
    try:
        limit = int(request.args.get("limit", "5"))
    except ValueError:
        raise GarminError("invalid_limit", "Activity limit must be an integer from 1 to 20.", 400) from None
    return jsonify(status="success", **garmin_service.get_activities(*identity(), request.args["start"], request.args["end"], limit))

@blueprint.post("/refresh")
def refresh():
    body = request.get_json(silent=True)
    if (not isinstance(body, dict) or not {"resources", "start", "end"} <= set(body) <= {"resources", "start", "end", "limit"}
            or not isinstance(body["resources"], list) or len(body["resources"]) != 1
            or body["resources"][0] not in ("steps", "sleep", "activities")):
        raise GarminError("invalid_request", "Select one of steps, sleep, or activities and provide start and end dates.", 400)
    resource = body["resources"][0]
    if resource != "activities" and "limit" in body:
        raise GarminError("invalid_request", "Only activities accepts a limit.", 400)
    if resource == "sleep":
        if body["start"] != body["end"]:
            raise GarminError("invalid_date_range", "Select a single sleep date.", 400)
        result = garmin_service.get_sleep(*identity(), body["start"], force=True)
    elif resource == "activities":
        result = garmin_service.get_activities(*identity(), body["start"], body["end"], body.get("limit", 5), force=True)
    else:
        result = garmin_service.get_steps(*identity(), body["start"], body["end"], force=True)
    return jsonify(status="success", **result)
