"""
Learning Session Module - Service Layer

Minimal business logic to support existing frontend functionality.
This is a migration, not new feature development.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..content.public import ContentProvider
from ..lesson_catalog.public import LessonCatalogProvider
from .models import LearningSessionModel, SessionStatus
from .repo import LearningSessionRepo

# ================================
# Service DTOs (matching frontend expectations)
# ================================


@dataclass
class LearningSession:
    """Learning session DTO - matches frontend ApiLearningSession"""

    id: str
    lesson_id: str
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
    lesson_id: str
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

    lesson_id: str
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
        lesson_catalog_provider: LessonCatalogProvider,
    ):
        self.repo = repo
        self.content = content_provider
        self.lesson_catalog = lesson_catalog_provider

    async def start_session(self, request: StartSessionRequest) -> LearningSession:
        """Start a new learning session"""
        # Validate lesson exists
        lesson_detail = self.lesson_catalog.get_lesson_details(request.lesson_id)
        if not lesson_detail:
            raise ValueError(f"Lesson {request.lesson_id} not found")

        # Check for existing active session (if user provided)
        if request.user_id:
            existing_session = self.repo.get_active_session_for_user_and_lesson(request.user_id, request.lesson_id)
            if existing_session:
                # Return existing session instead of creating new one
                return self._to_session_dto(existing_session)

        # Get lesson content to determine component count
        lesson_content = self.content.get_lesson(request.lesson_id)
        if lesson_content:
            # Calculate total components from package structure
            # 1 didactic snippet + exercises + glossary terms
            total_components = 1 + len(lesson_content.package.exercises) + len(lesson_content.package.glossary.get("terms", []))
        else:
            total_components = 0

        # Create new session
        session = self.repo.create_session(
            lesson_id=request.lesson_id,
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
        """Update session progress and store component results"""
        # Get session to validate it exists and is active
        session = self.repo.get_session_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")

        if session.status not in [SessionStatus.ACTIVE.value, SessionStatus.PAUSED.value]:
            raise ValueError(f"Cannot update progress for {session.status} session")

        # Update session data with component results
        session_data = session.session_data or {}
        component_results = session_data.get("component_results", {})

        # Store this component's result
        component_results[request.component_id] = {
            "is_correct": request.is_correct,
            "user_answer": request.user_answer,
            "time_spent_seconds": request.time_spent_seconds,
            "completed_at": datetime.utcnow().isoformat(),
        }

        session_data["component_results"] = component_results
        session_data["total_time_seconds"] = session_data.get("total_time_seconds", 0) + request.time_spent_seconds

        # Update session progress
        new_index = session.current_component_index + 1
        progress_percentage = (new_index / session.total_components * 100) if session.total_components > 0 else 0

        # Update both progress and session data
        self.repo.update_session_progress(
            session_id=request.session_id,
            current_component_index=new_index,
            progress_percentage=min(progress_percentage, 100),
            session_data=session_data,
        )

        # Return progress response
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
        lesson_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionListResponse:
        """Get user sessions with filtering"""
        sessions, total = self.repo.get_user_sessions(
            user_id=user_id,
            status=status,
            lesson_id=lesson_id,
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
            lesson_id=session.lesson_id,
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
        """Calculate session results based on actual performance"""

        # Extract MCQ results from session data
        session_data = session.session_data or {}
        component_results = session_data.get("component_results", {})

        # Count MCQ questions and correct answers
        mcq_total = 0
        mcq_correct = 0

        for component_id, result in component_results.items():
            # Check if this is an MCQ component (component_id starts with 'mcq_')
            if component_id.startswith("mcq_") and isinstance(result, dict):
                mcq_total += 1
                if result.get("is_correct", False):
                    mcq_correct += 1

        # Calculate score percentage based only on MCQ questions
        score_percentage = (mcq_correct / mcq_total * 100) if mcq_total > 0 else 0.0

        # Calculate completion percentage based on all components
        completion_percentage = (session.current_component_index / session.total_components * 100) if session.total_components > 0 else 0.0

        # Determine achievements based on performance
        achievements = []
        if completion_percentage >= 100:
            achievements.append("Session Complete")
        if score_percentage >= 90:
            achievements.append("Perfect Score")
        elif score_percentage >= 80:
            achievements.append("Great Job")
        elif score_percentage >= 70:
            achievements.append("Well Done")

        return SessionResults(
            session_id=session.id,
            lesson_id=session.lesson_id,
            total_components=session.total_components,
            completed_components=session.current_component_index,
            correct_answers=mcq_correct,  # Only count MCQ correct answers
            total_time_seconds=session_data.get("total_time_seconds", 300),  # Use actual time or default
            completion_percentage=completion_percentage,
            score_percentage=score_percentage,  # Based only on MCQ performance
            achievements=achievements,
        )
