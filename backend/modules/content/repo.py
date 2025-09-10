"""
Content Module - Repository Layer

Database access layer that returns ORM objects.
Handles all CRUD operations for lessons and lesson components.
"""

from modules.infrastructure.public import DatabaseSession

from .models import LessonComponentModel, LessonModel


class ContentRepo:
    """Repository for content data access operations."""

    def __init__(self, session: DatabaseSession):
        """Initialize repository with database session."""
        self.s = session.session

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

    # Lesson component operations
    def get_component_by_id(self, component_id: str) -> LessonComponentModel | None:
        """Get lesson component by ID."""
        return self.s.get(LessonComponentModel, component_id)

    def get_components_by_lesson_id(self, lesson_id: str) -> list[LessonComponentModel]:
        """Get all components for a lesson."""
        return self.s.query(LessonComponentModel).filter(LessonComponentModel.lesson_id == lesson_id).all()

    def save_component(self, component: LessonComponentModel) -> LessonComponentModel:
        """Save lesson component to database."""
        self.s.add(component)
        self.s.flush()
        return component

    def delete_component(self, component_id: str) -> bool:
        """Delete lesson component by ID."""
        component = self.get_component_by_id(component_id)
        if component:
            self.s.delete(component)
            return True
        return False
