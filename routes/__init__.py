"""Register feature blueprints without importing the application entry point."""


def register_routes(app):
    from . import ai_settings, auth, garmin, habits, health, nutrition, push

    for feature in (auth, ai_settings, nutrition, push, habits, garmin, health):
        app.register_blueprint(feature.blueprint)
