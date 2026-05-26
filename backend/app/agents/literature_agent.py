from __future__ import annotations

from app.agents.base_agent import AgentContext, AgentStepResult, BaseAgent
from app.models.grant_opportunity import GrantOpportunity
from app.services.openalex_service import build_opportunity_literature_query, search_and_persist


class LiteratureAgent(BaseAgent):
    name = "literature"

    def run(self, context: AgentContext) -> AgentStepResult:
        if context.profile is None:
            return AgentStepResult(
                step=self.name,
                status="failed",
                message="Research profile is required for literature search.",
            )

        target_ids = context.top_opportunity_ids[:3]
        if not target_ids:
            return AgentStepResult(
                step=self.name,
                status="skipped",
                message="No top opportunities selected for literature search.",
                data={"results": []},
            )

        results: list[dict] = []
        for opp_id in target_ids:
            opp = context.db.get(GrantOpportunity, opp_id)
            if opp is None:
                continue
            query = build_opportunity_literature_query(opp, context.profile)
            try:
                saved = search_and_persist(
                    context.db,
                    query=query,
                    per_page=10,
                    opportunity_id=opp_id,
                )
            except RuntimeError as exc:
                results.append(
                    {
                        "opportunity_id": opp_id,
                        "title": opp.title,
                        "status": "failed",
                        "message": str(exc),
                        "items_saved": 0,
                    }
                )
                continue

            results.append(
                {
                    "opportunity_id": opp_id,
                    "title": opp.title,
                    "status": "completed",
                    "query": query,
                    "items_saved": len(saved),
                }
            )

        total_items = sum(item.get("items_saved", 0) for item in results)
        return AgentStepResult(
            step=self.name,
            status="completed",
            message=f"Found literature for {len(results)} opportunities ({total_items} items saved).",
            data={"results": results},
        )
