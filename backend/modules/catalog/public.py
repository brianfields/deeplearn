"""
Lesson Catalog Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from modules.content.public import ContentProvider, content_provider
from modules.learning_session.public import LearningSessionAnalyticsProvider

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

    async def browse_lessons(self, learner_level: str | None = None, limit: int = 100) -> BrowseLessonsResponse: ...
    async def get_lesson_details(self, lesson_id: str) -> LessonDetail | None: ...
    async def browse_units(self, limit: int = 100, offset: int = 0) -> list[UnitSummary]: ...
    async def browse_units_for_user(
        self,
        user_id: int,
        *,
        include_global: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> UserUnitCollections: ...
    async def get_unit_details(self, unit_id: str) -> UnitDetail | None: ...
    async def search_lessons(
        self,
        query: str | None = None,
        learner_level: str | None = None,
        min_duration: int | None = None,
        max_duration: int | None = None,
        ready_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> SearchLessonsResponse: ...
    async def get_popular_lessons(self, limit: int = 10) -> list[LessonSummary]: ...
    async def get_catalog_statistics(self) -> CatalogStatistics: ...
    async def refresh_catalog(self) -> RefreshCatalogResponse: ...


def catalog_provider(
    session: AsyncSession,
    *,
    content: ContentProvider | None = None,
    units: ContentProvider | None = None,
    learning_sessions: LearningSessionAnalyticsProvider | None = None,
) -> CatalogProvider:
    """
    Dependency injection provider for lesson catalog services.

    Args:
        session: Database session shared across module providers.
        content: Optional content service instance. When not provided, a new
            instance is created using the supplied session.
        units: Optional units service instance. Defaults to the content service.

    Returns:
        CatalogService instance that implements the CatalogProvider protocol.
    """
    content_service = content or content_provider(session)
    units_service = units or content_service
    return CatalogService(content_service, units_service, learning_sessions)


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
