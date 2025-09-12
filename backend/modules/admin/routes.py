# /backend/modules/admin/routes.py
"""
Admin Module - API Routes

Minimal FastAPI routes for admin dashboard functionality.
"""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from modules.infrastructure.public import infrastructure_provider

from .service import (
    AdminService,
    FlowRunDetails,
    FlowRunsListResponse,
    FlowStepDetails,
    LLMRequestDetails,
)

# Create router with admin prefix
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def get_session() -> Generator[Session, None, None]:
    """Request-scoped database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()

    with infra.get_session_context() as s:
        yield s


def get_admin_service(session: Session = Depends(get_session)) -> AdminService:
    """
    Build AdminService for this request.

    WARNING: This service provides access to sensitive system data.
    Ensure proper authentication and authorization before calling.
    """
    from modules.content.public import content_provider
    from modules.flow_engine.public import flow_engine_admin_provider
    from modules.lesson_catalog.public import lesson_catalog_provider
    from modules.llm_services.public import llm_services_admin_provider

    # Get minimal admin providers through proper public interfaces
    flow_engine_admin = flow_engine_admin_provider(session)
    llm_services_admin = llm_services_admin_provider(session)

    # Get other module providers (using same session for consistency)
    content = content_provider(session)
    lesson_catalog = lesson_catalog_provider(content)

    # Create placeholder providers for async services
    # In practice, these would be properly initialized with async context
    learning_sessions = None  # Would need proper async initialization

    # Create admin service with all dependencies
    return AdminService(
        flow_engine_admin=flow_engine_admin,
        llm_services_admin=llm_services_admin,
        content=content,
        lesson_catalog=lesson_catalog,
        learning_sessions=learning_sessions,  # type: ignore
    )


# ---- Flow Management Routes ----


@router.get("/flows", response_model=FlowRunsListResponse)
async def list_flow_runs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    admin_service: AdminService = Depends(get_admin_service),
) -> FlowRunsListResponse:
    """Get paginated list of recent flow runs."""
    return await admin_service.get_flow_runs(page=page, page_size=page_size)


@router.get("/flows/{flow_run_id}", response_model=FlowRunDetails)
async def get_flow_run_details(
    flow_run_id: str,
    admin_service: AdminService = Depends(get_admin_service),
) -> FlowRunDetails:
    """Get detailed information about a specific flow run including all steps."""
    flow_details = await admin_service.get_flow_run_details(flow_run_id)
    if not flow_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Flow run {flow_run_id} not found")
    return flow_details


@router.get("/flows/{flow_run_id}/steps/{step_run_id}", response_model=FlowStepDetails)
async def get_flow_step_details(
    flow_run_id: str,
    step_run_id: str,
    admin_service: AdminService = Depends(get_admin_service),
) -> FlowStepDetails:
    """Get detailed information about a specific flow step."""
    step_details = await admin_service.get_flow_step_details(step_run_id)
    if not step_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Flow step {step_run_id} not found")

    # Verify the step belongs to the specified flow run
    if step_details.flow_run_id != flow_run_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Flow step {step_run_id} not found in flow run {flow_run_id}")

    return step_details


# ---- LLM Request Management Routes ----


@router.get("/llm-requests/{request_id}", response_model=LLMRequestDetails)
async def get_llm_request_details(
    request_id: str,
    admin_service: AdminService = Depends(get_admin_service),
) -> LLMRequestDetails:
    """Get detailed information about a specific LLM request."""
    request_details = await admin_service.get_llm_request_details(request_id)
    if not request_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"LLM request {request_id} not found")
    return request_details
