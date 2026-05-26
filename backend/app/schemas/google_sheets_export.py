from __future__ import annotations

from pydantic import BaseModel


class GoogleSheetsExportResult(BaseModel):
    spreadsheet_id: str
    worksheet: str
    total_rows: int
    rows_updated: int
    rows_appended: int
