"""
HTTP REST API endpoints for Content Creation.

This module contains API endpoints for the content creation interface,
providing functionality for creating refined material and MCQs.
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


@router.post("/refined-material", response_model=RefinedMaterialResponse)
async def create_refined_material(
    request: CreateRefinedMaterialRequest,
    mcq_service: MCQService = Depends(get_mcq_service)
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

        # Extract refined material (first pass of MCQ creation)
        refined_material, _ = await mcq_service.create_mcqs_from_text(
            source_material=request.source_material,
            topic_title=request.topic,
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