"""
Lesson Catalog Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Protocol

from modules.content.public import ContentProvider
from modules.learning_session.repo import LearningSessionRepo

from .service import (
    BrowseLessonsResponse,
    CatalogService,
    CatalogStatistics,
    LessonDetail,
    LessonSummary,
    RefreshCatalogResponse,
    SearchLessonsResponse,
    UnitDetail,
    UnitSummary,
    UserUnitCollections,
)


class CatalogProvider(Protocol):
    """Protocol defining the lesson catalog module's public interface."""

    def browse_lessons(self, learner_level: str | None = None, limit: int = 100) -> BrowseLessonsResponse: ...
    def get_lesson_details(self, lesson_id: str) -> LessonDetail | None: ...
    def browse_units(self, limit: int = 100, offset: int = 0) -> list[UnitSummary]: ...
    def browse_units_for_user(
        self,
        user_id: int,
        *,
        include_global: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> UserUnitCollections: ...
    def get_unit_details(self, unit_id: str) -> UnitDetail | None: ...
    def search_lessons(
        self,
        query: str | None = None,
        learner_level: str | None = None,
        min_duration: int | None = None,
        max_duration: int | None = None,
        ready_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> SearchLessonsResponse: ...
    def get_popular_lessons(self, limit: int = 10) -> list[LessonSummary]: ...
    def get_catalog_statistics(self) -> CatalogStatistics: ...
    def refresh_catalog(self) -> RefreshCatalogResponse: ...


def catalog_provider(
    content: ContentProvider,
    units: ContentProvider,
    learning_sessions: LearningSessionRepo | None = None,
) -> CatalogProvider:
    """
    Dependency injection provider for lesson catalog services.

    Args:
        content: Content service instance (built with same session as caller).
        units: Units service instance (built with same session as caller).

    Returns:
        CatalogService instance that implements the CatalogProvider protocol.
    """
    return CatalogService(content, units, learning_sessions)


__all__ = [
    "BrowseLessonsResponse",
    "CatalogProvider",
    "CatalogStatistics",
    "LessonDetail",
    "LessonSummary",
    "RefreshCatalogResponse",
    "SearchLessonsResponse",
    "UnitDetail",
    "UnitSummary",
    "UserUnitCollections",
    "catalog_provider",
]
