"""Authenticated Garmin milestone routes, registered with Janus's identity check."""

from flask import Blueprint, g, jsonify, request

from services import garmin_service
from services.garmin_errors import GarminError


def register_garmin_routes(app, authenticate):
    routes = Blueprint("garmin", __name__, url_prefix="/api/garmin")

    @routes.before_request
    def require_account():
        request.max_content_length = 8192
        if request.method == "OPTIONS":
            return None
        g.garmin_identity = authenticate()
        if not g.garmin_identity:
            return jsonify(status="error", error="unauthorized", message="Sign in to continue."), 401

    @routes.after_request
    def private_response(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    @routes.errorhandler(GarminError)
    def integration_error(error):
        response = jsonify(status="error", error=error.code, message=error.message, retry_after=error.retry_after)
        if error.retry_after:
            response.headers["Retry-After"] = str(error.retry_after)
        return response, error.status

    def identity():
        return g.garmin_identity["email"], g.garmin_identity["account_id"]

    @routes.route("/connection", methods=["GET", "PUT", "DELETE"])
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

    @routes.get("/data/steps")
    def steps():
        if set(request.args) != {"start", "end"} or any(len(request.args.getlist(k)) != 1 for k in request.args):
            raise GarminError("invalid_request", "Provide start and end dates only.", 400)
        return jsonify(status="success", **garmin_service.get_steps(*identity(), request.args["start"], request.args["end"]))

    @routes.post("/refresh")
    def refresh():
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) != {"resources", "start", "end"} or body["resources"] != ["steps"]:
            raise GarminError("invalid_request", "Select the steps resource and provide start and end dates.", 400)
        return jsonify(status="success", **garmin_service.get_steps(*identity(), body["start"], body["end"], force=True))

    app.register_blueprint(routes)
