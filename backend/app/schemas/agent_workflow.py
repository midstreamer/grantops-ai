from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DiscoveryWorkflowRequest(BaseModel):
    query: str = Field(..., min_length=1)
    rows: int = Field(25, ge=1, le=200)


class WorkflowStepRead(BaseModel):
    step: str
    status: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class DiscoveryWorkflowResponse(BaseModel):
    query: str
    rows: int
    status: Literal["running", "completed", "completed_with_errors", "failed"]
    orchestrator: Literal["internal", "google_adk"] = "internal"
    steps: list[WorkflowStepRead]
    profile: dict[str, Any] = Field(default_factory=dict)
    opportunities_saved: int = 0
    opportunities_scored: int = 0
    top_opportunities: list[dict[str, Any]] = Field(default_factory=list)
    literature: list[dict[str, Any]] = Field(default_factory=list)
    ai_summaries: list[dict[str, Any]] = Field(default_factory=list)
