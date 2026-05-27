from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.agents.adk.base_agent import (
    ADK_AVAILABLE,
    STEP_STATE_KEY,
    GrantOpsAdkStepUnavailableError,
    GrantOpsStoppingSequentialAgent,
)
from app.agents.adk.fit_scoring_agent import create_fit_scoring_adk_agent
from app.agents.adk.funding_discovery_agent import create_funding_discovery_adk_agent
from app.agents.adk.grantops_tools import (
    grantops_find_supporting_literature,
    grantops_generate_ai_summaries,
    grantops_load_research_profile,
    grantops_score_discovered_opportunities,
    grantops_search_grants_gov,
    grantops_select_top_opportunities,
)
from app.agents.adk.literature_review_agent import create_literature_review_adk_agent
from app.agents.adk.proposal_drafting_agent import create_proposal_drafting_adk_agent
from app.agents.adk.research_profile_agent import create_research_profile_adk_agent
from app.agents.adk.base_agent import make_step_agent
from app.agents.base_agent import AgentContext, AgentStepResult
from app.agents.grantops_orchestrator import DiscoveryWorkflowReport

logger = logging.getLogger(__name__)

ADK_APP_NAME = "grant_ops_adk_discovery"


def _build_discovery_root_agent(db: Session, ctx: AgentContext) -> Any:
    """Compose ADK sequential workflow with deterministic sub-agents."""

    sub_agents: list[Any] = [
        create_research_profile_adk_agent(lambda: grantops_load_research_profile(ctx)),
        create_funding_discovery_adk_agent(lambda: grantops_search_grants_gov(ctx)),
        create_fit_scoring_adk_agent(lambda: grantops_score_discovered_opportunities(ctx)),
        make_step_agent(
            name="OpportunityRankingAgent",
            description="Selects top scored opportunities for deep-dive steps.",
            runner=lambda: grantops_select_top_opportunities(db, ctx),
        ),
        create_literature_review_adk_agent(
            lambda: grantops_find_supporting_literature(ctx)
        ),
        create_proposal_drafting_adk_agent(
            lambda: grantops_generate_ai_summaries(ctx)
        ),
    ]

    missing = [a for a in sub_agents if a is None]
    if missing:
        raise GrantOpsAdkStepUnavailableError(
            "Failed to instantiate ADK sub-agents; is google-adk installed?"
        )

    return GrantOpsStoppingSequentialAgent(
        name="GrantOpsAdkDiscoverySequential",
        description="Grant discovery orchestrated through Google ADK agents.",
        sub_agents=sub_agents,
    )


def _discovery_report_from_step_dicts(
    query: str,
    rows: int,
    step_dicts: list[dict[str, Any]],
) -> DiscoveryWorkflowReport:
    steps: list[AgentStepResult] = [
        AgentStepResult(
            step=s["step"],
            status=s["status"],
            message=s["message"],
            data=s.get("data") or {},
        )
        for s in step_dicts
    ]

    report = DiscoveryWorkflowReport(
        query=query.strip(),
        rows=rows,
        status="completed",
        steps=steps,
    )

    for s in steps:
        if s.step == "research_profile":
            report.profile = s.data
        elif s.step == "funding_discovery":
            report.opportunities_saved = int(s.data.get("opportunities_saved", 0))
        elif s.step == "fit_scoring":
            report.opportunities_scored = int(s.data.get("opportunities_scored", 0))
        elif s.step == "select_top_opportunities":
            report.top_opportunities = list(s.data.get("top_opportunities") or [])
        elif s.step == "literature":
            report.literature = list(s.data.get("results") or [])
        elif s.step == "proposal":
            report.ai_summaries = list(s.data.get("results") or [])

    if not steps:
        report.status = "failed"
    elif any(s.status == "failed" for s in steps):
        if steps[0].status == "failed":
            report.status = "failed"
        else:
            report.status = "completed_with_errors"
    elif any(s.status == "skipped" for s in steps):
        report.status = "completed"
    return report


async def run_discovery_workflow_via_adk(
    db: Session,
    *,
    query: str,
    rows: int,
) -> DiscoveryWorkflowReport:
    """
    Run the discovery workflow through Google ADK (SequentialAgent + sub-agents).

    Raises:
        GrantOpsAdkStepUnavailableError: If google-adk is not installed.
    """

    if not ADK_AVAILABLE:
        raise GrantOpsAdkStepUnavailableError(
            "google-adk is not installed. See docs/adk_setup.md and requirements-adk.txt."
        )

    from google.adk.runners import Runner
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.genai import types

    workflow_context = AgentContext(db=db, query=query, rows=rows)
    root = _build_discovery_root_agent(db, workflow_context)

    session_service = InMemorySessionService()
    session_id = str(uuid.uuid4())
    user_id = "grantops_api"

    await session_service.create_session(
        app_name=ADK_APP_NAME,
        user_id=user_id,
        session_id=session_id,
        state={},
    )

    runner = Runner(
        app_name=ADK_APP_NAME,
        agent=root,
        session_service=session_service,
    )

    kickoff = types.Content(
        role="user",
        parts=[types.Part(text="Run GrantOps discovery workflow.")],
    )

    async for _event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=kickoff,
    ):
        pass

    session = await session_service.get_session(
        app_name=ADK_APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    if session is None:
        logger.error("ADK session missing after workflow run")
        step_dicts: list[dict[str, Any]] = []
    else:
        step_dicts = list(session.state.get(STEP_STATE_KEY, []))

    return _discovery_report_from_step_dicts(query, rows, step_dicts)
