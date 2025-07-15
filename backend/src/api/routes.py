"""
HTTP REST API endpoints for the Conversational Learning platform.

This module contains all the HTTP REST endpoints for managing learning paths,
conversations, and progress tracking.
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
    StartTopicRequest,
    ChatMessage,
    LearningPathResponse,
    ConversationResponse,
    ProgressResponse,
    TopicResponse,
    BiteSizedTopicResponse,
    ComponentResponse,
    BiteSizedTopicDetailResponse
)

# Import the existing learning components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import enhanced_conversational_learning
    import simple_storage
    import data_structures
    import llm_interface

    EnhancedConversationalLearningEngine = enhanced_conversational_learning.EnhancedConversationalLearningEngine
    EnhancedConversationSession = enhanced_conversational_learning.EnhancedConversationSession
    SimpleStorage = simple_storage.SimpleStorage
    create_learning_path_from_syllabus = simple_storage.create_learning_path_from_syllabus
    SimpleProgress = simple_storage.SimpleProgress
    ProgressStatus = data_structures.ProgressStatus
    MessageRole = llm_interface.MessageRole

except ImportError as e:
    print(f"Import error in routes.py: {e}")
    import traceback
    traceback.print_exc()

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
    from .server import storage, learning_service, conversation_engine

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "storage": storage is not None,
            "learning_service": learning_service is not None,
            "conversation_engine": conversation_engine is not None
        }
    }


@router.post("/api/learning-paths", response_model=LearningPathResponse)
async def create_learning_path(request: StartTopicRequest):
    """
    Create a new learning path for a topic.

    This endpoint generates a comprehensive learning path including syllabus,
    learning objectives, and structured topics for the specified subject.

    Args:
        request (StartTopicRequest): Contains topic and user level information

    Returns:
        LearningPathResponse: Complete learning path with topics and metadata

    Raises:
        HTTPException: 503 if learning service unavailable, 500 for other errors
    """
    from .server import learning_service, storage

    if not learning_service or not storage:
        raise HTTPException(status_code=503, detail="Learning service not available")

    try:
        # Generate syllabus
        logger.info(f"Creating learning path for topic: {request.topic}")
        syllabus = await learning_service.generate_syllabus(
            topic=request.topic,
            user_level=request.user_level
        )

        # Create learning path
        learning_path = create_learning_path_from_syllabus(syllabus)
        storage.save_learning_path(learning_path)

        # Convert to response format
        response = LearningPathResponse(
            id=learning_path.id,
            topic_name=learning_path.topic_name,
            description=learning_path.description,
            topics=[TopicResponse(
                id=topic.id,
                title=topic.title,
                description=topic.description,
                learning_objectives=topic.learning_objectives,
                estimated_duration=15,  # Default duration
                difficulty_level=1,  # Default difficulty
                bite_sized_topic_id=topic.bite_sized_topic_id,
                has_bite_sized_content=topic.has_bite_sized_content
            ) for topic in learning_path.topics],
            current_topic_index=learning_path.current_topic_index,
            estimated_total_hours=len(learning_path.topics) * 0.25,  # Default estimate
            bite_sized_content_info=syllabus.get('bite_sized_content')
        )

        logger.info(f"Created learning path: {learning_path.id}")
        return response

    except Exception as e:
        logger.error(f"Error creating learning path: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create learning path: {str(e)}")


@router.get("/api/learning-paths")
async def get_learning_paths():
    """
    Get all learning paths.

    Returns a list of all learning paths with summary information including
    progress statistics and metadata.

    Returns:
        list: List of learning path summaries

    Raises:
        HTTPException: 503 if storage service unavailable, 500 for other errors
    """
    from .server import storage

    if not storage:
        raise HTTPException(status_code=503, detail="Storage service not available")

    try:
        learning_paths = storage.list_learning_paths()
        return [
            {
                "id": path_data["id"],
                "topic_name": path_data["topic_name"],
                "description": path_data["description"],
                "total_topics": path_data["topics_count"],
                "progress_count": path_data["progress_count"],
                "created_at": path_data["created_at"],
                "estimated_total_hours": path_data["topics_count"] * 0.25  # Default estimate
            }
            for path_data in learning_paths
        ]
    except Exception as e:
        logger.error(f"Error fetching learning paths: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch learning paths")


@router.get("/api/learning-paths/{path_id}")
async def get_learning_path(path_id: str):
    """
    Get a specific learning path by ID.

    Returns detailed information about a learning path including all topics,
    progress status, and learning objectives.

    Args:
        path_id (str): Unique identifier for the learning path

    Returns:
        dict: Detailed learning path information

    Raises:
        HTTPException: 503 if storage unavailable, 404 if path not found, 500 for other errors
    """
    from .server import storage

    if not storage:
        raise HTTPException(status_code=503, detail="Storage service not available")

    learning_path = storage.load_learning_path(path_id)
    if not learning_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Build topics list with proper status handling
    topics = []
    for topic in learning_path.topics:
        # Get progress for this topic
        topic_progress = learning_path.progress.get(topic.id, SimpleProgress(topic.id, ProgressStatus.NOT_STARTED))

        # Handle status value - could be enum or string
        if hasattr(topic_progress.status, 'value'):
            status_value = topic_progress.status.value
        else:
            status_value = str(topic_progress.status)

        topics.append({
            "id": topic.id,
            "title": topic.title,
            "description": topic.description,
            "learning_objectives": topic.learning_objectives,
            "estimated_duration": 15,  # Default duration
            "difficulty_level": 1,  # Default difficulty
            "position": topic.position,
            "status": status_value
        })

    return {
        "id": learning_path.id,
        "topic_name": learning_path.topic_name,
        "description": learning_path.description,
        "topics": topics,
        "current_topic_index": learning_path.current_topic_index,
        "estimated_total_hours": len(learning_path.topics) * 0.25,  # Default estimate
        "created_at": learning_path.created_at
    }


@router.post("/api/conversations/start")
async def start_conversation(path_id: str, topic_id: str):
    """
    Start a new conversation for a topic.

    Initializes a new conversational learning session for the specified topic
    within a learning path.

    Args:
        path_id (str): Learning path identifier
        topic_id (str): Topic identifier within the learning path

    Returns:
        dict: Conversation session information including initial AI message

    Raises:
        HTTPException: 503 if conversation engine unavailable, 500 for other errors
    """
    from .server import conversation_engine

    if not conversation_engine:
        raise HTTPException(status_code=503, detail="Conversation engine not available")

    try:
        session = conversation_engine.start_conversation(path_id, topic_id)

        # Get the initial AI message
        initial_message = ""
        if session.messages:
            last_message = session.messages[-1]
            if last_message.role == MessageRole.ASSISTANT:
                initial_message = last_message.content

        return {
            "session_id": f"{path_id}_{topic_id}",
            "ai_message": initial_message,
            "conversation_state": session.conversation_state.value if hasattr(session.conversation_state, 'value') else str(session.conversation_state),
            "topic_title": session.topic_title
        }

    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")


@router.post("/api/conversations/continue")
async def continue_conversation(path_id: str, topic_id: str):
    """
    Continue an existing conversation.

    Resumes an existing conversational learning session or starts a new one
    if no previous session exists.

    Args:
        path_id (str): Learning path identifier
        topic_id (str): Topic identifier within the learning path

    Returns:
        dict: Conversation session information including message history

    Raises:
        HTTPException: 503 if conversation engine unavailable, 500 for other errors
    """
    from .server import conversation_engine

    if not conversation_engine:
        raise HTTPException(status_code=503, detail="Conversation engine not available")

    try:
        session = conversation_engine.continue_conversation(path_id, topic_id)

        if not session:
            # No existing conversation, start a new one
            return await start_conversation(path_id, topic_id)

        # Get the last AI message
        last_ai_message = ""
        for message in reversed(session.messages):
            if message.role == MessageRole.ASSISTANT:
                last_ai_message = message.content
                break

        return {
            "session_id": f"{path_id}_{topic_id}",
            "ai_message": last_ai_message,
            "conversation_state": session.conversation_state.value if hasattr(session.conversation_state, 'value') else str(session.conversation_state),
            "topic_title": session.topic_title,
            "message_history": [
                {
                    "role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in session.messages[-10:]  # Last 10 messages
            ]
        }

    except Exception as e:
        logger.error(f"Error continuing conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to continue conversation: {str(e)}")


@router.get("/api/progress")
async def get_progress():
    """
    Get overall learning progress.

    Returns comprehensive progress information including all learning paths,
    completion statistics, and current learning session details.

    Returns:
        dict: Complete progress information including:
            - learning_paths: List of learning paths with progress
            - overall_progress: Summary statistics
            - total_paths: Total number of learning paths
            - completed_paths: Number of completed learning paths

    Raises:
        HTTPException: 503 if services unavailable, 500 for other errors
    """
    from .server import storage, conversation_engine

    if not storage or not conversation_engine:
        raise HTTPException(status_code=503, detail="Services not available")

    try:
        # Get all learning paths
        learning_paths = storage.list_learning_paths()

        # Get progress summary from conversation engine
        progress_summary = conversation_engine.get_progress_summary()

        return {
            "learning_paths": [
                {
                    "id": path.id,
                    "topic_name": path.topic_name,
                    "progress": (path.current_topic_index / len(path.topics)) * 100 if path.topics else 0,
                    "current_topic": path.topics[path.current_topic_index].title if path.current_topic_index < len(path.topics) else None
                }
                for path in [storage.load_learning_path(path_data["id"]) for path_data in storage.list_learning_paths()]
                if path is not None
            ],
            "overall_progress": progress_summary,
            "total_paths": len(storage.list_learning_paths()),
            "completed_paths": sum(1 for path in [storage.load_learning_path(path_data["id"]) for path_data in storage.list_learning_paths()] if path and path.current_topic_index >= len(path.topics))
        }

    except Exception as e:
        logger.error(f"Error fetching progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch progress")


# Bite-Sized Topic Endpoints

@router.get("/api/bite-sized-topics", response_model=List[BiteSizedTopicResponse])
async def get_bite_sized_topics():
    """
    Get all bite-sized topics.

    Returns a list of all available bite-sized topics with summary information.

    Returns:
        list: List of bite-sized topic summaries

    Raises:
        HTTPException: 503 if storage service unavailable, 500 for other errors
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
            id=topic_id,  # Use the provided topic_id
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
            created_at="",  # Will be filled from metadata if available
            updated_at=""   # Will be filled from metadata if available
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bite-sized topic detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch bite-sized topic detail")


@router.post("/api/bite-sized-topics/{topic_id}/start-conversation")
async def start_bite_sized_topic_conversation(topic_id: str):
    """
    Start a conversation session for a bite-sized topic.

    Initializes a conversational learning session directly for a bite-sized topic,
    bypassing the learning path structure for simplified prototyping.

    Args:
        topic_id (str): Bite-sized topic identifier

    Returns:
        dict: Conversation session information including initial AI message

    Raises:
        HTTPException: 404 if topic not found, 503 if conversation engine unavailable, 500 for other errors
    """
    from .server import conversation_engine

    if not conversation_engine:
        raise HTTPException(status_code=503, detail="Conversation engine not available")

    try:
        # Import here to avoid circular imports
        from modules.lesson_planning.bite_sized_topics.postgresql_storage import PostgreSQLTopicRepository

        repository = PostgreSQLTopicRepository()
        topic_content = await repository.get_topic(topic_id)

        if not topic_content:
            raise HTTPException(status_code=404, detail="Bite-sized topic not found")

        # For now, we'll create a simple session using existing conversation engine
        # In the future, this would be replaced with a bite-sized topic specific engine
        session = conversation_engine.start_conversation("bite-sized", topic_id)

        # Get the initial AI message
        initial_message = ""
        if session.messages:
            last_message = session.messages[-1]
            if last_message.role == MessageRole.ASSISTANT:
                initial_message = last_message.content

        return {
            "session_id": f"bite-sized_{topic_id}",
            "ai_message": initial_message,
            "conversation_state": session.conversation_state.value if hasattr(session.conversation_state, 'value') else str(session.conversation_state),
            "topic_title": topic_content.topic_spec.topic_title
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting bite-sized topic conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")