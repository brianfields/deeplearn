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
    exercise_type: str  # "mcq", "short_answer", "coding" (only actual exercises)
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
    current_exercise_index: int  # Index within exercises array only
    total_exercises: int
    exercises_completed: int
    exercises_correct: int
    progress_percentage: float
    exercise_answers: dict[str, Any]  # exercise_id -> answer details
    exercise_id: str  # The exercise that was just updated
    exercise_type: str
    time_spent_seconds: int
    attempts: int
    started_at: str
    completed_at: str | None
    is_correct: bool | None
    user_answer: Any | None


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
class UnitLessonProgress:
    """Per-lesson progress within a unit for a user."""

    lesson_id: str
    total_exercises: int
    completed_exercises: int
    correct_exercises: int
    progress_percentage: float
    last_activity_at: str | None


@dataclass
class UnitProgress:
    """Aggregated unit progress for a user across lessons."""

    unit_id: str
    total_lessons: int
    lessons_completed: int
    progress_percentage: float
    lessons: list[UnitLessonProgress]


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
    exercise_type: str  # "mcq", "short_answer", "coding" (only actual exercises)
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
    ) -> None:
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

        # If user and unit context exist, ensure a unit session is created
        try:
            if request.user_id:
                # Determine unit for this lesson using the lesson_content we already fetched
                unit_id = getattr(lesson_content, "unit_id", None) if lesson_content else None
                if unit_id:
                    # Ensure unit session exists
                    self.content.get_or_create_unit_session(user_id=request.user_id, unit_id=unit_id)
        except Exception as _e:
            # Non-fatal; proceed even if unit session cannot be created
            pass

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
        existing = exercise_answers.get(request.exercise_id, {})
        exercise_answers[request.exercise_id] = {
            "exercise_type": request.exercise_type,
            "is_correct": request.is_correct,
            "user_answer": request.user_answer,
            "time_spent_seconds": request.time_spent_seconds,
            "completed_at": datetime.utcnow().isoformat(),
            "attempts": existing.get("attempts", 0) + 1,
            "started_at": existing.get("started_at", datetime.utcnow().isoformat()),
        }

        session_data["exercise_answers"] = exercise_answers
        session_data["total_time_seconds"] = session_data.get("total_time_seconds", 0) + request.time_spent_seconds

        # Validate exercise type
        valid_exercise_types = ["mcq", "short_answer", "coding"]
        if request.exercise_type not in valid_exercise_types:
            raise ValueError(f"Invalid exercise type: {request.exercise_type}. Must be one of {valid_exercise_types}")

        # Update session progress based on exercise type
        updates: dict[str, Any] = {}
        if request.exercise_type in valid_exercise_types:
            # Update exercise progress
            exercise_not_completed = request.exercise_id not in [k for k, v in exercise_answers.items() if v.get("completed_at") and k != request.exercise_id]
            if exercise_not_completed:
                updates["exercises_completed"] = (session.exercises_completed or 0) + 1
                if request.is_correct:
                    updates["exercises_correct"] = (session.exercises_correct or 0) + 1

            # Move to next exercise (advance from current position)
            current_index = session.current_exercise_index or 0
            updates["current_exercise_index"] = current_index + 1

        # Calculate overall progress percentage
        # Progress is based solely on actual exercises completed vs total exercises
        total_exercises = session.total_exercises or 0
        completed_exercises = updates.get("exercises_completed", session.exercises_completed or 0)
        progress_percentage = (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0

        updates["progress_percentage"] = int(min(progress_percentage, 100))
        updates["session_data"] = session_data

        # Update session in database
        self.repo.update_session_progress(session_id=request.session_id, **updates)

        # Return session progress response
        return SessionProgress(
            session_id=request.session_id,
            lesson_id=session.lesson_id,
            current_exercise_index=updates.get("current_exercise_index", session.current_exercise_index or 0),
            total_exercises=session.total_exercises or 0,
            exercises_completed=updates.get("exercises_completed", session.exercises_completed or 0),
            exercises_correct=updates.get("exercises_correct", session.exercises_correct or 0),
            progress_percentage=updates["progress_percentage"],
            exercise_answers=exercise_answers,
            exercise_id=request.exercise_id,
            exercise_type=request.exercise_type,
            time_spent_seconds=request.time_spent_seconds,
            attempts=exercise_answers[request.exercise_id]["attempts"],
            started_at=exercise_answers[request.exercise_id]["started_at"],
            completed_at=exercise_answers[request.exercise_id]["completed_at"],
            is_correct=request.is_correct,
            user_answer=request.user_answer,
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

        results = self._calculate_session_results(completed_session)

        # Update unit session progress if user and unit context available
        try:
            if completed_session.user_id:
                # Fetch lesson and unit to update unit session state
                lesson = self.content.get_lesson(completed_session.lesson_id)
                unit_id = getattr(lesson, "unit_id", None) if lesson else None
                if unit_id:
                    # Determine total lessons in unit for percentage calculation
                    lessons_in_unit = self.content.get_lessons_by_unit(unit_id)
                    total_lessons = len(lessons_in_unit)
                    # Compute if completing this lesson finishes the unit
                    try:
                        us = self.content.get_or_create_unit_session(user_id=completed_session.user_id, unit_id=unit_id)
                        already_completed = set(us.completed_lesson_ids or [])
                    except Exception:
                        already_completed = set()
                    will_be_completed = len(already_completed | {completed_session.lesson_id}) >= total_lessons and total_lessons > 0

                    self.content.update_unit_session_progress(
                        user_id=completed_session.user_id,
                        unit_id=unit_id,
                        completed_lesson_id=completed_session.lesson_id,
                        total_lessons=total_lessons,
                        mark_completed=will_be_completed,
                    )
        except Exception as _e:
            # Non-fatal; unit session updates should not break session completion
            pass

        return results

    async def get_unit_progress(self, user_id: str, unit_id: str) -> UnitProgress:
        """Get unit progress primarily from persistent unit session, fallback to aggregation."""
        # Try persistent unit session
        unit = self.lesson_catalog.get_unit_details(unit_id)
        lessons = self.content.get_lessons_by_unit(unit_id)
        total_lessons = len(lessons)

        # Fallback aggregation list for lesson-level stats
        lesson_progress_list: list[UnitLessonProgress] = []
        lessons_completed = 0

        # Build lesson-level details from latest sessions
        for lesson in lessons:
            sessions, _ = self.repo.get_user_sessions(user_id=user_id, lesson_id=lesson.id, limit=1, offset=0)
            if sessions:
                s = sessions[0]
                total_exercises = len(lesson.package.exercises)
                completed_exercises = s.exercises_completed or 0
                correct_exercises = s.exercises_correct or 0
                progress_percentage = min(
                    (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0.0,
                    100.0,
                )
                last_activity_at = (s.completed_at or s.started_at).isoformat() if (s.completed_at or s.started_at) else None
                if progress_percentage >= 100.0:
                    lessons_completed += 1
            else:
                total_exercises = len(lesson.package.exercises)
                completed_exercises = 0
                correct_exercises = 0
                progress_percentage = 0.0
                last_activity_at = None

            lesson_progress_list.append(
                UnitLessonProgress(
                    lesson_id=lesson.id,
                    total_exercises=total_exercises,
                    completed_exercises=completed_exercises,
                    correct_exercises=correct_exercises,
                    progress_percentage=progress_percentage,
                    last_activity_at=last_activity_at,
                )
            )

        # Try persistent session
        try:
            us = self.content.get_or_create_unit_session(user_id=user_id, unit_id=unit_id)
            avg_progress = us.progress_percentage if us else sum(lp.progress_percentage for lp in lesson_progress_list) / total_lessons if total_lessons > 0 else 0.0
        except Exception:
            avg_progress = sum(lp.progress_percentage for lp in lesson_progress_list) / total_lessons if total_lessons > 0 else 0.0

        return UnitProgress(
            unit_id=unit_id,
            total_lessons=total_lessons,
            lessons_completed=lessons_completed,
            progress_percentage=avg_progress,
            lessons=lesson_progress_list,
        )

    def _unit_all_lessons_completed(self, user_id: str, unit_id: str, total_lessons: int) -> bool:
        """Check if all lessons in a unit are completed for a user based on unit session."""
        try:
            us = self.content.get_or_create_unit_session(user_id=user_id, unit_id=unit_id)
            return len(us.completed_lesson_ids or []) >= total_lessons and total_lessons > 0
        except Exception:
            return False

    async def get_next_lesson_to_resume(self, user_id: str, unit_id: str) -> str | None:
        """Return next incomplete lesson id within a unit for resuming learning."""
        unit_detail = self.lesson_catalog.get_unit_details(unit_id)
        if not unit_detail:
            return None
        try:
            us = self.content.get_or_create_unit_session(user_id=user_id, unit_id=unit_id)
            completed = set(us.completed_lesson_ids or [])
        except Exception:
            completed = set()

        # Prefer configured order
        for lid in list(unit_detail.lesson_order or []):
            if lid not in completed:
                return lid
        # Fallback to first lesson not completed
        for lesson in unit_detail.lessons:
            if lesson.id not in completed:
                return lesson.id
        return None

    async def get_units_progress_overview(self, user_id: str, limit: int = 100, offset: int = 0) -> list[UnitProgress]:
        """Get progress overview for multiple units using the catalog's unit browsing."""
        units = self.lesson_catalog.browse_units(limit=limit, offset=offset)
        results: list[UnitProgress] = []
        for u in units:
            results.append(await self.get_unit_progress(user_id=user_id, unit_id=u.id))
        return results

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
            started_at=session.started_at.isoformat() if session.started_at else "",
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
            current_exercise_index=session.current_exercise_index,
            total_exercises=session.total_exercises,
            progress_percentage=session.progress_percentage,
            session_data=session.session_data or {},
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

        # Calculate completion percentage based solely on exercises
        completion_percentage = (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0.0

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
            total_exercises=total_exercises,
            completed_exercises=completed_exercises,
            correct_exercises=correct_exercises,
            total_time_seconds=session_data.get("total_time_seconds", 0),
            completion_percentage=completion_percentage,
            score_percentage=score_percentage,
            achievements=achievements,
        )
