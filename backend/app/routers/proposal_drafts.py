from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.proposal_draft import ProposalDraftRead
from app.services.google_docs_service import (
    GoogleDocsError,
    GoogleDocsNotConfiguredError,
    create_google_doc_from_proposal_draft,
)

router = APIRouter(prefix="/api", tags=["proposal-drafts"])


@router.post(
    "/proposal-drafts/{id}/export/google-doc",
    response_model=ProposalDraftRead,
)
def export_proposal_draft_to_google_doc(
    id: int,
    db: Session = Depends(get_db),
) -> ProposalDraftRead:
    try:
        draft = create_google_doc_from_proposal_draft(db, id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GoogleDocsNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GoogleDocsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return draft
