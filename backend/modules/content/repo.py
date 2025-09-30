"""
Content Module - Repository Layer

Database access layer that returns ORM objects.
Handles all CRUD operations for lessons with embedded package content.
"""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import LessonModel, UnitModel


class ContentRepo:
    """Repository for content data access operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with async SQLAlchemy session."""
        self.s = session

    # Lesson operations
    async def get_lesson_by_id(self, lesson_id: str) -> LessonModel | None:
        """Get lesson by ID."""
        return await self.s.get(LessonModel, lesson_id)

    async def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonModel]:
        """Get all lessons with pagination."""
        stmt = select(LessonModel).offset(offset).limit(limit)
        result = await self.s.execute(stmt)
        return list(result.scalars().all())

    async def search_lessons(
        self,
        query: str | None = None,
        learner_level: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LessonModel]:
        """Search lessons with optional filters."""
        stmt = select(LessonModel)

        if query:
            stmt = stmt.filter(LessonModel.title.contains(query))
        if learner_level:
            stmt = stmt.filter(LessonModel.learner_level == learner_level)

        stmt = stmt.offset(offset).limit(limit)
        result = await self.s.execute(stmt)
        return list(result.scalars().all())

    async def get_lessons_by_unit(self, unit_id: str, limit: int = 100, offset: int = 0) -> list[LessonModel]:
        """Get lessons for a specific unit."""
        stmt = select(LessonModel).filter(LessonModel.unit_id == unit_id).offset(offset).limit(limit)
        result = await self.s.execute(stmt)
        return list(result.scalars().all())

    async def save_lesson(self, lesson: LessonModel) -> LessonModel:
        """Save lesson to database."""
        self.s.add(lesson)
        await self.s.flush()
        return lesson

    async def delete_lesson(self, lesson_id: str) -> bool:
        """Delete lesson by ID."""
        lesson = await self.get_lesson_by_id(lesson_id)
        if lesson is None:
            return False
        await self.s.delete(lesson)
        await self.s.flush()
        return True

    async def lesson_exists(self, lesson_id: str) -> bool:
        """Check if lesson exists."""
        stmt = select(LessonModel.id).filter(LessonModel.id == lesson_id)
        result = await self.s.execute(stmt)
        return result.scalar_one_or_none() is not None

    # Unit operations (moved from modules.units.repo)
    async def get_unit_by_id(self, unit_id: str) -> UnitModel | None:
        """Get unit by ID."""
        return await self.s.get(UnitModel, unit_id)

    async def list_units(self, limit: int = 100, offset: int = 0) -> list[UnitModel]:
        """List units with pagination, ordered by updated_at descending (newest first)."""
        stmt = select(UnitModel).order_by(desc(UnitModel.updated_at)).offset(offset).limit(limit)
        result = await self.s.execute(stmt)
        return list(result.scalars().all())

    async def list_units_for_user(self, user_id: int, limit: int = 100, offset: int = 0) -> list[UnitModel]:
        """Return units owned by the specified user ordered by most recently updated."""
        stmt = select(UnitModel).filter(UnitModel.user_id == user_id).order_by(desc(UnitModel.updated_at)).offset(offset).limit(limit)
        result = await self.s.execute(stmt)
        return list(result.scalars().all())

    async def list_global_units(self, limit: int = 100, offset: int = 0) -> list[UnitModel]:
        """Return globally shared units ordered by most recently updated."""
        stmt = select(UnitModel).filter(UnitModel.is_global.is_(True)).order_by(desc(UnitModel.updated_at)).offset(offset).limit(limit)
        result = await self.s.execute(stmt)
        return list(result.scalars().all())

    async def get_units_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[UnitModel]:
        """Get units by status, ordered by updated_at descending."""
        stmt = select(UnitModel).filter(UnitModel.status == status).order_by(desc(UnitModel.updated_at)).offset(offset).limit(limit)
        result = await self.s.execute(stmt)
        return list(result.scalars().all())

    async def add_unit(self, unit: UnitModel) -> UnitModel:
        """Add a new unit to the database and flush to obtain ID."""
        self.s.add(unit)
        await self.s.flush()
        return unit

    async def save_unit(self, unit: UnitModel) -> None:
        """Persist changes to a unit."""
        self.s.add(unit)

    async def update_unit_status(
        self,
        unit_id: str,
        status: str,
        error_message: str | None = None,
        creation_progress: dict[str, Any] | None = None,
    ) -> UnitModel | None:
        """Update unit status and related fields, returning the updated model or None if not found."""
        unit = await self.get_unit_by_id(unit_id)
        if unit is None:
            return None

        unit.status = status  # type: ignore[assignment]
        if error_message is not None:
            unit.error_message = error_message  # type: ignore[assignment]
        if creation_progress is not None:
            unit.creation_progress = creation_progress  # type: ignore[assignment]

        unit.updated_at = datetime.utcnow()  # type: ignore[assignment]

        self.s.add(unit)
        await self.s.flush()
        return unit

    async def update_unit_lesson_order(self, unit_id: str, lesson_ids: list[str]) -> UnitModel | None:
        """Update lesson order for the given unit and return the updated model, or None if not found."""
        unit = await self.get_unit_by_id(unit_id)
        if unit is None:
            return None
        unit.lesson_order = list(lesson_ids)  # type: ignore[assignment]
        self.s.add(unit)
        await self.s.flush()
        return unit

    async def associate_lessons_with_unit(self, unit_id: str, lesson_ids: list[str]) -> UnitModel | None:
        """Associate the specified lessons with the unit and set the unit's lesson order.

        This method:
        - Ensures the `units.lesson_order` matches the provided order (filtered to existing lessons)
        - Sets `lessons.unit_id` for all provided lesson IDs
        - Detaches any lessons currently assigned to the unit but not present in the provided list

        Returns None if the unit is not found.
        """
        unit = await self.get_unit_by_id(unit_id)
        if unit is None:
            return None

        # Detach lessons no longer associated
        existing_result = await self.s.execute(select(LessonModel).filter(LessonModel.unit_id == unit_id))
        existing_in_unit: list[LessonModel] = list(existing_result.scalars().all())
        provided_ids = set(lesson_ids)
        for lesson in existing_in_unit:
            if lesson.id not in provided_ids:
                lesson.unit_id = None  # type: ignore[assignment]
                self.s.add(lesson)

        # Attach provided lessons (preserve provided order; skip missing IDs)
        ordered_existing_ids: list[str] = []
        for lid in lesson_ids:
            lesson_obj = await self.get_lesson_by_id(lid)
            if lesson_obj is None:
                continue
            lesson_obj.unit_id = unit_id  # type: ignore[assignment]
            self.s.add(lesson_obj)
            ordered_existing_ids.append(lid)

        # Update unit order to reflect attached lessons only
        unit.lesson_order = ordered_existing_ids  # type: ignore[assignment]
        self.s.add(unit)
        await self.s.flush()
        return unit

    async def set_unit_podcast(
        self,
        unit_id: str,
        *,
        transcript: str | None,
        audio_object_id: uuid.UUID | None,
        voice: str | None,
    ) -> UnitModel | None:
        """Persist podcast transcript and object store reference for a unit."""

        unit = await self.get_unit_by_id(unit_id)
        if unit is None:
            return None

        unit.podcast_transcript = transcript  # type: ignore[assignment]
        unit.podcast_audio_object_id = audio_object_id  # type: ignore[assignment]
        unit.podcast_voice = voice  # type: ignore[assignment]
        has_audio_reference = audio_object_id is not None
        if transcript or has_audio_reference:
            unit.podcast_generated_at = datetime.utcnow()  # type: ignore[assignment]
        else:
            unit.podcast_generated_at = None  # type: ignore[assignment]
        unit.updated_at = datetime.utcnow()  # type: ignore[assignment]
        self.s.add(unit)
        await self.s.flush()
        return unit

    async def set_unit_art(
        self,
        unit_id: str,
        *,
        image_object_id: uuid.UUID | None,
        description: str | None,
    ) -> UnitModel | None:
        """Persist unit artwork metadata and return the updated model."""

        unit = await self.get_unit_by_id(unit_id)
        if unit is None:
            return None

        unit.art_image_id = image_object_id  # type: ignore[assignment]
        unit.art_image_description = description  # type: ignore[assignment]
        unit.updated_at = datetime.utcnow()  # type: ignore[assignment]
        self.s.add(unit)
        await self.s.flush()
        return unit

    async def set_unit_owner(self, unit_id: str, user_id: int | None) -> UnitModel | None:
        """Update the owner of a unit, returning the updated model or None if not found."""
        unit = await self.get_unit_by_id(unit_id)
        if unit is None:
            return None

        unit.user_id = user_id  # type: ignore[assignment]
        unit.updated_at = datetime.utcnow()  # type: ignore[assignment]
        self.s.add(unit)
        await self.s.flush()
        return unit

    async def set_unit_sharing(self, unit_id: str, is_global: bool) -> UnitModel | None:
        """Toggle whether a unit is globally shared."""
        unit = await self.get_unit_by_id(unit_id)
        if unit is None:
            return None

        unit.is_global = bool(is_global)  # type: ignore[assignment]
        unit.updated_at = datetime.utcnow()  # type: ignore[assignment]
        self.s.add(unit)
        await self.s.flush()
        return unit

    async def is_unit_owned_by_user(self, unit_id: str, user_id: int) -> bool:
        """Return True when the given unit is owned by the provided user id."""
        stmt = select(UnitModel.id).filter(UnitModel.id == unit_id, UnitModel.user_id == user_id)
        result = await self.s.execute(stmt)
        return result.scalar_one_or_none() is not None

    # Unit session operations
    async def get_unit_session(self, user_id: str, unit_id: str) -> Any | None:
        """Get the latest unit session for a user and unit."""
        from ..learning_session.models import UnitSessionModel  # Local import to avoid circular deps # noqa: PLC0415

        stmt = select(UnitSessionModel).filter(and_(UnitSessionModel.user_id == user_id, UnitSessionModel.unit_id == unit_id)).order_by(desc(UnitSessionModel.updated_at)).limit(1)
        result = await self.s.execute(stmt)
        return result.scalars().first()

    async def add_unit_session(self, unit_session: Any) -> Any:
        """Add a new unit session and flush to obtain ID."""
        self.s.add(unit_session)
        await self.s.flush()
        return unit_session

    async def save_unit_session(self, unit_session: Any) -> None:
        """Persist changes to a unit session (no flush)."""
        self.s.add(unit_session)

    async def delete_unit(self, unit_id: str) -> bool:
        """Delete a unit by ID. Returns True if successful, False if not found."""
        unit = await self.get_unit_by_id(unit_id)
        if unit is None:
            return False

        # First, unlink any lessons from this unit
        lesson_result = await self.s.execute(select(LessonModel).filter(LessonModel.unit_id == unit_id))
        lessons = list(lesson_result.scalars().all())
        for lesson in lessons:
            lesson.unit_id = None  # type: ignore[assignment]
            self.s.add(lesson)

        # Delete the unit
        await self.s.delete(unit)
        await self.s.flush()
        return True
