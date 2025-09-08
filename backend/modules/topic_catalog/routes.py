"""
Topic Catalog Module - HTTP Routes

HTTP API for topic browsing and discovery.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from .public import TopicCatalogProvider, topic_catalog_provider
from .service import BrowseTopicsResponse, TopicDetail

router = APIRouter(prefix="/api/topics", tags=["topic-catalog"])


@router.get("/", response_model=BrowseTopicsResponse)
def browse_topics(
    user_level: str | None = Query(None, description="Filter by user level (beginner, intermediate, advanced)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of topics to return"),
    catalog: TopicCatalogProvider = Depends(topic_catalog_provider),
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
def get_topic_details(topic_id: str, catalog: TopicCatalogProvider = Depends(topic_catalog_provider)) -> TopicDetail:
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
