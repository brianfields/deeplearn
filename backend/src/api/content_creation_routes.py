"""
Content Creation Studio API Routes

PURPOSE: Handle the content creation workflow and session management.
This module provides endpoints for the step-by-step content creation process,
allowing users to create educational content in a structured workflow.

SCOPE:
- Creating refined material from source text
- Creating individual content components (MCQs, etc.)
- Managing creation sessions and temporary workspace
- Providing creation utilities and tools

ROUTES:
- POST /api/content/refined-material - Extract structured material from source text
- POST /api/content/mcq - Create individual MCQ for a learning objective
- GET  /api/content/sessions - List all content creation sessions
- POST /api/content/sessions - Create new content creation session
- GET  /api/content/sessions/{session_id} - Get content creation session details
- DELETE /api/content/sessions/{session_id} - Delete content creation session

WORKFLOW:
1. User provides source material → Creates refined material
2. User selects learning objectives → Creates individual components
3. Session manages temporary state during creation process
4. Once satisfied, user can save to permanent topic storage via Topic API

RELATIONSHIP TO OTHER MODULES:
- Uses RefinedMaterialService and MCQService for content generation
- Temporary storage only - permanent storage handled by Topic API
- Consumed by Content Creation Studio frontend interface
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
import json
import uuid

from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

# Import the MCQ service
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import create_llm_client
from core.prompt_base import PromptContext
from modules.lesson_planning.bite_sized_topics.mcq_service import MCQService
from modules.lesson_planning.bite_sized_topics.refined_material_service import RefinedMaterialService


# Additional Request/Response Models for Topic Management
class CreateTopicFromMaterialRequest(BaseModel):
    """Request model for creating a topic from source material"""
    title: str = Field(..., description="Topic title")
    source_material: str = Field(..., description="Source material text")
    source_domain: str = Field("", description="Subject domain (optional)")
    source_level: str = Field("intermediate", description="Target user level")

class CreateTopicComponentRequest(BaseModel):
    """Request model for creating a component for a topic"""
    component_type: str = Field(..., description="Type of component to create")
    learning_objective: Optional[str] = Field(None, description="Specific learning objective")
    source_material: Optional[str] = Field(None, description="Source material for generation")
    topic_context: Optional[Dict[str, Any]] = Field(None, description="Additional context from refined material")

class TopicResponse(BaseModel):
    """Response model for topic data"""
    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: List[str]
    key_concepts: List[str]
    key_aspects: List[str]
    target_insights: List[str]
    source_material: Optional[str]
    source_domain: Optional[str]
    source_level: Optional[str]
    refined_material: Optional[Dict[str, Any]]
    components: List[Dict[str, Any]]
    created_at: str
    updated_at: str

class TopicComponentResponse(BaseModel):
    """Response model for component data"""
    id: str
    topic_id: str
    component_type: str
    title: str
    content: Dict[str, Any]
    created_at: str
    updated_at: str

logger = logging.getLogger(__name__)

# Create router for content creation endpoints
router = APIRouter(prefix="/api/content", tags=["content-creation"])


# Request/Response Models
class CreateRefinedMaterialRequest(BaseModel):
    """Request model for creating refined material"""
    topic: str = Field(..., description="Topic title for the MCQs")
    source_material: str = Field(..., description="Source material text")
    domain: str = Field("", description="Subject domain (optional)")
    level: str = Field("intermediate", description="Target user level")
    model: str = Field("gpt-4o", description="LLM model to use")

    class Config:
        schema_extra = {
            "example": {
                "topic": "Python Functions",
                "source_material": "Functions in Python are reusable blocks of code that perform specific tasks...",
                "domain": "Programming",
                "level": "intermediate",
                "model": "gpt-4o"
            }
        }


class CreateMCQRequest(BaseModel):
    """Request model for creating a single MCQ"""
    session_id: str = Field(..., description="Content creation session ID")
    topic: str = Field(..., description="Subtopic name")
    learning_objective: str = Field(..., description="Learning objective to target")
    key_facts: List[str] = Field([], description="Key facts for the topic")
    common_misconceptions: List[Dict[str, str]] = Field([], description="Common misconceptions")
    assessment_angles: List[str] = Field([], description="Assessment angles")
    level: str = Field("intermediate", description="Target user level")
    model: str = Field("gpt-4o", description="LLM model to use")


class RefinedMaterialResponse(BaseModel):
    """Response model for refined material"""
    session_id: str
    topic: str
    domain: str
    level: str
    source_material_length: int
    refined_material: Dict[str, Any]
    created_at: str

    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "topic": "Python Functions",
                "domain": "Programming",
                "level": "intermediate",
                "source_material_length": 1500,
                "refined_material": {
                    "topics": [
                        {
                            "topic": "Function Basics",
                            "learning_objectives": ["Define Python functions", "Use parameters"],
                            "key_facts": ["Functions use 'def' keyword", "Parameters allow input"],
                            "common_misconceptions": [
                                {
                                    "misconception": "Functions can only return one value",
                                    "correct_concept": "Functions can return multiple values"
                                }
                            ],
                            "assessment_angles": ["Syntax definition", "Parameter usage"]
                        }
                    ]
                },
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class MCQResponse(BaseModel):
    """Response model for a created MCQ"""
    session_id: str
    mcq_id: str
    topic: str
    learning_objective: str
    mcq: Dict[str, Any]
    evaluation: Dict[str, Any]
    created_at: str

    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "mcq_id": "mcq_001",
                "topic": "Function Basics",
                "learning_objective": "Define Python functions",
                "mcq": {
                    "stem": "What is the correct syntax for defining a function in Python?",
                    "options": ["def my_function():", "function my_function():", "def my_function[]:", "define my_function():"],
                    "correct_answer": "def my_function():",
                    "correct_answer_index": 0,
                    "rationale": "The 'def' keyword is required for function definitions in Python"
                },
                "evaluation": {
                    "alignment": "Directly tests function definition knowledge",
                    "stem_quality": "Clear and complete question",
                    "options_quality": "One correct option with plausible distractors",
                    "overall": "High quality MCQ following best practices"
                },
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class ContentSessionResponse(BaseModel):
    """Response model for content creation session"""
    session_id: str
    topic: str
    domain: str
    level: str
    refined_material: Optional[Dict[str, Any]] = None
    mcqs: List[Dict[str, Any]] = []
    created_at: str
    updated_at: str


# In-memory storage for content creation sessions (in production, use a database)
content_sessions: Dict[str, Dict[str, Any]] = {}


async def get_mcq_service() -> MCQService:
    """Dependency to get MCQ service instance"""
    try:
        # Get API key from environment or use dummy for testing
        import os
        api_key = os.environ.get('OPENAI_API_KEY', 'dummy_key')

        llm_client = create_llm_client(api_key=api_key, model="gpt-4o")
        return MCQService(llm_client)
    except Exception as e:
        logger.error(f"Failed to create MCQ service: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize MCQ service")


async def get_refined_material_service() -> RefinedMaterialService:
    """Dependency to get RefinedMaterialService instance"""
    try:
        # Get API key from environment or use dummy for testing
        import os
        api_key = os.environ.get('OPENAI_API_KEY', 'dummy_key')

        llm_client = create_llm_client(api_key=api_key, model="gpt-4o")
        return RefinedMaterialService(llm_client)
    except Exception as e:
        logger.error(f"Failed to create refined material service: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize refined material service")


@router.post("/refined-material", response_model=RefinedMaterialResponse)
async def create_refined_material(
    request: CreateRefinedMaterialRequest,
    refined_material_service: RefinedMaterialService = Depends(get_refined_material_service)
):
    """
    Create refined material from source text.

    This endpoint takes source material and creates a structured breakdown
    with topics, learning objectives, key facts, and assessment angles.
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())

        # Create prompt context
        context = PromptContext(
            user_level=request.level,
            time_constraint=30
        )

        # Extract refined material directly
        refined_material = await refined_material_service.extract_refined_material(
            source_material=request.source_material,
            domain=request.domain,
            user_level=request.level,
            context=context
        )

        # Store session data
        session_data = {
            "session_id": session_id,
            "topic": request.topic,
            "domain": request.domain,
            "level": request.level,
            "source_material": request.source_material,
            "source_material_length": len(request.source_material),
            "refined_material": refined_material,
            "mcqs": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        content_sessions[session_id] = session_data

        logger.info(f"Created refined material for session {session_id}, topic: {request.topic}")

        return RefinedMaterialResponse(
            session_id=session_id,
            topic=request.topic,
            domain=request.domain,
            level=request.level,
            source_material_length=len(request.source_material),
            refined_material=refined_material,
            created_at=session_data["created_at"]
        )

    except Exception as e:
        logger.error(f"Failed to create refined material: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create refined material: {str(e)}")


@router.post("/mcq", response_model=MCQResponse)
async def create_mcq(
    request: CreateMCQRequest,
    mcq_service: MCQService = Depends(get_mcq_service)
):
    """
    Create a single MCQ for a specific learning objective.

    This endpoint creates an MCQ for a specific learning objective
    from a previously created refined material session.
    """
    try:
        # Check if session exists
        if request.session_id not in content_sessions:
            raise HTTPException(status_code=404, detail="Content creation session not found")

        session_data = content_sessions[request.session_id]

        # Create prompt context
        context = PromptContext(
            user_level=request.level,
            time_constraint=30
        )

        # Create single MCQ
        mcq = await mcq_service._create_single_mcq(
            subtopic=request.topic,
            learning_objective=request.learning_objective,
            key_facts=request.key_facts,
            common_misconceptions=request.common_misconceptions,
            assessment_angles=request.assessment_angles,
            context=context
        )

        # Evaluate MCQ
        evaluation = await mcq_service._evaluate_mcq(
            mcq=mcq,
            learning_objective=request.learning_objective,
            context=context
        )

        # Generate MCQ ID
        mcq_id = f"mcq_{len(session_data['mcqs']) + 1:03d}"

        # Create MCQ data
        mcq_data = {
            "mcq_id": mcq_id,
            "topic": request.topic,
            "learning_objective": request.learning_objective,
            "mcq": mcq,
            "evaluation": evaluation,
            "created_at": datetime.utcnow().isoformat()
        }

        # Add to session
        session_data["mcqs"].append(mcq_data)
        session_data["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"Created MCQ {mcq_id} for session {request.session_id}")

        return MCQResponse(
            session_id=request.session_id,
            mcq_id=mcq_id,
            topic=request.topic,
            learning_objective=request.learning_objective,
            mcq=mcq,
            evaluation=evaluation,
            created_at=mcq_data["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create MCQ: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create MCQ: {str(e)}")


@router.get("/sessions/{session_id}", response_model=ContentSessionResponse)
async def get_content_session(session_id: str):
    """
    Get a content creation session by ID.

    This endpoint retrieves all data for a content creation session,
    including refined material and any created MCQs.
    """
    try:
        if session_id not in content_sessions:
            raise HTTPException(status_code=404, detail="Content creation session not found")

        session_data = content_sessions[session_id]

        return ContentSessionResponse(
            session_id=session_id,
            topic=session_data["topic"],
            domain=session_data["domain"],
            level=session_data["level"],
            refined_material=session_data["refined_material"],
            mcqs=session_data["mcqs"],
            created_at=session_data["created_at"],
            updated_at=session_data["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get content session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get content session: {str(e)}")


@router.get("/sessions", response_model=List[ContentSessionResponse])
async def list_content_sessions():
    """
    List all content creation sessions.

    This endpoint returns a list of all content creation sessions
    with their basic information.
    """
    try:
        sessions = []
        for session_id, session_data in content_sessions.items():
            sessions.append(ContentSessionResponse(
                session_id=session_id,
                topic=session_data["topic"],
                domain=session_data["domain"],
                level=session_data["level"],
                refined_material=session_data["refined_material"],
                mcqs=session_data["mcqs"],
                created_at=session_data["created_at"],
                updated_at=session_data["updated_at"]
            ))

        return sessions

    except Exception as e:
        logger.error(f"Failed to list content sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list content sessions: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_content_session(session_id: str):
    """
    Delete a content creation session.

    This endpoint deletes a content creation session and all its data.
    """
    try:
        if session_id not in content_sessions:
            raise HTTPException(status_code=404, detail="Content creation session not found")

        del content_sessions[session_id]

        logger.info(f"Deleted content session {session_id}")

        return {"message": "Content session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete content session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete content session: {str(e)}")


# Topic Management Endpoints (moved from topic_routes.py)

@router.post("/topics", response_model=TopicResponse)
async def create_topic_from_material(
    request: CreateTopicFromMaterialRequest,
    refined_material_service: RefinedMaterialService = Depends(get_refined_material_service)
):
    """
    Create a new topic from source material.

    This endpoint creates a permanent topic by processing source material through
    the RefinedMaterialService to extract structured learning content.
    """
    try:
        from database_service import DatabaseService
        from data_structures import BiteSizedTopic

        db_service = DatabaseService()

        # Create prompt context
        context = PromptContext(
            user_level=request.source_level,
            time_constraint=30
        )

        # Extract refined material using the dedicated service
        refined_material = await refined_material_service.extract_refined_material(
            source_material=request.source_material,
            domain=request.source_domain,
            user_level=request.source_level,
            context=context
        )

        # Generate topic ID
        topic_id = str(uuid.uuid4())

        # Extract learning objectives and key concepts from refined material
        learning_objectives = []
        key_concepts = []

        for topic_data in refined_material.get('topics', []):
            if topic_data.get('learning_objectives'):
                learning_objectives.extend(topic_data['learning_objectives'])
            if topic_data.get('key_facts'):
                key_concepts.extend(topic_data['key_facts'])

        # Create core concept from first topic or use title
        core_concept = (
            refined_material.get('topics', [{}])[0].get('topic', request.title)
            if refined_material.get('topics')
            else request.title
        )

        with db_service.get_session() as session:
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
                creation_strategy="custom",
                creation_metadata={"created_from": "source_material"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            session.add(topic)
            session.commit()

            logger.info(f"Created topic {topic_id} from source material: {request.title}")

            return TopicResponse(
                id=str(topic.id),
                title=str(topic.title),
                core_concept=str(topic.core_concept),
                user_level=str(topic.user_level),
                learning_objectives=topic.learning_objectives if topic.learning_objectives is not None else [],
                key_concepts=topic.key_concepts if topic.key_concepts is not None else [],
                key_aspects=topic.key_aspects if topic.key_aspects is not None else [],
                target_insights=topic.target_insights if topic.target_insights is not None else [],
                source_material=str(topic.source_material) if topic.source_material else None,
                source_domain=str(topic.source_domain) if topic.source_domain else None,
                source_level=str(topic.source_level) if topic.source_level else None,
                refined_material=topic.refined_material,
                components=[],
                created_at=topic.created_at.isoformat(),
                updated_at=topic.updated_at.isoformat()
            )

    except Exception as e:
        logger.error(f"Failed to create topic from material: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create topic from material: {str(e)}")


@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: str):
    """
    Get a topic with all its components for content creation/editing.
    """
    try:
        from database_service import DatabaseService
        from data_structures import BiteSizedTopic, BiteSizedComponent

        db_service = DatabaseService()

        with db_service.get_session() as session:
            # Get topic from database
            topic = session.query(BiteSizedTopic).filter(BiteSizedTopic.id == topic_id).first()
            if not topic:
                raise HTTPException(status_code=404, detail="Topic not found")

            # Get components for this topic
            components = session.query(BiteSizedComponent).filter(
                BiteSizedComponent.topic_id == topic_id
            ).all()

            # Convert components to dict format
            component_dicts = []
            for component in components:
                component_dicts.append({
                    "id": component.id,
                    "topic_id": component.topic_id,
                    "component_type": component.component_type,
                    "title": component.title,
                    "content": component.content,
                    "created_at": component.created_at.isoformat() if hasattr(component.created_at, 'isoformat') else str(component.created_at),
                    "updated_at": component.updated_at.isoformat() if hasattr(component.updated_at, 'isoformat') else str(component.updated_at)
                })

            return TopicResponse(
                id=topic.id,
                title=topic.title,
                core_concept=topic.core_concept,
                user_level=topic.user_level,
                learning_objectives=topic.learning_objectives or [],
                key_concepts=topic.key_concepts or [],
                key_aspects=topic.key_aspects or [],
                target_insights=topic.target_insights or [],
                source_material=topic.source_material,
                source_domain=topic.source_domain,
                source_level=topic.source_level,
                refined_material=topic.refined_material,
                components=component_dicts,
                created_at=topic.created_at.isoformat() if hasattr(topic.created_at, 'isoformat') else str(topic.created_at),
                updated_at=topic.updated_at.isoformat() if hasattr(topic.updated_at, 'isoformat') else str(topic.updated_at)
            )

    except Exception as e:
        logger.error(f"Failed to get topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get topic: {str(e)}")


@router.post("/topics/{topic_id}/components", response_model=TopicComponentResponse)
async def create_topic_component(
    topic_id: str,
    request: CreateTopicComponentRequest,
    mcq_service: MCQService = Depends(get_mcq_service)
):
    """
    Create a new component for a topic during content creation.
    """
    try:
        from database_service import DatabaseService
        from data_structures import BiteSizedTopic, BiteSizedComponent

        db_service = DatabaseService()

        with db_service.get_session() as session:
            # Verify topic exists
            topic = session.query(BiteSizedTopic).filter(BiteSizedTopic.id == topic_id).first()
            if not topic:
                raise HTTPException(status_code=404, detail="Topic not found")

            # Generate component ID
            component_id = str(uuid.uuid4())

            # Create component based on type
            if request.component_type == "mcq":
                # Use MCQ service to create MCQ
                context = PromptContext(user_level=topic.user_level)

                # Use learning objective from request or first available
                learning_objective = request.learning_objective or (
                    topic.learning_objectives[0] if topic.learning_objectives else "General understanding"
                )

                # Get context data from topic_context if provided
                topic_context = request.topic_context or {}
                key_facts = topic_context.get('key_facts', topic.key_concepts or [])
                common_misconceptions = topic_context.get('common_misconceptions', [])
                assessment_angles = topic_context.get('assessment_angles', [])

                # Create MCQ using service
                mcq_data = await mcq_service._create_single_mcq(
                    subtopic=topic_context.get('topic', topic.title),
                    learning_objective=learning_objective,
                    key_facts=key_facts,
                    common_misconceptions=common_misconceptions,
                    assessment_angles=assessment_angles,
                    context=context
                )

                # Evaluate MCQ
                evaluation = await mcq_service._evaluate_mcq(
                    mcq=mcq_data,
                    learning_objective=learning_objective,
                    context=context
                )

                component_content = {
                    "mcq": mcq_data,
                    "evaluation": evaluation,
                    "learning_objective": learning_objective
                }
                title = f"MCQ: {learning_objective[:50]}..."

            else:
                # For other component types, create placeholder content
                component_content = {
                    "type": request.component_type,
                    "learning_objective": request.learning_objective,
                    "placeholder": True
                }
                title = f"{request.component_type.replace('_', ' ').title()}"

            # Create component in database
            component = BiteSizedComponent(
                id=component_id,
                topic_id=topic_id,
                component_type=request.component_type,
                title=title,
                content=component_content,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            session.add(component)
            session.commit()

            logger.info(f"Created component {component_id} for topic {topic_id}")

            return TopicComponentResponse(
                id=component.id,
                topic_id=component.topic_id,
                component_type=component.component_type,
                title=component.title,
                content=component.content,
                created_at=component.created_at.isoformat(),
                updated_at=component.updated_at.isoformat()
            )

    except Exception as e:
        logger.error(f"Failed to create component for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create component: {str(e)}")


@router.delete("/topics/{topic_id}/components/{component_id}")
async def delete_topic_component(
    topic_id: str,
    component_id: str
):
    """
    Delete a component from a topic during content creation.
    """
    try:
        from database_service import DatabaseService
        from data_structures import BiteSizedComponent

        db_service = DatabaseService()

        with db_service.get_session() as session:
            # Find the component
            component = session.query(BiteSizedComponent).filter(
                BiteSizedComponent.id == component_id,
                BiteSizedComponent.topic_id == topic_id
            ).first()

            if not component:
                raise HTTPException(status_code=404, detail="Component not found")

            # Delete the component
            session.delete(component)
            session.commit()

            logger.info(f"Deleted component {component_id} from topic {topic_id}")

            return {"message": "Component deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete component {component_id} from topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete component: {str(e)}")


@router.post("/topics/{topic_id}/generate-all-components")
async def generate_all_topic_components(
    topic_id: str,
    mcq_service: MCQService = Depends(get_mcq_service)
):
    """
    Generate all components for a topic using AI during content creation.
    """
    try:
        from database_service import DatabaseService
        from data_structures import BiteSizedTopic, BiteSizedComponent

        db_service = DatabaseService()

        with db_service.get_session() as session:
            # Get topic from database
            topic = session.query(BiteSizedTopic).filter(BiteSizedTopic.id == topic_id).first()
            if not topic:
                raise HTTPException(status_code=404, detail="Topic not found")

            # Create context for generation
            context = PromptContext(user_level=topic.user_level)

            # Generate components for each learning objective
            components_created = []

            for objective in topic.learning_objectives or []:
                # Create MCQ for this objective
                try:
                    mcq_data = await mcq_service._create_single_mcq(
                        subtopic=topic.title,
                        learning_objective=objective,
                        key_facts=topic.key_concepts or [],
                        common_misconceptions=[],
                        assessment_angles=[],
                        context=context
                    )

                    # Evaluate MCQ
                    evaluation = await mcq_service._evaluate_mcq(
                        mcq=mcq_data,
                        learning_objective=objective,
                        context=context
                    )

                    # Create MCQ component
                    component_id = str(uuid.uuid4())
                    component = BiteSizedComponent(
                        id=component_id,
                        topic_id=topic_id,
                        component_type="mcq",
                        title=f"MCQ: {objective[:50]}...",
                        content={
                            "mcq": mcq_data,
                            "evaluation": evaluation,
                            "learning_objective": objective
                        },
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )

                    session.add(component)
                    components_created.append(component_id)

                except Exception as e:
                    logger.warning(f"Failed to create MCQ for objective '{objective}': {e}")
                    continue

            # Commit all components
            session.commit()

            logger.info(f"Generated {len(components_created)} components for topic {topic_id}")

            return {
                "message": f"Generated {len(components_created)} components",
                "components_created": components_created
            }

    except Exception as e:
        logger.error(f"Failed to generate components for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate components: {str(e)}")


@router.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str):
    """
    Delete a topic and all its components during content creation.
    """
    try:
        from database_service import DatabaseService
        from data_structures import BiteSizedTopic, BiteSizedComponent

        db_service = DatabaseService()

        with db_service.get_session() as session:
            # Get topic from database
            topic = session.query(BiteSizedTopic).filter(BiteSizedTopic.id == topic_id).first()
            if not topic:
                raise HTTPException(status_code=404, detail="Topic not found")

            # Delete all components first
            session.query(BiteSizedComponent).filter(
                BiteSizedComponent.topic_id == topic_id
            ).delete()

            # Delete the topic
            session.delete(topic)
            session.commit()

            logger.info(f"Deleted topic {topic_id} and all its components")

            return {"message": "Topic deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete topic: {str(e)}")