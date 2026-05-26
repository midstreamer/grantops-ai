from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.grant_opportunity import GrantOpportunity
from app.models.literature_item import LiteratureItem
from app.models.research_profile import ResearchProfile
from app.schemas.literature import LiteratureItemRead, LiteratureSearchRequest
from app.services.openalex_service import (
    build_opportunity_literature_query,
    search_and_persist,
)

router = APIRouter(prefix="/api", tags=["literature"])


def _get_primary_profile(db: Session) -> ResearchProfile:
    stmt = select(ResearchProfile).order_by(asc(ResearchProfile.id)).limit(1)
    profile = db.execute(stmt).scalars().first()
    if profile is None:
        raise HTTPException(status_code=404, detail="No research profile available.")
    return profile


@router.post("/literature/search", response_model=list[LiteratureItemRead])
def search_literature(
    payload: LiteratureSearchRequest,
    db: Session = Depends(get_db),
) -> list[LiteratureItemRead]:
    saved = search_and_persist(
        db,
        query=payload.query,
        per_page=payload.per_page,
        opportunity_id=payload.opportunity_id,
    )
    return saved


@router.post("/opportunities/{id}/literature", response_model=list[LiteratureItemRead])
def find_opportunity_literature(id: int, db: Session = Depends(get_db)) -> list[LiteratureItemRead]:
    opp = db.get(GrantOpportunity, id)
    if opp is None:
        raise HTTPException(status_code=404, detail=f"Opportunity {id} not found.")

    profile = _get_primary_profile(db)
    query = build_opportunity_literature_query(opp, profile)
    saved = search_and_persist(db, query=query, per_page=10, opportunity_id=id)
    return saved


@router.get("/opportunities/{id}/literature", response_model=list[LiteratureItemRead])
def list_opportunity_literature(id: int, db: Session = Depends(get_db)) -> list[LiteratureItemRead]:
    opp = db.get(GrantOpportunity, id)
    if opp is None:
        raise HTTPException(status_code=404, detail=f"Opportunity {id} not found.")

    stmt = (
        select(LiteratureItem)
        .where(LiteratureItem.opportunity_id == id)
        .order_by(
            desc(LiteratureItem.cited_by_count).nulls_last(),
            desc(LiteratureItem.publication_year).nulls_last(),
            desc(LiteratureItem.id),
        )
    )
    return list(db.execute(stmt).scalars().all())
