from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.opportunity_export import (
    EXPORT_COLUMNS,
    export_row_key,
    export_row_to_values,
    list_opportunities_for_export,
    opportunity_to_export_row,
)

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DEFAULT_WORKSHEET_NAME = "Opportunities"


class GoogleSheetsNotConfiguredError(Exception):
    """Raised when Google Sheets credentials or spreadsheet ID are missing."""


class GoogleSheetsError(Exception):
    """Raised when a Google Sheets API call fails."""


def _require_sheets_config() -> tuple[str, str]:
    settings = get_settings()
    credentials_path = (settings.google_application_credentials or "").strip()
    spreadsheet_id = (settings.google_sheets_spreadsheet_id or "").strip()

    if not credentials_path or not spreadsheet_id:
        raise GoogleSheetsNotConfiguredError(
            "Google Sheets export is not configured. Set GOOGLE_APPLICATION_CREDENTIALS "
            "and GOOGLE_SHEETS_SPREADSHEET_ID in backend/.env."
        )

    path = Path(credentials_path).expanduser()
    if not path.is_file():
        raise GoogleSheetsNotConfiguredError(
            f"Google credentials file not found: {path}"
        )

    return str(path), spreadsheet_id


def get_sheets_service(credentials_path: Optional[str] = None) -> Any:
    path, _spreadsheet_id = _require_sheets_config()
    creds_file = credentials_path or path
    credentials = service_account.Credentials.from_service_account_file(
        creds_file,
        scopes=SCOPES,
    )
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def _ensure_worksheet(service: Any, spreadsheet_id: str, worksheet_name: str) -> str:
    meta = (
        service.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title")
        .execute()
    )
    sheets = meta.get("sheets", [])
    for sheet in sheets:
        title = sheet.get("properties", {}).get("title", "")
        if title == worksheet_name:
            return worksheet_name

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": worksheet_name}}}]},
    ).execute()
    return worksheet_name


def _sheet_range(worksheet_name: str, cell_range: str) -> str:
    return f"'{worksheet_name}'!{cell_range}"


def append_or_update_opportunity_rows(
    service: Any,
    spreadsheet_id: str,
    rows: list[dict[str, str]],
    *,
    worksheet_name: str = DEFAULT_WORKSHEET_NAME,
) -> dict[str, int]:
    """Write export rows to Google Sheets, updating existing keys and appending new ones."""
    worksheet_name = _ensure_worksheet(service, spreadsheet_id, worksheet_name)
    read_range = _sheet_range(worksheet_name, "A1:Z")

    try:
        existing = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=read_range)
            .execute()
        )
    except HttpError as exc:
        raise GoogleSheetsError(f"Failed to read spreadsheet: {exc}") from exc

    values: list[list[str]] = existing.get("values", [])

    if not values:
        sheet_values = [EXPORT_COLUMNS] + [export_row_to_values(row) for row in rows]
        try:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=_sheet_range(worksheet_name, "A1"),
                valueInputOption="USER_ENTERED",
                body={"values": sheet_values},
            ).execute()
        except HttpError as exc:
            raise GoogleSheetsError(f"Failed to write spreadsheet: {exc}") from exc
        return {
            "rows_updated": 0,
            "rows_appended": len(rows),
            "total_rows": len(rows),
        }

    key_to_row_index: dict[str, int] = {}
    header = values[0]
    if [cell.strip() for cell in header] != EXPORT_COLUMNS:
        try:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=_sheet_range(worksheet_name, "A1"),
                valueInputOption="USER_ENTERED",
                body={"values": [EXPORT_COLUMNS]},
            ).execute()
        except HttpError as exc:
            raise GoogleSheetsError(f"Failed to update spreadsheet header: {exc}") from exc

    for row_offset, sheet_row in enumerate(values[1:], start=2):
        row_dict = {
            EXPORT_COLUMNS[idx]: sheet_row[idx] if idx < len(sheet_row) else ""
            for idx in range(len(EXPORT_COLUMNS))
        }
        key_to_row_index[export_row_key(row_dict)] = row_offset

    updates: list[dict[str, Any]] = []
    append_rows: list[list[str]] = []
    rows_updated = 0
    rows_appended = 0

    for row in rows:
        values_list = export_row_to_values(row)
        key = export_row_key(row)
        row_index = key_to_row_index.get(key)
        if row_index is not None:
            updates.append(
                {
                    "range": _sheet_range(worksheet_name, f"A{row_index}"),
                    "values": [values_list],
                }
            )
            rows_updated += 1
        else:
            append_rows.append(values_list)
            rows_appended += 1

    if updates:
        try:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"valueInputOption": "USER_ENTERED", "data": updates},
            ).execute()
        except HttpError as exc:
            raise GoogleSheetsError(f"Failed to update spreadsheet rows: {exc}") from exc

    if append_rows:
        try:
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=_sheet_range(worksheet_name, "A1"),
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": append_rows},
            ).execute()
        except HttpError as exc:
            raise GoogleSheetsError(f"Failed to append spreadsheet rows: {exc}") from exc

    return {
        "rows_updated": rows_updated,
        "rows_appended": rows_appended,
        "total_rows": len(rows),
    }


def export_opportunities_to_google_sheet(
    db: Session,
    *,
    worksheet_name: str = DEFAULT_WORKSHEET_NAME,
) -> dict[str, Any]:
    """Export all opportunities to the configured Google Sheet."""
    credentials_path, spreadsheet_id = _require_sheets_config()
    opportunities = list_opportunities_for_export(db)
    rows = [opportunity_to_export_row(opp) for opp in opportunities]

    service = get_sheets_service(credentials_path)
    stats = append_or_update_opportunity_rows(
        service,
        spreadsheet_id,
        rows,
        worksheet_name=worksheet_name,
    )

    return {
        "spreadsheet_id": spreadsheet_id,
        "worksheet": worksheet_name,
        **stats,
    }
