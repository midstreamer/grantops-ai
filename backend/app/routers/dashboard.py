from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.grant_opportunity import GrantOpportunity
from app.schemas.dashboard import DashboardStats
from app.schemas.grant_opportunity import GrantOpportunityRead

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStats:
    opps = list(db.execute(select(GrantOpportunity)).scalars().all())
    today = date.today()
    in_30 = today + timedelta(days=30)
    in_90 = today + timedelta(days=90)

    def is_due_within(end: date) -> int:
        count = 0
        for opp in opps:
            if opp.deadline is None:
                continue
            if today <= opp.deadline <= end:
                count += 1
        return count

    scored = [o.fit_score for o in opps if o.fit_score is not None]
    avg_fit = round(sum(scored) / len(scored), 1) if scored else None

    top_stmt = (
        select(GrantOpportunity)
        .where(GrantOpportunity.fit_score.is_not(None))
        .order_by(desc(GrantOpportunity.fit_score), desc(GrantOpportunity.updated_at))
        .limit(5)
    )
    top_opps = list(db.execute(top_stmt).scalars().all())

    return DashboardStats(
        total_opportunities=len(opps),
        pursue_count=sum(1 for o in opps if o.recommendation == "pursue"),
        monitor_count=sum(1 for o in opps if o.recommendation == "monitor"),
        decline_count=sum(1 for o in opps if o.recommendation == "decline"),
        due_in_30_days=is_due_within(in_30),
        due_in_90_days=is_due_within(in_90),
        average_fit_score=avg_fit,
        top_opportunities=[GrantOpportunityRead.model_validate(o) for o in top_opps],
    )
