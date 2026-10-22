"""Health HTTP endpoints."""

from flask import Blueprint, jsonify

from services.firebase_service import get_database_status


blueprint = Blueprint("health", __name__)


@blueprint.get("/health")
def health_check():
    return jsonify(status="healthy", database=get_database_status())


@blueprint.get("/")
def root():
    return jsonify(
        service="Janus API",
        endpoints={
            "register": "POST /api/auth/register",
            "login": "POST /api/auth/login",
            "current_user": "GET /api/auth/me",
            "delete_account": "DELETE /api/auth/account",
            "get_garmin_connection": "GET /api/garmin/connection",
            "set_garmin_connection": "PUT /api/garmin/connection",
            "disconnect_garmin": "DELETE /api/garmin/connection",
            "get_garmin_steps": "GET /api/garmin/data/steps?start=YYYY-MM-DD&end=YYYY-MM-DD",
            "refresh_garmin_steps": "POST /api/garmin/refresh",
            "get_ai_settings": "GET /api/user/ai-settings",
            "set_ai_settings": "PUT /api/user/ai-settings",
            "set_ai_credential": "PUT /api/user/ai-credentials/{provider}",
            "get_ai_credential_status": "GET /api/user/ai-credentials/{provider}",
            "delete_ai_credential": "DELETE /api/user/ai-credentials/{provider}",
            "set_openai_key": "PUT /api/user/openai-key",
            "get_openai_key_status": "GET /api/user/openai-key",
            "delete_openai_key": "DELETE /api/user/openai-key",
            "get_push_settings": "GET /api/user/push-settings",
            "set_push_settings": "PUT /api/user/push-settings",
            "add_push_subscription": "POST /api/user/push-subscriptions",
            "delete_push_subscription": "DELETE /api/user/push-subscriptions",
            "analyze_meal": "POST /api/nutrition/analyze",
            "recommend_meals": "POST /api/nutrition/recommend",
            "create_nutrition_entry": "POST /api/nutrition/entries",
            "list_nutrition_entries": "GET /api/nutrition/entries",
            "delete_nutrition_entry": "DELETE /api/nutrition/entries/{entry_id}",
            "update_nutrition_entry": "PUT /api/nutrition/entries/{entry_id}",
            "habits": "GET/POST /api/habits",
            "habit": "PUT/DELETE /api/habits/{habit_id}",
            "habit_checkins": "GET /api/habit-checkins; PUT /api/habits/{habit_id}/checkins/{date}",
            "habit_labels": "POST /api/habit-categories|habit-groups; PUT/DELETE /api/habit-categories|habit-groups/{id}",
            "habit_settings": "PUT /api/habits/settings",
            "draft_habits": "POST /api/habits/draft",
            "health": "GET /health",
        },
    )
