from __future__ import annotations

"""
Content Module - Service Layer

Business logic layer that returns DTOs (Pydantic models).
Handles content operations and data transformation.
"""

from datetime import UTC, datetime
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


# DTOs (Data Transfer Objects)
class LessonRead(BaseModel):
    """DTO for reading lesson data with embedded package."""

    id: str
    title: str
    core_concept: str
    user_level: str
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
    core_concept: str
    user_level: str
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
            # Convert package JSON to LessonPackage model for validation
            package = LessonPackage.model_validate(lesson.package)

            # Create lesson dict for DTO conversion
            lesson_dict = {
                "id": lesson.id,
                "title": lesson.title,
                "core_concept": lesson.core_concept,
                "user_level": lesson.user_level,
                "unit_id": getattr(lesson, "unit_id", None),
                "source_material": lesson.source_material,
                "source_domain": lesson.source_domain,
                "source_level": lesson.source_level,
                "refined_material": lesson.refined_material,
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
                # Convert package JSON to LessonPackage model for validation
                package = LessonPackage.model_validate(lesson.package)

                lesson_dict = {
                    "id": lesson.id,
                    "title": lesson.title,
                    "core_concept": lesson.core_concept,
                    "user_level": lesson.user_level,
                    "unit_id": getattr(lesson, "unit_id", None),
                    "source_material": lesson.source_material,
                    "source_domain": lesson.source_domain,
                    "source_level": lesson.source_level,
                    "refined_material": lesson.refined_material,
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

    def search_lessons(self, query: str | None = None, user_level: str | None = None, limit: int = 100, offset: int = 0) -> list[LessonRead]:
        """Search lessons with optional filters."""
        lessons = self.repo.search_lessons(query, user_level, limit, offset)
        result = []

        for lesson in lessons:
            try:
                # Convert package JSON to LessonPackage model for validation
                package = LessonPackage.model_validate(lesson.package)

                lesson_dict = {
                    "id": lesson.id,
                    "title": lesson.title,
                    "core_concept": lesson.core_concept,
                    "user_level": lesson.user_level,
                    "unit_id": getattr(lesson, "unit_id", None),
                    "source_material": lesson.source_material,
                    "source_domain": lesson.source_domain,
                    "source_level": lesson.source_level,
                    "refined_material": lesson.refined_material,
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
                    "core_concept": lesson.core_concept,
                    "user_level": lesson.user_level,
                    "source_material": lesson.source_material,
                    "source_domain": lesson.source_domain,
                    "source_level": lesson.source_level,
                    "refined_material": lesson.refined_material,
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
        # Validate package before saving
        package_dict = lesson_data.package.model_dump()

        lesson_model = LessonModel(
            id=lesson_data.id,
            title=lesson_data.title,
            core_concept=lesson_data.core_concept,
            user_level=lesson_data.user_level,
            source_material=lesson_data.source_material,
            source_domain=lesson_data.source_domain,
            source_level=lesson_data.source_level,
            refined_material=lesson_data.refined_material or {},
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
            "core_concept": saved_lesson.core_concept,
            "user_level": saved_lesson.user_level,
            "unit_id": getattr(saved_lesson, "unit_id", None),
            "source_material": saved_lesson.source_material,
            "source_domain": saved_lesson.source_domain,
            "source_level": saved_lesson.source_level,
            "refined_material": saved_lesson.refined_material,
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
        difficulty: str
        lesson_order: list[str]
        # New fields
        learning_objectives: list[Any] | None = None
        target_lesson_count: int | None = None
        source_material: str | None = None
        generated_from_topic: bool = False
        flow_type: str = "standard"
        created_at: datetime
        updated_at: datetime

        model_config = ConfigDict(from_attributes=True)

    class UnitCreate(BaseModel):
        id: str | None = None
        title: str
        description: str | None = None
        difficulty: str = "beginner"
        lesson_order: list[str] = []
        learning_objectives: list[Any] | None = None
        target_lesson_count: int | None = None
        source_material: str | None = None
        generated_from_topic: bool = False
        flow_type: str = "standard"

    # New DTOs for unit creation workflows
    class UnitCreateFromTopic(BaseModel):
        topic: str
        target_lesson_count: int | None = None
        user_level: str = "beginner"
        domain: str | None = None

    class UnitCreateFromSource(BaseModel):
        title: str
        source_material: str
        target_lesson_count: int | None = None
        user_level: str = "beginner"
        domain: str | None = None

    def get_unit(self, unit_id: str) -> ContentService.UnitRead | None:
        u = self.repo.get_unit_by_id(unit_id)
        return self.UnitRead.model_validate(u) if u else None

    def list_units(self, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]:
        arr = self.repo.list_units(limit=limit, offset=offset)
        return [self.UnitRead.model_validate(u) for u in arr]

    def create_unit(self, data: ContentService.UnitCreate) -> ContentService.UnitRead:
        unit_id = data.id or str(uuid.uuid4())
        model = UnitModel(
            id=unit_id,
            title=data.title,
            description=data.description,
            difficulty=data.difficulty,
            lesson_order=list(data.lesson_order or []),
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

    def assign_lessons_to_unit(self, unit_id: str, lesson_ids: list[str]) -> ContentService.UnitRead:
        """Assign lessons to a unit and set ordering in one operation.

        Skips lesson IDs that don't exist. Removes lessons previously in the unit
        if they are not in the provided list.
        """
        updated = self.repo.associate_lessons_with_unit(unit_id, lesson_ids)
        if not updated:
            raise ValueError("Unit not found")
        return self.UnitRead.model_validate(updated)

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
