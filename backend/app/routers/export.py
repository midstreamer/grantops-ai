from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.google_sheets_export import GoogleSheetsExportResult
from app.services.google_sheets_service import (
    GoogleSheetsError,
    GoogleSheetsNotConfiguredError,
    export_opportunities_to_google_sheet,
)
from app.services.opportunity_export import (
    EXPORT_COLUMNS,
    list_opportunities_for_export,
    opportunity_to_export_row,
)

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/opportunities.csv")
def export_opportunities_csv(db: Session = Depends(get_db)) -> Response:
    opportunities = list_opportunities_for_export(db)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for opp in opportunities:
        writer.writerow(opportunity_to_export_row(opp))

    content = buffer.getvalue()
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="grantops-opportunities.csv"',
        },
    )


@router.post("/google-sheets", response_model=GoogleSheetsExportResult)
def export_opportunities_google_sheets(
    db: Session = Depends(get_db),
) -> GoogleSheetsExportResult:
    try:
        result = export_opportunities_to_google_sheet(db)
    except GoogleSheetsNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GoogleSheetsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return GoogleSheetsExportResult(**result)
