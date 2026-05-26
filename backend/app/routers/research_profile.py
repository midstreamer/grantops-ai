from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.seed import ensure_default_research_profile
from app.models.research_profile import ResearchProfile
from app.schemas.research_profile import (
    ResearchProfileCreate,
    ResearchProfileRead,
    ResearchProfileUpdate,
)

router = APIRouter(prefix="/api", tags=["research-profile"])


@router.get("/research-profile", response_model=ResearchProfileRead)
def get_research_profile(db: Session = Depends(get_db)) -> ResearchProfileRead:
    stmt = select(ResearchProfile).order_by(asc(ResearchProfile.id)).limit(1)
    profile = db.execute(stmt).scalars().first()

    if profile is None:
        seeded = ensure_default_research_profile(db)
        if seeded is not None:
            db.commit()
            db.refresh(seeded)
            profile = seeded

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No research profile exists yet.",
        )

    return profile


@router.post(
    "/research-profile",
    response_model=ResearchProfileRead,
    status_code=status.HTTP_201_CREATED,
)
def create_research_profile(
    payload: ResearchProfileCreate,
    db: Session = Depends(get_db),
) -> ResearchProfileRead:
    profile = ResearchProfile(**payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/research-profile/{id}", response_model=ResearchProfileRead)
def update_research_profile(
    id: int,
    payload: ResearchProfileUpdate,
    db: Session = Depends(get_db),
) -> ResearchProfileRead:
    profile = db.get(ResearchProfile, id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research profile {id} not found.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

