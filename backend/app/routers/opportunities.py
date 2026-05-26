from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.grant_opportunity import GrantOpportunity
from app.models.literature_item import LiteratureItem
from app.models.proposal_draft import ProposalDraft
from app.models.research_profile import ResearchProfile
from app.schemas.ai_summary import OpportunityAISummary
from app.schemas.proposal_draft import ProposalDraftRead, ProposalDraftUpdate
from app.schemas.grant_opportunity import (
    GrantOpportunityCreate,
    GrantOpportunityRead,
    GrantOpportunityUpdate,
)
from app.services.fit_scoring_service import score_opportunity
from app.services.llm_service import (
    LLMNotConfiguredError,
    LLMProviderError,
    concept_note_to_markdown,
    draft_concept_note_structured,
    summarize_opportunity,
)

router = APIRouter(prefix="/api", tags=["opportunities"])


@router.get("/opportunities", response_model=list[GrantOpportunityRead])
def list_opportunities(db: Session = Depends(get_db)) -> list[GrantOpportunityRead]:
    stmt = (
        select(GrantOpportunity)
        .order_by(
            asc(GrantOpportunity.deadline).nulls_last(),
            desc(GrantOpportunity.updated_at),
            desc(GrantOpportunity.id),
        )
    )
    return list(db.execute(stmt).scalars().all())


@router.post(
    "/opportunities",
    response_model=GrantOpportunityRead,
    status_code=status.HTTP_201_CREATED,
)
def create_opportunity(
    payload: GrantOpportunityCreate,
    db: Session = Depends(get_db),
) -> GrantOpportunityRead:
    data = payload.model_dump()
    if data.get("url") is not None:
        data["url"] = str(data["url"])

    opp = GrantOpportunity(**data)
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp


@router.get("/opportunities/{id}", response_model=GrantOpportunityRead)
def get_opportunity(id: int, db: Session = Depends(get_db)) -> GrantOpportunityRead:
    opp = db.get(GrantOpportunity, id)
    if opp is None:
        raise HTTPException(status_code=404, detail=f"Opportunity {id} not found.")
    return opp


@router.put("/opportunities/{id}", response_model=GrantOpportunityRead)
def update_opportunity(
    id: int,
    payload: GrantOpportunityUpdate,
    db: Session = Depends(get_db),
) -> GrantOpportunityRead:
    opp = db.get(GrantOpportunity, id)
    if opp is None:
        raise HTTPException(status_code=404, detail=f"Opportunity {id} not found.")

    data = payload.model_dump(exclude_unset=True)
    if "url" in data and data["url"] is not None:
        data["url"] = str(data["url"])

    for field, value in data.items():
        setattr(opp, field, value)

    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp


@router.delete("/opportunities/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(id: int, db: Session = Depends(get_db)) -> Response:
    opp = db.get(GrantOpportunity, id)
    if opp is None:
        raise HTTPException(status_code=404, detail=f"Opportunity {id} not found.")

    db.delete(opp)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_primary_profile(db: Session) -> ResearchProfile:
    stmt = select(ResearchProfile).order_by(asc(ResearchProfile.id)).limit(1)
    profile = db.execute(stmt).scalars().first()
    if profile is None:
        raise HTTPException(status_code=404, detail="No research profile available for scoring.")
    return profile


@router.post("/opportunities/{id}/score")
def score_one_opportunity(id: int, db: Session = Depends(get_db)) -> dict:
    opp = db.get(GrantOpportunity, id)
    if opp is None:
        raise HTTPException(status_code=404, detail=f"Opportunity {id} not found.")

    profile = _get_primary_profile(db)
    result = score_opportunity(opp, profile)

    opp.fit_score = int(result["fit_score"])
    opp.recommendation = str(result["recommendation"])
    opp.fit_summary = str(result["fit_summary"])
    opp.next_action = str(result["recommended_next_action"])

    existing_raw = opp.raw_data if isinstance(opp.raw_data, dict) else {}
    opp.raw_data = {**existing_raw, "fit_analysis": result}
    db.add(opp)
    db.commit()
    db.refresh(opp)

    return {
        "opportunity": GrantOpportunityRead.model_validate(opp).model_dump(),
        "score": result,
    }


@router.post("/opportunities/score-all")
def score_all_opportunities(db: Session = Depends(get_db)) -> dict:
    profile = _get_primary_profile(db)
    opps = db.execute(select(GrantOpportunity)).scalars().all()

    scored: list[dict] = []
    for opp in opps:
        result = score_opportunity(opp, profile)
        opp.fit_score = int(result["fit_score"])
        opp.recommendation = str(result["recommendation"])
        opp.fit_summary = str(result["fit_summary"])
        opp.next_action = str(result["recommended_next_action"])
        existing_raw = opp.raw_data if isinstance(opp.raw_data, dict) else {}
        opp.raw_data = {**existing_raw, "fit_analysis": result}
        db.add(opp)
        scored.append(
            {
                "opportunity_id": opp.id,
                "fit_score": result["fit_score"],
                "recommendation": result["recommendation"],
            }
        )

    db.commit()
    return {"count": len(scored), "results": scored}


@router.post("/opportunities/{id}/ai-summary", response_model=OpportunityAISummary)
def generate_ai_summary(id: int, db: Session = Depends(get_db)) -> OpportunityAISummary:
    opp = db.get(GrantOpportunity, id)
    if opp is None:
        raise HTTPException(status_code=404, detail=f"Opportunity {id} not found.")

    profile = _get_primary_profile(db)
    lit_stmt = select(LiteratureItem).where(LiteratureItem.opportunity_id == id)
    literature_items = list(db.execute(lit_stmt).scalars().all())

    try:
        summary = summarize_opportunity(opp, profile, literature_items)
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    existing_raw = opp.raw_data if isinstance(opp.raw_data, dict) else {}
    opp.raw_data = {**existing_raw, "ai_summary": summary}
    db.add(opp)
    db.commit()

    return OpportunityAISummary(**summary)


@router.get("/opportunities/{id}/drafts", response_model=list[ProposalDraftRead])
def list_opportunity_drafts(id: int, db: Session = Depends(get_db)) -> list[ProposalDraftRead]:
    opp = db.get(GrantOpportunity, id)
    if opp is None:
        raise HTTPException(status_code=404, detail=f"Opportunity {id} not found.")

    stmt = (
        select(ProposalDraft)
        .where(ProposalDraft.opportunity_id == id)
        .order_by(desc(ProposalDraft.updated_at), desc(ProposalDraft.id))
    )
    return list(db.execute(stmt).scalars().all())


@router.put("/opportunities/{id}/drafts/{draft_id}", response_model=ProposalDraftRead)
def update_opportunity_draft(
    id: int,
    draft_id: int,
    payload: ProposalDraftUpdate,
    db: Session = Depends(get_db),
) -> ProposalDraftRead:
    draft = db.get(ProposalDraft, draft_id)
    if draft is None or draft.opportunity_id != id:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found.")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(draft, field, value)

    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@router.post(
    "/opportunities/{id}/concept-note",
    response_model=ProposalDraftRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_concept_note(id: int, db: Session = Depends(get_db)) -> ProposalDraftRead:
    opp = db.get(GrantOpportunity, id)
    if opp is None:
        raise HTTPException(status_code=404, detail=f"Opportunity {id} not found.")

    profile = _get_primary_profile(db)
    lit_stmt = select(LiteratureItem).where(LiteratureItem.opportunity_id == id)
    literature_items = list(db.execute(lit_stmt).scalars().all())

    try:
        structured = draft_concept_note_structured(opp, profile, literature_items)
        content = concept_note_to_markdown(structured)
        title = structured.get("working_title") or f"Concept note: {opp.title[:120]}"
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    draft = ProposalDraft(
        opportunity_id=id,
        title=title[:500],
        draft_type="concept_note",
        content=content,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft

