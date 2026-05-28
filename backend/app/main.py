from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.schemas.health import HealthResponse
from app.routers.research_profile import router as research_profile_router
from app.routers.opportunities import router as opportunities_router
from app.routers.grants_gov_search import router as grants_gov_search_router
from app.routers.dashboard import router as dashboard_router
from app.routers.export import router as export_router
from app.routers.literature import router as literature_router
from app.routers.proposal_drafts import router as proposal_drafts_router
from app.routers.agents import router as agents_router
from app.routers.ai import router as ai_router
from app.routers.scheduled_searches import router as scheduled_searches_router
from app.routers.weekly_reports import router as weekly_reports_router
from app.db.session import Base, SessionLocal, engine
from app.db.seed import ensure_default_research_profile
from app.services.scheduled_search_service import shutdown_scheduler, start_scheduler

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    # Create tables for local development.
    Base.metadata.create_all(bind=engine)

    # Lightweight SQLite migration for new columns on existing DBs.
    with engine.connect() as conn:
        for migration_sql in (
            "ALTER TABLE grant_opportunities ADD COLUMN notes TEXT",
            "ALTER TABLE proposal_drafts ADD COLUMN google_doc_url VARCHAR(2048)",
        ):
            try:
                conn.execute(text(migration_sql))
                conn.commit()
            except Exception:
                conn.rollback()

    # Seed a bundled default profile if the table is empty.
    db = SessionLocal()
    try:
        seeded_profile = ensure_default_research_profile(db)
        if seeded_profile is not None:
            db.commit()
    finally:
        db.close()

    start_scheduler()


@app.on_event("shutdown")
def on_shutdown() -> None:
    shutdown_scheduler()


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="grantops-ai", version="0.1.0")


app.include_router(research_profile_router)
app.include_router(opportunities_router)
app.include_router(grants_gov_search_router)
app.include_router(dashboard_router)
app.include_router(export_router)
app.include_router(literature_router)
app.include_router(proposal_drafts_router)
app.include_router(agents_router)
app.include_router(ai_router)
app.include_router(scheduled_searches_router)
app.include_router(weekly_reports_router)
