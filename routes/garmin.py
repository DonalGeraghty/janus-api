"""Authenticated Garmin connection and cached data endpoints."""

from flask import Blueprint, g, jsonify, request
from services import garmin_service
from services.garmin_errors import GarminError
from core.request_auth import authenticated_identity
from services.garmin_catalog import HEALTH_RESOURCES, PANEL_IDS
from services.firebase.garmin import preferences as stored_preferences


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


@blueprint.route("/preferences", methods=["GET", "PUT"])
def preferences():
    panels = None
    if request.method == "PUT":
        body = request.get_json(silent=True)
        if (not isinstance(body, dict) or set(body) != {"visible_panels"}
                or not isinstance(body["visible_panels"], list)
                or len(body["visible_panels"]) > len(PANEL_IDS)
                or any(not isinstance(panel, str) or panel not in PANEL_IDS for panel in body["visible_panels"])
                or len(set(body["visible_panels"])) != len(body["visible_panels"])):
            raise GarminError("invalid_preferences", "Select valid dashboard panels without duplicates.", 400)
        panels = body["visible_panels"]
    return jsonify(status="success", preferences=stored_preferences(*identity(), panels))


@blueprint.get("/data/<resource>")
def health_resource(resource):
    if resource not in HEALTH_RESOURCES:
        raise GarminError("invalid_resource", "Unknown Garmin resource.", 404)
    if set(request.args) != {"start", "end"} or any(len(request.args.getlist(key)) != 1 for key in request.args):
        raise GarminError("invalid_request", "Provide start and end dates only.", 400)
    return jsonify(status="success", **garmin_service.get_health(*identity(), resource, request.args["start"], request.args["end"]))


@blueprint.route("/activities/<int:activity_id>", methods=["GET", "POST"])
@blueprint.route("/activities/<int:activity_id>/workouts", methods=["GET", "POST"])
def activity_detail(activity_id):
    if request.args or request.get_data():
        raise GarminError("invalid_request", "This activity request accepts no additional parameters.", 400)
    return jsonify(status="success", **garmin_service.get_activity(*identity(), activity_id,
                    workouts=request.path.endswith("/workouts"), force=request.method == "POST"))

@blueprint.get("/data/steps")
def steps():
    if set(request.args) != {"start", "end"} or any(len(request.args.getlist(k)) != 1 for k in request.args):
        raise GarminError("invalid_request", "Provide start and end dates only.", 400)
    return jsonify(status="success", **garmin_service.get_steps(*identity(), request.args["start"], request.args["end"]))


@blueprint.get("/data/sleep")
def sleep():
    if any(len(request.args.getlist(key)) != 1 for key in request.args):
        raise GarminError("invalid_request", "Provide a sleep date or start and end dates.", 400)
    if set(request.args) == {"date"}:
        result = garmin_service.get_sleep(*identity(), request.args["date"])
    elif set(request.args) == {"start", "end"}:
        result = garmin_service.get_sleep_history(*identity(), request.args["start"], request.args["end"])
    else:
        raise GarminError("invalid_request", "Provide a sleep date or start and end dates.", 400)
    return jsonify(status="success", **result)


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
            or not isinstance(body["resources"][0], str)
            or body["resources"][0] not in PANEL_IDS):
        raise GarminError("invalid_request", "Select one Garmin resource and provide start and end dates.", 400)
    resource = body["resources"][0]
    if resource != "activities" and "limit" in body:
        raise GarminError("invalid_request", "Only activities accepts a limit.", 400)
    if resource in HEALTH_RESOURCES:
        result = garmin_service.get_health(*identity(), resource, body["start"], body["end"], force=True)
    elif resource == "sleep":
        if body["start"] == body["end"]:
            result = garmin_service.get_sleep(*identity(), body["start"], force=True)
        else:
            result = garmin_service.get_sleep_history(*identity(), body["start"], body["end"], force=True)
    elif resource == "activities":
        result = garmin_service.get_activities(*identity(), body["start"], body["end"], body.get("limit", 5), force=True)
    else:
        result = garmin_service.get_steps(*identity(), body["start"], body["end"], force=True)
    return jsonify(status="success", **result)
