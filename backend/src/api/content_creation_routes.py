"""
Content Creation Studio API Routes

PURPOSE: Handle the content creation workflow using the existing database structure.
This module provides endpoints for creating educational content directly in the database
without temporary sessions.

SCOPE:
- Creating topics with refined material from source text
- Creating individual content components (MCQs, etc.) as BiteSizedComponents
- Managing topics and components during content creation
- Direct database storage using existing schema

ROUTES:
- POST /api/content/topics - Create topic with refined material from source text
- GET  /api/content/topics/{topic_id} - Get topic with components for editing
- POST /api/content/topics/{topic_id}/components - Create component for topic
- DELETE /api/content/topics/{topic_id}/components/{component_id} - Delete component
- POST /api/content/topics/{topic_id}/generate-all-components - Generate all components
- DELETE /api/content/topics/{topic_id} - Delete topic

WORKFLOW:
1. User provides source material → Creates topic with refined material
2. User creates individual components (MCQs, etc.) for the topic
3. All data stored directly in database using existing BiteSizedTopic/BiteSizedComponent tables
4. No temporary storage - everything is permanent and immediately available

RELATIONSHIP TO OTHER MODULES:
- Uses RefinedMaterialService and MCQService for content generation
- Direct storage using DatabaseService and existing schema
- Consumed by Content Creation Studio frontend interface
"""

from datetime import UTC, datetime
import logging
import os
from pathlib import Path
import sys
from typing import Any
import uuid

from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.llm_client import create_llm_client
from src.core.prompt_base import PromptContext
from src.data_structures import (
    BiteSizedTopic,
    ComponentData,
    TopicResult,
    PodcastGenerationRequest,
    PodcastGenerationResponse,
    PodcastEpisodeResponse,
    PodcastScript,
)
from src.modules.content_creation.service import BiteSizedTopicService
from src.modules.content_creation.mcq_service import MCQService
from src.modules.content_creation.models import GenerationMetadata, MultipleChoiceQuestion
from src.modules.content_creation.refined_material_service import RefinedMaterialService
from src.modules.podcast.service import PodcastService
from src.core.service_base import ServiceConfig

# Import shared dependencies
from .dependencies import DatabaseDep


# Simplified Request/Response Models for Direct Database Usage
class CreateTopicFromMaterialRequest(BaseModel):
    """Request model for creating a topic from source material"""

    title: str = Field(..., description="Topic title")
    source_material: str = Field(..., description="Source material text")
    source_domain: str = Field("", description="Subject domain (optional)")
    source_level: str = Field("intermediate", description="Target user level")


class CreateComponentRequest(BaseModel):
    """Request model for creating a component for a topic"""

    component_type: str = Field(..., description="Type of component to create")
    learning_objective: str = Field(..., description="Specific learning objective")


class TopicResponse(BaseModel):
    """Response model for topic data"""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    source_material: str | None
    source_domain: str | None
    source_level: str | None
    refined_material: dict[str, Any] | None
    components: list[dict[str, Any]]
    created_at: str
    updated_at: str


class ComponentResponse(BaseModel):
    """Response model for component data"""

    id: str
    topic_id: str
    component_type: str
    title: str
    content: dict[str, Any]
    created_at: str
    updated_at: str


logger = logging.getLogger(__name__)

# Create router for content creation endpoints
router = APIRouter(prefix="/api/content", tags=["content-creation"])


# Request/Response Models for New Database-First API


async def get_mcq_service() -> MCQService:
    """Dependency to get MCQ service instance"""
    try:
        # Get API key from environment or use dummy for testing

        api_key = os.environ.get("OPENAI_API_KEY", "dummy_key")

        llm_client = create_llm_client(api_key=api_key, model="gpt-4o")
        return MCQService(llm_client)
    except Exception as e:
        logger.error(f"Failed to create MCQ service: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize MCQ service") from e


async def get_refined_material_service() -> RefinedMaterialService:
    """Dependency to get RefinedMaterialService instance"""
    try:
        # Get API key from environment or use dummy for testing

        api_key = os.environ.get("OPENAI_API_KEY", "dummy_key")

        llm_client = create_llm_client(api_key=api_key, model="gpt-4o")
        return RefinedMaterialService(llm_client)
    except Exception as e:
        logger.error(f"Failed to create refined material service: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize refined material service") from e


# Legacy route removed - use POST /api/content/topics instead


# Legacy session-based routes removed - use the new topic-based endpoints below


# Topic Management Endpoints (moved from topic_routes.py)


@router.post("/topics", response_model=TopicResponse)
async def create_topic_from_material(
    request: CreateTopicFromMaterialRequest,
    db_service: DatabaseDep,
    refined_material_service: RefinedMaterialService = Depends(get_refined_material_service),
) -> TopicResponse:
    """
    Create a new topic from source material.

    This endpoint:
    1. Takes user-provided source material
    2. Uses RefinedMaterialService to extract structured information
    3. Creates a BiteSizedTopic in the database with refined material
    4. Returns the created topic

    Args:
        request: Topic creation request with source material
        db_service: Database service injected via dependency injection
        refined_material_service: Service for processing source material

    Returns:
        TopicResponse: Created topic with refined material
    """
    try:
        # Create prompt context
        context = PromptContext(user_level=request.source_level, time_constraint=30)

        # Extract refined material
        refined_material = await refined_material_service.extract_refined_material(
            source_material=request.source_material,
            domain=request.source_domain,
            user_level=request.source_level,
            context=context,
        )

        # Generate topic ID
        topic_id = str(uuid.uuid4())

        # Extract learning objectives and key concepts from refined material
        learning_objectives = []
        key_concepts = []

        for topic_data in refined_material.topics:
            if topic_data.learning_objectives:
                learning_objectives.extend(topic_data.learning_objectives)
            if topic_data.key_facts:
                key_concepts.extend(topic_data.key_facts)

        # Create core concept from first topic or use title
        core_concept = refined_material.topics[0].topic if refined_material.topics else request.title

        # Create topic in database
        topic = BiteSizedTopic(
            id=topic_id,
            title=request.title,
            core_concept=core_concept,
            user_level=request.source_level,
            learning_objectives=learning_objectives,
            key_concepts=key_concepts,
            key_aspects=[],
            target_insights=[],
            source_material=request.source_material,
            source_domain=request.source_domain,
            source_level=request.source_level,
            refined_material=refined_material.model_dump(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        success = db_service.save_bite_sized_topic(topic)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save topic")

        logger.info(f"Created topic {topic_id} from source material: {request.title}")

        return TopicResponse(
            id=topic_id,
            title=request.title,
            core_concept=core_concept,
            user_level=request.source_level,
            learning_objectives=learning_objectives,
            key_concepts=key_concepts,
            source_material=request.source_material,
            source_domain=request.source_domain,
            source_level=request.source_level,
            refined_material=refined_material.model_dump(),
            components=[],
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to create topic from material: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create topic from material: {e!s}") from e


@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: str, db_service: DatabaseDep) -> TopicResponse:
    """
    Get a topic with all its components for content creation/editing.

    Args:
        topic_id: Unique identifier for the topic
        db_service: Database service injected via dependency injection

    Returns:
        TopicResponse: Topic data with all components
    """
    try:
        # Get topic from database using DatabaseService method (returns Pydantic model)
        topic = db_service.get_bite_sized_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Get components using database service method (returns Pydantic models)
        components = db_service.get_topic_components(topic_id)

        # Convert Pydantic models to dict format for response
        component_dicts = [comp.model_dump() for comp in components]

        return TopicResponse(
            id=topic.id,
            title=topic.title,
            core_concept=topic.core_concept,
            user_level=topic.user_level,
            learning_objectives=topic.learning_objectives,
            key_concepts=topic.key_concepts,
            source_material=topic.source_material,
            source_domain=topic.source_domain,
            source_level=topic.source_level,
            refined_material=topic.refined_material,
            components=component_dicts,
            created_at=topic.created_at.isoformat(),
            updated_at=topic.updated_at.isoformat(),
        )

    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is (404, etc.)
    except Exception as e:
        logger.error(f"Failed to get topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get topic: {e!s}") from e


@router.post("/topics/{topic_id}/components", response_model=ComponentResponse)
async def create_component(
    topic_id: str,
    request: CreateComponentRequest,
    db_service: DatabaseDep,
    mcq_service: MCQService = Depends(get_mcq_service),
) -> ComponentResponse:
    """
    Create a new component (MCQ) for a topic.
    """
    try:
        # Verify topic exists
        topic = db_service.get_bite_sized_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Generate component ID
        component_id = str(uuid.uuid4())

        # Create component based on type
        if request.component_type == "mcq":
            # Create prompt context
            context = PromptContext(user_level=str(topic.user_level))

            # Get key facts from topic
            key_facts = list(topic.key_concepts) if topic.key_concepts else []

            # Create MCQ using service
            mcq_data = await mcq_service._create_single_mcq(
                subtopic=str(topic.title),
                learning_objective=request.learning_objective,
                key_facts=key_facts,
                common_misconceptions=[],
                assessment_angles=[],
                context=context,
            )

            # Evaluate MCQ
            evaluation = await mcq_service._evaluate_mcq(
                mcq=mcq_data,
                learning_objective=request.learning_objective,
                context=context,
            )

            # Convert to MultipleChoiceQuestion format (consistent with create_topic.py)

            # Helper function to convert options array to choices dict
            def convert_options_to_dict(options: list[str]) -> dict[str, str]:
                choices = {}
                for i, option in enumerate(options):
                    letter = chr(65 + i)  # A, B, C, D, etc.
                    choices[letter] = option
                return choices

            # Helper function to get correct answer index
            def get_correct_answer_index(options: list[str], correct_answer: str) -> int:
                try:
                    return options.index(correct_answer)
                except ValueError:
                    return 0  # Default to first option if not found

            generation_metadata = GenerationMetadata(
                generation_method="api_mcq_service",
                topic=str(topic.title),
                learning_objective=request.learning_objective,
                evaluation=evaluation.model_dump() if evaluation else {},
                refined_material="",
            )

            # Create MultipleChoiceQuestion in correct format
            mcq_question = MultipleChoiceQuestion(
                title=mcq_data.stem[:50] + "..." if len(mcq_data.stem) > 50 else mcq_data.stem,
                question=mcq_data.stem,
                choices=convert_options_to_dict(mcq_data.options),
                correct_answer=mcq_data.correct_answer,
                correct_answer_index=get_correct_answer_index(mcq_data.options, mcq_data.correct_answer),
                justifications={"rationale": mcq_data.rationale},
                target_concept=str(topic.core_concept),
                purpose=f"Assess understanding of {request.learning_objective}",
                difficulty=3,  # Default difficulty
                tags=str(topic.core_concept),
                number=1,
                generation_metadata=generation_metadata,
            )

            # Store in correct format (same as create_topic.py)
            component_content = mcq_question.model_dump()
            title = f"MCQ: {request.learning_objective[:50]}..."

        else:
            # For other component types, create placeholder content
            component_content = {
                "type": request.component_type,
                "learning_objective": request.learning_objective,
                "placeholder": "true",
            }
            title = f"{request.component_type.replace('_', ' ').title()}"

        # Create component in database
        component = BiteSizedComponent(
            id=component_id,
            topic_id=topic_id,
            component_type=request.component_type,
            title=title,
            content=component_content,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with db_service.get_session() as session:
            session.add(component)
            session.commit()

        logger.info(f"Created component {component_id} for topic {topic_id}")

        return ComponentResponse(
            id=component_id,
            topic_id=topic_id,
            component_type=request.component_type,
            title=title,
            content=component_content,
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is (404, etc.)
    except Exception as e:
        logger.error(f"Failed to create component for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create component: {e!s}") from e


@router.delete("/topics/{topic_id}/components/{component_id}")
async def delete_component(
    topic_id: str,
    component_id: str,
    db_service: DatabaseDep,
) -> dict[str, str]:
    """
    Delete a component from a topic.
    """
    try:
        with db_service.get_session() as session:
            # Find the component
            component = (
                session.query(BiteSizedComponent)
                .filter(
                    BiteSizedComponent.id == component_id,
                    BiteSizedComponent.topic_id == topic_id,
                )
                .first()
            )

            if not component:
                raise HTTPException(status_code=404, detail="Component not found")

            # Delete the component
            session.delete(component)
            session.commit()

        logger.info(f"Deleted component {component_id} from topic {topic_id}")
        return {"message": "Component deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete component {component_id} from topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete component: {e!s}") from e


@router.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str, db_service: DatabaseDep) -> dict[str, str]:
    """
    Delete a topic and all its components.
    """
    try:
        success = db_service.delete_bite_sized_topic(topic_id)
        if not success:
            raise HTTPException(status_code=404, detail="Topic not found")

        logger.info(f"Deleted topic {topic_id} and all its components")
        return {"message": "Topic deleted successfully"}

    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is (404, etc.)
    except Exception as e:
        logger.error(f"Failed to delete topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete topic: {e!s}") from e


# Podcast Generation Routes
async def get_podcast_service() -> PodcastService:
    """Get podcast service instance"""
    try:
        llm_client = create_llm_client()
        config = ServiceConfig(llm_client=llm_client)
        service = PodcastService(config, llm_client)
        await service.initialize()
        return service
    except Exception as e:
        logger.error(f"Failed to create podcast service: {e}")
        raise HTTPException(status_code=500, detail="Failed to create podcast service")


@router.post("/podcasts/generate", response_model=PodcastGenerationResponse)
async def generate_podcast(
    request: PodcastGenerationRequest,
    db_service: DatabaseDep,
    podcast_service: PodcastService = Depends(get_podcast_service),
) -> PodcastGenerationResponse:
    """
    Generate a podcast episode from a topic.

    Args:
        request: Podcast generation request with topic ID
        db_service: Database service
        podcast_service: Podcast service

    Returns:
        PodcastGenerationResponse: Generated podcast data
    """
    try:
        # Check if topic exists
        topic = db_service.get_bite_sized_topic(request.topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Generate podcast script
        script = await podcast_service.generate_podcast_script(request.topic_id)

        # Save to database
        episode_id = db_service.save_podcast_episode(script, request.topic_id)

        logger.info(f"Generated podcast episode {episode_id} for topic {request.topic_id}")

        return PodcastGenerationResponse(
            episode_id=episode_id,
            title=script.title,
            description=script.description,
            total_duration_minutes=script.total_duration_seconds // 60,
            learning_outcomes=script.learning_outcomes,
            segments=script.segments,
            full_script=script.full_script,
            status="generated"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate podcast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate podcast: {e!s}") from e


@router.get("/podcasts/{episode_id}", response_model=PodcastEpisodeResponse)
async def get_podcast_episode(
    episode_id: str,
    db_service: DatabaseDep,
    podcast_service: PodcastService = Depends(get_podcast_service),
) -> PodcastEpisodeResponse:
    """
    Get a podcast episode by ID.

    Args:
        episode_id: ID of the podcast episode
        db_service: Database service
        podcast_service: Podcast service

    Returns:
        PodcastEpisodeResponse: Podcast episode data
    """
    try:
        episode = await podcast_service.get_podcast_episode(episode_id)
        if not episode:
            raise HTTPException(status_code=404, detail="Podcast episode not found")

        # Get topic ID from database
        episode_data = db_service.get_podcast_episode(episode_id)
        topic_id = ""
        if episode_data and hasattr(episode_data, 'topic_links') and episode_data.topic_links:
            topic_id = episode_data.topic_links[0].topic_id if episode_data.topic_links else ""

        return PodcastEpisodeResponse(
            episode_id=episode.id,
            title=episode.title,
            description=episode.description,
            total_duration_minutes=episode.total_duration_minutes,
            learning_outcomes=episode.learning_outcomes,
            segments=[],  # TODO: Add segment conversion
            full_script=episode.full_script,
            created_at=episode.created_at,
            topic_id=topic_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get podcast episode: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get podcast episode: {e!s}") from e


@router.get("/podcasts/topic/{topic_id}", response_model=PodcastEpisodeResponse)
async def get_topic_podcast(
    topic_id: str,
    db_service: DatabaseDep,
    podcast_service: PodcastService = Depends(get_podcast_service),
) -> PodcastEpisodeResponse:
    """
    Get the podcast episode for a specific topic.

    Args:
        topic_id: ID of the topic
        db_service: Database service
        podcast_service: Podcast service

    Returns:
        PodcastEpisodeResponse: Podcast episode data
    """
    try:
        episode = await podcast_service.get_topic_podcast(topic_id)
        if not episode:
            raise HTTPException(status_code=404, detail="No podcast found for this topic")

        return PodcastEpisodeResponse(
            episode_id=episode.id,
            title=episode.title,
            description=episode.description,
            total_duration_minutes=episode.total_duration_minutes,
            learning_outcomes=episode.learning_outcomes,
            segments=[],  # TODO: Add segment conversion
            full_script=episode.full_script,
            created_at=episode.created_at,
            topic_id=topic_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get topic podcast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get topic podcast: {e!s}") from e
