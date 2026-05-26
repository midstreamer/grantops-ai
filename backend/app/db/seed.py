from __future__ import annotations

from sqlalchemy import Select, asc, func, select
from sqlalchemy.orm import Session

from app.db.default_research_profile import DEFAULT_RESEARCH_PROFILE
from app.models.research_profile import ResearchProfile


def ensure_default_research_profile(db: Session) -> ResearchProfile | None:
    """Insert the bundled default profile when the table has no rows."""
    count_stmt = select(func.count()).select_from(ResearchProfile)
    count_value = db.execute(count_stmt).scalar_one()

    if count_value > 0:
        return None

    profile = ResearchProfile(
        researcher_name=DEFAULT_RESEARCH_PROFILE["researcher_name"],  # type: ignore[arg-type]
        title=DEFAULT_RESEARCH_PROFILE.get("title"),  # type: ignore[arg-type]
        institution=DEFAULT_RESEARCH_PROFILE.get("institution"),  # type: ignore[arg-type]
        primary_research_focus=DEFAULT_RESEARCH_PROFILE["primary_research_focus"],  # type: ignore[arg-type]
        research_domains=list(DEFAULT_RESEARCH_PROFILE["research_domains"]),  # type: ignore[arg-type]
        methods=list(DEFAULT_RESEARCH_PROFILE["methods"]),  # type: ignore[arg-type]
        target_funders=list(DEFAULT_RESEARCH_PROFILE["target_funders"]),  # type: ignore[arg-type]
        preferred_outputs=list(DEFAULT_RESEARCH_PROFILE["preferred_outputs"]),  # type: ignore[arg-type]
        keywords=list(DEFAULT_RESEARCH_PROFILE["keywords"]),  # type: ignore[arg-type]
    )
    db.add(profile)
    return profile


def get_primary_profile_statement() -> Select[tuple[ResearchProfile]]:
    return select(ResearchProfile).order_by(asc(ResearchProfile.id)).limit(1)
