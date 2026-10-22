"""Janus application setup and local development entry point."""

import os
import time

from flask import Flask, jsonify, request
from flask_cors import CORS

from routes import register_routes
from services.logging_service import get_flask_app_logger


logger = get_flask_app_logger()


def create_app(test_config=None):
    """Create an independently configured app with the same public API."""
    application = Flask(__name__)
    if test_config is not None:
        application.config.update(test_config)

    CORS(
        application,
        resources={r"/api/*": {"origins": "*"}},
        allow_headers=["Authorization", "Content-Type"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    @application.before_request
    def start_request_timer():
        request.start_time = time.monotonic()

    @application.after_request
    def log_response(response):
        duration_ms = (time.monotonic() - request.start_time) * 1000
        logger.info(
            "%s %s %s %.2fms",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response

    @application.errorhandler(404)
    def not_found(_error):
        return jsonify(status="error", error="Not found"), 404

    @application.errorhandler(500)
    def internal_error(error):
        logger.exception("Unhandled server error: %s", error)
        return jsonify(status="error", error="Internal server error"), 500

    register_routes(application)
    return application


# Preserve existing imports, Flask tooling, and the production/local entry point.
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
