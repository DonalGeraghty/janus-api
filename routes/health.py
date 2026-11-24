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
            "finance_connection": "GET/PUT/DELETE /api/finance/connection",
            "finance_sync": "POST /api/finance/sync; GET /api/finance/sync/status",
            "finance_transactions": "GET /api/finance/transactions?period=&start=&end=&month=&type=&category=&merchant=&account=&search=&sort=&order=&limit=&offset=",
            "finance_summary": "GET /api/finance/summary?period=|start=&end=",
            "finance_cashflow": "GET /api/finance/cashflow?period=&by=month|category",
            "finance_categories": "GET /api/finance/categories?period=",
            "finance_merchants": "GET /api/finance/merchants?period=",
            "finance_trends": "GET /api/finance/trends?period=",
            "finance_net_worth": "GET /api/finance/net-worth",
            "finance_sinking_funds": "GET /api/finance/sinking-funds",
            "finance_budgets": "GET /api/finance/budgets",
            "finance_chat": "POST /api/finance/chat {message, history}",
            "finance_rules": "GET/POST /api/finance/rules; PUT/DELETE /api/finance/rules/{rule_id}",
            "finance_rules_import": "POST /api/finance/rules/import (preview or commit)",
            "finance_rules_export": "GET /api/finance/rules/export?format=csv|json",
            "finance_rules_test": "POST /api/finance/rules/test",
            "finance_rules_history": "GET /api/finance/rules/history; POST /api/finance/rules/restore/{version}",
            "health": "GET /health",
        },
    )
