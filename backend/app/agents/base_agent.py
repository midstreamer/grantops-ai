from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.research_profile import ResearchProfile


@dataclass
class AgentStepResult:
    step: str
    status: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    db: Session
    query: str = ""
    rows: int = 25
    profile: Optional[ResearchProfile] = None
    opportunity_ids: list[int] = field(default_factory=list)
    top_opportunity_ids: list[int] = field(default_factory=list)


class BaseAgent:
    name: str = "base"

    def run(self, context: AgentContext) -> AgentStepResult:
        raise NotImplementedError
