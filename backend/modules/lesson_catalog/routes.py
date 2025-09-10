"""
Lesson Catalog Module - HTTP Routes

HTTP API for lesson browsing and discovery.
"""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from modules.content.public import content_provider
from modules.infrastructure.public import infrastructure_provider

from .service import (
    BrowseLessonsResponse,
    CatalogStatistics,
    LessonCatalogService,
    LessonDetail,
    LessonSummary,
    RefreshCatalogResponse,
    SearchLessonsResponse,
)

router = APIRouter(prefix="/api/v1/lessons")


def get_session() -> Generator[Session, None, None]:
    """Request-scoped database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as s:
        yield s


def get_lesson_catalog_service(s: Session = Depends(get_session)) -> LessonCatalogService:
    """Build LessonCatalogService for this request."""
    content_service = content_provider(s)
    return LessonCatalogService(content_service)


@router.get("/", response_model=BrowseLessonsResponse)
def browse_lessons(
    user_level: str | None = Query(None, description="Filter by user level (beginner, intermediate, advanced)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of lessons to return"),
    catalog: LessonCatalogService = Depends(get_lesson_catalog_service),
) -> BrowseLessonsResponse:
    """
    Browse lessons with optional user level filter.

    Returns a list of lesson summaries for browsing.
    """
    try:
        return catalog.browse_lessons(user_level=user_level, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to browse lessons") from e


@router.get("/{lesson_id}", response_model=LessonDetail)
def get_lesson_details(lesson_id: str, catalog: LessonCatalogService = Depends(get_lesson_catalog_service)) -> LessonDetail:
    """
    Get detailed information about a specific lesson.

    Includes all components and metadata for learning.
    """
    try:
        lesson = catalog.get_lesson_details(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return lesson
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get lesson details") from e


@router.get("/search", response_model=SearchLessonsResponse)
def search_lessons(
    query: str | None = Query(None, description="Search query string"),
    user_level: str | None = Query(None, description="Filter by user level (beginner, intermediate, advanced)"),
    min_duration: int | None = Query(None, ge=1, description="Minimum duration in minutes"),
    max_duration: int | None = Query(None, ge=1, description="Maximum duration in minutes"),
    ready_only: bool = Query(False, description="Only return ready lessons"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of lessons to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    catalog: LessonCatalogService = Depends(get_lesson_catalog_service),
) -> SearchLessonsResponse:
    """
    Search lessons with query and filters.

    Supports text search across title, core concept, learning objectives, and key concepts.
    """
    try:
        return catalog.search_lessons(
            query=query,
            user_level=user_level,
            min_duration=min_duration,
            max_duration=max_duration,
            ready_only=ready_only,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to search lessons") from e


@router.get("/popular", response_model=list[LessonSummary])
def get_popular_lessons(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of lessons to return"),
    catalog: LessonCatalogService = Depends(get_lesson_catalog_service),
) -> list[LessonSummary]:
    """
    Get popular lessons.

    Returns lessons ordered by popularity (currently just first N lessons).
    """
    try:
        return catalog.get_popular_lessons(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get popular lessons") from e


@router.get("/statistics", response_model=CatalogStatistics)
def get_catalog_statistics(
    catalog: LessonCatalogService = Depends(get_lesson_catalog_service),
) -> CatalogStatistics:
    """
    Get catalog statistics.

    Returns statistics about lessons, user levels, readiness, and duration distribution.
    """
    try:
        return catalog.get_catalog_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get catalog statistics") from e


@router.post("/refresh", response_model=RefreshCatalogResponse)
def refresh_catalog(
    catalog: LessonCatalogService = Depends(get_lesson_catalog_service),
) -> RefreshCatalogResponse:
    """
    Refresh the catalog.

    Triggers a refresh of lesson data (placeholder implementation).
    """
    try:
        return catalog.refresh_catalog()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to refresh catalog") from e
