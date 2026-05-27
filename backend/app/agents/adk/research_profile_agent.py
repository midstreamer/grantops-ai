from __future__ import annotations

from app.agents.adk.base_agent import make_step_agent


def create_research_profile_adk_agent(runner):
    """
    ADK agent wrapping :func:`grantops_load_research_profile`.

    ``runner`` must be a zero-arg callable capturing the current :class:`AgentContext`.
    """

    return make_step_agent(
        name="ResearchProfileAgent",
        description="Loads the primary research profile for fit-scoring and literature.",
        runner=runner,
    )
