"""
Learning Session Module - Service Layer

Minimal business logic to support existing frontend functionality.
This is a migration, not new feature development.
"""

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from ..content.public import ContentProvider
from ..lesson_catalog.public import LessonCatalogProvider
from .models import LearningSessionModel, SessionStatus
from .repo import LearningSessionRepo

logger = logging.getLogger(__name__)

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
    current_exercise_index: int
    total_exercises: int
    progress_percentage: float
    session_data: dict[str, Any]


@dataclass
class ExerciseProgress:
    """Exercise progress DTO - tracks individual exercise completion"""

    session_id: str
    exercise_id: str
    exercise_type: str  # "mcq", "short_answer", etc.
    started_at: str
    completed_at: str | None
    is_correct: bool | None
    user_answer: Any | None
    time_spent_seconds: int
    attempts: int


@dataclass
class SessionProgress:
    """Overall session progress DTO - matches frontend expectations"""

    session_id: str
    lesson_id: str
    current_exercise_index: int  # 0 = show didactic, 1+ = show exercise N-1
    total_exercises: int
    exercises_completed: int
    exercises_correct: int
    progress_percentage: float
    exercise_answers: dict[str, Any]  # exercise_id -> answer details


@dataclass
class SessionResults:
    """Session results DTO - matches frontend ApiSessionResults"""

    session_id: str
    lesson_id: str
    total_exercises: int
    completed_exercises: int
    correct_exercises: int
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
    """Request DTO for updating exercise progress"""

    session_id: str
    exercise_id: str  # Changed from component_id
    exercise_type: str  # "didactic_snippet" or "mcq", etc.
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

        # Get lesson content to determine exercise count
        lesson_content = self.content.get_lesson(request.lesson_id)
        total_exercises = len(lesson_content.package.exercises) if lesson_content else 0

        # Create new session
        session = self.repo.create_session(
            lesson_id=request.lesson_id,
            user_id=request.user_id,
            total_exercises=total_exercises,
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

    async def update_progress(self, request: UpdateProgressRequest) -> ExerciseProgress:
        """Update session progress and store exercise results"""
        # Get session to validate it exists and is active
        session = self.repo.get_session_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")

        if session.status not in [SessionStatus.ACTIVE.value, SessionStatus.PAUSED.value]:
            raise ValueError(f"Cannot update progress for {session.status} session")

        # Update session data with exercise results
        session_data = session.session_data or {}
        exercise_answers = session_data.get("exercise_answers", {})

        # Store this exercise's result
        exercise_answers[request.exercise_id] = {
            "exercise_type": request.exercise_type,
            "is_correct": request.is_correct,
            "user_answer": request.user_answer,
            "time_spent_seconds": request.time_spent_seconds,
            "completed_at": datetime.utcnow().isoformat(),
            "attempts": exercise_answers.get(request.exercise_id, {}).get("attempts", 0) + 1,
        }

        session_data["exercise_answers"] = exercise_answers  # type: ignore
        session_data["total_time_seconds"] = session_data.get("total_time_seconds", 0) + request.time_spent_seconds  # type: ignore

        # Update session progress based on exercise type
        updates = {}
        if request.exercise_type == "didactic_snippet":
            # Move to first exercise after completing didactic
            updates["current_exercise_index"] = 1
        elif request.exercise_type in ["mcq", "short_answer", "coding"]:
            # Update exercise progress
            exercise_not_completed = request.exercise_id not in [k for k, v in exercise_answers.items() if v.get("completed_at") and k != request.exercise_id]
            if exercise_not_completed:
                updates["exercises_completed"] = (session.exercises_completed or 0) + 1
                if request.is_correct:
                    updates["exercises_correct"] = (session.exercises_correct or 0) + 1
                # Move to next exercise
                updates["current_exercise_index"] = (session.current_exercise_index or 0) + 1

        # Calculate overall progress percentage
        # Progress is based on: didactic viewed (if current_exercise_index > 0) + exercises completed
        didactic_viewed = 1 if (session.current_exercise_index or 0) > 0 or updates.get("current_exercise_index", 0) > 0 else 0
        total_items = 1 + (session.total_exercises or 0)  # 1 didactic + N exercises
        completed_items = didactic_viewed + updates.get("exercises_completed", session.exercises_completed or 0)
        progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0

        updates["progress_percentage"] = min(progress_percentage, 100)
        updates["session_data"] = session_data

        # Update session in database
        self.repo.update_session_progress(session_id=request.session_id, **updates)

        # Return exercise progress response
        return ExerciseProgress(
            session_id=request.session_id,
            exercise_id=request.exercise_id,
            exercise_type=request.exercise_type,
            started_at=datetime.utcnow().isoformat(),
            completed_at=datetime.utcnow().isoformat(),
            is_correct=request.is_correct,
            user_answer=request.user_answer,
            time_spent_seconds=request.time_spent_seconds,
            attempts=exercise_answers[request.exercise_id]["attempts"],
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
            id=session.id,  # type: ignore
            lesson_id=session.lesson_id,  # type: ignore
            user_id=session.user_id,  # type: ignore
            status=session.status,  # type: ignore
            started_at=session.started_at.isoformat() if session.started_at else "",
            completed_at=session.completed_at.isoformat() if session.completed_at else None,  # type: ignore
            current_exercise_index=session.current_exercise_index,  # type: ignore
            total_exercises=1 + session.total_exercises,  # type: ignore
            progress_percentage=session.progress_percentage,  # type: ignore
            session_data=session.session_data or {},  # type: ignore
        )

    def _calculate_session_results(self, session: LearningSessionModel) -> SessionResults:
        """Calculate session results based on actual performance"""

        # Extract exercise results from session data
        session_data = session.session_data or {}
        exercise_answers = session_data.get("exercise_answers", {})

        # Count exercises and correct answers from session fields
        total_exercises = session.total_exercises or 0
        completed_exercises = session.exercises_completed or 0
        correct_exercises = session.exercises_correct or 0

        # Debug logging
        logger.info(f"Calculating results for session {session.id}")
        logger.info(f"Exercise answers: {exercise_answers}")
        logger.info(f"Session stats: {completed_exercises}/{total_exercises} completed, {correct_exercises} correct")

        # Calculate score percentage based on exercises
        score_percentage = (correct_exercises / total_exercises * 100) if total_exercises > 0 else 0.0
        logger.info(f"Final calculation: {correct_exercises}/{total_exercises} = {score_percentage}%")

        # Calculate completion percentage (didactic + exercises)
        # Didactic is considered "completed" if current_exercise_index > 0
        didactic_viewed = 1 if (session.current_exercise_index or 0) > 0 else 0
        total_items = 1 + total_exercises  # 1 didactic + N exercises
        completed_items = didactic_viewed + completed_exercises
        completion_percentage = (completed_items / total_items * 100) if total_items > 0 else 0.0

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
            session_id=session.id,  # type: ignore
            lesson_id=session.lesson_id,  # type: ignore
            total_exercises=total_exercises,  # type: ignore
            completed_exercises=completed_exercises,  # type: ignore
            correct_exercises=correct_exercises,  # type: ignore
            total_time_seconds=session_data.get("total_time_seconds", 0),
            completion_percentage=completion_percentage,  # type: ignore
            score_percentage=score_percentage,  # type: ignore
            achievements=achievements,
        )
