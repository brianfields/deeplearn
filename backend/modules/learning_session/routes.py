"""
Learning Session Module - HTTP Routes

Minimal FastAPI routes to support existing frontend functionality.
This is a migration, not new feature development.
"""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from modules.content.public import content_provider
from modules.infrastructure.public import infrastructure_provider
from modules.topic_catalog.public import topic_catalog_provider

from .public import LearningSessionProvider, learning_session_provider
from .service import (
    CompleteSessionRequest,
    StartSessionRequest,
    UpdateProgressRequest,
)

# ================================
# Request/Response Models (matching frontend expectations)
# ================================


class StartSessionRequestModel(BaseModel):
    """Request model for starting a session"""

    topic_id: str = Field(..., description="ID of the topic to start learning")
    user_id: str | None = Field(None, description="Optional user ID for tracking")


class UpdateProgressRequestModel(BaseModel):
    """Request model for updating progress"""

    component_id: str = Field(..., description="ID of the component being completed")
    user_answer: dict | None = Field(None, description="User's answer/response")
    is_correct: bool | None = Field(None, description="Whether the answer was correct")
    time_spent_seconds: int = Field(0, ge=0, description="Time spent on this component")


class SessionResponseModel(BaseModel):
    """Response model for session data - matches frontend ApiLearningSession"""

    id: str
    topic_id: str
    user_id: str | None
    status: str
    started_at: str
    completed_at: str | None
    current_component_index: int
    total_components: int
    progress_percentage: float
    session_data: dict


class ProgressResponseModel(BaseModel):
    """Response model for progress data - matches frontend ApiSessionProgress"""

    session_id: str
    component_id: str
    component_type: str
    started_at: str
    completed_at: str | None
    is_correct: bool | None
    user_answer: dict | None
    time_spent_seconds: int
    attempts: int


class SessionResultsResponseModel(BaseModel):
    """Response model for session results - matches frontend ApiSessionResults"""

    session_id: str
    topic_id: str
    total_components: int
    completed_components: int
    correct_answers: int
    total_time_seconds: int
    completion_percentage: float
    score_percentage: float
    achievements: list[str]


class SessionListResponseModel(BaseModel):
    """Response model for session list - matches frontend ApiSessionListResponse"""

    sessions: list[SessionResponseModel]
    total: int


class HealthResponseModel(BaseModel):
    """Response model for health check"""

    status: str
    timestamp: str


# ================================
# Router Setup
# ================================

router = APIRouter(prefix="/api/v1/sessions")


# ================================
# Dependency Injection
# ================================


def get_session() -> Generator[Session, None, None]:
    """Request-scoped database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as s:
        yield s


def get_learning_session_service(s: Session = Depends(get_session)) -> LearningSessionProvider:
    """Build LearningSessionService with all dependencies sharing the same session."""
    # Build all services with the same session for transactional consistency
    content_service = content_provider(s)
    topic_catalog_service = topic_catalog_provider(content_service)
    return learning_session_provider(s, content_service, topic_catalog_service)


# ================================
# API Routes (matching frontend expectations)
# ================================


@router.post("/", response_model=SessionResponseModel)
async def start_session(
    request: StartSessionRequestModel,
    service: LearningSessionProvider = Depends(get_learning_session_service),
) -> SessionResponseModel:
    """Start a new learning session"""
    try:
        start_request = StartSessionRequest(
            topic_id=request.topic_id,
            user_id=request.user_id,
        )

        session = await service.start_session(start_request)

        return SessionResponseModel(
            id=session.id,
            topic_id=session.topic_id,
            user_id=session.user_id,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            current_component_index=session.current_component_index,
            total_components=session.total_components,
            progress_percentage=session.progress_percentage,
            session_data=session.session_data,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start session: {e!s}") from e


@router.get("/{session_id}", response_model=SessionResponseModel)
async def get_session(
    session_id: str,
    service: LearningSessionProvider = Depends(get_learning_session_service),
) -> SessionResponseModel:
    """Get session details by ID"""
    try:
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponseModel(
            id=session.id,
            topic_id=session.topic_id,
            user_id=session.user_id,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            current_component_index=session.current_component_index,
            total_components=session.total_components,
            progress_percentage=session.progress_percentage,
            session_data=session.session_data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {e!s}") from e


@router.put("/{session_id}/progress", response_model=ProgressResponseModel)
async def update_session_progress(
    session_id: str,
    request: UpdateProgressRequestModel,
    service: LearningSessionProvider = Depends(get_learning_session_service),
) -> ProgressResponseModel:
    """Update session progress"""
    try:
        progress_request = UpdateProgressRequest(
            session_id=session_id,
            component_id=request.component_id,
            user_answer=request.user_answer,
            is_correct=request.is_correct,
            time_spent_seconds=request.time_spent_seconds,
        )

        progress = await service.update_progress(progress_request)

        return ProgressResponseModel(
            session_id=progress.session_id,
            component_id=progress.component_id,
            component_type=progress.component_type,
            started_at=progress.started_at,
            completed_at=progress.completed_at,
            is_correct=progress.is_correct,
            user_answer=progress.user_answer,
            time_spent_seconds=progress.time_spent_seconds,
            attempts=progress.attempts,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {e!s}") from e


@router.post("/{session_id}/complete", response_model=SessionResultsResponseModel)
async def complete_session(
    session_id: str,
    service: LearningSessionProvider = Depends(get_learning_session_service),
) -> SessionResultsResponseModel:
    """Complete a learning session"""
    try:
        complete_request = CompleteSessionRequest(session_id=session_id)
        results = await service.complete_session(complete_request)

        return SessionResultsResponseModel(
            session_id=results.session_id,
            topic_id=results.topic_id,
            total_components=results.total_components,
            completed_components=results.completed_components,
            correct_answers=results.correct_answers,
            total_time_seconds=results.total_time_seconds,
            completion_percentage=results.completion_percentage,
            score_percentage=results.score_percentage,
            achievements=results.achievements,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete session: {e!s}") from e


@router.post("/{session_id}/pause", response_model=SessionResponseModel)
async def pause_session(
    session_id: str,
    service: LearningSessionProvider = Depends(get_learning_session_service),
) -> SessionResponseModel:
    """Pause a learning session"""
    try:
        session = await service.pause_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponseModel(
            id=session.id,
            topic_id=session.topic_id,
            user_id=session.user_id,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            current_component_index=session.current_component_index,
            total_components=session.total_components,
            progress_percentage=session.progress_percentage,
            session_data=session.session_data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause session: {e!s}") from e


@router.get("/", response_model=SessionListResponseModel)
async def get_user_sessions(
    user_id: str | None = Query(None, description="Filter by user ID"),
    status: str | None = Query(None, description="Filter by session status"),
    topic_id: str | None = Query(None, description="Filter by topic ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    service: LearningSessionProvider = Depends(get_learning_session_service),
) -> SessionListResponseModel:
    """Get user sessions with filtering"""
    try:
        response = await service.get_user_sessions(
            user_id=user_id,
            status=status,
            topic_id=topic_id,
            limit=limit,
            offset=offset,
        )

        session_models = [
            SessionResponseModel(
                id=session.id,
                topic_id=session.topic_id,
                user_id=session.user_id,
                status=session.status,
                started_at=session.started_at,
                completed_at=session.completed_at,
                current_component_index=session.current_component_index,
                total_components=session.total_components,
                progress_percentage=session.progress_percentage,
                session_data=session.session_data,
            )
            for session in response.sessions
        ]

        return SessionListResponseModel(
            sessions=session_models,
            total=response.total,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {e!s}") from e


@router.get("/health", response_model=HealthResponseModel)
async def health_check(
    service: LearningSessionProvider = Depends(get_learning_session_service),
) -> HealthResponseModel:
    """Health check endpoint"""
    try:
        from datetime import datetime

        is_healthy = await service.check_health()

        return HealthResponseModel(
            status="ok" if is_healthy else "error",
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e!s}") from e


# Export the router for inclusion in main app
__all__ = ["router"]
