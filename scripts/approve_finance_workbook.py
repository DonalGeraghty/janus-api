"""Approve one workbook for an existing Janus account, using administrator ADC."""

import argparse
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from google.cloud import firestore
from services.finance.connection import workbook_id
from services.firebase.account_state import ACCOUNT_DELETION_FIELD


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--email", help="Janus login email; prompted if omitted")
    parser.add_argument("--workbook", help="Private Sheet link or ID; prompted if omitted")
    args = parser.parse_args()
    email = (args.email or input("Janus login email: ")).strip().lower()
    workbook = workbook_id(args.workbook or input("Private spreadsheet link or ID: "))
    if not email or "@" not in email:
        parser.error("Supply the existing Janus login email.")
    database = firestore.Client(project=args.project)
    user_ref = database.collection("users").document(email)
    settings_ref = user_ref.collection("finance_settings").document("settings")

    @firestore.transactional
    def approve(transaction):
        user = user_ref.get(transaction=transaction)
        data = user.to_dict() if user.exists else {}
        if not data.get("account_id") or data.get(ACCOUNT_DELETION_FIELD):
            raise SystemExit("The Janus account does not exist or is being deleted. Nothing changed.")
        document = settings_ref.get(transaction=transaction)
        settings = document.to_dict() if document.exists else {}
        settings["finance_service_account_approval"] = {
            "account_id": data["account_id"], "workbook_id": workbook,
            "approved_at": datetime.now(timezone.utc).isoformat(),
        }
        transaction.set(settings_ref, settings)

    approve(database.transaction())
    print("Workbook approved for the existing Janus account generation. No spreadsheet data was read or changed.")


if __name__ == "__main__":
    main()
