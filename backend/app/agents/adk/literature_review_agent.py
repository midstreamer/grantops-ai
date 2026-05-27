from __future__ import annotations

from app.agents.adk.base_agent import make_step_agent


def create_literature_review_adk_agent(runner):
    """ADK agent for OpenAlex literature retrieval (top opportunities)."""

    return make_step_agent(
        name="LiteratureReviewAgent",
        description="Finds supporting literature for the top matching opportunities.",
        runner=runner,
    )
