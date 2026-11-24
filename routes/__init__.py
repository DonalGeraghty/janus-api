"""Register feature blueprints without importing the application entry point."""


def register_routes(app):
    from . import ai_settings, auth, finance, habits, health, nutrition, push

    for feature in (auth, ai_settings, nutrition, push, habits, health, finance):
        app.register_blueprint(feature.blueprint)
