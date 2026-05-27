from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.adk.grantops_orchestrator import (
    GrantOpsAdkStepUnavailableError,
    run_discovery_workflow_via_adk,
)
from app.agents.grantops_orchestrator import GrantOpsOrchestrator
from app.config import get_settings
from app.db.session import get_db
from app.schemas.agent_workflow import DiscoveryWorkflowRequest, DiscoveryWorkflowResponse

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/discovery-workflow", response_model=DiscoveryWorkflowResponse)
async def run_discovery_workflow(
    payload: DiscoveryWorkflowRequest,
    db: Session = Depends(get_db),
) -> DiscoveryWorkflowResponse:
    settings = get_settings()
    if settings.use_adk_orchestrator:
        try:
            report = await run_discovery_workflow_via_adk(
                db, query=payload.query, rows=payload.rows
            )
        except GrantOpsAdkStepUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return DiscoveryWorkflowResponse(
            orchestrator="google_adk",
            **report.to_dict(),
        )

    orchestrator = GrantOpsOrchestrator(db)
    report = orchestrator.run_discovery_workflow(query=payload.query, rows=payload.rows)
    return DiscoveryWorkflowResponse(
        orchestrator="internal",
        **report.to_dict(),
    )
