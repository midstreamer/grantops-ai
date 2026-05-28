from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


Frequency = Literal["weekly"]


class ScheduledSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    query: str = Field(..., min_length=1)
    rows: int = Field(25, ge=1, le=200)
    frequency: Frequency = "weekly"
    active: bool = True


class ScheduledSearchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    query: Optional[str] = Field(None, min_length=1)
    rows: Optional[int] = Field(None, ge=1, le=200)
    frequency: Optional[Frequency] = None
    active: Optional[bool] = None


class ScheduledSearchRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    query: str
    rows: int
    frequency: Frequency
    active: bool
    last_run_at: Optional[datetime]
    created_at: datetime
