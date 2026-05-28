from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.grant_opportunity import GrantOpportunity
from app.models.research_profile import ResearchProfile
from app.models.scheduled_search import ScheduledSearch
from app.models.weekly_report import WeeklyReport
from app.services.fit_scoring_service import score_opportunity
from app.services.grants_gov_service import (
    search_grants_gov,
    upsert_grants_gov_opportunity_from_hit,
)

JOB_PREFIX = "scheduled_search_"
_scheduler: Optional[BackgroundScheduler] = None


def _primary_profile(db: Session) -> Optional[ResearchProfile]:
    stmt = select(ResearchProfile).order_by(asc(ResearchProfile.id)).limit(1)
    return db.execute(stmt).scalars().first()


def _job_id(search_id: int) -> str:
    return f"{JOB_PREFIX}{search_id}"


def run_scheduled_search(
    db: Session,
    search_id: int,
    *,
    triggered_by: str = "manual",
) -> WeeklyReport:
    scheduled = db.get(ScheduledSearch, search_id)
    if scheduled is None:
        raise ValueError(f"Scheduled search {search_id} not found.")

    hits = search_grants_gov(scheduled.query, rows=scheduled.rows)
    new_opportunity_ids: list[int] = []

    for hit in hits:
        source_id = str(hit.get("id") or "")
        existing = None
        if source_id:
            stmt = select(GrantOpportunity.id).where(
                GrantOpportunity.source == "grants.gov",
                GrantOpportunity.source_id == source_id,
            )
            existing = db.execute(stmt).first()

        opp = upsert_grants_gov_opportunity_from_hit(db, hit, fetch_detail=False)
        if opp is None:
            continue
        db.flush()

        if existing is None:
            new_opportunity_ids.append(opp.id)

    scored_count = 0
    profile = _primary_profile(db)
    if profile is not None:
        for opp_id in new_opportunity_ids:
            opp = db.get(GrantOpportunity, opp_id)
            if opp is None:
                continue
            result = score_opportunity(opp, profile)
            opp.fit_score = int(result["fit_score"])
            opp.recommendation = str(result["recommendation"])
            opp.fit_summary = str(result["fit_summary"])
            opp.next_action = str(result["recommended_next_action"])
            raw = opp.raw_data if isinstance(opp.raw_data, dict) else {}
            opp.raw_data = {**raw, "fit_analysis": result}
            db.add(opp)
            scored_count += 1

    scheduled.last_run_at = datetime.now(timezone.utc)
    db.add(scheduled)

    title = f"Weekly discovery report: {scheduled.name}"
    content = (
        f"Query: {scheduled.query}\n"
        f"Rows requested: {scheduled.rows}\n"
        f"Triggered by: {triggered_by}\n"
        f"Grants.gov hits: {len(hits)}\n"
        f"New opportunities saved: {len(new_opportunity_ids)}\n"
        f"New opportunities scored: {scored_count}\n"
        f"Run time (UTC): {scheduled.last_run_at.isoformat()}"
    )
    report = WeeklyReport(title=title, content=content)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def _run_scheduled_search_job(search_id: int) -> None:
    db = SessionLocal()
    try:
        run_scheduled_search(db, search_id, triggered_by="scheduler")
    finally:
        db.close()


def scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
    return _scheduler


def sync_scheduled_jobs(db: Session) -> None:
    sch = scheduler()
    existing_ids = {_job_id(item.id): item for item in db.execute(select(ScheduledSearch)).scalars().all()}

    for job in sch.get_jobs():
        if job.id.startswith(JOB_PREFIX) and job.id not in existing_ids:
            sch.remove_job(job.id)

    for item in existing_ids.values():
        job_id = _job_id(item.id)
        if not item.active:
            if sch.get_job(job_id):
                sch.remove_job(job_id)
            continue

        trigger = IntervalTrigger(weeks=1)
        sch.add_job(
            _run_scheduled_search_job,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs={"search_id": item.id},
        )


def start_scheduler() -> None:
    sch = scheduler()
    if not sch.running:
        sch.start()
    db = SessionLocal()
    try:
        sync_scheduled_jobs(db)
    finally:
        db.close()


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
