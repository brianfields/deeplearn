"""
Topic Catalog HTTP API Routes.

Simple REST endpoints for topic browsing and discovery.
"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Query
from fastapi.routing import APIRouter

from ..module_api import (
    BrowseTopicsRequest,
    TopicCatalogError,
    TopicCatalogService,
    create_topic_catalog_service,
)
from ..module_api.types import BrowseTopicsResponse, TopicDetailResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/topics", tags=["topic-catalog"])


async def get_topic_catalog_service() -> TopicCatalogService:
    """Dependency to get topic catalog service."""
    return create_topic_catalog_service()


TopicCatalogServiceDep = Annotated[TopicCatalogService, Depends(get_topic_catalog_service)]


@router.get("/", response_model=BrowseTopicsResponse)
async def browse_topics(
    service: TopicCatalogServiceDep,
    user_level: str | None = Query(None, description="Filter by user level (beginner, intermediate, advanced)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of topics to return"),
) -> BrowseTopicsResponse:
    """
    Browse available topics for learning.

    Returns a list of topics with basic information for browsing and selection.
    """
    try:
        request = BrowseTopicsRequest(user_level=user_level, limit=limit)
        return await service.browse_topics(request)
    except TopicCatalogError as e:
        logger.error(f"Topic catalog error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unexpected error browsing topics: {e}")
        raise HTTPException(status_code=500, detail="Failed to browse topics") from e


@router.get("/{topic_id}", response_model=TopicDetailResponse)
async def get_topic_details(
    topic_id: str,
    service: TopicCatalogServiceDep,
) -> TopicDetailResponse:
    """
    Get detailed information about a specific topic.

    Returns complete topic information including components for learning.
    """
    try:
        return await service.get_topic_by_id(topic_id)
    except TopicCatalogError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        logger.error(f"Topic catalog error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unexpected error getting topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get topic details") from e
