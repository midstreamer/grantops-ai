from __future__ import annotations

from datetime import date

from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.models.grant_opportunity import GrantOpportunity

EXPORT_COLUMNS = [
    "title",
    "agency",
    "program",
    "source",
    "source_id",
    "deadline",
    "posted_date",
    "opportunity_status",
    "fit_score",
    "recommendation",
    "status",
    "next_action",
    "url",
    "fit_summary",
]


def format_export_date(value: date | None) -> str:
    if value is None:
        return ""
    return value.isoformat()


def opportunity_to_export_row(opp: GrantOpportunity) -> dict[str, str]:
    return {
        "title": opp.title or "",
        "agency": opp.agency or "",
        "program": opp.program or "",
        "source": opp.source or "",
        "source_id": opp.source_id or "",
        "deadline": format_export_date(opp.deadline),
        "posted_date": format_export_date(opp.posted_date),
        "opportunity_status": opp.opportunity_status or "",
        "fit_score": "" if opp.fit_score is None else str(opp.fit_score),
        "recommendation": opp.recommendation or "",
        "status": opp.status or "",
        "next_action": opp.next_action or "",
        "url": opp.url or "",
        "fit_summary": opp.fit_summary or "",
    }


def export_row_key(row: dict[str, str]) -> str:
    source = row.get("source", "").strip()
    source_id = row.get("source_id", "").strip()
    if source_id:
        return f"{source}|{source_id}"
    title = row.get("title", "").strip().lower()
    agency = row.get("agency", "").strip().lower()
    deadline = row.get("deadline", "").strip()
    return f"{title}|{agency}|{deadline}"


def export_row_to_values(row: dict[str, str]) -> list[str]:
    return [row.get(column, "") for column in EXPORT_COLUMNS]


def list_opportunities_for_export(db: Session) -> list[GrantOpportunity]:
    stmt = (
        select(GrantOpportunity)
        .order_by(
            asc(GrantOpportunity.deadline).nulls_last(),
            desc(GrantOpportunity.updated_at),
            desc(GrantOpportunity.id),
        )
    )
    return list(db.execute(stmt).scalars().all())
