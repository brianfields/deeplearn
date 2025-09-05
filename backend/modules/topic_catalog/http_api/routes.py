"""
HTTP API routes for Topic Catalog module.

This module provides thin HTTP routes that delegate to the service layer.
Routes handle only HTTP concerns (request/response, status codes, etc.).
"""

from datetime import UTC, datetime
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..module_api import (
    BrowseTopicsRequest,
    BrowseTopicsResponse,
    GetRecommendationsRequest,
    GetRecommendationsResponse,
    ModuleHealthResponse,
    SearchSuggestionsRequest,
    SearchSuggestionsResponse,
    SearchTopicsRequest,
    SearchTopicsResponse,
    TopicCatalogError,
    TopicCatalogService,
    TopicCatalogStatsResponse,
    TopicSummaryResponse,
)

logger = logging.getLogger(__name__)

# Create router for topic catalog endpoints
router = APIRouter(prefix="/api/catalog", tags=["topic-catalog"])


# Dependency injection placeholder - will be configured by main app
async def get_topic_catalog_service() -> TopicCatalogService:
    """
    Dependency to get topic catalog service.

    This should be configured by the main application with proper
    repository and dependencies.
    """
    raise HTTPException(status_code=500, detail="Topic catalog service not configured")


@router.get("/topics", response_model=SearchTopicsResponse)
async def search_topics(
    query: str | None = Query(default=None, description="Search query"),
    user_level: str | None = Query(default=None, description="Filter by user level"),
    min_duration: int | None = Query(default=None, ge=0, description="Minimum duration in minutes"),
    max_duration: int | None = Query(default=None, ge=0, description="Maximum duration in minutes"),
    ready_only: bool | None = Query(default=None, description="Filter by readiness status"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    service: TopicCatalogService = Depends(get_topic_catalog_service),
) -> SearchTopicsResponse:
    """
    Search topics in the catalog.

    This endpoint provides comprehensive topic search with filtering,
    pagination, and relevance ranking.
    """
    try:
        logger.info(f"Searching topics: query='{query}', user_level={user_level}")

        request = SearchTopicsRequest(
            query=query,
            user_level=user_level,
            min_duration=min_duration,
            max_duration=max_duration,
            ready_only=ready_only,
            limit=limit,
            offset=offset,
        )

        response = await service.search_topics(request)
        logger.info(f"Successfully found {len(response.topics)} topics")
        return response

    except TopicCatalogError as e:
        logger.error(f"Topic catalog error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error searching topics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/topics/{topic_id}", response_model=TopicSummaryResponse)
async def get_topic(topic_id: str, service: TopicCatalogService = Depends(get_topic_catalog_service)) -> TopicSummaryResponse:
    """Get a specific topic by ID."""
    try:
        logger.info(f"Getting topic: {topic_id}")
        topic_response = await service.get_topic_by_id(topic_id)
        return topic_response

    except TopicCatalogError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"Topic catalog error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/browse", response_model=BrowseTopicsResponse)
async def browse_topics(
    user_level: str | None = Query(default=None, description="Filter by user level"),
    ready_only: bool = Query(default=True, description="Only include ready topics"),
    service: TopicCatalogService = Depends(get_topic_catalog_service),
) -> BrowseTopicsResponse:
    """
    Browse topics organized by categories.

    This endpoint provides a curated browsing experience with topics
    organized into meaningful categories for discovery.
    """
    try:
        logger.info(f"Browsing topics: user_level={user_level}, ready_only={ready_only}")

        request = BrowseTopicsRequest(user_level=user_level, ready_only=ready_only)
        response = await service.browse_topics(request)

        logger.info(f"Successfully organized {response.total_topics} topics into categories")
        return response

    except TopicCatalogError as e:
        logger.error(f"Topic catalog error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error browsing topics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/popular", response_model=list[TopicSummaryResponse])
async def get_popular_topics(
    limit: int = Query(default=10, ge=1, le=50, description="Maximum results"),
    service: TopicCatalogService = Depends(get_topic_catalog_service),
) -> list[TopicSummaryResponse]:
    """Get popular topics for discovery."""
    try:
        logger.info(f"Getting popular topics: limit={limit}")
        topics = await service.get_popular_topics(limit=limit)
        logger.info(f"Successfully retrieved {len(topics)} popular topics")
        return topics

    except TopicCatalogError as e:
        logger.error(f"Topic catalog error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting popular topics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/recommendations", response_model=GetRecommendationsResponse)
async def get_recommendations(request: GetRecommendationsRequest, service: TopicCatalogService = Depends(get_topic_catalog_service)) -> GetRecommendationsResponse:
    """
    Get personalized topic recommendations.

    This endpoint provides intelligent topic recommendations based on
    user level and learning history.
    """
    try:
        logger.info(f"Getting recommendations: user_level={request.user_level}")
        response = await service.get_recommendations(request)
        logger.info(f"Successfully generated {len(response.recommendations)} recommendations")
        return response

    except TopicCatalogError as e:
        logger.error(f"Topic catalog error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Partial search query"),
    service: TopicCatalogService = Depends(get_topic_catalog_service),
) -> SearchSuggestionsResponse:
    """Get search suggestions for a partial query."""
    try:
        logger.info(f"Getting search suggestions for: '{query}'")

        request = SearchSuggestionsRequest(query=query)
        response = await service.get_search_suggestions(request)

        logger.info(f"Successfully generated {len(response.suggestions)} suggestions")
        return response

    except TopicCatalogError as e:
        logger.error(f"Topic catalog error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=TopicCatalogStatsResponse)
async def get_catalog_statistics(
    service: TopicCatalogService = Depends(get_topic_catalog_service),
) -> TopicCatalogStatsResponse:
    """Get catalog statistics and overview."""
    try:
        logger.info("Getting catalog statistics")
        stats = await service.get_catalog_statistics()
        logger.info("Successfully retrieved catalog statistics")
        return stats

    except TopicCatalogError as e:
        logger.error(f"Topic catalog error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh")
async def refresh_catalog(
    service: TopicCatalogService = Depends(get_topic_catalog_service),
) -> dict[str, Any]:
    """Refresh the catalog with latest data."""
    try:
        logger.info("Refreshing catalog")
        result = await service.refresh_catalog()
        logger.info(f"Successfully refreshed catalog: {result}")
        return result

    except TopicCatalogError as e:
        logger.error(f"Topic catalog error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error refreshing catalog: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=ModuleHealthResponse)
async def health_check(
    service: TopicCatalogService = Depends(get_topic_catalog_service),
) -> ModuleHealthResponse:
    """Health check endpoint for the topic catalog module."""
    try:
        # Basic health check - could be expanded to check dependencies
        # Get some basic statistics to test connectivity
        stats = await service.get_catalog_statistics()

        return ModuleHealthResponse(
            status="healthy",
            service="topic_catalog",
            timestamp=datetime.now(UTC).isoformat(),
            dependencies={
                "content_creation": "healthy",  # Could check actual content creation service health
                "database": "healthy",  # Could check database connectivity
            },
            statistics={
                "total_topics": stats.total_topics,
                "service_initialized": True,
                "last_check": datetime.now(UTC).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return ModuleHealthResponse(
            status="unhealthy",
            service="topic_catalog",
            timestamp=datetime.now(UTC).isoformat(),
            dependencies={"content_creation": "unknown", "database": "unknown"},
            statistics={"error": str(e), "last_check": datetime.now(UTC).isoformat()},
        )


def create_topic_catalog_router(topic_catalog_service: TopicCatalogService) -> APIRouter:
    """
    Create a topic catalog router with dependency injection.

    Args:
        topic_catalog_service: The topic catalog service instance

    Returns:
        Configured FastAPI router
    """

    # Override the dependency
    def get_injected_service() -> TopicCatalogService:
        return topic_catalog_service

    # Create a new router with the injected dependency
    new_router = APIRouter()

    # Copy all routes from the main router but with the injected service
    for route in router.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            # This is a simplified approach - in a real implementation you might want
            # to properly clone the routes with the new dependency
            pass

    return router  # For now, return the main router
