"""
Learning Session Module - HTTP Routes

Minimal FastAPI routes to support existing frontend functionality.
This is a migration, not new feature development.
"""

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from modules.content.public import content_provider
from modules.infrastructure.public import infrastructure_provider

from .repo import LearningSessionRepo
from .service import (
    CompleteSessionRequest,
    ExerciseProgressUpdate,
    LearningSessionService,
    StartSessionRequest,
    UpdateProgressRequest,
)

# ================================
# Request/Response Models (matching frontend expectations)
# ================================


class StartSessionRequestModel(BaseModel):
    """Request model for starting a session"""

    lesson_id: str = Field(..., description="ID of the lesson to start learning")
    user_id: str = Field(..., min_length=1, description="Authenticated user ID for tracking")
    unit_id: str = Field(..., min_length=1, description="ID of the unit that owns the lesson")
    session_id: str | None = Field(None, description="Optional client-generated session ID for offline-first support")


class UpdateProgressRequestModel(BaseModel):
    """Request model for updating exercise progress"""

    exercise_id: str = Field(..., description="ID of the exercise being completed")
    exercise_type: str = Field(..., description="Type of exercise, e.g. 'mcq', 'short_answer', 'coding'", pattern="^(mcq|short_answer|coding)$")
    user_answer: dict[str, Any] | None = Field(None, description="User's answer/response")
    is_correct: bool | None = Field(None, description="Whether the answer was correct")
    time_spent_seconds: int = Field(0, ge=0, description="Time spent on this exercise")
    user_id: str = Field(..., min_length=1, description="Authenticated user identifier")


class SessionResponseModel(BaseModel):
    """Response model for session data - matches frontend ApiLearningSession"""

    id: str
    lesson_id: str
    unit_id: str
    user_id: str | None
    status: str
    started_at: str
    completed_at: str | None
    current_exercise_index: int
    total_exercises: int
    progress_percentage: float
    session_data: dict[str, Any]


class ProgressResponseModel(BaseModel):
    """Response model for exercise progress data - matches frontend expectations"""

    session_id: str
    exercise_id: str
    exercise_type: str
    started_at: str
    completed_at: str | None
    is_correct: bool | None
    user_answer: dict[str, Any] | None
    time_spent_seconds: int
    attempts: int
    attempt_history: list[dict[str, Any]]
    has_been_answered_correctly: bool


class ExerciseProgressUpdateModel(BaseModel):
    """Individual exercise progress for batch updates"""

    exercise_id: str
    exercise_type: str
    user_answer: dict[str, Any] | None
    is_correct: bool | None
    time_spent_seconds: int


class CompleteSessionRequestModel(BaseModel):
    """Request model for completing a session with optional batch progress"""

    progress_updates: list[ExerciseProgressUpdateModel] | None = Field(
        None,
        description="Optional batch of exercise progress updates to apply before completion",
    )
    lesson_id: str | None = Field(
        None,
        description="Optional lesson ID to create session if it doesn't exist (for offline-first support)",
    )


class SessionResultsResponseModel(BaseModel):
    """Response model for session results - matches frontend ApiSessionResults"""

    session_id: str
    lesson_id: str
    unit_id: str
    total_exercises: int
    completed_exercises: int
    correct_exercises: int
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

router = APIRouter(prefix="/api/v1/learning_session")


# ================================
# Dependency Injection
# ================================


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Request-scoped database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()
    async with infra.get_async_session_context() as s:
        yield s


def get_learning_session_service(s: AsyncSession = Depends(get_db_session)) -> LearningSessionService:
    """Build LearningSessionService with all dependencies sharing the same session."""
    # Build all services with the same session for transactional consistency
    content_service = content_provider(s)
    # Units are consolidated under content provider
    return LearningSessionService(LearningSessionRepo(s), content_service)


# ================================
# API Routes (matching frontend expectations)
# ================================


@router.post("/", response_model=SessionResponseModel)
async def start_session(
    request: StartSessionRequestModel,
    service: LearningSessionService = Depends(get_learning_session_service),
) -> SessionResponseModel:
    """Start a new learning session"""
    start_request = StartSessionRequest(
        lesson_id=request.lesson_id,
        user_id=request.user_id,
        unit_id=request.unit_id,
        session_id=request.session_id,
    )

    session = await service.start_session(start_request)

    return SessionResponseModel(
        id=session.id,
        lesson_id=session.lesson_id,
        unit_id=session.unit_id,
        user_id=session.user_id,
        status=session.status,
        started_at=session.started_at,
        completed_at=session.completed_at,
        current_exercise_index=session.current_exercise_index,
        total_exercises=session.total_exercises,
        progress_percentage=session.progress_percentage,
        session_data=session.session_data,
    )


@router.get("/{session_id}", response_model=SessionResponseModel)
async def get_session(
    session_id: str,
    user_id: str = Query(..., description="Authenticated user identifier"),
    service: LearningSessionService = Depends(get_learning_session_service),
) -> SessionResponseModel:
    """Get session details by ID"""
    session = await service.get_session(session_id, user_id=user_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponseModel(
        id=session.id,
        lesson_id=session.lesson_id,
        unit_id=session.unit_id,
        user_id=session.user_id,
        status=session.status,
        started_at=session.started_at,
        completed_at=session.completed_at,
        current_exercise_index=session.current_exercise_index,
        total_exercises=session.total_exercises,
        progress_percentage=session.progress_percentage,
        session_data=session.session_data,
    )


@router.put("/{session_id}/progress", response_model=ProgressResponseModel)
async def update_session_progress(
    session_id: str,
    request: UpdateProgressRequestModel,
    service: LearningSessionService = Depends(get_learning_session_service),
) -> ProgressResponseModel:
    """Update session progress"""
    progress_request = UpdateProgressRequest(
        session_id=session_id,
        exercise_id=request.exercise_id,
        exercise_type=request.exercise_type,
        user_answer=request.user_answer,
        is_correct=request.is_correct,
        time_spent_seconds=request.time_spent_seconds,
        user_id=request.user_id,
    )

    progress = await service.update_progress(progress_request)

    return ProgressResponseModel(
        session_id=progress.session_id,
        exercise_id=progress.exercise_id,
        exercise_type=progress.exercise_type,
        started_at=progress.started_at,
        completed_at=progress.completed_at,
        is_correct=progress.is_correct,
        user_answer=progress.user_answer,
        time_spent_seconds=progress.time_spent_seconds,
        attempts=progress.attempts,
        attempt_history=progress.attempt_history,
        has_been_answered_correctly=progress.has_been_answered_correctly,
    )


@router.post("/{session_id}/complete", response_model=SessionResultsResponseModel)
async def complete_session(
    session_id: str,
    request: CompleteSessionRequestModel,
    user_id: str = Query(..., description="Authenticated user identifier"),
    service: LearningSessionService = Depends(get_learning_session_service),
) -> SessionResultsResponseModel:
    """Complete a learning session with optional batch progress updates"""
    progress_updates = None
    if request.progress_updates:
        progress_updates = [
            ExerciseProgressUpdate(
                exercise_id=p.exercise_id,
                exercise_type=p.exercise_type,
                user_answer=p.user_answer,
                is_correct=p.is_correct,
                time_spent_seconds=p.time_spent_seconds,
            )
            for p in request.progress_updates
        ]

    complete_request = CompleteSessionRequest(
        session_id=session_id,
        user_id=user_id,
        progress_updates=progress_updates,
        lesson_id=request.lesson_id,
    )
    results = await service.complete_session(complete_request)

    return SessionResultsResponseModel(
        session_id=results.session_id,
        lesson_id=results.lesson_id,
        unit_id=results.unit_id,
        total_exercises=results.total_exercises,
        completed_exercises=results.completed_exercises,
        correct_exercises=results.correct_exercises,
        total_time_seconds=results.total_time_seconds,
        completion_percentage=results.completion_percentage,
        score_percentage=results.score_percentage,
        achievements=results.achievements,
    )


@router.post("/{session_id}/pause", response_model=SessionResponseModel)
async def pause_session(
    session_id: str,
    user_id: str = Query(..., description="Authenticated user identifier"),
    service: LearningSessionService = Depends(get_learning_session_service),
) -> SessionResponseModel:
    """Pause a learning session"""
    session = await service.pause_session(session_id, user_id=user_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponseModel(
        id=session.id,
        lesson_id=session.lesson_id,
        unit_id=session.unit_id,
        user_id=session.user_id,
        status=session.status,
        started_at=session.started_at,
        completed_at=session.completed_at,
        current_exercise_index=session.current_exercise_index,
        total_exercises=session.total_exercises,
        progress_percentage=session.progress_percentage,
        session_data=session.session_data,
    )


@router.get("/", response_model=SessionListResponseModel)
async def get_user_sessions(
    user_id: str = Query(..., description="Filter by user ID"),
    status: str | None = Query(None, description="Filter by session status"),
    lesson_id: str | None = Query(None, description="Filter by lesson ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    service: LearningSessionService = Depends(get_learning_session_service),
) -> SessionListResponseModel:
    """Get user sessions with filtering"""
    response = await service.get_user_sessions(
        user_id=user_id,
        status=status,
        lesson_id=lesson_id,
        limit=limit,
        offset=offset,
    )

    session_models = [
        SessionResponseModel(
            id=session.id,
            lesson_id=session.lesson_id,
            unit_id=session.unit_id,
            user_id=session.user_id,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            current_exercise_index=session.current_exercise_index,
            total_exercises=session.total_exercises,
            progress_percentage=session.progress_percentage,
            session_data=session.session_data,
        )
        for session in response.sessions
    ]

    return SessionListResponseModel(
        sessions=session_models,
        total=response.total,
    )


@router.get("/health", response_model=HealthResponseModel)
async def health_check(
    service: LearningSessionService = Depends(get_learning_session_service),
) -> HealthResponseModel:
    """Health check endpoint"""
    is_healthy = await service.check_health()

    return HealthResponseModel(
        status="ok" if is_healthy else "error",
        timestamp=datetime.utcnow().isoformat(),
    )


# Export the router for inclusion in main app
__all__ = ["router"]
