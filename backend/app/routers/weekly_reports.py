from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.weekly_report import WeeklyReport
from app.schemas.weekly_report import WeeklyReportRead

router = APIRouter(prefix="/api", tags=["weekly-reports"])


@router.get("/weekly-reports", response_model=list[WeeklyReportRead])
def list_weekly_reports(db: Session = Depends(get_db)) -> list[WeeklyReportRead]:
    stmt = select(WeeklyReport).order_by(desc(WeeklyReport.created_at), desc(WeeklyReport.id))
    return list(db.execute(stmt).scalars().all())
