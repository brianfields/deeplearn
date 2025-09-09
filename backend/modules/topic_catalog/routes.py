"""
Topic Catalog Module - HTTP Routes

HTTP API for topic browsing and discovery.
"""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from modules.content.public import content_provider
from modules.infrastructure.public import infrastructure_provider
from modules.topic_catalog.public import TopicCatalogProvider, topic_catalog_provider

from .service import (
    BrowseTopicsResponse,
    CatalogStatistics,
    RefreshCatalogResponse,
    SearchTopicsResponse,
    TopicDetail,
    TopicSummary,
)

router = APIRouter(prefix="/api/v1/topics")


def get_session() -> Generator[Session, None, None]:
    """Request-scoped database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as s:
        yield s


def get_topic_catalog_service(s: Session = Depends(get_session)) -> TopicCatalogProvider:
    """Build TopicCatalogService for this request."""
    content_service = content_provider(s)
    return topic_catalog_provider(content_service)


@router.get("/", response_model=BrowseTopicsResponse)
def browse_topics(
    user_level: str | None = Query(None, description="Filter by user level (beginner, intermediate, advanced)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of topics to return"),
    catalog: TopicCatalogProvider = Depends(get_topic_catalog_service),
) -> BrowseTopicsResponse:
    """
    Browse topics with optional user level filter.

    Returns a list of topic summaries for browsing.
    """
    try:
        return catalog.browse_topics(user_level=user_level, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to browse topics") from e


@router.get("/{topic_id}", response_model=TopicDetail)
def get_topic_details(topic_id: str, catalog: TopicCatalogService = Depends(get_topic_catalog_service)) -> TopicDetail:
    """
    Get detailed information about a specific topic.

    Includes all components and metadata for learning.
    """
    try:
        topic = catalog.get_topic_details(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        return topic
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get topic details") from e


@router.get("/search", response_model=SearchTopicsResponse)
def search_topics(
    query: str | None = Query(None, description="Search query string"),
    user_level: str | None = Query(None, description="Filter by user level (beginner, intermediate, advanced)"),
    min_duration: int | None = Query(None, ge=1, description="Minimum duration in minutes"),
    max_duration: int | None = Query(None, ge=1, description="Maximum duration in minutes"),
    ready_only: bool = Query(False, description="Only return ready topics"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of topics to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    catalog: TopicCatalogProvider = Depends(get_topic_catalog_service),
) -> SearchTopicsResponse:
    """
    Search topics with query and filters.

    Supports text search across title, core concept, learning objectives, and key concepts.
    """
    try:
        return catalog.search_topics(
            query=query,
            user_level=user_level,
            min_duration=min_duration,
            max_duration=max_duration,
            ready_only=ready_only,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to search topics") from e


@router.get("/popular", response_model=list[TopicSummary])
def get_popular_topics(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of topics to return"),
    catalog: TopicCatalogProvider = Depends(get_topic_catalog_service),
) -> list[TopicSummary]:
    """
    Get popular topics.

    Returns topics ordered by popularity (currently just first N topics).
    """
    try:
        return catalog.get_popular_topics(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get popular topics") from e


@router.get("/statistics", response_model=CatalogStatistics)
def get_catalog_statistics(
    catalog: TopicCatalogProvider = Depends(get_topic_catalog_service),
) -> CatalogStatistics:
    """
    Get catalog statistics.

    Returns statistics about topics, user levels, readiness, and duration distribution.
    """
    try:
        return catalog.get_catalog_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get catalog statistics") from e


@router.post("/refresh", response_model=RefreshCatalogResponse)
def refresh_catalog(
    catalog: TopicCatalogProvider = Depends(get_topic_catalog_service),
) -> RefreshCatalogResponse:
    """
    Refresh the catalog.

    Triggers a refresh of topic data (placeholder implementation).
    """
    try:
        return catalog.refresh_catalog()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to refresh catalog") from e
