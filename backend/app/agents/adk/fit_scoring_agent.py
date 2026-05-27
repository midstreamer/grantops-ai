from __future__ import annotations

from app.agents.adk.base_agent import make_step_agent


def create_fit_scoring_adk_agent(runner):
    """ADK agent that scores opportunities discovered in this workflow run."""

    return make_step_agent(
        name="FitScoringAgent",
        description="Scores opportunities against the research profile.",
        runner=runner,
    )
