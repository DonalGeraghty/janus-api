"""Console logging helpers for Janus API."""

import logging
import os


def setup_logging(environment=None):
    environment = environment or os.environ.get("FLASK_ENV", "production")
    level = logging.DEBUG if environment == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return logging.getLogger("janus-api")


def get_logger(name, _environment=None):
    return logging.getLogger(name)


def get_flask_app_logger():
    return get_logger("flask_app")


logger = setup_logging()
