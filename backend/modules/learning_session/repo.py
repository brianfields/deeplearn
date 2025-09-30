"""
Learning Session Module - Repository Layer

Minimal database access layer to support existing frontend functionality.
This is a migration, not new feature development.
"""

from collections.abc import Iterable
from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import and_, desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import LearningSessionModel, SessionStatus


class LearningSessionRepo:
    """Repository for learning session database operations"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(
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
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session_by_id(self, session_id: str) -> LearningSessionModel | None:
        """Get session by ID"""
        return await self.db.get(LearningSessionModel, session_id)

    async def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        completed_at: datetime | None = None,
    ) -> LearningSessionModel | None:
        """Update session status"""
        session = await self.get_session_by_id(session_id)
        if not session:
            return None

        session.status = status.value
        if completed_at:
            session.completed_at = completed_at

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def update_session_progress(
        self,
        session_id: str,
        current_exercise_index: int | None = None,
        progress_percentage: float | None = None,
        exercises_completed: int | None = None,
        exercises_correct: int | None = None,
        session_data: dict[str, Any] | None = None,
    ) -> LearningSessionModel | None:
        """Update session progress"""
        session = await self.get_session_by_id(session_id)
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

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_user_sessions(
        self,
        user_id: str | None = None,
        status: str | None = None,
        lesson_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[LearningSessionModel], int]:
        """Get user sessions with filtering and pagination"""
        filters = []
        if user_id:
            filters.append(LearningSessionModel.user_id == user_id)
        if status:
            filters.append(LearningSessionModel.status == status)
        if lesson_id:
            filters.append(LearningSessionModel.lesson_id == lesson_id)

        base_stmt = select(LearningSessionModel)
        if filters:
            base_stmt = base_stmt.where(*filters)

        total_stmt = select(func.count(LearningSessionModel.id))
        if filters:
            total_stmt = total_stmt.where(*filters)

        ordered_stmt = base_stmt.order_by(desc(LearningSessionModel.started_at)).offset(offset).limit(limit)

        result = await self.db.execute(ordered_stmt)
        sessions = list(result.scalars().all())

        total_result = await self.db.execute(total_stmt)
        total = int(total_result.scalar() or 0)

        return sessions, total

    async def get_active_session_for_user_and_lesson(self, user_id: str, lesson_id: str) -> LearningSessionModel | None:
        """Get active session for user and lesson (if any)"""
        stmt = (
            select(LearningSessionModel)
            .where(
                and_(
                    LearningSessionModel.user_id == user_id,
                    LearningSessionModel.lesson_id == lesson_id,
                    LearningSessionModel.status == SessionStatus.ACTIVE.value,
                )
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_sessions_for_lessons(self, lesson_ids: Iterable[str]) -> list[LearningSessionModel]:
        """Return all sessions associated with the provided lesson identifiers."""

        lesson_ids = list(lesson_ids)
        if not lesson_ids:
            return []

        stmt = select(LearningSessionModel).where(LearningSessionModel.lesson_id.in_(lesson_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def assign_session_user(self, session_id: str, user_id: str) -> LearningSessionModel:
        """Persist the user association for a session if it has not been set."""

        session = await self.get_session_by_id(session_id)
        if session is None:
            raise ValueError(f"Learning session {session_id} does not exist")

        if session.user_id is not None and session.user_id != user_id:
            raise PermissionError("Learning session already belongs to a different user")

        if session.user_id is None:
            session.user_id = user_id
            await self.db.commit()
            await self.db.refresh(session)

        return session

    async def health_check(self) -> bool:
        """Health check - verify database connectivity"""
        try:
            # Simple query to test database connection
            await self.db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
