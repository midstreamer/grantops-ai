from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.grant_opportunity import GrantOpportunityRead
from app.services.grants_gov_service import search_and_persist_grants_gov

router = APIRouter(prefix="/api/search", tags=["search"])


class GrantsGovSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    rows: int = Field(25, ge=1, le=200)


@router.post("/grants-gov", response_model=list[GrantOpportunityRead])
def search_grants_gov_endpoint(
    payload: GrantsGovSearchRequest,
    db: Session = Depends(get_db),
) -> list[GrantOpportunityRead]:
    # Search + save normalized opportunities.
    saved = search_and_persist_grants_gov(db, query=payload.query, rows=payload.rows)
    return saved

