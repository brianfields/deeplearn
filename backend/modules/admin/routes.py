# /backend/modules/admin/routes.py
"""
Admin Module - API Routes

Minimal FastAPI routes for admin dashboard functionality.
"""

from collections.abc import AsyncGenerator, Generator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from modules.catalog.public import catalog_provider
from modules.content.public import content_provider
from modules.conversation_engine.public import conversation_engine_provider
from modules.flow_engine.public import flow_engine_admin_provider
from modules.infrastructure.public import infrastructure_provider
from modules.learning_coach.public import learning_coach_provider
from modules.learning_session.public import (
    learning_session_analytics_provider,
    learning_session_provider,
)
from modules.llm_services.public import llm_services_admin_provider
from modules.user.public import user_provider

from .models import (
    FlowRunDetails,
    FlowRunsListResponse,
    FlowStepDetails,
    LearningCoachConversationDetail,
    LearningCoachConversationsListResponse,
    LessonDetails,
    LessonsListResponse,
    LLMRequestDetails,
    LLMRequestsListResponse,
    UserDetail,
    UserListResponse,
    UserUpdateRequest,
)
from .service import AdminService

# Create router with admin prefix
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def get_sync_session() -> Generator[Any, None, None]:
    """Request-scoped synchronous database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()

    with infra.get_session_context() as s:
        yield s


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Request-scoped async database session."""
    infra = infrastructure_provider()
    infra.initialize()

    async with infra.get_async_session_context() as session:
        yield session


async def get_admin_service(
    async_session: AsyncSession = Depends(get_async_session),
    sync_session: Any = Depends(get_sync_session),
) -> AdminService:
    """
    Build AdminService for this request.

    WARNING: This service provides access to sensitive system data.
    Ensure proper authentication and authorization before calling.
    """

    # Get minimal admin providers through proper public interfaces
    flow_engine_admin = flow_engine_admin_provider(sync_session)
    llm_services_admin = llm_services_admin_provider(sync_session)

    # Get other module providers (using same session for consistency)
    content = content_provider(async_session)
    # Units are consolidated under content provider
    learning_session_analytics = learning_session_analytics_provider(async_session)
    catalog = catalog_provider(
        async_session,
        content=content,
        units=content,
        learning_sessions=learning_session_analytics,
    )

    users = user_provider(sync_session)
    learning_sessions = learning_session_provider(async_session, content)
    learning_coach = learning_coach_provider()
    conversations = conversation_engine_provider(sync_session)

    # Create admin service with all dependencies
    return AdminService(
        flow_engine_admin=flow_engine_admin,
        llm_services_admin=llm_services_admin,
        catalog=catalog,
        content=content,
        users=users,
        learning_sessions=learning_sessions,
        learning_coach=learning_coach,
        conversation_engine=conversations,
    )


# ---- User Management Routes ----


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Filter by name or email"),
    admin_service: AdminService = Depends(get_admin_service),
) -> UserListResponse:
    """List users with aggregated association counts."""

    return await admin_service.get_users(page=page, page_size=page_size, search=search)


@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user_detail(
    user_id: int,
    admin_service: AdminService = Depends(get_admin_service),
) -> UserDetail:
    """Fetch detailed information about a specific user."""

    detail = await admin_service.get_user_detail(user_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return detail


@router.put("/users/{user_id}", response_model=UserDetail)
async def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    admin_service: AdminService = Depends(get_admin_service),
) -> UserDetail:
    """Update basic account information for a user."""

    updated = await admin_service.update_user(user_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return updated


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


@router.get("/llm-requests", response_model=LLMRequestsListResponse)
async def list_llm_requests(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    admin_service: AdminService = Depends(get_admin_service),
) -> LLMRequestsListResponse:
    """Get paginated list of LLM requests."""
    return await admin_service.get_llm_requests(page=page, page_size=page_size)


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


# ---- Learning Coach Conversation Routes ----


@router.get(
    "/learning-coach/conversations",
    response_model=LearningCoachConversationsListResponse,
)
async def list_learning_coach_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    admin_service: AdminService = Depends(get_admin_service),
) -> LearningCoachConversationsListResponse:
    """List learning coach conversations for admin review."""

    return await admin_service.list_learning_coach_conversations(page=page, page_size=page_size)


@router.get(
    "/learning-coach/conversations/{conversation_id}",
    response_model=LearningCoachConversationDetail,
)
async def get_learning_coach_conversation(
    conversation_id: str,
    admin_service: AdminService = Depends(get_admin_service),
) -> LearningCoachConversationDetail:
    """Return transcript detail for a single learning coach conversation."""

    detail = await admin_service.get_learning_coach_conversation(conversation_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return detail


# ---- Lesson Management Routes ----


@router.get("/lessons", response_model=LessonsListResponse)
async def list_lessons(
    learner_level: str | None = Query(None, description="Filter by learner level"),
    search: str | None = Query(None, description="Search in title"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    admin_service: AdminService = Depends(get_admin_service),
) -> LessonsListResponse:
    """Get paginated list of lessons with optional filtering."""
    return await admin_service.get_lessons(
        learner_level=learner_level,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/lessons/{lesson_id}", response_model=LessonDetails)
async def get_lesson_details(
    lesson_id: str,
    admin_service: AdminService = Depends(get_admin_service),
) -> LessonDetails:
    """Get detailed information about a specific lesson including its package."""
    lesson_details = await admin_service.get_lesson_details(lesson_id)
    if not lesson_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lesson {lesson_id} not found")
    return lesson_details
