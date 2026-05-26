from __future__ import annotations

from sqlalchemy import asc, select

from app.agents.base_agent import AgentContext, AgentStepResult, BaseAgent
from app.models.research_profile import ResearchProfile


class ResearchProfileAgent(BaseAgent):
    name = "research_profile"

    def run(self, context: AgentContext) -> AgentStepResult:
        stmt = select(ResearchProfile).order_by(asc(ResearchProfile.id)).limit(1)
        profile = context.db.execute(stmt).scalars().first()
        if profile is None:
            return AgentStepResult(
                step=self.name,
                status="failed",
                message="No research profile found. Create one before running workflows.",
            )

        context.profile = profile
        return AgentStepResult(
            step=self.name,
            status="completed",
            message=f"Loaded research profile for {profile.researcher_name}.",
            data={
                "profile_id": profile.id,
                "researcher_name": profile.researcher_name,
                "institution": profile.institution,
                "primary_research_focus": profile.primary_research_focus,
            },
        )
