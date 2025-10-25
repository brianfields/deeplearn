"""Admin observability routes for flow engine data."""

from collections.abc import Generator
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..infrastructure.public import infrastructure_provider
from .public import FlowRunQueryService, flow_engine_admin_provider

router = APIRouter(prefix="/api/v1/flow-engine", tags=["flow-engine"])


def get_session() -> Generator[Session, None, None]:
    """Request-scoped database session with auto-commit."""

    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as session:
        yield session


def get_query_service(session: Session = Depends(get_session)) -> FlowRunQueryService:
    """Build FlowRunQueryService for admin observability queries."""

    return flow_engine_admin_provider(session)


@router.get("/runs")
def list_flow_runs(
    arq_task_id: str | None = Query(default=None, description="Filter by ARQ task identifier"),
    unit_id: str | None = Query(default=None, description="Filter by unit identifier"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: FlowRunQueryService = Depends(get_query_service),
) -> list[dict[str, Any]]:
    """Admin Observability: list flow runs with optional filters."""

    runs = service.list_flow_runs(arq_task_id=arq_task_id, unit_id=unit_id, limit=limit, offset=offset)
    return [
        {
            "id": flow_run.id,
            "flow_name": flow_run.flow_name,
            "status": flow_run.status,
            "execution_mode": flow_run.execution_mode,
            "arq_task_id": flow_run.arq_task_id,
            "user_id": flow_run.user_id,
            "created_at": flow_run.created_at.isoformat(),
            "started_at": flow_run.started_at.isoformat() if flow_run.started_at else None,
            "completed_at": flow_run.completed_at.isoformat() if flow_run.completed_at else None,
            "execution_time_ms": flow_run.execution_time_ms,
            "total_tokens": flow_run.total_tokens,
            "total_cost": flow_run.total_cost,
            "step_count": flow_run.step_count,
            "error_message": flow_run.error_message,
        }
        for flow_run in runs
    ]


@router.get("/runs/{flow_run_id}")
def get_flow_run(
    flow_run_id: uuid.UUID,
    service: FlowRunQueryService = Depends(get_query_service),
) -> dict[str, Any]:
    """Admin Observability: retrieve a flow run with steps inline."""

    run = service.get_flow_run_by_id(flow_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Flow run not found")

    return {
        "id": run.id,
        "flow_name": run.flow_name,
        "status": run.status,
        "execution_mode": run.execution_mode,
        "arq_task_id": run.arq_task_id,
        "user_id": run.user_id,
        "current_step": run.current_step,
        "step_progress": run.step_progress,
        "total_steps": run.total_steps,
        "progress_percentage": run.progress_percentage,
        "created_at": run.created_at.isoformat(),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "last_heartbeat": run.last_heartbeat.isoformat() if run.last_heartbeat else None,
        "execution_time_ms": run.execution_time_ms,
        "total_tokens": run.total_tokens,
        "total_cost": run.total_cost,
        "inputs": run.inputs,
        "outputs": run.outputs,
        "flow_metadata": run.flow_metadata,
        "error_message": run.error_message,
        "steps": [
            {
                "id": step.id,
                "flow_run_id": step.flow_run_id,
                "llm_request_id": step.llm_request_id,
                "step_name": step.step_name,
                "step_order": step.step_order,
                "status": step.status,
                "inputs": step.inputs,
                "outputs": step.outputs,
                "tokens_used": step.tokens_used,
                "cost_estimate": step.cost_estimate,
                "execution_time_ms": step.execution_time_ms,
                "error_message": step.error_message,
                "step_metadata": step.step_metadata,
                "created_at": step.created_at.isoformat(),
                "completed_at": step.completed_at.isoformat() if step.completed_at else None,
            }
            for step in run.steps
        ],
    }
