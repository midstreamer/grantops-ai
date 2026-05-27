from __future__ import annotations

"""
Callable tools used by Google ADK pipeline agents.

Each function performs one logical step of the discovery workflow by delegating
to the existing internal agent classes in :mod:`app.agents`.
"""

from app.agents.base_agent import AgentContext, AgentStepResult
from app.agents.fit_scoring_agent import FitScoringAgent
from app.agents.funding_discovery_agent import FundingDiscoveryAgent
from app.agents.grantops_orchestrator import select_top_opportunities_for_context
from app.agents.literature_agent import LiteratureAgent
from app.agents.proposal_agent import ProposalAgent
from app.agents.research_profile_agent import ResearchProfileAgent


def grantops_load_research_profile(ctx: AgentContext) -> AgentStepResult:
    """Load the primary research profile (internal ResearchProfileAgent)."""
    return ResearchProfileAgent().run(ctx)


def grantops_search_grants_gov(ctx: AgentContext) -> AgentStepResult:
    """Search Grants.gov and persist opportunities (internal FundingDiscoveryAgent)."""
    return FundingDiscoveryAgent().run(ctx)


def grantops_score_discovered_opportunities(ctx: AgentContext) -> AgentStepResult:
    """Score opportunities from the current discovery batch (internal FitScoringAgent)."""
    return FitScoringAgent().run(ctx)


def grantops_select_top_opportunities(db, ctx: AgentContext) -> AgentStepResult:
    """Rank and select top opportunities (shared with internal orchestrator)."""
    return select_top_opportunities_for_context(db, ctx)


def grantops_find_supporting_literature(ctx: AgentContext) -> AgentStepResult:
    """OpenAlex literature for top opportunities (internal LiteratureAgent)."""
    return LiteratureAgent().run(ctx)


def grantops_generate_ai_summaries(ctx: AgentContext) -> AgentStepResult:
    """AI summaries for top opportunities — internal ProposalAgent (LLM-aware)."""
    return ProposalAgent().run(ctx)
