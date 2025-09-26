"""
Content Module - Repository Layer

Database access layer that returns ORM objects.
Handles all CRUD operations for lessons with embedded package content.
"""

from datetime import UTC, datetime
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

    def search_lessons(self, query: str | None = None, learner_level: str | None = None, limit: int = 100, offset: int = 0) -> list[LessonModel]:
        """Search lessons with optional filters."""
        q = self.s.query(LessonModel)

        if query:
            q = q.filter(LessonModel.title.contains(query))
        if learner_level:
            q = q.filter(LessonModel.learner_level == learner_level)

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
        """List units with pagination, ordered by updated_at descending (newest first)."""
        return self.s.query(UnitModel).order_by(desc(UnitModel.updated_at)).offset(offset).limit(limit).all()

    def get_units_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[UnitModel]:
        """Get units by status, ordered by updated_at descending."""
        return self.s.query(UnitModel).filter(UnitModel.status == status).order_by(desc(UnitModel.updated_at)).offset(offset).limit(limit).all()

    def add_unit(self, unit: UnitModel) -> UnitModel:
        """Add a new unit to the database and flush to obtain ID."""
        self.s.add(unit)
        self.s.flush()
        return unit

    def save_unit(self, unit: UnitModel) -> None:
        """Persist changes to a unit."""
        self.s.add(unit)

    def update_unit_status(self, unit_id: str, status: str, error_message: str | None = None, creation_progress: dict[str, Any] | None = None) -> UnitModel | None:
        """Update unit status and related fields, returning the updated model or None if not found."""
        unit = self.get_unit_by_id(unit_id)
        if not unit:
            return None

        unit.status = status  # type: ignore[assignment]
        if error_message is not None:
            unit.error_message = error_message  # type: ignore[assignment]
        if creation_progress is not None:
            unit.creation_progress = creation_progress  # type: ignore[assignment]

        # Update timestamp
        unit.updated_at = datetime.now(UTC)  # type: ignore[assignment]

        self.s.add(unit)
        self.s.flush()
        return unit

    def update_unit_lesson_order(self, unit_id: str, lesson_ids: list[str]) -> UnitModel | None:
        """Update lesson order for the given unit and return the updated model, or None if not found."""
        unit = self.get_unit_by_id(unit_id)
        if not unit:
            return None
        unit.lesson_order = list(lesson_ids)  # type: ignore[assignment]
        self.s.add(unit)
        self.s.flush()
        return unit

    def associate_lessons_with_unit(self, unit_id: str, lesson_ids: list[str]) -> UnitModel | None:
        """Associate the specified lessons with the unit and set the unit's lesson order.

        This method:
        - Ensures the `units.lesson_order` matches the provided order (filtered to existing lessons)
        - Sets `lessons.unit_id` for all provided lesson IDs
        - Detaches any lessons currently assigned to the unit but not present in the provided list

        Returns None if the unit is not found.
        """
        unit = self.get_unit_by_id(unit_id)
        if not unit:
            return None

        # Detach lessons no longer associated
        existing_in_unit: list[LessonModel] = self.s.query(LessonModel).filter(LessonModel.unit_id == unit_id).all()
        provided_ids = set(lesson_ids)
        for lesson in existing_in_unit:
            if lesson.id not in provided_ids:
                lesson.unit_id = None  # type: ignore[assignment]
                self.s.add(lesson)

        # Attach provided lessons (preserve provided order; skip missing IDs)
        ordered_existing_ids: list[str] = []
        for lid in lesson_ids:
            lesson_obj: LessonModel | None = self.get_lesson_by_id(lid)
            if not lesson_obj:
                continue
            lesson_obj.unit_id = unit_id  # type: ignore[assignment]
            self.s.add(lesson_obj)
            ordered_existing_ids.append(lid)

        # Update unit order to reflect attached lessons only
        unit.lesson_order = ordered_existing_ids  # type: ignore[assignment]
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

    def delete_unit(self, unit_id: str) -> bool:
        """Delete a unit by ID. Returns True if successful, False if not found."""
        unit = self.get_unit_by_id(unit_id)
        if not unit:
            return False

        # First, unlink any lessons from this unit
        lessons = self.s.query(LessonModel).filter(LessonModel.unit_id == unit_id).all()
        for lesson in lessons:
            lesson.unit_id = None  # type: ignore[assignment]
            self.s.add(lesson)

        # Delete the unit
        self.s.delete(unit)
        self.s.flush()
        return True
