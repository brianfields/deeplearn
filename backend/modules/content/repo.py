"""
Content Module - Repository Layer

Database access layer that returns ORM objects.
Handles all CRUD operations for lessons with embedded package content.
"""

from typing import Any

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from .models import LessonModel, UnitModel


class ContentRepo:
    """Repository for content data access operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with raw SQLAlchemy session."""
        self.s = session

    # Lesson operations
    def get_lesson_by_id(self, lesson_id: str) -> LessonModel | None:
        """Get lesson by ID."""
        return self.s.get(LessonModel, lesson_id)

    def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonModel]:
        """Get all lessons with pagination."""
        return self.s.query(LessonModel).offset(offset).limit(limit).all()

    def search_lessons(self, query: str | None = None, user_level: str | None = None, limit: int = 100, offset: int = 0) -> list[LessonModel]:
        """Search lessons with optional filters."""
        q = self.s.query(LessonModel)

        if query:
            q = q.filter(LessonModel.title.contains(query))
        if user_level:
            q = q.filter(LessonModel.user_level == user_level)

        return q.offset(offset).limit(limit).all()

    # New: filter by unit
    def get_lessons_by_unit(self, unit_id: str, limit: int = 100, offset: int = 0) -> list[LessonModel]:
        """Get lessons for a specific unit."""
        q = self.s.query(LessonModel).filter(LessonModel.unit_id == unit_id)
        return q.offset(offset).limit(limit).all()

    def save_lesson(self, lesson: LessonModel) -> LessonModel:
        """Save lesson to database."""
        self.s.add(lesson)
        self.s.flush()
        return lesson

    def delete_lesson(self, lesson_id: str) -> bool:
        """Delete lesson by ID."""
        lesson = self.get_lesson_by_id(lesson_id)
        if lesson:
            self.s.delete(lesson)
            return True
        return False

    def lesson_exists(self, lesson_id: str) -> bool:
        """Check if lesson exists."""
        return self.s.query(LessonModel.id).filter(LessonModel.id == lesson_id).first() is not None

    # Unit operations (moved from modules.units.repo)
    def get_unit_by_id(self, unit_id: str) -> UnitModel | None:
        """Get unit by ID."""
        return self.s.get(UnitModel, unit_id)

    def list_units(self, limit: int = 100, offset: int = 0) -> list[UnitModel]:
        """List units with pagination."""
        return self.s.query(UnitModel).offset(offset).limit(limit).all()

    def add_unit(self, unit: UnitModel) -> UnitModel:
        """Add a new unit to the database and flush to obtain ID."""
        self.s.add(unit)
        self.s.flush()
        return unit

    def save_unit(self, unit: UnitModel) -> None:
        """Persist changes to a unit."""
        self.s.add(unit)

    def delete_unit(self, unit_id: str) -> bool:
        """Delete unit by ID, returning True if removed."""
        unit = self.get_unit_by_id(unit_id)
        if not unit:
            return False
        self.s.delete(unit)
        return True

    def update_unit_lesson_order(self, unit_id: str, lesson_ids: list[str]) -> UnitModel | None:
        """Update lesson order for the given unit and return the updated model, or None if not found."""
        unit = self.get_unit_by_id(unit_id)
        if not unit:
            return None
        unit.lesson_order = list(lesson_ids)  # type: ignore[assignment]
        self.s.add(unit)
        self.s.flush()
        return unit

    # Unit session operations
    def get_unit_session(self, user_id: str, unit_id: str) -> Any | None:
        """Get the latest unit session for a user and unit."""
        from ..learning_session.models import UnitSessionModel  # Local import to avoid circular deps # noqa: PLC0415

        return self.s.query(UnitSessionModel).filter(and_(UnitSessionModel.user_id == user_id, UnitSessionModel.unit_id == unit_id)).order_by(desc(UnitSessionModel.updated_at)).first()

    def add_unit_session(self, unit_session: Any) -> Any:
        """Add a new unit session and flush to obtain ID."""
        self.s.add(unit_session)
        self.s.flush()
        return unit_session

    def save_unit_session(self, unit_session: Any) -> None:
        """Persist changes to a unit session (no flush)."""
        self.s.add(unit_session)
