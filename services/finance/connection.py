"""Validate a personal workbook binding before connecting the shared Sheets reader."""

import re
from urllib.parse import urlparse

from core.finance.sheets import rows_to_transactions
from . import sheets as google_sheets, identity as sheets_identity
from services.firebase.finance.connections import (
    get_finance_connection_status,
    save_finance_connection,
)
from services.firebase.finance.rules import FinanceError

WORKBOOK_PATTERN = re.compile(r"^[A-Za-z0-9_-]{10,128}$")


def workbook_id(value):
    if not isinstance(value, str):
        raise FinanceError("Supply a Google Sheets link or workbook ID.", 400)
    value = value.strip()
    if value.startswith("https://"):
        parsed = urlparse(value)
        match = re.match(r"^/spreadsheets/d/([A-Za-z0-9_-]+)(?:/|$)", parsed.path)
        if parsed.netloc != "docs.google.com" or not match:
            raise FinanceError("Supply a docs.google.com spreadsheet link.", 400)
        value = match.group(1)
    if not WORKBOOK_PATTERN.fullmatch(value):
        raise FinanceError("Supply a valid Google Sheets link or workbook ID.", 400)
    return value


def connect(email, account_id, value):
    target = workbook_id(value)
    status = get_finance_connection_status(email, account_id)
    if not status.get("service_account_email"):
        raise FinanceError("The Google Sheets reader has not been configured.", 503)
    # Check approval before making any Google request. A shared service identity
    # being able to read a workbook does not authorize every Janus user to read it.
    if status.get("approved_workbook_id") != target:
        raise FinanceError("This workbook is not approved for your Janus account.", 403)
    try:
        token = sheets_identity.access_token()
        header = google_sheets.fetch_values(target, "'combined data'!A1:Q1", token)
    except sheets_identity.SheetsIdentityError as error:
        raise FinanceError(str(error), 503) from None
    except google_sheets.SheetsError as error:
        if error.code in ("sheets_reconnect_required", "workbook_not_found"):
            raise FinanceError("Share the approved workbook with the reader email as Viewer, then try again.",
                               403, details={"code": "workbook_not_shared"}) from None
        raise FinanceError("Google Sheets could not be reached. Your existing connection is unchanged.", 502) from None
    _rows, _warnings, errors = rows_to_transactions(header[:1])
    if errors:
        raise FinanceError("The workbook's combined data tab has an invalid header.", 422, details=errors)
    return save_finance_connection(email, account_id, None, None, target, mode="service_account")
