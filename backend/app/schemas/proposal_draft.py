from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProposalDraftRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    opportunity_id: int
    title: str
    draft_type: str
    content: str
    google_doc_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProposalDraftUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
