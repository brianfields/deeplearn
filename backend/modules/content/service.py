"""
Content Module - Service Layer

Business logic layer that returns DTOs (Pydantic models).
Handles content operations and data transformation.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict

from .models import LessonComponentModel, LessonModel
from .repo import ContentRepo


# DTOs (Data Transfer Objects)
class LessonComponentRead(BaseModel):
    """DTO for reading lesson component data."""

    id: str
    lesson_id: str
    component_type: str
    title: str
    content: dict
    learning_objective: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LessonRead(BaseModel):
    """DTO for reading lesson data."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict | None = None
    created_at: datetime
    updated_at: datetime
    components: list[LessonComponentRead] = []

    model_config = ConfigDict(from_attributes=True)


class LessonCreate(BaseModel):
    """DTO for creating new lessons."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict | None = None


class LessonComponentCreate(BaseModel):
    """DTO for creating new lesson components."""

    id: str
    lesson_id: str
    component_type: str
    title: str
    content: dict
    learning_objective: str | None = None


class ContentService:
    """Service for content operations."""

    def __init__(self, repo: ContentRepo):
        """Initialize service with repository."""
        self.repo = repo

    # Lesson operations
    def get_lesson(self, lesson_id: str) -> LessonRead | None:
        """Get lesson with components by ID."""
        lesson = self.repo.get_lesson_by_id(lesson_id)
        if not lesson:
            return None

        # Load components
        components = self.repo.get_components_by_lesson_id(lesson_id)

        # Convert to DTO
        lesson_dict = {
            "id": lesson.id,
            "title": lesson.title,
            "core_concept": lesson.core_concept,
            "user_level": lesson.user_level,
            "learning_objectives": lesson.learning_objectives,
            "key_concepts": lesson.key_concepts,
            "source_material": lesson.source_material,
            "source_domain": lesson.source_domain,
            "source_level": lesson.source_level,
            "refined_material": lesson.refined_material,
            "created_at": lesson.created_at,
            "updated_at": lesson.updated_at,
            "components": [LessonComponentRead.model_validate(c) for c in components],
        }

        return LessonRead.model_validate(lesson_dict)

    def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonRead]:
        """Get all lessons with components."""
        lessons = self.repo.get_all_lessons(limit, offset)
        result = []

        for lesson in lessons:
            components = self.repo.get_components_by_lesson_id(lesson.id)
            lesson_dict = {
                "id": lesson.id,
                "title": lesson.title,
                "core_concept": lesson.core_concept,
                "user_level": lesson.user_level,
                "learning_objectives": lesson.learning_objectives,
                "key_concepts": lesson.key_concepts,
                "source_material": lesson.source_material,
                "source_domain": lesson.source_domain,
                "source_level": lesson.source_level,
                "refined_material": lesson.refined_material,
                "created_at": lesson.created_at,
                "updated_at": lesson.updated_at,
                "components": [LessonComponentRead.model_validate(c) for c in components],
            }
            result.append(LessonRead.model_validate(lesson_dict))

        return result

    def search_lessons(self, query: str | None = None, user_level: str | None = None, limit: int = 100, offset: int = 0) -> list[LessonRead]:
        """Search lessons with optional filters."""
        lessons = self.repo.search_lessons(query, user_level, limit, offset)
        result = []

        for lesson in lessons:
            components = self.repo.get_components_by_lesson_id(lesson.id)
            lesson_dict = {
                "id": lesson.id,
                "title": lesson.title,
                "core_concept": lesson.core_concept,
                "user_level": lesson.user_level,
                "learning_objectives": lesson.learning_objectives,
                "key_concepts": lesson.key_concepts,
                "source_material": lesson.source_material,
                "source_domain": lesson.source_domain,
                "source_level": lesson.source_level,
                "refined_material": lesson.refined_material,
                "created_at": lesson.created_at,
                "updated_at": lesson.updated_at,
                "components": [LessonComponentRead.model_validate(c) for c in components],
            }
            result.append(LessonRead.model_validate(lesson_dict))

        return result

    def save_lesson(self, lesson_data: LessonCreate) -> LessonRead:
        """Create new lesson."""
        lesson_model = LessonModel(
            id=lesson_data.id,
            title=lesson_data.title,
            core_concept=lesson_data.core_concept,
            user_level=lesson_data.user_level,
            learning_objectives=lesson_data.learning_objectives,
            key_concepts=lesson_data.key_concepts,
            source_material=lesson_data.source_material,
            source_domain=lesson_data.source_domain,
            source_level=lesson_data.source_level,
            refined_material=lesson_data.refined_material or {},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        saved_lesson = self.repo.save_lesson(lesson_model)

        # Return as DTO with empty components list
        lesson_dict = {
            "id": saved_lesson.id,
            "title": saved_lesson.title,
            "core_concept": saved_lesson.core_concept,
            "user_level": saved_lesson.user_level,
            "learning_objectives": saved_lesson.learning_objectives,
            "key_concepts": saved_lesson.key_concepts,
            "source_material": saved_lesson.source_material,
            "source_domain": saved_lesson.source_domain,
            "source_level": saved_lesson.source_level,
            "refined_material": saved_lesson.refined_material,
            "created_at": saved_lesson.created_at,
            "updated_at": saved_lesson.updated_at,
            "components": [],
        }

        return LessonRead.model_validate(lesson_dict)

    def delete_lesson(self, lesson_id: str) -> bool:
        """Delete lesson by ID."""
        return self.repo.delete_lesson(lesson_id)

    def lesson_exists(self, lesson_id: str) -> bool:
        """Check if lesson exists."""
        return self.repo.lesson_exists(lesson_id)

    # Lesson component operations
    def get_lesson_component(self, component_id: str) -> LessonComponentRead | None:
        """Get lesson component by ID."""
        component = self.repo.get_component_by_id(component_id)
        return LessonComponentRead.model_validate(component) if component else None

    def get_components_by_lesson(self, lesson_id: str) -> list[LessonComponentRead]:
        """Get all components for a lesson."""
        components = self.repo.get_components_by_lesson_id(lesson_id)
        return [LessonComponentRead.model_validate(c) for c in components]

    def save_lesson_component(self, component_data: LessonComponentCreate) -> LessonComponentRead:
        """Create new lesson component."""
        component_model = LessonComponentModel(
            id=component_data.id,
            lesson_id=component_data.lesson_id,
            component_type=component_data.component_type,
            title=component_data.title,
            content=component_data.content,
            learning_objective=component_data.learning_objective,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        saved_component = self.repo.save_component(component_model)
        return LessonComponentRead.model_validate(saved_component)

    def delete_lesson_component(self, component_id: str) -> bool:
        """Delete lesson component by ID."""
        return self.repo.delete_component(component_id)
