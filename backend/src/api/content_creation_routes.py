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

import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import create_llm_client
from core.prompt_base import PromptContext
from data_structures import BiteSizedComponent, BiteSizedTopic
from database_service import DatabaseService
from modules.lesson_planning.bite_sized_topics.mcq_service import MCQService
from modules.lesson_planning.bite_sized_topics.refined_material_service import RefinedMaterialService


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


async def get_database_service() -> DatabaseService:
    """Dependency to get database service instance"""
    try:
        return DatabaseService()
    except Exception as e:
        logger.error(f"Failed to create database service: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize database service") from e


async def get_mcq_service() -> MCQService:
    """Dependency to get MCQ service instance"""
    try:
        # Get API key from environment or use dummy for testing
        import os

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
        import os

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
async def create_topic_from_material(request: CreateTopicFromMaterialRequest, refined_material_service: RefinedMaterialService = Depends(get_refined_material_service), db_service: DatabaseService = Depends(get_database_service)):
    """
    Create a new topic with refined material from source text.
    This directly creates a BiteSizedTopic with the refined material.
    """
    try:
        # Create prompt context
        context = PromptContext(user_level=request.source_level, time_constraint=30)

        # Extract refined material
        refined_material = await refined_material_service.extract_refined_material(source_material=request.source_material, domain=request.source_domain, user_level=request.source_level, context=context)

        # Generate topic ID
        topic_id = str(uuid.uuid4())

        # Extract learning objectives and key concepts from refined material
        learning_objectives = []
        key_concepts = []

        for topic_data in refined_material.get("topics", []):
            if topic_data.get("learning_objectives"):
                learning_objectives.extend(topic_data["learning_objectives"])
            if topic_data.get("key_facts"):
                key_concepts.extend(topic_data["key_facts"])

        # Create core concept from first topic or use title
        core_concept = refined_material.get("topics", [{}])[0].get("topic", request.title) if refined_material.get("topics") else request.title

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
            refined_material=refined_material,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
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
            refined_material=refined_material,
            components=[],
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to create topic from material: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create topic from material: {str(e)}") from e


@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: str, db_service: DatabaseService = Depends(get_database_service)):
    """
    Get a topic with all its components for content creation/editing.
    """
    try:
        # Get topic from database using DatabaseService method (returns Pydantic model)
        topic = db_service.get_bite_sized_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Get components using database service method (returns Pydantic models)
        components = db_service.get_topic_components(topic_id)

        # Convert Pydantic models to dict format for response
        component_dicts = [comp.dict() for comp in components]

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
        raise HTTPException(status_code=500, detail=f"Failed to get topic: {str(e)}") from e


@router.post("/topics/{topic_id}/components", response_model=ComponentResponse)
async def create_component_for_topic(topic_id: str, request: CreateComponentRequest, mcq_service: MCQService = Depends(get_mcq_service), db_service: DatabaseService = Depends(get_database_service)):
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
            mcq_data = await mcq_service._create_single_mcq(subtopic=str(topic.title), learning_objective=request.learning_objective, key_facts=key_facts, common_misconceptions=[], assessment_angles=[], context=context)

            # Evaluate MCQ
            evaluation = await mcq_service._evaluate_mcq(mcq=mcq_data, learning_objective=request.learning_objective, context=context)

            component_content = {"mcq": mcq_data, "evaluation": evaluation, "learning_objective": request.learning_objective}
            title = f"MCQ: {request.learning_objective[:50]}..."

        else:
            # For other component types, create placeholder content
            component_content = {"type": request.component_type, "learning_objective": request.learning_objective, "placeholder": True}
            title = f"{request.component_type.replace('_', ' ').title()}"

        # Create component in database
        component = BiteSizedComponent(id=component_id, topic_id=topic_id, component_type=request.component_type, title=title, content=component_content, created_at=datetime.utcnow(), updated_at=datetime.utcnow())

        with db_service.get_session() as session:
            session.add(component)
            session.commit()

        logger.info(f"Created component {component_id} for topic {topic_id}")

        return ComponentResponse(id=component_id, topic_id=topic_id, component_type=request.component_type, title=title, content=component_content, created_at=datetime.utcnow().isoformat(), updated_at=datetime.utcnow().isoformat())

    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is (404, etc.)
    except Exception as e:
        logger.error(f"Failed to create component for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create component: {str(e)}") from e


@router.delete("/topics/{topic_id}/components/{component_id}")
async def delete_component(topic_id: str, component_id: str, db_service: DatabaseService = Depends(get_database_service)):
    """
    Delete a component from a topic.
    """
    try:
        with db_service.get_session() as session:
            # Find the component
            component = session.query(BiteSizedComponent).filter(BiteSizedComponent.id == component_id, BiteSizedComponent.topic_id == topic_id).first()

            if not component:
                raise HTTPException(status_code=404, detail="Component not found")

            # Delete the component
            session.delete(component)
            session.commit()

        logger.info(f"Deleted component {component_id} from topic {topic_id}")
        return {"message": "Component deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete component {component_id} from topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete component: {str(e)}") from e


@router.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str, db_service: DatabaseService = Depends(get_database_service)):
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
        raise HTTPException(status_code=500, detail=f"Failed to delete topic: {str(e)}") from e
