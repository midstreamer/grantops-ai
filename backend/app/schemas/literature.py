from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class LiteratureSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    per_page: int = Field(10, ge=1, le=100)
    opportunity_id: Optional[int] = None


class LiteratureItemRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    opportunity_id: Optional[int]
    source: str
    source_id: str
    title: str
    authors: list[str]
    publication_year: Optional[int]
    venue: Optional[str]
    doi: Optional[str]
    url: Optional[str]
    abstract: Optional[str]
    cited_by_count: Optional[int]
    raw_data: dict[str, Any]
    created_at: datetime
