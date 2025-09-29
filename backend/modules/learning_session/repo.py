"""
Learning Session Module - Repository Layer

Minimal database access layer to support existing frontend functionality.
This is a migration, not new feature development.
"""

from datetime import datetime
from typing import Any, Iterable
import uuid

from sqlalchemy import and_, desc, text
from sqlalchemy.orm import Session

from .models import LearningSessionModel, SessionStatus


class LearningSessionRepo:
    """Repository for learning session database operations"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_session(
        self,
        lesson_id: str,
        user_id: str | None = None,
        total_exercises: int = 0,
    ) -> LearningSessionModel:
        """Create a new learning session"""
        session = LearningSessionModel(
            id=str(uuid.uuid4()),
            lesson_id=lesson_id,
            user_id=user_id,
            status=SessionStatus.ACTIVE.value,
            total_exercises=total_exercises,
            current_exercise_index=0,
            exercises_completed=0,
            exercises_correct=0,
            session_data={},
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_id(self, session_id: str) -> LearningSessionModel | None:
        """Get session by ID"""
        return self.db.query(LearningSessionModel).filter(LearningSessionModel.id == session_id).first()

    def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        completed_at: datetime | None = None,
    ) -> LearningSessionModel | None:
        """Update session status"""
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        session.status = status.value
        if completed_at:
            session.completed_at = completed_at

        self.db.commit()
        self.db.refresh(session)
        return session

    def update_session_progress(
        self,
        session_id: str,
        current_exercise_index: int | None = None,
        progress_percentage: float | None = None,
        exercises_completed: int | None = None,
        exercises_correct: int | None = None,
        session_data: dict[str, Any] | None = None,
    ) -> LearningSessionModel | None:
        """Update session progress"""
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        # Update fields only if provided
        if current_exercise_index is not None:
            session.current_exercise_index = current_exercise_index
        if progress_percentage is not None:
            session.progress_percentage = progress_percentage
        if exercises_completed is not None:
            session.exercises_completed = exercises_completed
        if exercises_correct is not None:
            session.exercises_correct = exercises_correct

        if session_data:
            # Merge with existing session data
            current_data: dict[str, Any] = session.session_data or {}
            current_data.update(session_data)
            session.session_data = current_data

        self.db.commit()
        self.db.refresh(session)
        return session

    def get_user_sessions(
        self,
        user_id: str | None = None,
        status: str | None = None,
        lesson_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[LearningSessionModel], int]:
        """Get user sessions with filtering and pagination"""
        query = self.db.query(LearningSessionModel)

        # Apply filters
        if user_id:
            query = query.filter(LearningSessionModel.user_id == user_id)
        if status:
            query = query.filter(LearningSessionModel.status == status)
        if lesson_id:
            query = query.filter(LearningSessionModel.lesson_id == lesson_id)

        # Get total count before pagination
        total = query.count()

        # Apply pagination and ordering
        sessions = query.order_by(desc(LearningSessionModel.started_at)).offset(offset).limit(limit).all()

        return sessions, total

    def get_active_session_for_user_and_lesson(self, user_id: str, lesson_id: str) -> LearningSessionModel | None:
        """Get active session for user and lesson (if any)"""
        return (
            self.db.query(LearningSessionModel)
            .filter(
                and_(
                    LearningSessionModel.user_id == user_id,
                    LearningSessionModel.lesson_id == lesson_id,
                    LearningSessionModel.status == SessionStatus.ACTIVE.value,
                )
            )
            .first()
        )

    def get_sessions_for_lessons(self, lesson_ids: Iterable[str]) -> list[LearningSessionModel]:
        """Return all sessions associated with the provided lesson identifiers."""

        lesson_ids = list(lesson_ids)
        if not lesson_ids:
            return []

        return (
            self.db.query(LearningSessionModel)
            .filter(LearningSessionModel.lesson_id.in_(lesson_ids))
            .all()
        )

    def assign_session_user(self, session_id: str, user_id: str) -> LearningSessionModel:
        """Persist the user association for a session if it has not been set."""

        session = self.get_session_by_id(session_id)
        if session is None:
            raise ValueError(f"Learning session {session_id} does not exist")

        if session.user_id is not None and session.user_id != user_id:
            raise PermissionError("Learning session already belongs to a different user")

        if session.user_id is None:
            session.user_id = user_id
            self.db.commit()
            self.db.refresh(session)

        return session

    def health_check(self) -> bool:
        """Health check - verify database connectivity"""
        try:
            # Simple query to test database connection
            self.db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
