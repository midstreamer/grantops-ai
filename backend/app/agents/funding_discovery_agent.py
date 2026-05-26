from __future__ import annotations

from app.agents.base_agent import AgentContext, AgentStepResult, BaseAgent
from app.services.grants_gov_service import search_and_persist_grants_gov


class FundingDiscoveryAgent(BaseAgent):
    name = "funding_discovery"

    def run(self, context: AgentContext) -> AgentStepResult:
        if not context.query.strip():
            return AgentStepResult(
                step=self.name,
                status="failed",
                message="Discovery query is required.",
            )

        try:
            saved = search_and_persist_grants_gov(
                context.db,
                query=context.query.strip(),
                rows=context.rows,
            )
        except RuntimeError as exc:
            return AgentStepResult(
                step=self.name,
                status="failed",
                message=str(exc),
            )

        context.opportunity_ids = [opp.id for opp in saved]
        return AgentStepResult(
            step=self.name,
            status="completed",
            message=f"Saved {len(saved)} opportunities from Grants.gov.",
            data={
                "query": context.query.strip(),
                "rows_requested": context.rows,
                "opportunities_saved": len(saved),
                "opportunity_ids": context.opportunity_ids,
            },
        )
