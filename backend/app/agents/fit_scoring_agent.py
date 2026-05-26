from __future__ import annotations

from app.agents.base_agent import AgentContext, AgentStepResult, BaseAgent
from app.models.grant_opportunity import GrantOpportunity
from app.services.fit_scoring_service import score_opportunity


class FitScoringAgent(BaseAgent):
    name = "fit_scoring"

    def run(self, context: AgentContext) -> AgentStepResult:
        if context.profile is None:
            return AgentStepResult(
                step=self.name,
                status="failed",
                message="Research profile is required before scoring.",
            )

        if not context.opportunity_ids:
            return AgentStepResult(
                step=self.name,
                status="skipped",
                message="No opportunities to score.",
                data={"opportunities_scored": 0},
            )

        scored: list[dict] = []
        for opp_id in context.opportunity_ids:
            opp = context.db.get(GrantOpportunity, opp_id)
            if opp is None:
                continue

            result = score_opportunity(opp, context.profile)
            opp.fit_score = int(result["fit_score"])
            opp.recommendation = str(result["recommendation"])
            opp.fit_summary = str(result["fit_summary"])
            opp.next_action = str(result["recommended_next_action"])
            existing_raw = opp.raw_data if isinstance(opp.raw_data, dict) else {}
            opp.raw_data = {**existing_raw, "fit_analysis": result}
            context.db.add(opp)
            scored.append(
                {
                    "opportunity_id": opp.id,
                    "title": opp.title,
                    "fit_score": result["fit_score"],
                    "recommendation": result["recommendation"],
                }
            )

        context.db.commit()
        return AgentStepResult(
            step=self.name,
            status="completed",
            message=f"Scored {len(scored)} opportunities.",
            data={"opportunities_scored": len(scored), "results": scored},
        )
