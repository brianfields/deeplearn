"""
Learning Session Module - Service Layer

Minimal business logic to support existing frontend functionality.
This is a migration, not new feature development.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..content.public import ContentProvider
from ..topic_catalog.public import TopicCatalogProvider
from .models import LearningSessionModel, SessionStatus
from .repo import LearningSessionRepo

# ================================
# Service DTOs (matching frontend expectations)
# ================================


@dataclass
class LearningSession:
    """Learning session DTO - matches frontend ApiLearningSession"""

    id: str
    topic_id: str
    user_id: str | None
    status: str
    started_at: str
    completed_at: str | None
    current_component_index: int
    total_components: int
    progress_percentage: float
    session_data: dict[str, Any]


@dataclass
class SessionProgress:
    """Session progress DTO - matches frontend ApiSessionProgress"""

    session_id: str
    component_id: str
    component_type: str
    started_at: str
    completed_at: str | None
    is_correct: bool | None
    user_answer: Any | None
    time_spent_seconds: int
    attempts: int


@dataclass
class SessionResults:
    """Session results DTO - matches frontend ApiSessionResults"""

    session_id: str
    topic_id: str
    total_components: int
    completed_components: int
    correct_answers: int
    total_time_seconds: int
    completion_percentage: float
    score_percentage: float
    achievements: list[str]


@dataclass
class StartSessionRequest:
    """Request DTO for starting a session"""

    topic_id: str
    user_id: str | None = None


@dataclass
class UpdateProgressRequest:
    """Request DTO for updating progress"""

    session_id: str
    component_id: str
    user_answer: Any | None = None
    is_correct: bool | None = None
    time_spent_seconds: int = 0


@dataclass
class CompleteSessionRequest:
    """Request DTO for completing a session"""

    session_id: str


@dataclass
class SessionListResponse:
    """Response DTO for session list"""

    sessions: list[LearningSession]
    total: int


# ================================
# Service Implementation
# ================================


class LearningSessionService:
    """Service for learning session business logic"""

    def __init__(
        self,
        repo: LearningSessionRepo,
        content_provider: ContentProvider,
        topic_catalog_provider: TopicCatalogProvider,
    ):
        self.repo = repo
        self.content = content_provider
        self.topic_catalog = topic_catalog_provider

    async def start_session(self, request: StartSessionRequest) -> LearningSession:
        """Start a new learning session"""
        # Validate topic exists
        topic_detail = self.topic_catalog.get_topic_details(request.topic_id)
        if not topic_detail:
            raise ValueError(f"Topic {request.topic_id} not found")

        # Check for existing active session (if user provided)
        if request.user_id:
            existing_session = self.repo.get_active_session_for_user_and_topic(request.user_id, request.topic_id)
            if existing_session:
                # Return existing session instead of creating new one
                return self._to_session_dto(existing_session)

        # Get topic content to determine component count
        topic_content = self.content.get_topic(request.topic_id)
        total_components = len(topic_content.components) if topic_content else 0

        # Create new session
        session = self.repo.create_session(
            topic_id=request.topic_id,
            user_id=request.user_id,
            total_components=total_components,
        )

        return self._to_session_dto(session)

    async def get_session(self, session_id: str) -> LearningSession | None:
        """Get session by ID"""
        session = self.repo.get_session_by_id(session_id)
        if not session:
            return None
        return self._to_session_dto(session)

    async def pause_session(self, session_id: str) -> LearningSession | None:
        """Pause a session"""
        session = self.repo.update_session_status(session_id, SessionStatus.PAUSED)
        if not session:
            return None
        return self._to_session_dto(session)

    async def update_progress(self, request: UpdateProgressRequest) -> SessionProgress:
        """Update session progress - simplified implementation"""
        # Get session to validate it exists and is active
        session = self.repo.get_session_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")

        if session.status not in [SessionStatus.ACTIVE.value, SessionStatus.PAUSED.value]:
            raise ValueError(f"Cannot update progress for {session.status} session")

        # Update session progress (simplified - just increment component index)
        new_index = session.current_component_index + 1
        progress_percentage = (new_index / session.total_components * 100) if session.total_components > 0 else 0

        self.repo.update_session_progress(
            session_id=request.session_id,
            current_component_index=new_index,
            progress_percentage=min(progress_percentage, 100),
        )

        # Return mock progress response (matches frontend expectations)
        return SessionProgress(
            session_id=request.session_id,
            component_id=request.component_id,
            component_type="unknown",
            started_at=datetime.utcnow().isoformat(),
            completed_at=datetime.utcnow().isoformat(),
            is_correct=request.is_correct,
            user_answer=request.user_answer,
            time_spent_seconds=request.time_spent_seconds,
            attempts=1,
        )

    async def complete_session(self, request: CompleteSessionRequest) -> SessionResults:
        """Complete a session and calculate results"""
        session = self.repo.get_session_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")

        if session.status == SessionStatus.COMPLETED.value:
            # Already completed, return existing results
            return self._calculate_session_results(session)

        # Mark session as completed
        completed_session = self.repo.update_session_status(
            request.session_id,
            SessionStatus.COMPLETED,
            completed_at=datetime.utcnow(),
        )

        if not completed_session:
            raise ValueError("Failed to complete session")

        return self._calculate_session_results(completed_session)

    async def get_user_sessions(
        self,
        user_id: str | None = None,
        status: str | None = None,
        topic_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionListResponse:
        """Get user sessions with filtering"""
        sessions, total = self.repo.get_user_sessions(
            user_id=user_id,
            status=status,
            topic_id=topic_id,
            limit=limit,
            offset=offset,
        )

        session_dtos = [self._to_session_dto(session) for session in sessions]
        return SessionListResponse(sessions=session_dtos, total=total)

    async def check_health(self) -> bool:
        """Health check for the learning session service"""
        return self.repo.health_check()

    # ================================
    # Private Helper Methods
    # ================================

    def _to_session_dto(self, session: LearningSessionModel) -> LearningSession:
        """Convert session model to DTO"""
        return LearningSession(
            id=session.id,
            topic_id=session.topic_id,
            user_id=session.user_id,
            status=session.status,
            started_at=session.started_at.isoformat(),
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
            current_component_index=session.current_component_index,
            total_components=session.total_components,
            progress_percentage=session.progress_percentage,
            session_data=session.session_data or {},
        )

    def _calculate_session_results(self, session: LearningSessionModel) -> SessionResults:
        """Calculate session results - simplified implementation"""
        # Mock results that match frontend expectations
        return SessionResults(
            session_id=session.id,
            topic_id=session.topic_id,
            total_components=session.total_components,
            completed_components=session.current_component_index,
            correct_answers=max(0, session.current_component_index - 1),  # Mock: assume most are correct
            total_time_seconds=300,  # Mock: 5 minutes
            completion_percentage=session.progress_percentage,
            score_percentage=80.0,  # Mock score
            achievements=["Session Complete"],  # Mock achievement
        )
