"""Minimal Google Sheets API v4 client using the account's stored OAuth token.

Read-only by construction: only GET values endpoints are used. Upstream failures
become safe SheetsError codes; the token itself never leaves the server.
"""

import json
import urllib.error
import urllib.parse
import urllib.request


SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
TIMEOUT_SECONDS = 30


class SheetsError(Exception):
    def __init__(self, code, status=502):
        super().__init__(code)
        self.code = code
        self.status = status


def fetch_values(workbook_id, range_name, access_token, value_render_option="UNFORMATTED_VALUE"):
    """Return the raw `values` grid for a range. Dates arrive as serial numbers,
    numbers as JSON numbers when value_render_option is UNFORMATTED_VALUE."""
    if not workbook_id or not access_token:
        raise SheetsError("sheets_not_configured", 409)
    url = (
        f"{SHEETS_BASE}/{urllib.parse.quote(str(workbook_id), safe='')}"
        f"/values/{urllib.parse.quote(range_name, safe='')}"
        f"?{urllib.parse.urlencode({'valueRenderOption': value_render_option, 'majorDimension': 'ROWS'})}"
    )
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            raise SheetsError("sheets_reconnect_required", 409) from error
        if error.code == 404:
            raise SheetsError("workbook_not_found", 404) from error
        raise SheetsError("sheets_upstream_error", 502) from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError) as error:
        raise SheetsError("sheets_unreachable", 502) from error
    values = payload.get("values") if isinstance(payload, dict) else None
    if not isinstance(values, list):
        raise SheetsError("sheets_bad_response", 502)
    return values
