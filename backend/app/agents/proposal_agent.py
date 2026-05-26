from __future__ import annotations

from sqlalchemy import select

from app.agents.base_agent import AgentContext, AgentStepResult, BaseAgent
from app.models.grant_opportunity import GrantOpportunity
from app.models.literature_item import LiteratureItem
from app.services.llm_service import (
    LLMNotConfiguredError,
    LLMProviderError,
    summarize_opportunity,
)


class ProposalAgent(BaseAgent):
    name = "proposal"

    def run(self, context: AgentContext) -> AgentStepResult:
        if context.profile is None:
            return AgentStepResult(
                step=self.name,
                status="failed",
                message="Research profile is required for AI summaries.",
            )

        target_ids = context.top_opportunity_ids[:3]
        if not target_ids:
            return AgentStepResult(
                step=self.name,
                status="skipped",
                message="No top opportunities selected for AI summaries.",
                data={"results": []},
            )

        results: list[dict] = []
        for opp_id in target_ids:
            opp = context.db.get(GrantOpportunity, opp_id)
            if opp is None:
                continue

            lit_stmt = select(LiteratureItem).where(LiteratureItem.opportunity_id == opp_id)
            literature_items = list(context.db.execute(lit_stmt).scalars().all())

            try:
                summary = summarize_opportunity(opp, context.profile, literature_items)
            except LLMNotConfiguredError:
                return AgentStepResult(
                    step=self.name,
                    status="skipped",
                    message="LLM is not configured; skipped AI summary generation.",
                    data={"results": results, "llm_configured": False},
                )
            except LLMProviderError as exc:
                results.append(
                    {
                        "opportunity_id": opp_id,
                        "title": opp.title,
                        "status": "failed",
                        "message": str(exc),
                    }
                )
                continue

            existing_raw = opp.raw_data if isinstance(opp.raw_data, dict) else {}
            opp.raw_data = {**existing_raw, "ai_summary": summary}
            context.db.add(opp)
            results.append(
                {
                    "opportunity_id": opp_id,
                    "title": opp.title,
                    "status": "completed",
                    "possible_proposal_title": summary.get("possible_proposal_title"),
                    "recommended_next_actions": summary.get("recommended_next_actions"),
                }
            )

        context.db.commit()

        if not results:
            return AgentStepResult(
                step=self.name,
                status="skipped",
                message="AI summaries were not generated.",
                data={"results": []},
            )

        return AgentStepResult(
            step=self.name,
            status="completed",
            message=f"Generated AI summaries for {len(results)} opportunities.",
            data={"results": results, "llm_configured": True},
        )
