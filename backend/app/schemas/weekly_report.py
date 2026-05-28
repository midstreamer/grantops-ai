from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WeeklyReportRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    content: str
    created_at: datetime
