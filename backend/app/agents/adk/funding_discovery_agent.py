from __future__ import annotations

from app.agents.adk.base_agent import make_step_agent


def create_funding_discovery_adk_agent(runner):
    """ADK agent for Grants.gov discovery (uses internal FundingDiscoveryAgent)."""

    return make_step_agent(
        name="FundingDiscoveryAgent",
        description="Searches Grants.gov and saves opportunities.",
        runner=runner,
    )
