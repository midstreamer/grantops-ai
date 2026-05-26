from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ResearchProfileCreate(BaseModel):
    researcher_name: str = Field(..., max_length=255)
    title: Optional[str] = Field(None, max_length=500)
    institution: Optional[str] = Field(None, max_length=500)
    primary_research_focus: str = Field(...)
    research_domains: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    target_funders: list[str] = Field(default_factory=list)
    preferred_outputs: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class ResearchProfileUpdate(BaseModel):
    researcher_name: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=500)
    institution: Optional[str] = Field(None, max_length=500)
    primary_research_focus: Optional[str] = None
    research_domains: Optional[list[str]] = None
    methods: Optional[list[str]] = None
    target_funders: Optional[list[str]] = None
    preferred_outputs: Optional[list[str]] = None
    keywords: Optional[list[str]] = None


class ResearchProfileRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    researcher_name: str
    title: Optional[str]
    institution: Optional[str]
    primary_research_focus: str
    research_domains: list[str]
    methods: list[str]
    target_funders: list[str]
    preferred_outputs: list[str]
    keywords: list[str]
    created_at: datetime
    updated_at: datetime
