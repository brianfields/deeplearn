"""
Content Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Protocol

from sqlalchemy.orm import Session

from modules.infrastructure.public import DatabaseSession

from .repo import ContentRepo
from .service import ContentService, LessonCreate, LessonRead


class ContentProvider(Protocol):
    """Protocol defining the content module's public interface."""

    def get_lesson(self, lesson_id: str) -> LessonRead | None: ...
    def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonRead]: ...
    def search_lessons(self, query: str | None = None, user_level: str | None = None, limit: int = 100, offset: int = 0) -> list[LessonRead]: ...
    def save_lesson(self, lesson_data: LessonCreate) -> LessonRead: ...
    def delete_lesson(self, lesson_id: str) -> bool: ...
    def lesson_exists(self, lesson_id: str) -> bool: ...


def content_provider(session: Session) -> ContentProvider:
    """
    Dependency injection provider for content services.

    Args:
        session: Database session managed at the route level for proper commits.

    Returns:
        ContentService instance that implements the ContentProvider protocol.
    """
    return ContentService(ContentRepo(DatabaseSession(session=session, connection_id="api")))


__all__ = ["ContentProvider", "LessonCreate", "LessonRead", "content_provider"]
