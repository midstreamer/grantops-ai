from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.scheduled_search import ScheduledSearch
from app.schemas.scheduled_search import (
    ScheduledSearchCreate,
    ScheduledSearchRead,
    ScheduledSearchUpdate,
)
from app.services.scheduled_search_service import run_scheduled_search, sync_scheduled_jobs

router = APIRouter(prefix="/api", tags=["scheduled-searches"])


@router.get("/scheduled-searches", response_model=list[ScheduledSearchRead])
def list_scheduled_searches(db: Session = Depends(get_db)) -> list[ScheduledSearchRead]:
    stmt = select(ScheduledSearch).order_by(desc(ScheduledSearch.created_at), desc(ScheduledSearch.id))
    return list(db.execute(stmt).scalars().all())


@router.post(
    "/scheduled-searches",
    response_model=ScheduledSearchRead,
    status_code=status.HTTP_201_CREATED,
)
def create_scheduled_search(
    payload: ScheduledSearchCreate,
    db: Session = Depends(get_db),
) -> ScheduledSearchRead:
    item = ScheduledSearch(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    sync_scheduled_jobs(db)
    return item


@router.put("/scheduled-searches/{id}", response_model=ScheduledSearchRead)
def update_scheduled_search(
    id: int,
    payload: ScheduledSearchUpdate,
    db: Session = Depends(get_db),
) -> ScheduledSearchRead:
    item = db.get(ScheduledSearch, id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Scheduled search {id} not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.add(item)
    db.commit()
    db.refresh(item)
    sync_scheduled_jobs(db)
    return item


@router.delete("/scheduled-searches/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduled_search(id: int, db: Session = Depends(get_db)) -> Response:
    item = db.get(ScheduledSearch, id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Scheduled search {id} not found.")
    db.delete(item)
    db.commit()
    sync_scheduled_jobs(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/scheduled-searches/{id}/run-now")
def run_scheduled_search_now(id: int, db: Session = Depends(get_db)) -> dict:
    try:
        report = run_scheduled_search(db, id, triggered_by="manual")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    sync_scheduled_jobs(db)
    return {"status": "ok", "report_id": report.id, "title": report.title}
