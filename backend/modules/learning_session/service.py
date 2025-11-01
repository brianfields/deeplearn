"""
Learning Session Module - Service Layer

Minimal business logic to support existing frontend functionality.
This is a migration, not new feature development.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from modules.content.public import ContentProvider
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
    unit_id: str
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
    attempt_history: list[dict[str, Any]]
    has_been_answered_correctly: bool


@dataclass
class SessionResults:
    """Session results DTO - matches frontend ApiSessionResults"""

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


class LearningObjectiveStatus(str, Enum):
    """Lifecycle state for a learning objective."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    NOT_STARTED = "not_started"


@dataclass
class LearningObjectiveProgressItem:
    """Progress summary for a single learning objective."""

    lo_id: str
    title: str
    description: str
    exercises_total: int
    exercises_attempted: int
    exercises_correct: int
    status: LearningObjectiveStatus


@dataclass
class UnitLearningObjectiveProgress:
    """Aggregated learning objective progress for a unit."""

    unit_id: str
    items: list[LearningObjectiveProgressItem]


@dataclass
class StartSessionRequest:
    """Request DTO for starting a session"""

    lesson_id: str
    user_id: str
    unit_id: str
    session_id: str | None = None


@dataclass
class UpdateProgressRequest:
    """Request DTO for updating exercise progress"""

    session_id: str
    exercise_id: str  # Changed from component_id
    exercise_type: str  # "mcq", "short_answer", "coding" (only actual exercises)
    user_answer: Any | None = None
    is_correct: bool | None = None
    time_spent_seconds: int = 0
    user_id: str | None = None


@dataclass
class ExerciseProgressUpdate:
    """Individual exercise progress for batch updates"""

    exercise_id: str
    exercise_type: str
    user_answer: Any | None
    is_correct: bool | None
    time_spent_seconds: int


@dataclass
class CompleteSessionRequest:
    """Request DTO for completing a session"""

    session_id: str
    user_id: str | None = None
    progress_updates: list[ExerciseProgressUpdate] | None = None
    lesson_id: str | None = None  # Optional, for creating session if not exists


@dataclass
class SessionListResponse:
    """Response DTO for session list"""

    sessions: list[LearningSession]
    total: int


@dataclass(slots=True)
class AssistantSessionContext:
    """Aggregated learning session context for the teaching assistant."""

    session: LearningSession
    exercise_attempt_history: list[dict[str, Any]]
    lesson: dict[str, Any] | None
    unit: dict[str, Any] | None
    unit_session: dict[str, Any] | None = None
    unit_resources: list[dict[str, Any]] = field(default_factory=list)


# ================================
# Service Implementation
# ================================


class LearningSessionService:
    """Service for learning session business logic"""

    def __init__(
        self,
        repo: LearningSessionRepo,
        content_provider: "ContentProvider",
    ) -> None:
        self.repo = repo
        self.content = content_provider
        self.catalog = None

    async def start_session(self, request: StartSessionRequest) -> LearningSession:
        """Start a new learning session"""
        if not request.user_id:
            raise ValueError("User identifier is required to start a session")
        if not request.unit_id:
            raise ValueError("Unit identifier is required to start a session")

        # If client provided a session_id, check if it already exists (idempotency)
        if request.session_id:
            existing_session = await self.repo.get_session_by_id(request.session_id)
            if existing_session:
                if existing_session.unit_id != request.unit_id:
                    raise ValueError("Existing session belongs to a different unit")
                logger.info(f"Session {request.session_id} already exists, returning it (idempotent)")
                existing_session = await self._ensure_session_user(existing_session, request.user_id)
                return self._to_session_dto(existing_session)

        # Validate lesson exists
        lesson_content = await self.content.get_lesson(request.lesson_id)
        if not lesson_content:
            raise ValueError(f"Lesson {request.lesson_id} not found")

        lesson_unit_id = getattr(lesson_content, "unit_id", None)
        if not lesson_unit_id:
            raise ValueError(f"Lesson {request.lesson_id} is missing unit context")
        if lesson_unit_id != request.unit_id:
            raise ValueError("Lesson does not belong to the provided unit")

        # Check for existing active session for this user/lesson combo (if no session_id provided)
        if not request.session_id:
            existing_session = await self.repo.get_active_session_for_user_and_lesson(request.user_id, request.lesson_id)
            if existing_session:
                if existing_session.unit_id != request.unit_id:
                    raise ValueError("Existing session belongs to a different unit")
                # Ensure the session is bound to the requesting user (for legacy records)
                existing_session = await self._ensure_session_user(existing_session, request.user_id)
                return self._to_session_dto(existing_session)

        total_exercises = len(lesson_content.package.exercises) if lesson_content else 0

        # Create new session (use client-provided ID if available for offline-first support)
        session = await self.repo.create_session(
            lesson_id=request.lesson_id,
            unit_id=request.unit_id,
            user_id=request.user_id,
            total_exercises=total_exercises,
            session_id=request.session_id,
        )

        # If user and unit context exist, ensure a unit session is created
        try:
            # Determine unit for this lesson using the lesson_content we already fetched
            await self.content.get_or_create_unit_session(user_id=request.user_id, unit_id=request.unit_id)
        except Exception as e:
            logger.warning(f"Failed to create unit session: {e}")
            # Non-fatal; proceed even if unit session cannot be created
            pass

        return self._to_session_dto(session)

    async def get_session(self, session_id: str, user_id: str | None = None) -> LearningSession | None:
        """Get session by ID"""
        session = await self.repo.get_session_by_id(session_id)
        if not session:
            return None
        session = await self._ensure_session_user(session, user_id)
        return self._to_session_dto(session)

    async def pause_session(self, session_id: str, user_id: str | None = None) -> LearningSession | None:
        """Pause a session"""
        session = await self.repo.update_session_status(session_id, SessionStatus.PAUSED)
        if not session:
            return None
        session = await self._ensure_session_user(session, user_id)
        return self._to_session_dto(session)

    async def update_progress(self, request: UpdateProgressRequest) -> SessionProgress:
        """Update session progress and store exercise results"""
        # Get session to validate it exists and is active
        session = await self.repo.get_session_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session {request.session_id} not found")

        session = await self._ensure_session_user(session, request.user_id)

        if session.status not in [SessionStatus.ACTIVE.value, SessionStatus.PAUSED.value]:
            raise ValueError(f"Cannot update progress for {session.status} session")

        # Update session data with exercise results
        session_data = session.session_data or {}
        exercise_answers = session_data.get("exercise_answers", {})

        # Store this exercise's result
        existing = exercise_answers.get(request.exercise_id, {})
        attempt_timestamp = datetime.utcnow().isoformat()
        history: list[dict[str, Any]] = list(existing.get("attempt_history", []))
        attempt_record = {
            "attempt_number": len(history) + 1,
            "is_correct": request.is_correct,
            "user_answer": request.user_answer,
            "time_spent_seconds": request.time_spent_seconds,
            "submitted_at": attempt_timestamp,
        }
        history.append(attempt_record)

        has_been_answered_correctly = bool(existing.get("has_been_answered_correctly")) or bool(request.is_correct)
        started_at = existing.get("started_at") or attempt_timestamp
        exercise_answers[request.exercise_id] = {
            "exercise_type": request.exercise_type,
            "is_correct": request.is_correct,
            "user_answer": request.user_answer,
            "time_spent_seconds": request.time_spent_seconds,
            "completed_at": attempt_timestamp,
            "attempts": len(history),
            "started_at": started_at,
            "attempt_history": history,
            "has_been_answered_correctly": has_been_answered_correctly,
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
            previously_completed = bool(existing.get("completed_at"))
            if not previously_completed:
                updates["exercises_completed"] = (session.exercises_completed or 0) + 1

            previously_correct = bool(existing.get("has_been_answered_correctly") or existing.get("is_correct"))
            now_correct = bool(request.is_correct)
            if now_correct and not previously_correct:
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
        await self.repo.update_session_progress(session_id=request.session_id, **updates)

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
            attempt_history=exercise_answers[request.exercise_id]["attempt_history"],
            has_been_answered_correctly=exercise_answers[request.exercise_id]["has_been_answered_correctly"],
        )

    async def complete_session(self, request: CompleteSessionRequest) -> SessionResults:
        """Complete a session and calculate results"""
        session = await self.repo.get_session_by_id(request.session_id)

        # If session doesn't exist and we have lesson_id, create it (handles outbox out-of-order processing)
        if not session and request.lesson_id and request.user_id:
            logger.info(f"Session {request.session_id} not found, creating it for lesson {request.lesson_id}")
            # Validate lesson exists
            lesson_content = await self.content.get_lesson(request.lesson_id)
            if not lesson_content:
                raise ValueError(f"Lesson {request.lesson_id} not found")

            total_exercises = len(lesson_content.package.exercises) if lesson_content else 0
            lesson_unit_id = getattr(lesson_content, "unit_id", None)
            if not lesson_unit_id:
                raise ValueError(f"Lesson {request.lesson_id} is missing unit context")

            # Create the session with the client-provided ID
            session = await self.repo.create_session(
                lesson_id=request.lesson_id,
                unit_id=lesson_unit_id,
                user_id=request.user_id,
                total_exercises=total_exercises,
                session_id=request.session_id,
            )
        elif not session:
            raise ValueError(f"Session {request.session_id} not found and no lesson_id provided")

        session = await self._ensure_session_user(session, request.user_id)

        # Apply any pending progress updates before completing
        if request.progress_updates:
            logger.info(f"Applying {len(request.progress_updates)} progress updates before completion")
            for progress_update in request.progress_updates:
                update_request = UpdateProgressRequest(
                    session_id=request.session_id,
                    exercise_id=progress_update.exercise_id,
                    exercise_type=progress_update.exercise_type,
                    user_answer=progress_update.user_answer,
                    is_correct=progress_update.is_correct,
                    time_spent_seconds=progress_update.time_spent_seconds,
                    user_id=request.user_id,
                )
                await self.update_progress(update_request)

            # Re-fetch session after updates
            session = await self.repo.get_session_by_id(request.session_id)
            if not session:
                raise ValueError("Session not found after progress updates")

        if session.status == SessionStatus.COMPLETED.value:
            # Already completed, return existing results
            return self._calculate_session_results(session)

        # Mark session as completed
        completed_session = await self.repo.update_session_status(
            request.session_id,
            SessionStatus.COMPLETED,
            completed_at=datetime.utcnow(),
        )

        if not completed_session:
            raise ValueError("Failed to complete session")

        completed_session = await self._ensure_session_user(completed_session, request.user_id)

        results = self._calculate_session_results(completed_session)

        # Update unit session progress if user and unit context available
        try:
            if completed_session.user_id:
                # Fetch lesson and unit to update unit session state
                lesson = await self.content.get_lesson(completed_session.lesson_id)
                unit_id = getattr(lesson, "unit_id", None) if lesson else None
                if unit_id:
                    # Determine total lessons in unit for percentage calculation
                    lessons_in_unit = await self.content.get_lessons_by_unit(unit_id)
                    total_lessons = len(lessons_in_unit)
                    # Compute if completing this lesson finishes the unit
                    try:
                        us = await self.content.get_or_create_unit_session(user_id=completed_session.user_id, unit_id=unit_id)
                        already_completed = set(us.completed_lesson_ids or [])
                    except Exception:
                        already_completed = set()
                    will_be_completed = len(already_completed | {completed_session.lesson_id}) >= total_lessons > 0

                    await self.content.update_unit_session_progress(
                        user_id=completed_session.user_id,
                        unit_id=unit_id,
                        completed_lesson_id=completed_session.lesson_id,
                        total_lessons=total_lessons,
                        mark_completed=will_be_completed,
                    )
        except Exception as e:
            logger.warning(f"Failed to update unit session: {e}")
            # Non-fatal; unit session updates should not break session completion
            pass

        return results

    async def get_unit_progress(self, user_id: str, unit_id: str) -> UnitProgress:
        """Get unit progress primarily from persistent unit session, fallback to aggregation."""
        # Try persistent unit session
        lessons = await self.content.get_lessons_by_unit(unit_id)
        total_lessons = len(lessons)

        # Fallback aggregation list for lesson-level stats
        lesson_progress_list: list[UnitLessonProgress] = []
        lessons_completed = 0

        # Build lesson-level details from latest sessions
        for lesson in lessons:
            sessions, _ = await self.repo.get_user_sessions(user_id=user_id, lesson_id=lesson.id, limit=1, offset=0)
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
            us = await self.content.get_or_create_unit_session(user_id=user_id, unit_id=unit_id)
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

    async def get_unit_lo_progress(self, user_id: str, unit_id: str) -> UnitLearningObjectiveProgress:
        """Aggregate learning objective progress for a user within a unit."""

        if not user_id:
            raise ValueError("User identifier is required to compute learning objective progress")

        unit = await self.content.get_unit(unit_id)
        if not unit:
            raise ValueError(f"Unit {unit_id} not found")

        objective_order, objective_lookup = self._normalize_unit_objectives(getattr(unit, "learning_objectives", None))

        lessons = await self.content.get_lessons_by_unit(unit_id)
        exercise_to_objective: dict[str, str] = {}
        totals_by_objective: defaultdict[str, int] = defaultdict(int)

        for lesson in lessons:
            package = getattr(lesson, "package", None)
            if not package:
                continue
            for exercise in getattr(package, "exercises", []) or []:
                lo_id = getattr(exercise, "lo_id", None)
                if not lo_id:
                    continue
                exercise_to_objective[exercise.id] = lo_id
                totals_by_objective[lo_id] += 1

        sessions = await self.repo.get_sessions_for_user_and_lessons(user_id, [lesson.id for lesson in lessons])
        attempted_exercises: set[str] = set()
        correct_exercises: set[str] = set()

        for session in sessions:
            answers = (session.session_data or {}).get("exercise_answers", {}) or {}
            for exercise_id, answer_data in answers.items():
                if exercise_id not in exercise_to_objective:
                    continue
                attempted_exercises.add(exercise_id)

                attempt_history = answer_data.get("attempt_history") or []
                last_attempt_correct = False
                if attempt_history:
                    last_attempt = attempt_history[-1]
                    last_attempt_correct = bool(last_attempt.get("is_correct"))
                else:
                    last_attempt_correct = bool(answer_data.get("has_been_answered_correctly") or answer_data.get("is_correct"))

                if last_attempt_correct:
                    correct_exercises.add(exercise_id)

        attempted_counts: defaultdict[str, int] = defaultdict(int)
        for exercise_id in attempted_exercises:
            lo_id = exercise_to_objective.get(exercise_id)
            if lo_id:
                attempted_counts[lo_id] += 1

        correct_counts: defaultdict[str, int] = defaultdict(int)
        for exercise_id in correct_exercises:
            lo_id = exercise_to_objective.get(exercise_id)
            if lo_id:
                correct_counts[lo_id] += 1

        ordered_ids: list[str] = list(objective_order)
        seen_ids: set[str] = set(ordered_ids)
        for lo_id in exercise_to_objective.values():
            if lo_id not in seen_ids:
                ordered_ids.append(lo_id)
                seen_ids.add(lo_id)

        items: list[LearningObjectiveProgressItem] = []
        for lo_id in ordered_ids:
            total = totals_by_objective.get(lo_id, 0)
            attempted = attempted_counts.get(lo_id, 0)
            correct = correct_counts.get(lo_id, 0)
            if total > 0 and correct >= total:
                status = LearningObjectiveStatus.COMPLETED
            elif attempted > 0:
                status = LearningObjectiveStatus.PARTIAL
            else:
                status = LearningObjectiveStatus.NOT_STARTED

            lookup_entry = objective_lookup.get(lo_id, {"title": lo_id, "description": lo_id})
            items.append(
                LearningObjectiveProgressItem(
                    lo_id=lo_id,
                    title=str(lookup_entry.get("title") or lo_id),
                    description=str(lookup_entry.get("description") or lookup_entry.get("title") or lo_id),
                    exercises_total=total,
                    exercises_attempted=attempted,
                    exercises_correct=correct,
                    status=status,
                )
            )

        return UnitLearningObjectiveProgress(unit_id=unit_id, items=items)

    async def _unit_all_lessons_completed(self, user_id: str, unit_id: str, total_lessons: int) -> bool:
        """Check if all lessons in a unit are completed for a user based on unit session."""
        try:
            us = await self.content.get_or_create_unit_session(user_id=user_id, unit_id=unit_id)
            return len(us.completed_lesson_ids or []) >= total_lessons > 0
        except Exception:
            return False

    async def get_next_lesson_to_resume(self, user_id: str, unit_id: str) -> str | None:
        """Return next incomplete lesson id within a unit for resuming learning."""
        unit_detail = await self.content.get_unit_detail(unit_id)
        if not unit_detail:
            return None
        try:
            us = await self.content.get_or_create_unit_session(user_id=user_id, unit_id=unit_id)
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

    async def get_user_sessions(
        self,
        user_id: str | None = None,
        status: str | None = None,
        lesson_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionListResponse:
        """Get user sessions with filtering"""
        sessions, total = await self.repo.get_user_sessions(
            user_id=user_id,
            status=status,
            lesson_id=lesson_id,
            limit=limit,
            offset=offset,
        )

        session_dtos: list[LearningSession] = []
        for session in sessions:
            ensured_session = await self._ensure_session_user(session, user_id)
            session_dtos.append(self._to_session_dto(ensured_session))
        return SessionListResponse(sessions=session_dtos, total=total)

    async def list_sessions(
        self,
        *,
        user_id: str | None = None,
        status: str | None = None,
        lesson_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionListResponse:
        """Return learning sessions for administrative dashboards."""

        sessions, total = await self.repo.get_sessions(
            user_id=user_id,
            status=status,
            lesson_id=lesson_id,
            limit=limit,
            offset=offset,
        )

        session_dtos = [self._to_session_dto(session) for session in sessions]
        return SessionListResponse(sessions=session_dtos, total=total)

    async def get_session_admin(self, session_id: str) -> LearningSession | None:
        """Return a learning session without enforcing user ownership."""

        session = await self.repo.get_session_by_id(session_id)
        if not session:
            return None
        return self._to_session_dto(session)

    async def get_session_context_for_assistant(self, session_id: str) -> AssistantSessionContext:
        """Return enriched context for teaching assistant experiences."""

        session = await self.repo.get_session_by_id(session_id)
        if session is None:
            raise ValueError(f"Learning session {session_id} not found")

        lesson = await self.content.get_lesson(session.lesson_id)
        unit = await self.content.get_unit(session.unit_id)

        session_dto = self._to_session_dto(session)
        session_data = session.session_data or {}
        exercise_answers = session_data.get("exercise_answers", {})

        attempt_history: list[dict[str, Any]] = []
        for exercise_id, payload in exercise_answers.items():
            entry: dict[str, Any] = {"exercise_id": exercise_id}
            if isinstance(payload, dict):
                entry.update(payload)
            else:
                entry["value"] = payload
            attempt_history.append(entry)

        return AssistantSessionContext(
            session=session_dto,
            exercise_attempt_history=attempt_history,
            lesson=lesson.model_dump(mode="json") if lesson else None,
            unit=unit.model_dump(mode="json") if unit else None,
        )

    async def check_health(self) -> bool:
        """Health check for the learning session service"""
        return await self.repo.health_check()

    # ================================
    # Private Helper Methods
    # ================================

    async def _ensure_session_user(self, session: LearningSessionModel, user_id: str | None) -> LearningSessionModel:
        """Validate or persist the session's user association."""

        if user_id is None:
            if session.user_id is None:
                return session
            raise PermissionError("User context is required for this learning session")

        if session.user_id is None:
            return await self.repo.assign_session_user(session.id, user_id)

        if session.user_id != user_id:
            raise PermissionError("Learning session belongs to a different user")

        return session

    def _to_session_dto(self, session: LearningSessionModel) -> LearningSession:
        """Convert session model to DTO"""
        return LearningSession(
            id=session.id,
            lesson_id=session.lesson_id,
            unit_id=session.unit_id,
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
            unit_id=session.unit_id,
            total_exercises=total_exercises,
            completed_exercises=completed_exercises,
            correct_exercises=correct_exercises,
            total_time_seconds=session_data.get("total_time_seconds", 0),
            completion_percentage=completion_percentage,
            score_percentage=score_percentage,
            achievements=achievements,
        )

    def _normalize_unit_objectives(
        self,
        raw_objectives: Any | None,
    ) -> tuple[list[str], dict[str, dict[str, str]]]:
        """Return ordered identifiers and lookup mapping for unit learning objectives."""

        ordered_ids: list[str] = []
        lookup: dict[str, dict[str, str]] = {}

        objectives = raw_objectives or []
        for index, objective in enumerate(objectives):
            if isinstance(objective, dict):
                payload = dict(objective)
            elif isinstance(objective, str):
                lo_id = f"lo_{index + 1}"
                lo_title = str(objective)
                lo_description = lo_title
                if lo_id not in lookup:
                    ordered_ids.append(lo_id)
                lookup[lo_id] = {"title": lo_title, "description": lo_description}
                continue
            else:
                payload = {
                    "id": getattr(objective, "id", None) or getattr(objective, "lo_id", None),
                    "title": getattr(objective, "title", None) or getattr(objective, "short_title", None),
                    "description": getattr(objective, "description", None),
                }

            lo_id = str(payload.get("id") or payload.get("lo_id") or f"lo_{index + 1}")
            lo_title = str(payload.get("title") or payload.get("short_title") or payload.get("description") or lo_id)
            lo_description = str(payload.get("description") or lo_title)

            if lo_id not in lookup:
                ordered_ids.append(lo_id)
            lookup[lo_id] = {"title": lo_title, "description": lo_description}

        return ordered_ids, lookup
