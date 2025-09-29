"""
Lesson Catalog Module - HTTP Routes

HTTP API for lesson browsing and discovery.
"""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from modules.content.public import content_provider
from modules.infrastructure.public import infrastructure_provider
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
)

router = APIRouter(prefix="/api/v1/catalog")


def get_session() -> Generator[Session, None, None]:
    """Request-scoped database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as s:
        yield s


def get_catalog_service(s: Session = Depends(get_session)) -> CatalogService:
    """Build CatalogService for this request."""
    content_service = content_provider(s)
    units_via_content = content_service  # Units are consolidated in content provider
    learning_sessions = LearningSessionRepo(s)
    return CatalogService(content_service, units_via_content, learning_sessions)


@router.get("/", response_model=BrowseLessonsResponse)
def browse_lessons(
    learner_level: str | None = Query(None, description="Filter by learner level (beginner, intermediate, advanced)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of lessons to return"),
    catalog: CatalogService = Depends(get_catalog_service),
) -> BrowseLessonsResponse:
    """
    Browse lessons with optional user level filter.

    Returns a list of lesson summaries for browsing.
    """
    return catalog.browse_lessons(learner_level=learner_level, limit=limit)


@router.get("/search", response_model=SearchLessonsResponse)
def search_lessons(
    query: str | None = Query(None, description="Search query string"),
    learner_level: str | None = Query(None, description="Filter by learner level (beginner, intermediate, advanced)"),
    min_duration: int | None = Query(None, ge=1, description="Minimum duration in minutes"),
    max_duration: int | None = Query(None, ge=1, description="Maximum duration in minutes"),
    ready_only: bool = Query(False, description="Only return ready lessons"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of lessons to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    catalog: CatalogService = Depends(get_catalog_service),
) -> SearchLessonsResponse:
    """
    Search lessons with query and filters.
    """
    return catalog.search_lessons(
        query=query,
        learner_level=learner_level,
        min_duration=min_duration,
        max_duration=max_duration,
        ready_only=ready_only,
        limit=limit,
        offset=offset,
    )


@router.get("/popular", response_model=list[LessonSummary])
def get_popular_lessons(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of lessons to return"),
    catalog: CatalogService = Depends(get_catalog_service),
) -> list[LessonSummary]:
    """
    Get popular lessons.

    Returns lessons ordered by popularity (currently just first N lessons).
    """
    return catalog.get_popular_lessons(limit=limit)


@router.get("/statistics", response_model=CatalogStatistics)
def get_catalog_statistics(
    catalog: CatalogService = Depends(get_catalog_service),
) -> CatalogStatistics:
    """
    Get catalog statistics.

    Returns statistics about lessons, user levels, readiness, and duration distribution.
    """
    return catalog.get_catalog_statistics()


@router.post("/refresh", response_model=RefreshCatalogResponse)
def refresh_catalog(
    catalog: CatalogService = Depends(get_catalog_service),
) -> RefreshCatalogResponse:
    """
    Refresh the catalog.

    Triggers a refresh of lesson data (placeholder implementation).
    """
    return catalog.refresh_catalog()


@router.get("/units", response_model=list[UnitSummary])
def browse_units(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    catalog: CatalogService = Depends(get_catalog_service),
) -> list[UnitSummary]:
    """Browse learning units with simple metadata and lesson counts."""
    return catalog.browse_units(limit=limit, offset=offset)


@router.get("/units/{unit_id}", response_model=UnitDetail)
def get_unit_details(unit_id: str, catalog: CatalogService = Depends(get_catalog_service)) -> UnitDetail:
    """Get unit details with ordered aggregated lesson summaries."""
    unit = catalog.get_unit_details(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.get("/{lesson_id}", response_model=LessonDetail)
def get_lesson_details(lesson_id: str, catalog: CatalogService = Depends(get_catalog_service)) -> LessonDetail:
    """
    Get detailed information about a specific lesson.

    Includes package-aligned content and metadata for learning.
    """
    lesson = catalog.get_lesson_details(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson
