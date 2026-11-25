"""Isolated local development harness. Production continues to use app:app.

Only external storage/Sheets boundaries are substituted; authentication,
ingestion, accounting, rules and HTTP routes are the real application code.
"""

import os
import secrets
from contextlib import ExitStack, contextmanager
from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

DEMO_EMAIL = "demo@minerva.local"
DEMO_PASSWORD = "minerva-demo"
WORKBOOK = "synthetic-local-demo-workbook"


def demo_grids(today=None):
    from core.finance.sheets import HEADER_TO_FIELD, SHEETS_EPOCH

    today = today or datetime.now(ZoneInfo("Europe/Dublin")).date()
    ledger = [list(HEADER_TO_FIELD)]
    wealth = [["Date", "SUPERSAVER", "BOI Goalsaver", "BOI Current Account",
               "Revolut", "Monzo", "Cash Totals", "Pension Mercer Workday",
               "Pension Efx New Ireland", "Pension SIE Zurich", "Pension Totals",
               "Dejiro", "Mortgage (Owed)", "Apartment Value"]]
    # Six months of invented data, dated no later than today.
    for offset in range(5, -1, -1):
        index = today.year * 12 + today.month - 1 - offset
        year, month = divmod(index, 12)
        month += 1
        day = date(year, month, 1)
        scenario = 5 - offset
        groceries = ["-468.20", "-512.40", "-436.85", "-494.60", "-458.30", "-476.45"][scenario]
        electricity = ["-142.80", "-168.50", "-156.90", "-121.40", "-182.60", "-149.20"][scenario]
        dining = ["-187.50", "-246.80", "-165.25", "-228.75", "-192.35", "-204.85"][scenario]
        refund = ["20.00", "0.00", "45.00", "0.00", "15.00", "35.00"][scenario]
        entries = [
            ("Salary", "Example Employer", "4250.00" if scenario == 3 else "4000.00", "Income", "Salary", "BOI"),
            ("Mortgage payment", "Example Mortgage", "-1200.00", "Expense", "Housing", "BOI"),
            ("Grocery shopping", "Example Market", groceries, "Expense", "Groceries", "REVOLUT"),
            ("Electricity", "Example Energy", electricity, "Expense", "Utilities", "BOI"),
            ("Dining out", "Example Cafe", dining, "Expense", "Dining", "MONZO"),
            ("Returned item", "Example Shop", refund, "Refund", "Shopping", "REVOLUT"),
            ("Household and transport", "Example Services", "-650.00", "Expense", "Living costs", "BOI"),
            ("Move to savings", "Own savings", "-300.00", "Transfer", "Savings", "BOI"),
            ("Savings received", "Own current account", "300.00", "Transfer", "Savings", "MONZO"),
        ]
        # Irregular costs and a bonus create four positive and two negative months.
        extras = {
            1: ("Summer holiday", "Example Travel", "-1900.00", "Expense", "Travel", "REVOLUT"),
            2: ("Car service and tyres", "Example Garage", "-990.00", "Expense", "Transport", "BOI"),
            3: ("Performance bonus", "Example Employer", "750.00", "Income", "Bonus", "BOI"),
            4: ("Appliance replacement", "Example Appliances", "-2100.00", "Expense", "Home", "BOI"),
        }
        if scenario in extras:
            entries.append(extras[scenario])
        entries = [entry for entry in entries if entry[2] != "0.00"]
        for number, (description, merchant, amount, kind, category, account) in enumerate(entries):
            ledger.append([f"DEMO-{day:%Y%m}-{number}", (day - SHEETS_EPOCH).days,
                           f"{day:%Y-%m}", account, description, merchant, amount, "0",
                           kind, category, "Demo", "synthetic fixture", "Imported",
                           "Invented local demo data", "", "YES", ""])
        wealth.append([(day - SHEETS_EPOCH).days, 10000, 5000, 3000 + (5-offset)*200,
                       500, 500, 19000 + (5-offset)*200, 50000, 20000, 10000,
                       80000, 12000, 180000, 300000])
    return ledger, wealth


@contextmanager
def demo_application(today=None):
    """Run only in a dedicated process; all demo state disappears on exit."""
    from flask import jsonify, request
    from services.firebase import db_state

    if db_state.db is not None or db_state.users_collection_ref is not None:
        raise RuntimeError("Start the demo in a fresh process, without an initialized database.")

    with ExitStack() as stack:
        stack.enter_context(patch.dict(os.environ, {
            "FLASK_ENV": "development", "JWT_SECRET_KEY": secrets.token_urlsafe(48),
        }))
        # Installed cloud credentials are never used by this entry point.
        stack.enter_context(patch("services.firebase_service.initialize_firebase"))
        for name, value in vars(db_state).items():
            if name.endswith("_memory") and isinstance(value, dict):
                stack.enter_context(patch.dict(value, {}, clear=True))

        ledger, wealth = demo_grids(today)

        def fetch_values(workbook_id, range_name, access_token, **kwargs):
            from core.finance.sheets import LEDGER_RANGE, SNAPSHOT_RANGE
            from services.finance.sheets import SheetsError
            if workbook_id != WORKBOOK:
                raise SheetsError("workbook_not_found", 404)
            if range_name == LEDGER_RANGE:
                return ledger
            if range_name == SNAPSHOT_RANGE:
                return wealth
            raise SheetsError("workbook_not_found", 404)

        stack.enter_context(patch("services.finance.sheets.fetch_values", side_effect=fetch_values))
        stack.enter_context(patch("services.finance.sync._load_token", return_value="synthetic-demo-token"))

        from app import create_app
        from core.auth_service import register_user
        from services.firebase.finance.connections import save_finance_connection
        from services.finance import sync as finance_sync

        real_sync = finance_sync.sync_now

        def sync_demo(email, account_id):
            result = real_sync(email, account_id)
            finance_sync.get_snapshot(email)["source"] = "local_demo"
            result["source"] = "local_demo"
            return result

        stack.enter_context(patch("services.finance.sync.sync_now", side_effect=sync_demo))

        application = create_app({"LOCAL_DEMO": True})

        @application.before_request
        def demo_boundaries():
            if request.method == "OPTIONS":
                return None
            cloud_paths = ("/api/finance/chat", "/api/nutrition/analyze",
                           "/api/nutrition/recommend", "/api/habits/draft",
                           "/api/internal/push/")
            credentials = ("/api/user/ai-credentials", "/api/user/openai-key",
                           "/api/user/push-subscriptions")
            if (request.path.startswith(cloud_paths)
                    or request.path.startswith(credentials) and request.method != "GET"
                    or request.path == "/api/finance/connection" and request.method != "GET"):
                return jsonify(status="error", error="local_demo_only",
                               message="Local demo uses synthetic data. AI calls and external connections are disabled."), 403

        @application.after_request
        def demo_identity(response):
            if request.path.startswith("/api/auth/") and response.is_json:
                data = response.get_json()
                if isinstance(data.get("user"), dict) and data["user"].get("email") == DEMO_EMAIL:
                    data["user"]["is_demo"] = True
                    response.set_data(application.json.dumps(data))
            return response

        result, error, _ = register_user(DEMO_EMAIL, DEMO_PASSWORD)
        if error:
            raise RuntimeError(f"Could not seed demo account: {error}")
        save_finance_connection(DEMO_EMAIL, result["account_id"], "synthetic-placeholder", "demo", WORKBOOK)
        finance_sync.sync_now(DEMO_EMAIL, result["account_id"])
        yield application


if __name__ == "__main__":
    if os.environ.get("K_SERVICE"):
        raise SystemExit("The local demo launcher cannot run on Cloud Run.")
    with demo_application() as application:
        print(f"Local demo: {DEMO_EMAIL} / {DEMO_PASSWORD}", flush=True)
        application.run(host="127.0.0.1", port=5000, use_reloader=False)
