from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.grantops_orchestrator import GrantOpsOrchestrator
from app.db.session import get_db
from app.schemas.agent_workflow import DiscoveryWorkflowRequest, DiscoveryWorkflowResponse

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/discovery-workflow", response_model=DiscoveryWorkflowResponse)
def run_discovery_workflow(
    payload: DiscoveryWorkflowRequest,
    db: Session = Depends(get_db),
) -> DiscoveryWorkflowResponse:
    orchestrator = GrantOpsOrchestrator(db)
    report = orchestrator.run_discovery_workflow(query=payload.query, rows=payload.rows)
    return DiscoveryWorkflowResponse(**report.to_dict())
