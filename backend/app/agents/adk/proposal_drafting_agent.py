from __future__ import annotations

from app.agents.adk.base_agent import make_step_agent


def create_proposal_drafting_adk_agent(runner):
    """ADK agent for optional LLM AI summaries (maps to internal ProposalAgent)."""

    return make_step_agent(
        name="ProposalDraftingAgent",
        description="Generates AI opportunity summaries when LLM keys are configured.",
        runner=runner,
    )
