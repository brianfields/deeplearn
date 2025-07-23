"""
Learning Experience API Routes

PURPOSE: Handle the learning/consumption experience for educational content.
This module provides endpoints for learners to discover, access, and interact with
educational content in a learning-optimized format.

SCOPE:
- Learning-optimized topic discovery and browsing
- Topic access for learning consumption (not management)
- Learning progress tracking and state management
- Health monitoring and system status
- Learning session management

ROUTES:
- GET /health - Application health check and status
- GET /api/learning/topics - Browse topics for learning (discovery view)
- GET /api/learning/topics/{topic_id} - Get topic in learning format
- GET /api/learning/topics/{topic_id}/progress - Get learning progress
- POST /api/learning/topics/{topic_id}/progress - Update learning progress
- GET /api/learning/sessions - Get active learning sessions
- POST /api/learning/sessions - Create new learning session

WORKFLOW:
1. Learner discovers topics through learning-optimized browsing
2. Learner accesses topic content in consumption-ready format
3. System tracks learning progress and state
4. Learner can resume or continue learning sessions

RELATIONSHIP TO OTHER MODULES:
- Consumes topics created via Topic Management API
- Provides read-only access optimized for learning experience
- Separate from content creation and management workflows
- May include additional learning-specific metadata and formatting

NOTE: The legacy /api/bite-sized-topics endpoints should be migrated to
/api/learning/topics for consistency with the new architecture.
"""

from datetime import datetime
import logging

from fastapi import HTTPException
from fastapi.routing import APIRouter

# Additional models for learning-focused endpoints
from pydantic import BaseModel

from src.data_structures import BiteSizedComponent, BiteSizedTopic
from src.database_service import get_database_service

# Import dependency injection
from .dependencies import DatabaseDep

# Import the models
from .models import (
    BiteSizedTopicDetailResponse,
    BiteSizedTopicResponse,
    ComponentResponse,
)


class LearningTopicSummary(BaseModel):
    """Summary model for topic discovery in learning context"""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    estimated_duration: int  # in minutes
    component_count: int
    created_at: str


class LearningTopicDetail(BaseModel):
    """Detailed model for topic consumption in learning context"""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    key_aspects: list[str]
    target_insights: list[str]
    components: list[ComponentResponse]
    estimated_duration: int
    created_at: str
    updated_at: str


logger = logging.getLogger(__name__)

# Create router for API endpoints
router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str | dict[str, bool]]:
    """
    Health check endpoint.

    Returns the current status of the application and its services.

    Returns:
        dict: Health status information including:
            - status: Overall application health
            - timestamp: Current timestamp
            - services: Status of individual services
    """
    # Check if database service is available
    db_service = get_database_service()

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_service is not None,
        },
    }


# Bite-Sized Topic Endpoints


@router.get("/api/bite-sized-topics", response_model=list[BiteSizedTopicResponse])
async def get_bite_sized_topics(db_service: DatabaseDep) -> list[BiteSizedTopicResponse]:
    """
    Get all bite-sized topics.

    Returns a list of all available bite-sized topics with summary information.

    Args:
        db_service: Database service injected via dependency injection

    Returns:
        list: List of bite-sized topic summaries

    Raises:
        HTTPException: 503 if database service unavailable, 500 for other errors
    """
    try:
        topics = db_service.list_bite_sized_topics(limit=100)

        return [
            BiteSizedTopicResponse(
                id=topic.id,
                title=topic.title,
                core_concept=topic.core_concept,
                user_level=topic.user_level,
                learning_objectives=topic.learning_objectives,
                key_concepts=topic.key_concepts,
                estimated_duration=15,  # Default 15 minutes
                created_at=topic.created_at.isoformat(),
            )
            for topic in topics
        ]
    except Exception as e:
        logger.error(f"Error fetching bite-sized topics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bite-sized topics") from e


@router.get("/api/bite-sized-topics/{topic_id}", response_model=BiteSizedTopicDetailResponse)
async def get_bite_sized_topic_detail(topic_id: str, db_service: DatabaseDep) -> BiteSizedTopicDetailResponse:
    """
    Get detailed information about a specific bite-sized topic.

    Returns all content and components for a bite-sized topic in a readable format.

    Args:
        topic_id (str): Unique identifier for the bite-sized topic
        db_service: Database service injected via dependency injection

    Returns:
        BiteSizedTopicDetailResponse: Complete topic information with all components

    Raises:
        HTTPException: 404 if topic not found, 500 for other errors
    """
    try:
        # Get topic details
        topic = db_service.get_bite_sized_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Bite-sized topic not found")

        # Get topic components
        components = db_service.get_topic_components(topic_id)

        # Convert components to response format
        component_responses = [
            ComponentResponse(
                component_type=comp.component_type,
                content=comp.content,
                metadata={
                    "title": comp.title,
                    "created_at": comp.created_at.isoformat(),
                    "updated_at": comp.updated_at.isoformat(),
                    "generation_prompt": comp.generation_prompt,
                    "raw_llm_response": comp.raw_llm_response,
                    "evaluation": comp.evaluation,
                },
            )
            for comp in components
        ]

        return BiteSizedTopicDetailResponse(
            id=topic.id,
            title=topic.title,
            core_concept=topic.core_concept,
            user_level=topic.user_level,
            learning_objectives=topic.learning_objectives,
            key_concepts=topic.key_concepts,
            key_aspects=topic.key_aspects,
            target_insights=topic.target_insights,
            common_misconceptions=[],  # Not available in new model
            previous_topics=[],  # Not available in new model
            components=component_responses,
            created_at=topic.created_at.isoformat(),
            updated_at=topic.updated_at.isoformat(),
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error fetching bite-sized topic detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bite-sized topic details") from e


# Topic Discovery and Consumption Endpoints (moved from topic_routes.py)


@router.get("/api/learning/topics", response_model=list[LearningTopicSummary])
async def get_learning_topics(db_service: DatabaseDep, user_level: str | None = None, limit: int = 50, offset: int = 0) -> list[LearningTopicSummary]:
    """
    Get topics optimized for learning discovery.

    Returns a list of topics formatted for learning consumption with
    estimated durations and component counts.

    Args:
        db_service: Database service injected via dependency injection
        user_level: Optional filter by user level
        limit: Maximum number of topics to return
        offset: Number of topics to skip for pagination
    """
    try:
        with db_service.get_session() as session:
            # Build query
            query = session.query(BiteSizedTopic)

            # Filter by user level if provided
            if user_level:
                query = query.filter(BiteSizedTopic.user_level == user_level)

            # Apply pagination
            topics = query.offset(offset).limit(limit).all()

            # Get component counts for each topic
            topic_summaries = []
            for topic in topics:
                component_count = session.query(BiteSizedComponent).filter(BiteSizedComponent.topic_id == topic.id).count()

                # Estimate duration based on components (5 minutes per component + 5 base)
                estimated_duration = max(5 + (component_count * 5), 10)

                topic_summaries.append(
                    LearningTopicSummary(
                        id=str(topic.id),
                        title=str(topic.title),
                        core_concept=str(topic.core_concept),
                        user_level=str(topic.user_level),
                        learning_objectives=list(topic.learning_objectives) if topic.learning_objectives is not None else [],
                        key_concepts=list(topic.key_concepts) if topic.key_concepts is not None else [],
                        estimated_duration=estimated_duration,
                        component_count=component_count,
                        created_at=topic.created_at.isoformat() if topic.created_at and hasattr(topic.created_at, "isoformat") else str(topic.created_at) if topic.created_at else "",
                    )
                )

            return topic_summaries

    except Exception as e:
        logger.error(f"Failed to get learning topics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get learning topics: {e!s}") from e


@router.get("/api/learning/topics/{topic_id}", response_model=LearningTopicDetail)
async def get_learning_topic(topic_id: str, db_service: DatabaseDep) -> LearningTopicDetail:
    """
    Get a topic optimized for learning consumption.

    Returns topic content formatted specifically for the learning experience,
    with components optimized for consumption rather than editing.

    Args:
        topic_id: Unique identifier for the topic
        db_service: Database service injected via dependency injection
    """
    try:
        with db_service.get_session() as session:
            # Get topic from database
            topic = session.query(BiteSizedTopic).filter(BiteSizedTopic.id == topic_id).first()
            if not topic:
                raise HTTPException(status_code=404, detail="Topic not found")

            # Get components for this topic
            components = session.query(BiteSizedComponent).filter(BiteSizedComponent.topic_id == topic_id).all()

            # Convert components to learning-optimized format
            component_responses = []
            for component in components:
                component_responses.append(
                    ComponentResponse(
                        component_type=component.component_type or "unknown",
                        content=component.content,
                        metadata={
                            "title": component.title,
                            "created_at": component.created_at.isoformat() if component.created_at and hasattr(component.created_at, "isoformat") else str(component.created_at) if component.created_at else "",
                            "updated_at": component.updated_at.isoformat() if component.updated_at and hasattr(component.updated_at, "isoformat") else str(component.updated_at) if component.updated_at else "",
                        },
                    )
                )

            # Estimate duration based on components
            estimated_duration = max(5 + (len(components) * 5), 10)

            return LearningTopicDetail(
                id=str(topic.id),
                title=str(topic.title),
                core_concept=str(topic.core_concept),
                user_level=str(topic.user_level),
                learning_objectives=topic.learning_objectives if topic.learning_objectives is not None else [],
                key_concepts=topic.key_concepts if topic.key_concepts is not None else [],
                key_aspects=topic.key_aspects if topic.key_aspects is not None else [],
                target_insights=topic.target_insights if topic.target_insights is not None else [],
                components=component_responses,
                estimated_duration=estimated_duration,
                created_at=topic.created_at.isoformat() if topic.created_at and hasattr(topic.created_at, "isoformat") else str(topic.created_at) if topic.created_at else "",
                updated_at=topic.updated_at.isoformat() if topic.updated_at and hasattr(topic.updated_at, "isoformat") else str(topic.updated_at) if topic.updated_at else "",
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is (like 404)
        raise
    except Exception as e:
        logger.error(f"Failed to get learning topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get learning topic: {e!s}") from e


@router.get("/api/learning/topics/{topic_id}/components")
async def get_learning_topic_components(topic_id: str, db_service: DatabaseDep) -> list[ComponentResponse]:
    """
    Get all components for a topic in learning-optimized format.

    Returns components formatted specifically for learning consumption.

    Args:
        topic_id: Unique identifier for the topic
        db_service: Database service injected via dependency injection
    """
    try:
        with db_service.get_session() as session:
            # Verify topic exists
            topic = session.query(BiteSizedTopic).filter(BiteSizedTopic.id == topic_id).first()
            if not topic:
                raise HTTPException(status_code=404, detail="Topic not found")

            # Get components
            components = session.query(BiteSizedComponent).filter(BiteSizedComponent.topic_id == topic_id).all()

            # Convert to learning-optimized response format
            component_responses = []
            for component in components:
                component_responses.append(
                    ComponentResponse(
                        component_type=component.component_type or "unknown",
                        content=component.content,
                        metadata={
                            "title": component.title,
                            "created_at": component.created_at.isoformat() if component.created_at and hasattr(component.created_at, "isoformat") else str(component.created_at) if component.created_at else "",
                            "updated_at": component.updated_at.isoformat() if component.updated_at and hasattr(component.updated_at, "isoformat") else str(component.updated_at) if component.updated_at else "",
                        },
                    )
                )

            return component_responses

    except HTTPException:
        # Re-raise HTTP exceptions as-is (like 404)
        raise
    except Exception as e:
        logger.error(f"Failed to get learning components for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get learning components: {e!s}") from e
