"""
Content Module - Service Layer

Business logic layer that returns DTOs (Pydantic models).
Handles content operations and data transformation.
"""

from datetime import UTC, datetime
import logging

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

from .models import LessonModel
from .package_models import LessonPackage
from .repo import ContentRepo


# DTOs (Data Transfer Objects)
class LessonRead(BaseModel):
    """DTO for reading lesson data with embedded package."""

    id: str
    title: str
    core_concept: str
    user_level: str
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict | None = None
    package: LessonPackage
    package_version: int
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
    refined_material: dict | None = None
    package: LessonPackage
    package_version: int = 1


class ContentService:
    """Service for content operations."""

    def __init__(self, repo: ContentRepo):
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
                "source_material": lesson.source_material,
                "source_domain": lesson.source_domain,
                "source_level": lesson.source_level,
                "refined_material": lesson.refined_material,
                "package": package,
                "package_version": lesson.package_version,
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
                    "source_material": lesson.source_material,
                    "source_domain": lesson.source_domain,
                    "source_level": lesson.source_level,
                    "refined_material": lesson.refined_material,
                    "package": package,
                    "package_version": lesson.package_version,
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
                    "source_material": lesson.source_material,
                    "source_domain": lesson.source_domain,
                    "source_level": lesson.source_level,
                    "refined_material": lesson.refined_material,
                    "package": package,
                    "package_version": lesson.package_version,
                    "created_at": lesson.created_at,
                    "updated_at": lesson.updated_at,
                }

                result.append(LessonRead.model_validate(lesson_dict))
            except Exception as e:
                logger.warning(f"⚠️ Skipping lesson {lesson.id} ({lesson.title}) due to data validation error: {e}")
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
            "source_material": saved_lesson.source_material,
            "source_domain": saved_lesson.source_domain,
            "source_level": saved_lesson.source_level,
            "refined_material": saved_lesson.refined_material,
            "package": lesson_data.package,  # Use original validated package
            "package_version": saved_lesson.package_version,
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
