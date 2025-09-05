"""
HTTP API routes for Content Creation module.

This module provides thin HTTP routes that delegate to the service layer.
Routes handle only HTTP concerns (request/response, status codes, etc.).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ..module_api import (
    ComponentResponse,
    ContentCreationError,
    ContentCreationService,
    ContentCreationStatsResponse,
    CreateComponentRequest,
    CreateTopicRequest,
    GenerateAllComponentsRequest,
    ModuleHealthResponse,
    SearchTopicsRequest,
    TopicResponse,
    TopicSummaryResponse,
)

logger = logging.getLogger(__name__)

# Create router for content creation endpoints
router = APIRouter(prefix="/api/content", tags=["content-creation"])


# Dependency injection placeholder - will be configured by main app
async def get_content_creation_service() -> ContentCreationService:
    """
    Dependency to get content creation service.

    This should be configured by the main application with proper
    repository and LLM service instances.
    """
    raise HTTPException(status_code=500, detail="Content creation service not configured")


@router.post("/topics", response_model=TopicResponse)
async def create_topic(request: CreateTopicRequest, service: ContentCreationService = Depends(get_content_creation_service)) -> TopicResponse:
    """
    Create a new topic from source material.

    This endpoint:
    1. Takes user-provided source material
    2. Uses the content creation service to extract structured information
    3. Creates a topic with refined material
    4. Returns the created topic
    """
    try:
        logger.info(f"Creating topic: {request.title}")
        topic_response = await service.create_topic_from_source_material(request)
        logger.info(f"Successfully created topic {topic_response.id}")
        return topic_response

    except ContentCreationError as e:
        logger.error(f"Content creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating topic: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: str, service: ContentCreationService = Depends(get_content_creation_service)) -> TopicResponse:
    """Get a topic by ID with all its components."""
    try:
        logger.info(f"Getting topic: {topic_id}")
        topic_response = await service.get_topic(topic_id)
        return topic_response

    except ContentCreationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"Content creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/topics", response_model=list[TopicSummaryResponse])
async def list_topics(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), service: ContentCreationService = Depends(get_content_creation_service)) -> list[TopicSummaryResponse]:
    """List all topics with pagination."""
    try:
        logger.info(f"Listing topics: limit={limit}, offset={offset}")
        topic_responses = await service.get_all_topics(limit=limit, offset=offset)

        # Convert to summary responses for listing
        summaries = [TopicSummaryResponse.from_topic_response(tr) for tr in topic_responses]
        return summaries

    except ContentCreationError as e:
        logger.error(f"Content creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing topics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/topics/search", response_model=list[TopicSummaryResponse])
async def search_topics(request: SearchTopicsRequest, service: ContentCreationService = Depends(get_content_creation_service)) -> list[TopicSummaryResponse]:
    """Search topics by criteria."""
    try:
        logger.info(f"Searching topics: query={request.query}, user_level={request.user_level}")
        topic_responses = await service.search_topics(query=request.query, user_level=request.user_level, has_components=request.has_components, limit=request.limit, offset=request.offset)

        # Convert to summary responses
        summaries = [TopicSummaryResponse.from_topic_response(tr) for tr in topic_responses]
        return summaries

    except ContentCreationError as e:
        logger.error(f"Content creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error searching topics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/topics/{topic_id}/components", response_model=ComponentResponse)
async def create_component(topic_id: str, request: CreateComponentRequest, service: ContentCreationService = Depends(get_content_creation_service)) -> ComponentResponse:
    """Create a new component for a topic."""
    try:
        logger.info(f"Creating {request.component_type} component for topic {topic_id}")
        component_response = await service.create_component(topic_id, request)
        logger.info(f"Successfully created component {component_response.id}")
        return component_response

    except ContentCreationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"Content creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating component: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/topics/{topic_id}/components/{component_id}")
async def delete_component(topic_id: str, component_id: str, service: ContentCreationService = Depends(get_content_creation_service)) -> dict[str, str]:
    """Delete a component from a topic."""
    try:
        logger.info(f"Deleting component {component_id} from topic {topic_id}")
        deleted = await service.delete_component(topic_id, component_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Component not found")

        logger.info(f"Successfully deleted component {component_id}")
        return {"message": "Component deleted successfully"}

    except ContentCreationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"Content creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting component: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/topics/{topic_id}/generate-all-components", response_model=list[ComponentResponse])
async def generate_all_components(topic_id: str, request: GenerateAllComponentsRequest, service: ContentCreationService = Depends(get_content_creation_service)) -> list[ComponentResponse]:
    """Generate all components for a topic."""
    try:
        logger.info(f"Generating all components for topic {topic_id}")
        component_responses = await service.generate_all_components_for_topic(topic_id)
        logger.info(f"Successfully generated {len(component_responses)} components")
        return component_responses

    except ContentCreationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"Content creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating components: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str, service: ContentCreationService = Depends(get_content_creation_service)) -> dict[str, str]:
    """Delete a topic and all its components."""
    try:
        logger.info(f"Deleting topic {topic_id}")
        deleted = await service.delete_topic(topic_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Topic not found")

        logger.info(f"Successfully deleted topic {topic_id}")
        return {"message": "Topic deleted successfully"}

    except ContentCreationError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"Content creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting topic: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=ModuleHealthResponse)
async def health_check(service: ContentCreationService = Depends(get_content_creation_service)) -> ModuleHealthResponse:
    """Health check endpoint for the content creation module."""
    try:
        # Basic health check - could be expanded to check dependencies
        from datetime import UTC, datetime

        # Get some basic statistics
        topics = await service.get_all_topics(limit=1)  # Just to test connectivity

        return ModuleHealthResponse(
            status="healthy",
            service="content_creation",
            timestamp=datetime.now(UTC).isoformat(),
            dependencies={
                "database": "healthy",  # Could check actual database connectivity
                "llm_services": "healthy",  # Could check LLM service health
            },
            statistics={"service_initialized": True, "last_check": datetime.now(UTC).isoformat()},
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return ModuleHealthResponse(
            status="unhealthy", service="content_creation", timestamp=datetime.now(UTC).isoformat(), dependencies={"database": "unknown", "llm_services": "unknown"}, statistics={"error": str(e), "last_check": datetime.now(UTC).isoformat()}
        )


@router.get("/stats", response_model=ContentCreationStatsResponse)
async def get_statistics(service: ContentCreationService = Depends(get_content_creation_service)) -> ContentCreationStatsResponse:
    """Get content creation statistics."""
    try:
        logger.info("Getting content creation statistics")

        # Get all topics to calculate statistics
        all_topics = await service.get_all_topics(limit=1000)  # Reasonable limit

        # Calculate statistics
        total_topics = len(all_topics)
        topics_by_user_level = {}
        topics_by_readiness_status = {}
        total_components = 0
        components_by_type = {}
        completion_percentages = []
        quality_scores = []
        topics_ready_for_learning = 0

        for topic_response in all_topics:
            # User level distribution
            level = topic_response.user_level
            topics_by_user_level[level] = topics_by_user_level.get(level, 0) + 1

            # Readiness status distribution
            status = topic_response.readiness_status
            topics_by_readiness_status[status] = topics_by_readiness_status.get(status, 0) + 1

            # Component statistics
            total_components += len(topic_response.components)
            for component in topic_response.components:
                comp_type = component.component_type
                components_by_type[comp_type] = components_by_type.get(comp_type, 0) + 1

            # Quality metrics
            completion_percentages.append(topic_response.completion_percentage)
            quality_scores.append(topic_response.quality_score)

            if topic_response.is_ready_for_learning:
                topics_ready_for_learning += 1

        # Calculate averages
        avg_completion = sum(completion_percentages) / len(completion_percentages) if completion_percentages else 0.0
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        return ContentCreationStatsResponse(
            total_topics=total_topics,
            topics_by_user_level=topics_by_user_level,
            topics_by_readiness_status=topics_by_readiness_status,
            total_components=total_components,
            components_by_type=components_by_type,
            average_completion_percentage=round(avg_completion, 2),
            average_quality_score=round(avg_quality, 2),
            topics_ready_for_learning=topics_ready_for_learning,
        )

    except ContentCreationError as e:
        logger.error(f"Content creation error getting stats: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
