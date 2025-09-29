"""
Content Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Any, Protocol

from sqlalchemy.orm import Session

from .repo import ContentRepo
from .service import (
    ContentService,
    LessonCreate,
    LessonRead,
    UnitStatus,
)
from ..llm_services.public import llm_services_provider


class ContentProvider(Protocol):
    """Protocol defining the content module's public interface."""

    def get_lesson(self, lesson_id: str) -> LessonRead | None: ...
    def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonRead]: ...
    def search_lessons(self, query: str | None = None, learner_level: str | None = None, limit: int = 100, offset: int = 0) -> list[LessonRead]: ...
    def save_lesson(self, lesson_data: LessonCreate) -> LessonRead: ...
    def delete_lesson(self, lesson_id: str) -> bool: ...
    def lesson_exists(self, lesson_id: str) -> bool: ...
    # New unit-related method (do not change existing signatures)
    def get_lessons_by_unit(self, unit_id: str, limit: int = 100, offset: int = 0) -> list[LessonRead]: ...
    # Unit operations (consolidated)
    def get_unit(self, unit_id: str) -> ContentService.UnitRead | None: ...
    def get_unit_detail(self, unit_id: str) -> ContentService.UnitDetailRead | None: ...
    def list_units(self, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]: ...
    def list_units_for_user(self, user_id: int, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]: ...
    def list_global_units(self, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]: ...
    def get_units_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]: ...
    def update_unit_status(self, unit_id: str, status: str, error_message: str | None = None, creation_progress: dict[str, Any] | None = None) -> ContentService.UnitRead | None: ...
    async def create_unit(self, data: ContentService.UnitCreate) -> ContentService.UnitRead: ...
    def set_unit_lesson_order(self, unit_id: str, lesson_ids: list[str]) -> ContentService.UnitRead: ...
    def assign_lessons_to_unit(self, unit_id: str, lesson_ids: list[str]) -> ContentService.UnitRead: ...
    def assign_unit_owner(self, unit_id: str, owner_user_id: int | None) -> ContentService.UnitRead: ...
    def set_unit_sharing(self, unit_id: str, is_global: bool, acting_user_id: int | None = None) -> ContentService.UnitRead: ...
    def delete_unit(self, unit_id: str) -> bool: ...
    # Unit session operations
    def get_or_create_unit_session(self, user_id: str, unit_id: str) -> ContentService.UnitSessionRead: ...
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
    ) -> ContentService.UnitSessionRead: ...


def content_provider(session: Session) -> ContentProvider:
    """
    Dependency injection provider for content services.

    Args:
        session: Database session managed at the route level for proper commits.

    Returns:
        ContentService instance that implements the ContentProvider protocol.
    """
    return ContentService(ContentRepo(session), llm_services_provider(session))


# Create aliases for nested classes to maintain backward compatibility
UnitCreate = ContentService.UnitCreate
UnitRead = ContentService.UnitRead
UnitDetailRead = ContentService.UnitDetailRead
UnitSessionRead = ContentService.UnitSessionRead

__all__ = [
    "ContentProvider",
    "LessonCreate",
    "LessonRead",
    "UnitCreate",
    "UnitDetailRead",
    "UnitRead",
    "UnitSessionRead",
    "UnitStatus",
    "content_provider",
]
