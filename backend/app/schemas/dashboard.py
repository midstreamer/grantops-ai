from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas.grant_opportunity import GrantOpportunityRead


class DashboardStats(BaseModel):
    total_opportunities: int
    pursue_count: int
    monitor_count: int
    decline_count: int
    due_in_30_days: int
    due_in_90_days: int
    average_fit_score: Optional[float]
    top_opportunities: list[GrantOpportunityRead]
