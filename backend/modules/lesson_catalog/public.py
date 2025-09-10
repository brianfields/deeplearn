"""
Lesson Catalog Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Protocol

from modules.content.public import ContentProvider

from .service import (
    BrowseLessonsResponse,
    CatalogStatistics,
    LessonCatalogService,
    LessonDetail,
    LessonSummary,
    RefreshCatalogResponse,
    SearchLessonsResponse,
)


class LessonCatalogProvider(Protocol):
    """Protocol defining the lesson catalog module's public interface."""

    def browse_lessons(self, user_level: str | None = None, limit: int = 100) -> BrowseLessonsResponse: ...
    def get_lesson_details(self, lesson_id: str) -> LessonDetail | None: ...
    def search_lessons(
        self,
        query: str | None = None,
        user_level: str | None = None,
        min_duration: int | None = None,
        max_duration: int | None = None,
        ready_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> SearchLessonsResponse: ...
    def get_popular_lessons(self, limit: int = 10) -> list[LessonSummary]: ...
    def get_catalog_statistics(self) -> CatalogStatistics: ...
    def refresh_catalog(self) -> RefreshCatalogResponse: ...


def lesson_catalog_provider(content: ContentProvider) -> LessonCatalogProvider:
    """
    Dependency injection provider for lesson catalog services.

    Args:
        content: Content service instance (built with same session as caller).

    Returns:
        LessonCatalogService instance that implements the LessonCatalogProvider protocol.
    """
    return LessonCatalogService(content)


__all__ = [
    "BrowseLessonsResponse",
    "CatalogStatistics",
    "LessonCatalogProvider",
    "LessonDetail",
    "LessonSummary",
    "RefreshCatalogResponse",
    "SearchLessonsResponse",
    "lesson_catalog_provider",
]
