from __future__ import annotations

"""
Content Module - Service Layer

Business logic layer that returns DTOs (Pydantic models).
Handles content operations and data transformation.
"""

from datetime import UTC, datetime
from enum import Enum
import logging

# Import inside methods when needed to avoid circular imports with public/providers
from typing import TYPE_CHECKING, Any
import uuid

from pydantic import BaseModel, ConfigDict

from .models import LessonModel, UnitModel
from .package_models import LessonPackage
from .repo import ContentRepo

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from ..learning_session.models import UnitSessionModel  # noqa: F401

logger = logging.getLogger(__name__)


# Enums for status validation
class UnitStatus(str, Enum):
    """Valid unit statuses for creation flow tracking."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# DTOs (Data Transfer Objects)
class LessonRead(BaseModel):
    """DTO for reading lesson data with embedded package."""

    id: str
    title: str
    learner_level: str
    core_concept: str | None = None  # For admin compatibility
    unit_id: str | None = None
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict[str, Any] | None = None
    package: LessonPackage
    package_version: int
    flow_run_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LessonCreate(BaseModel):
    """DTO for creating new lessons with package."""

    id: str
    title: str
    learner_level: str
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict[str, Any] | None = None
    package: LessonPackage
    package_version: int = 1
    flow_run_id: uuid.UUID | None = None


class ContentService:
    """Service for content operations."""

    def __init__(self, repo: ContentRepo) -> None:
        """Initialize service with repository."""
        self.repo = repo

    # Lesson operations
    def get_lesson(self, lesson_id: str) -> LessonRead | None:
        """Get lesson with package by ID."""
        lesson = self.repo.get_lesson_by_id(lesson_id)
        if not lesson:
            return None

        try:
            package = LessonPackage.model_validate(lesson.package)

            lesson_dict = {
                "id": lesson.id,
                "title": lesson.title,
                "learner_level": lesson.learner_level,
                "unit_id": getattr(lesson, "unit_id", None),
                "source_material": lesson.source_material,
                "source_domain": getattr(lesson, "source_domain", None),
                "source_level": getattr(lesson, "source_level", None),
                "refined_material": getattr(lesson, "refined_material", None),
                "package": package,
                "package_version": lesson.package_version,
                "flow_run_id": lesson.flow_run_id,
                "created_at": lesson.created_at,
                "updated_at": lesson.updated_at,
            }

            return LessonRead.model_validate(lesson_dict)
        except Exception as e:
            logger.error(f"❌ Failed to validate lesson {lesson.id} ({lesson.title}): {e}")
            raise

    def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonRead]:
        """Get all lessons with packages."""
        lessons = self.repo.get_all_lessons(limit, offset)
        result = []

        for lesson in lessons:
            try:
                package = LessonPackage.model_validate(lesson.package)

                lesson_dict = {
                    "id": lesson.id,
                    "title": lesson.title,
                    "learner_level": lesson.learner_level,
                    "unit_id": getattr(lesson, "unit_id", None),
                    "source_material": lesson.source_material,
                    "source_domain": getattr(lesson, "source_domain", None),
                    "source_level": getattr(lesson, "source_level", None),
                    "refined_material": getattr(lesson, "refined_material", None),
                    "package": package,
                    "package_version": lesson.package_version,
                    "flow_run_id": lesson.flow_run_id,
                    "created_at": lesson.created_at,
                    "updated_at": lesson.updated_at,
                }

                result.append(LessonRead.model_validate(lesson_dict))
            except Exception as e:
                logger.warning(f"⚠️ Skipping lesson {lesson.id} ({lesson.title}) due to data validation error: {e}")
                continue

        return result

    def search_lessons(self, query: str | None = None, learner_level: str | None = None, limit: int = 100, offset: int = 0) -> list[LessonRead]:
        """Search lessons with optional filters."""
        lessons = self.repo.search_lessons(query, learner_level, limit, offset)
        result = []

        for lesson in lessons:
            try:
                package = LessonPackage.model_validate(lesson.package)

                lesson_dict = {
                    "id": lesson.id,
                    "title": lesson.title,
                    "learner_level": lesson.learner_level,
                    "unit_id": getattr(lesson, "unit_id", None),
                    "source_material": lesson.source_material,
                    "source_domain": getattr(lesson, "source_domain", None),
                    "source_level": getattr(lesson, "source_level", None),
                    "refined_material": getattr(lesson, "refined_material", None),
                    "package": package,
                    "package_version": lesson.package_version,
                    "flow_run_id": lesson.flow_run_id,
                    "created_at": lesson.created_at,
                    "updated_at": lesson.updated_at,
                }

                result.append(LessonRead.model_validate(lesson_dict))
            except Exception as e:
                logger.warning(f"⚠️ Skipping lesson {lesson.id} ({lesson.title}) due to data validation error: {e}")
                continue

        return result

    # New: Lessons by unit
    def get_lessons_by_unit(self, unit_id: str, limit: int = 100, offset: int = 0) -> list[LessonRead]:
        """Return lessons that belong to the given unit."""
        lessons = self.repo.get_lessons_by_unit(unit_id=unit_id, limit=limit, offset=offset)
        result: list[LessonRead] = []
        for lesson in lessons:
            try:
                package = LessonPackage.model_validate(lesson.package)
                lesson_dict = {
                    "id": lesson.id,
                    "title": lesson.title,
                    "learner_level": lesson.learner_level,
                    "source_material": lesson.source_material,
                    "source_domain": getattr(lesson, "source_domain", None),
                    "source_level": getattr(lesson, "source_level", None),
                    "refined_material": getattr(lesson, "refined_material", None),
                    "package": package,
                    "package_version": lesson.package_version,
                    "flow_run_id": lesson.flow_run_id,
                    "created_at": lesson.created_at,
                    "updated_at": lesson.updated_at,
                }
                result.append(LessonRead.model_validate(lesson_dict))
            except Exception as e:  # pragma: no cover - defensive
                logger.warning(f"⚠️ Skipping lesson {lesson.id} due to data validation error: {e}")
                continue
        return result

    def save_lesson(self, lesson_data: LessonCreate) -> LessonRead:
        """Create new lesson with package."""
        package_dict = lesson_data.package.model_dump()

        lesson_model = LessonModel(
            id=lesson_data.id,
            title=lesson_data.title,
            learner_level=lesson_data.learner_level,
            source_material=lesson_data.source_material,
            package=package_dict,
            package_version=lesson_data.package_version,
            flow_run_id=lesson_data.flow_run_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        saved_lesson = self.repo.save_lesson(lesson_model)

        # Return as DTO
        lesson_dict = {
            "id": saved_lesson.id,
            "title": saved_lesson.title,
            "learner_level": saved_lesson.learner_level,
            "unit_id": getattr(saved_lesson, "unit_id", None),
            "source_material": saved_lesson.source_material,
            "source_domain": getattr(saved_lesson, "source_domain", None),
            "source_level": getattr(saved_lesson, "source_level", None),
            "refined_material": getattr(saved_lesson, "refined_material", None),
            "package": lesson_data.package,  # Use original validated package
            "package_version": saved_lesson.package_version,
            "flow_run_id": saved_lesson.flow_run_id,
            "created_at": saved_lesson.created_at,
            "updated_at": saved_lesson.updated_at,
        }

        try:
            return LessonRead.model_validate(lesson_dict)
        except Exception as e:
            logger.error(f"❌ Failed to validate saved lesson {saved_lesson.id} ({saved_lesson.title}): {e}")
            raise

    def delete_lesson(self, lesson_id: str) -> bool:
        """Delete lesson by ID."""
        return self.repo.delete_lesson(lesson_id)

    def lesson_exists(self, lesson_id: str) -> bool:
        """Check if lesson exists."""
        return self.repo.lesson_exists(lesson_id)

    # ======================
    # Unit operations (moved)
    # ======================
    class UnitRead(BaseModel):
        id: str
        title: str
        description: str | None = None
        learner_level: str
        lesson_order: list[str]
        user_id: int | None = None
        is_global: bool = False
        # New fields
        learning_objectives: list[Any] | None = None
        target_lesson_count: int | None = None
        source_material: str | None = None
        generated_from_topic: bool = False
        flow_type: str = "standard"
        # Status tracking fields
        status: str = "completed"
        creation_progress: dict[str, Any] | None = None
        error_message: str | None = None
        created_at: datetime
        updated_at: datetime

        model_config = ConfigDict(from_attributes=True)

    class UnitLessonSummary(BaseModel):
        id: str
        title: str
        learner_level: str
        learning_objectives: list[str]
        key_concepts: list[str]
        exercise_count: int

    class UnitDetailRead(UnitRead):
        learning_objectives: list[str] | None = None
        lessons: list[ContentService.UnitLessonSummary]

        model_config = ConfigDict(from_attributes=True)

    class UnitCreate(BaseModel):
        id: str | None = None
        title: str
        description: str | None = None
        learner_level: str = "beginner"
        lesson_order: list[str] = []
        user_id: int | None = None
        is_global: bool = False
        learning_objectives: list[Any] | None = None
        target_lesson_count: int | None = None
        source_material: str | None = None
        generated_from_topic: bool = False
        flow_type: str = "standard"

    def get_unit(self, unit_id: str) -> ContentService.UnitRead | None:
        u = self.repo.get_unit_by_id(unit_id)
        return self.UnitRead.model_validate(u) if u else None

    def get_unit_detail(self, unit_id: str) -> ContentService.UnitDetailRead | None:
        unit = self.repo.get_unit_by_id(unit_id)
        if not unit:
            return None

        lesson_models = self.repo.get_lessons_by_unit(unit_id=unit_id)
        lesson_summaries: dict[str, ContentService.UnitLessonSummary] = {}

        for lesson in lesson_models:
            try:
                package = LessonPackage.model_validate(lesson.package)
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning(
                    "⚠️ Skipping lesson %s while building detail for unit %s due to package validation error: %s",
                    lesson.id,
                    unit.id,
                    exc,
                )
                continue

            objectives = [obj.text for obj in package.objectives]
            glossary_terms = package.glossary.get("terms", []) if package.glossary else []
            key_concepts: list[str] = []
            for term in glossary_terms:
                if hasattr(term, "term"):
                    key_concepts.append(str(term.term))
                elif isinstance(term, dict):
                    key_concepts.append(str(term.get("term") or term.get("label") or term))
                else:
                    key_concepts.append(str(term))

            summary = self.UnitLessonSummary(
                id=lesson.id,
                title=lesson.title,
                learner_level=lesson.learner_level,
                learning_objectives=objectives,
                key_concepts=key_concepts,
                exercise_count=len(package.exercises),
            )
            lesson_summaries[lesson.id] = summary

        ordered_ids = list(unit.lesson_order or [])
        ordered_lessons: list[ContentService.UnitLessonSummary] = []
        seen: set[str] = set()
        for lid in ordered_ids:
            summary = lesson_summaries.get(lid)
            if summary:
                ordered_lessons.append(summary)
                seen.add(lid)

        for lid, summary in lesson_summaries.items():
            if lid not in seen:
                ordered_lessons.append(summary)

        unit_summary = self.UnitRead.model_validate(unit)
        detail_dict = unit_summary.model_dump()
        detail_dict["lesson_order"] = ordered_ids
        detail_dict["lessons"] = [lesson.model_dump() for lesson in ordered_lessons]
        detail_dict["learning_objectives"] = self._normalize_unit_learning_objectives(getattr(unit, "learning_objectives", None))

        return self.UnitDetailRead.model_validate(detail_dict)

    def list_units(self, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]:
        arr = self.repo.list_units(limit=limit, offset=offset)
        return [self.UnitRead.model_validate(u) for u in arr]

    def list_units_for_user(self, user_id: int, *, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]:
        """Return units owned by a specific user."""
        arr = self.repo.list_units_for_user(user_id=user_id, limit=limit, offset=offset)
        return [self.UnitRead.model_validate(u) for u in arr]

    def list_global_units(self, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]:
        """Return units that have been shared globally."""
        arr = self.repo.list_global_units(limit=limit, offset=offset)
        return [self.UnitRead.model_validate(u) for u in arr]

    def get_units_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]:
        """Get units filtered by status."""
        arr = self.repo.get_units_by_status(status=status, limit=limit, offset=offset)
        return [self.UnitRead.model_validate(u) for u in arr]

    def update_unit_status(self, unit_id: str, status: str, error_message: str | None = None, creation_progress: dict[str, Any] | None = None) -> ContentService.UnitRead | None:
        """Update unit status and return the updated unit, or None if not found."""
        updated = self.repo.update_unit_status(unit_id=unit_id, status=status, error_message=error_message, creation_progress=creation_progress)
        return self.UnitRead.model_validate(updated) if updated else None

    def create_unit(self, data: ContentService.UnitCreate) -> ContentService.UnitRead:
        unit_id = data.id or str(uuid.uuid4())
        model = UnitModel(
            id=unit_id,
            title=data.title,
            description=data.description,
            learner_level=data.learner_level,
            lesson_order=list(data.lesson_order or []),
            user_id=data.user_id,
            is_global=bool(data.is_global),
            learning_objectives=list(data.learning_objectives or []) if data.learning_objectives is not None else None,
            target_lesson_count=data.target_lesson_count,
            source_material=data.source_material,
            generated_from_topic=bool(data.generated_from_topic),
            flow_type=str(getattr(data, "flow_type", "standard") or "standard"),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        created = self.repo.add_unit(model)
        return self.UnitRead.model_validate(created)

    def set_unit_lesson_order(self, unit_id: str, lesson_ids: list[str]) -> ContentService.UnitRead:
        updated = self.repo.update_unit_lesson_order(unit_id, lesson_ids)
        if not updated:
            raise ValueError("Unit not found")
        return self.UnitRead.model_validate(updated)

    def assign_unit_owner(self, unit_id: str, *, owner_user_id: int | None) -> ContentService.UnitRead:
        """Assign or clear ownership of a unit."""
        updated = self.repo.set_unit_owner(unit_id, owner_user_id)
        if not updated:
            raise ValueError("Unit not found")
        return self.UnitRead.model_validate(updated)

    @staticmethod
    def _normalize_unit_learning_objectives(raw: list[Any] | None) -> list[str] | None:
        if raw is None:
            return None

        normalized: list[str] = []
        for item in list(raw):
            try:
                if isinstance(item, str):
                    normalized.append(item)
                elif isinstance(item, dict):
                    text = item.get("text") or item.get("lo_text") or item.get("label")
                    normalized.append(str(text) if text else str(item))
                else:
                    text_attr = getattr(item, "text", None)
                    normalized.append(str(text_attr) if text_attr else str(item))
            except Exception:  # pragma: no cover - fall back to string conversion
                normalized.append(str(item))

        return normalized

    def set_unit_sharing(
        self,
        unit_id: str,
        *,
        is_global: bool,
        acting_user_id: int | None = None,
    ) -> ContentService.UnitRead:
        """Update whether a unit is shared globally, optionally enforcing ownership."""

        if acting_user_id is not None and not self.repo.is_unit_owned_by_user(unit_id, acting_user_id):
            raise PermissionError("User does not own this unit")

        updated = self.repo.set_unit_sharing(unit_id, is_global)
        if not updated:
            raise ValueError("Unit not found")
        return self.UnitRead.model_validate(updated)

    def assign_lessons_to_unit(self, unit_id: str, lesson_ids: list[str]) -> ContentService.UnitRead:
        """Assign lessons to a unit and set ordering in one operation.

        Skips lesson IDs that don't exist. Removes lessons previously in the unit
        if they are not in the provided list.
        """
        updated = self.repo.associate_lessons_with_unit(unit_id, lesson_ids)
        if not updated:
            raise ValueError("Unit not found")
        return self.UnitRead.model_validate(updated)

    def delete_unit(self, unit_id: str) -> bool:
        """Delete a unit by ID. Returns True if successful, False if not found."""
        return self.repo.delete_unit(unit_id)

    # ======================
    # Unit session operations
    # ======================
    class UnitSessionRead(BaseModel):
        id: str
        unit_id: str
        user_id: str
        status: str
        progress_percentage: float
        last_lesson_id: str | None = None
        completed_lesson_ids: list[str]
        started_at: datetime
        completed_at: datetime | None = None
        updated_at: datetime

        model_config = ConfigDict(from_attributes=True)

    def get_or_create_unit_session(self, user_id: str, unit_id: str) -> ContentService.UnitSessionRead:
        """Get existing unit session or create a new active one."""
        existing = self.repo.get_unit_session(user_id=user_id, unit_id=unit_id)
        if existing:
            return self.UnitSessionRead.model_validate(existing)

        from ..learning_session.models import UnitSessionModel  # noqa: PLC0415

        model = UnitSessionModel(
            id=str(uuid.uuid4()),
            unit_id=unit_id,
            user_id=user_id,
            status="active",
            progress_percentage=0.0,
            completed_lesson_ids=[],
            last_lesson_id=None,
            started_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        created = self.repo.add_unit_session(model)
        return self.UnitSessionRead.model_validate(created)

    def update_unit_session_progress(
        self,
        user_id: str,
        unit_id: str,
        *,
        last_lesson_id: str | None = None,
        completed_lesson_id: str | None = None,
        total_lessons: int | None = None,
        mark_completed: bool = False,
        progress_percentage: float | None = None,
    ) -> ContentService.UnitSessionRead:
        """Update progress for a unit session, creating one if needed."""
        model = self.repo.get_unit_session(user_id=user_id, unit_id=unit_id)
        if not model:
            from ..learning_session.models import UnitSessionModel  # noqa: PLC0415

            model = UnitSessionModel(
                id=str(uuid.uuid4()),
                unit_id=unit_id,
                user_id=user_id,
                status="active",
                progress_percentage=0.0,
                completed_lesson_ids=[],
                last_lesson_id=None,
                started_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            self.repo.add_unit_session(model)

        # Update fields
        if last_lesson_id:
            model.last_lesson_id = last_lesson_id
        if completed_lesson_id:
            existing = set(model.completed_lesson_ids or [])
            existing.add(completed_lesson_id)
            model.completed_lesson_ids = list(existing)

        # Compute progress if total provided
        if total_lessons is not None:
            completed_count = len(model.completed_lesson_ids or [])
            pct = (completed_count / total_lessons * 100) if total_lessons > 0 else 0.0
            model.progress_percentage = float(min(pct, 100.0))

        if progress_percentage is not None:
            model.progress_percentage = float(progress_percentage)

        if mark_completed:
            model.status = "completed"
            model.completed_at = datetime.now(UTC)

        model.updated_at = datetime.now(UTC)
        self.repo.save_unit_session(model)
        return self.UnitSessionRead.model_validate(model)
