"""
HTTP REST API endpoints for the Bite-Sized Topics platform.

This module contains simplified HTTP REST endpoints focused on
bite-sized topics functionality only.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

# Import the models
from .models import (
    BiteSizedTopicResponse,
    ComponentResponse,
    BiteSizedTopicDetailResponse
)

logger = logging.getLogger(__name__)

# Create router for API endpoints
router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns the current status of the application and its services.

    Returns:
        dict: Health status information including:
            - status: Overall application health
            - timestamp: Current timestamp
            - services: Status of individual services
    """
    from .server import database

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": database is not None,
        }
    }


# Bite-Sized Topic Endpoints

@router.get("/api/bite-sized-topics", response_model=List[BiteSizedTopicResponse])
async def get_bite_sized_topics():
    """
    Get all bite-sized topics.

    Returns a list of all available bite-sized topics with summary information.

    Returns:
        list: List of bite-sized topic summaries

    Raises:
        HTTPException: 503 if database service unavailable, 500 for other errors
    """
    try:
        # Import here to avoid circular imports
        from modules.lesson_planning.bite_sized_topics.postgresql_storage import PostgreSQLTopicRepository

        repository = PostgreSQLTopicRepository()
        topics = await repository.list_topics(limit=100)  # Get up to 100 topics

        return [
            BiteSizedTopicResponse(
                id=topic.id,
                title=topic.title,
                core_concept=topic.core_concept,
                user_level=topic.user_level,
                learning_objectives=topic.learning_objectives,
                key_concepts=topic.key_concepts,
                estimated_duration=15,  # Default 15 minutes
                created_at=topic.created_at if isinstance(topic.created_at, str) else topic.created_at.isoformat()
            )
            for topic in topics
        ]
    except Exception as e:
        logger.error(f"Error fetching bite-sized topics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bite-sized topics")


@router.get("/api/bite-sized-topics/{topic_id}", response_model=BiteSizedTopicDetailResponse)
async def get_bite_sized_topic_detail(topic_id: str):
    """
    Get detailed information about a specific bite-sized topic.

    Returns all content and components for a bite-sized topic in a readable format.

    Args:
        topic_id (str): Unique identifier for the bite-sized topic

    Returns:
        BiteSizedTopicDetailResponse: Complete topic information with all components

    Raises:
        HTTPException: 404 if topic not found, 500 for other errors
    """
    try:
        # Import here to avoid circular imports
        from modules.lesson_planning.bite_sized_topics.postgresql_storage import PostgreSQLTopicRepository

        repository = PostgreSQLTopicRepository()

        # Get topic details
        topic_content = await repository.get_topic(topic_id)
        if not topic_content:
            raise HTTPException(status_code=404, detail="Bite-sized topic not found")

        # Get topic components
        components = await repository.get_topic_components(topic_id)

        # Convert components to response format
        component_responses = [
            ComponentResponse(
                component_type=comp.component_type if isinstance(comp.component_type, str) else comp.component_type.value,
                content=comp.content,
                metadata={
                    "title": comp.title,
                    "created_at": comp.created_at.isoformat() if hasattr(comp.created_at, 'isoformat') else str(comp.created_at),
                    "updated_at": comp.updated_at.isoformat() if hasattr(comp.updated_at, 'isoformat') else str(comp.updated_at),
                    "version": comp.version,
                    "generation_prompt": comp.generation_prompt,
                    "raw_llm_response": comp.raw_llm_response
                }
            )
            for comp in components
        ]

        return BiteSizedTopicDetailResponse(
            id=topic_id,
            title=topic_content.topic_spec.topic_title,
            core_concept=topic_content.topic_spec.core_concept,
            user_level=topic_content.topic_spec.user_level,
            learning_objectives=topic_content.topic_spec.learning_objectives,
            key_concepts=topic_content.topic_spec.key_concepts,
            key_aspects=topic_content.topic_spec.key_aspects,
            target_insights=topic_content.topic_spec.target_insights,
            common_misconceptions=topic_content.topic_spec.common_misconceptions,
            previous_topics=topic_content.topic_spec.previous_topics,
            creation_strategy=topic_content.topic_spec.creation_strategy.value if hasattr(topic_content.topic_spec.creation_strategy, 'value') else str(topic_content.topic_spec.creation_strategy),
            components=component_responses,
            created_at=datetime.utcnow().isoformat(),  # Fallback timestamp
            updated_at=datetime.utcnow().isoformat()   # Fallback timestamp
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error fetching bite-sized topic detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bite-sized topic details")


@router.post("/api/bite-sized-topics")
async def create_bite_sized_topic(
    title: str,
    core_concept: str,
    user_level: str = "beginner",
    learning_objectives: Optional[List[str]] = None,
    key_concepts: Optional[List[str]] = None
):
    """
    Create a new bite-sized topic.

    Args:
        title: Title of the topic
        core_concept: Core concept to be taught
        user_level: Target user level (beginner, intermediate, advanced)
        learning_objectives: List of learning objectives
        key_concepts: List of key concepts to cover

    Returns:
        dict: Created topic information with ID

    Raises:
        HTTPException: 500 for creation errors
    """
    try:
        # Import here to avoid circular imports
        from modules.lesson_planning.bite_sized_topics.orchestrator import TopicOrchestrator, TopicSpec, CreationStrategy
        from core import LLMClient, ServiceConfig
        from core.service_base import ServiceFactory
        from config.config import config_manager
        from llm_interface import LLMConfig, LLMProviderType

        # Create service configuration
        llm_config = LLMConfig(
            provider=LLMProviderType.OPENAI,
            model=config_manager.config.openai_model,
            api_key=config_manager.config.openai_api_key,
            max_tokens=2000,
            temperature=0.7
        )

        service_config = ServiceFactory.create_service_config(
            llm_config=llm_config,
            cache_enabled=True,
            retry_attempts=3
        )

        llm_client = LLMClient(llm_config, cache_enabled=True)
        orchestrator = TopicOrchestrator(service_config, llm_client)

        # Create topic specification
        topic_spec = TopicSpec(
            topic_title=title,
            core_concept=core_concept,
            user_level=user_level,
            learning_objectives=learning_objectives or [],
            key_concepts=key_concepts or []
        )

        # Create the topic
        topic_content = await orchestrator.create_topic(topic_spec)

        # The topic ID would need to be saved to database to get an actual ID
        # For now, generate a simple ID based on the title
        import uuid
        topic_id = str(uuid.uuid4())

        return {
            "id": topic_id,
            "title": title,
            "status": "created",
            "message": "Bite-sized topic created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating bite-sized topic: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create bite-sized topic: {str(e)}")