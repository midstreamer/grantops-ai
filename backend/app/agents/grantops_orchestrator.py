from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import AgentContext, AgentStepResult
from app.agents.fit_scoring_agent import FitScoringAgent
from app.agents.funding_discovery_agent import FundingDiscoveryAgent
from app.agents.literature_agent import LiteratureAgent
from app.agents.proposal_agent import ProposalAgent
from app.agents.research_profile_agent import ResearchProfileAgent
from app.models.grant_opportunity import GrantOpportunity


TOP_FOR_DEEP_DIVE = 3
TOP_FOR_REPORT = 5


@dataclass
class DiscoveryWorkflowReport:
    query: str
    rows: int
    status: str
    steps: list[AgentStepResult] = field(default_factory=list)
    profile: dict[str, Any] = field(default_factory=dict)
    opportunities_saved: int = 0
    opportunities_scored: int = 0
    top_opportunities: list[dict[str, Any]] = field(default_factory=list)
    literature: list[dict[str, Any]] = field(default_factory=list)
    ai_summaries: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "rows": self.rows,
            "status": self.status,
            "steps": [
                {
                    "step": step.step,
                    "status": step.status,
                    "message": step.message,
                    "data": step.data,
                }
                for step in self.steps
            ],
            "profile": self.profile,
            "opportunities_saved": self.opportunities_saved,
            "opportunities_scored": self.opportunities_scored,
            "top_opportunities": self.top_opportunities,
            "literature": self.literature,
            "ai_summaries": self.ai_summaries,
        }


class GrantOpsOrchestrator:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.profile_agent = ResearchProfileAgent()
        self.discovery_agent = FundingDiscoveryAgent()
        self.scoring_agent = FitScoringAgent()
        self.literature_agent = LiteratureAgent()
        self.proposal_agent = ProposalAgent()

    def _select_top_opportunities(self, context: AgentContext) -> AgentStepResult:
        opps: list[GrantOpportunity] = []
        for opp_id in context.opportunity_ids:
            opp = self.db.get(GrantOpportunity, opp_id)
            if opp is not None:
                opps.append(opp)

        opps.sort(
            key=lambda item: (
                item.fit_score is None,
                -(item.fit_score or 0),
                item.deadline is None,
                item.deadline or "",
            ),
        )

        top_for_report = opps[:TOP_FOR_REPORT]
        top_for_deep_dive = opps[:TOP_FOR_DEEP_DIVE]
        context.top_opportunity_ids = [opp.id for opp in top_for_deep_dive]

        top_opportunities = [
            {
                "id": opp.id,
                "title": opp.title,
                "agency": opp.agency,
                "fit_score": opp.fit_score,
                "recommendation": opp.recommendation,
                "deadline": opp.deadline.isoformat() if opp.deadline else None,
                "fit_summary": opp.fit_summary,
            }
            for opp in top_for_report
        ]

        return AgentStepResult(
            step="select_top_opportunities",
            status="completed",
            message=(
                f"Selected {len(top_for_report)} top opportunities "
                f"({len(top_for_deep_dive)} for literature and AI summaries)."
            ),
            data={
                "top_count": len(top_for_report),
                "deep_dive_count": len(top_for_deep_dive),
                "top_opportunity_ids": context.top_opportunity_ids,
                "top_opportunities": top_opportunities,
            },
        )

    def run_discovery_workflow(self, query: str, rows: int = 25) -> DiscoveryWorkflowReport:
        context = AgentContext(db=self.db, query=query, rows=rows)
        report = DiscoveryWorkflowReport(query=query.strip(), rows=rows, status="running")

        profile_result = self.profile_agent.run(context)
        report.steps.append(profile_result)
        if profile_result.status == "failed":
            report.status = "failed"
            return report
        report.profile = profile_result.data

        discovery_result = self.discovery_agent.run(context)
        report.steps.append(discovery_result)
        if discovery_result.status == "failed":
            report.status = "failed"
            return report
        report.opportunities_saved = int(discovery_result.data.get("opportunities_saved", 0))

        scoring_result = self.scoring_agent.run(context)
        report.steps.append(scoring_result)
        if scoring_result.status == "failed":
            report.status = "failed"
            return report
        report.opportunities_scored = int(scoring_result.data.get("opportunities_scored", 0))

        selection_result = self._select_top_opportunities(context)
        report.steps.append(selection_result)
        report.top_opportunities = selection_result.data.get("top_opportunities", [])

        literature_result = self.literature_agent.run(context)
        report.steps.append(literature_result)
        report.literature = literature_result.data.get("results", [])

        proposal_result = self.proposal_agent.run(context)
        report.steps.append(proposal_result)
        report.ai_summaries = proposal_result.data.get("results", [])

        report.status = "completed"
        if any(step.status == "failed" for step in report.steps):
            report.status = "completed_with_errors"
        return report
