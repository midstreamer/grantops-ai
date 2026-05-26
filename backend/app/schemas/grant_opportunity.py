from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


Recommendation = Literal["pursue", "monitor", "decline", "unreviewed"]
OpportunityStatus = Literal[
    "new",
    "review",
    "pursuing",
    "drafting",
    "submitted",
    "declined",
]


class GrantOpportunityCreate(BaseModel):
    source: str = Field(..., max_length=100)
    source_id: Optional[str] = Field(None, max_length=200)

    title: str = Field(..., max_length=500)
    agency: Optional[str] = Field(None, max_length=255)
    program: Optional[str] = Field(None, max_length=255)

    description: Optional[str] = None
    eligibility: Optional[str] = None

    award_ceiling: Optional[float] = None
    award_floor: Optional[float] = None

    deadline: Optional[date] = None
    posted_date: Optional[date] = None
    opportunity_status: Optional[str] = Field(None, max_length=100)

    url: Optional[HttpUrl] = None

    raw_data: dict[str, Any] = Field(default_factory=dict)

    fit_score: Optional[int] = Field(None, ge=0, le=100)
    fit_summary: Optional[str] = None

    recommendation: Recommendation = "unreviewed"
    status: OpportunityStatus = "new"

    next_action: Optional[str] = None
    notes: Optional[str] = None


class GrantOpportunityUpdate(BaseModel):
    source: Optional[str] = Field(None, max_length=100)
    source_id: Optional[str] = Field(None, max_length=200)

    title: Optional[str] = Field(None, max_length=500)
    agency: Optional[str] = Field(None, max_length=255)
    program: Optional[str] = Field(None, max_length=255)

    description: Optional[str] = None
    eligibility: Optional[str] = None

    award_ceiling: Optional[float] = None
    award_floor: Optional[float] = None

    deadline: Optional[date] = None
    posted_date: Optional[date] = None
    opportunity_status: Optional[str] = Field(None, max_length=100)

    url: Optional[HttpUrl] = None

    raw_data: Optional[dict[str, Any]] = None

    fit_score: Optional[int] = Field(None, ge=0, le=100)
    fit_summary: Optional[str] = None

    recommendation: Optional[Recommendation] = None
    status: Optional[OpportunityStatus] = None

    next_action: Optional[str] = None
    notes: Optional[str] = None


class GrantOpportunityRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    source: str
    source_id: Optional[str]

    title: str
    agency: Optional[str]
    program: Optional[str]

    description: Optional[str]
    eligibility: Optional[str]

    award_ceiling: Optional[float]
    award_floor: Optional[float]

    deadline: Optional[date]
    posted_date: Optional[date]
    opportunity_status: Optional[str]

    url: Optional[str]

    raw_data: dict[str, Any]

    fit_score: Optional[int]
    fit_summary: Optional[str]

    recommendation: Recommendation
    status: OpportunityStatus

    next_action: Optional[str]
    notes: Optional[str]

    created_at: datetime
    updated_at: datetime

