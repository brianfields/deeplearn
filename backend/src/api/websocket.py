"""
WebSocket endpoint and helper functions for real-time conversational learning.

This module contains the main WebSocket endpoint for interactive learning
conversations and all related helper functions for sending updates to clients.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

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
    MessageRole = llm_interface.MessageRole

except ImportError as e:
    print(f"Import error in websocket.py: {e}")
    import traceback
    traceback.print_exc()

logger = logging.getLogger(__name__)

# Create router for WebSocket endpoints
router = APIRouter()


@router.websocket("/ws/conversation/{topic_id}")
async def websocket_conversation(websocket: WebSocket, topic_id: str):
    """
    WebSocket endpoint for real-time conversational learning.

    This endpoint establishes a persistent WebSocket connection for interactive learning
    conversations with an AI tutor. It handles the full conversation lifecycle including
    initialization, message exchange, progress tracking, and error handling.

    Connection Flow:
    1. Client connects to ws://localhost:8000/ws/conversation/{topic_id}
    2. Server validates services and finds learning path containing the topic
    3. Server initializes or continues existing conversation session
    4. Server sends welcome message (for new conversations) and initial state
    5. Client and server exchange messages in real-time
    6. Server provides progress updates and session state changes

    Message Types Sent by Server:
    - "chat_message": AI tutor responses and system messages
    - "progress_update": Learning progress, objectives, concepts covered
    - "session_state": Teaching strategy, learning phase, debug info
    - "error": Error messages and service unavailability

    Expected Client Message Format:
    {
        "message": "user's text message"
    }

    Expected Client Usage:
    - Send JSON messages with "message" field containing user input
    - Listen for different message types and handle appropriately
    - Display chat_message content in conversation UI
    - Update progress indicators from progress_update messages
    - Show debug/strategy info from session_state messages (optional)
    - Handle error messages gracefully

    Example Client Code:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/conversation/topic-123');

    ws.onopen = () => {
        console.log('Connected to learning session');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch(data.type) {
            case 'chat_message':
                displayMessage(data.message.content, data.message.role);
                break;
            case 'progress_update':
                updateProgressIndicators(data.progress);
                break;
            case 'session_state':
                updateDebugInfo(data.state); // Optional for debugging
                break;
            case 'error':
                handleError(data.message);
                break;
        }
    };

    // Send user message
    ws.send(JSON.stringify({
        message: "I have a question about this topic"
    }));
    ```

    Args:
        websocket (WebSocket): The WebSocket connection object
        topic_id (str): Unique identifier for the learning topic

    Raises:
        WebSocketDisconnect: When client disconnects (handled gracefully)
        Exception: Various errors during conversation processing

    Notes:
        - Requires conversation_engine and storage services to be available
        - Automatically finds learning path containing the specified topic
        - Maintains conversation state between messages
        - Provides real-time progress tracking and teaching strategy updates
        - Handles both new and continuing conversations seamlessly
    """
    # Get services from global state (will be injected by dependency injection)
    from .server import conversation_engine, storage

    await websocket.accept()

    try:
        # Check if conversation engine is available
        if not conversation_engine or not storage:
            await websocket.send_json({
                "type": "error",
                "message": "Conversation service not available"
            })
            return

        # Find the learning path that contains this topic
        learning_path_id = None

        # First, check if this is a bite-sized topic
        bite_sized_path_id = f"bite-sized-{topic_id}"
        bite_sized_path = storage.get_learning_path(bite_sized_path_id)

        if bite_sized_path:
            # This is a bite-sized topic
            learning_path_id = bite_sized_path_id
            logger.info(f"Found bite-sized topic learning path: {learning_path_id}")
        else:
            # Fall back to searching through all learning paths
            learning_paths = storage.list_learning_paths()

            for path_data in learning_paths:
                # Load the full learning path to check its topics
                learning_path = storage.get_learning_path(path_data["id"])
                if learning_path:
                    # Check if any topic in this learning path matches our topic_id
                    for topic in learning_path.topics:
                        if topic.get('id') == topic_id:
                            learning_path_id = learning_path.id
                            break
                    if learning_path_id:
                        break

        if not learning_path_id:
            await websocket.send_json({
                "type": "error",
                "message": f"No learning path found containing topic {topic_id}"
            })
            return

        # Initialize or continue conversation
        session = None
        try:
            logger.info(f"Attempting to start/continue conversation for topic: {topic_id}")
            session = conversation_engine.continue_conversation(learning_path_id, topic_id)
            if not session:
                logger.info(f"Starting new conversation for topic: {topic_id}")
                session = conversation_engine.start_conversation(learning_path_id, topic_id)

                # Send welcome message for new conversations
                learning_path = storage.get_learning_path(learning_path_id)
                if learning_path:
                    topic = next((t for t in learning_path.topics if t.get('id') == topic_id), None)

                    if topic:
                        logger.info(f"Preparing welcome message for topic: {topic.get('title', 'Unknown Topic')}")
                        welcome_message = f"""Welcome to your learning journey on {topic.get('title', 'Unknown Topic')}!

I'm your AI tutor, and I'm excited to guide you through this topic. Here's what we'll explore together:

Learning Objectives:
{chr(10).join(f"• {obj}" for obj in topic.get('learning_objectives', []))}

I'll adapt my teaching style based on how you're doing, using different approaches like:
- Direct instruction when you need clear explanations
- Socratic questioning to help you discover insights
- Guided practice for hands-on learning
- Assessment to check your understanding

Feel free to ask questions, request examples, or let me know if you'd like me to explain something differently. Let's start learning!

What would you like to begin with, or do you have any questions about {topic.get('title', 'Unknown Topic')}?"""

                        # Send the welcome message
                        try:
                            logger.info(f"Sending welcome message for topic: {topic.get('title', 'Unknown Topic')}")
                            await websocket.send_json({
                                "type": "chat_message",
                                "message": {
                                    "role": "assistant",
                                    "content": welcome_message,
                                    "timestamp": datetime.now().isoformat()
                                }
                            })
                            logger.info(f"Successfully sent welcome message for topic: {topic.get('title', 'Unknown Topic')}")
                        except Exception as e:
                            logger.error(f"Failed to send welcome message: {str(e)}")
                            logger.exception("Welcome message error details:")
                    else:
                        logger.warning(f"Could not find topic {topic_id} in learning path {learning_path_id}")
            else:
                logger.info(f"Continuing existing conversation for topic: {topic_id}")
        except Exception as e:
            logger.error(f"Failed to initialize conversation: {str(e)}")
            logger.exception("Conversation initialization error details:")
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Failed to start conversation: {str(e)}"
                })
            except:
                logger.error("Could not send error message - WebSocket may be closed")
                return

        # Send initial session state and progress if session exists
        if session:
            try:
                logger.info(f"Attempting to send session state update for topic: {topic_id}")
                await send_session_state_update(websocket, session)
                logger.info(f"Successfully sent session state update for topic: {topic_id}")
            except Exception as e:
                logger.error(f"Failed to send initial session state: {e}")
                logger.exception("Session state error details:")

            try:
                logger.info(f"Attempting to send progress update for topic: {topic_id}")
                await send_progress_update(websocket, session, topic_id=topic_id)
                logger.info(f"Successfully sent progress update for topic: {topic_id}")
            except Exception as e:
                logger.error(f"Failed to send initial progress: {e}")
                logger.exception("Progress update error details:")

        # Main message loop - handle incoming messages from client
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            user_message = data.get("message", "")

            if not user_message.strip():
                continue

            # Process message with enhanced conversational learning
            try:
                ai_response, progress_info = await conversation_engine.process_user_message(user_message)

                # Send AI response
                await websocket.send_json({
                    "type": "chat_message",
                    "message": {
                        "role": "assistant",
                        "content": ai_response,
                        "timestamp": datetime.now().isoformat()
                    }
                })

                # Send updated progress and session state with topic info
                if session:
                    await send_progress_update(websocket, session, progress_info, topic_id=topic_id)
                    await send_session_state_update(websocket, session)

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Failed to process message"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for topic {topic_id}")
    except Exception as e:
        logger.error(f"WebSocket error for topic {topic_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        except:
            pass  # Connection might already be closed


async def send_progress_update(websocket: WebSocket, session: "EnhancedConversationSession", progress_info: Optional[Dict] = None, topic_id: Optional[str] = None):
    """
    Send progress update to WebSocket client with enhanced learning progress details.

    This function sends comprehensive progress information to help the client display
    learning progress, objectives completion, concept understanding, and sub-topic status.

    Message Format Sent:
    {
        "type": "progress_update",
        "progress": {
            "understanding_level": int,        // 0-100 scale
            "engagement_score": int,           // 0-100 scale
            "objectives_covered": list,        // List of completed objectives
            "topic_title": str,                // Human-readable topic name
            "learning_objectives": [           // Detailed objective status
                {
                    "text": str,               // Objective description
                    "status": str              // "not_started", "introduced", "mastered"
                }
            ],
            "key_concepts": [                  // Core concepts and their status
                {
                    "name": str,               // Concept name
                    "status": str,             // "not_covered", "introduced", "mastered"
                    "definition": str          // Brief definition (optional)
                }
            ],
            "sub_topics": [                    // Sub-topic progress breakdown
                {
                    "name": str,               // Sub-topic name
                    "status": str,             // "upcoming", "current", "completed"
                    "progress_percentage": int // 0-100 completion percentage
                }
            ]
        }
    }

    Args:
        websocket (WebSocket): The WebSocket connection to send to
        session (EnhancedConversationSession): Current learning session
        progress_info (Optional[Dict]): Progress data from conversation engine
        topic_id (Optional[str]): Topic identifier for detailed progress lookup

    Usage by Client:
    - Display overall progress bars using understanding_level and engagement_score
    - Show learning objectives checklist with status indicators
    - Display key concepts with mastery indicators
    - Show sub-topic navigation with progress indicators
    - Update UI elements in real-time as learning progresses
    """
    from .server import conversation_engine, storage

    try:
        logger.info(f"Starting progress update for topic: {topic_id}")

        # Get progress info with error handling
        if not progress_info and conversation_engine:
            try:
                logger.info("Getting progress summary from conversation engine")
                progress_info = conversation_engine.get_progress_summary()
                logger.info(f"Got progress info: {progress_info}")
            except Exception as e:
                logger.error(f"Failed to get progress summary: {e}")
                progress_info = {}

        if not progress_info:
            progress_info = {}
            logger.info("Using empty progress info")

        # Get topic information for detailed progress
        topic_title = None
        learning_objectives = []

        # Try to get actual topic data from storage
        if topic_id and storage:
            try:
                logger.info(f"Looking up topic data for: {topic_id}")
                # Find the learning path containing this topic
                all_paths = storage.list_learning_paths()
                for path_data in all_paths:
                    learning_path = storage.get_learning_path(path_data["id"])
                    if learning_path:
                        for topic in learning_path.topics:
                            if topic.get('id') == topic_id:
                                topic_title = topic.get('title', 'Unknown Topic')
                                # Convert learning objectives to status format
                                learning_objectives = [
                                    {"text": obj, "status": "introduced" if i == 0 else "not_started"}
                                    for i, obj in enumerate(topic.get('learning_objectives', []))
                                ]
                                logger.info(f"Found topic: {topic_title} with {len(learning_objectives)} objectives")
                                break
                        if topic_title:
                            break
            except Exception as e:
                logger.error(f"Error getting topic data: {e}")

        # Sample concepts and subtopics for demonstration
        # In production, these would come from the teaching engine analysis
        sample_concepts = [
            {"name": "Core Principles", "status": "introduced", "definition": "Fundamental concepts of the topic"},
            {"name": "Key Terminology", "status": "not_covered"},
            {"name": "Practical Applications", "status": "not_covered"}
        ]

        sample_subtopics = [
            {"name": "Introduction & Overview", "status": "current", "progress_percentage": 30},
            {"name": "Core Concepts", "status": "upcoming", "progress_percentage": 0},
            {"name": "Advanced Topics", "status": "upcoming", "progress_percentage": 0}
        ]

        # Safely get session objectives
        objectives_covered = []
        if session:
            try:
                if hasattr(session, 'learning_objectives'):
                    objectives_covered = session.learning_objectives
                elif hasattr(session, 'objectives_covered'):
                    objectives_covered = getattr(session, 'objectives_covered', [])
                logger.info(f"Found {len(objectives_covered)} objectives from session")
            except Exception as e:
                logger.error(f"Error getting session objectives: {e}")

        logger.info("Sending progress update JSON")
        await websocket.send_json({
            "type": "progress_update",
            "progress": {
                "understanding_level": progress_info.get("understanding_level", 0),
                "engagement_score": progress_info.get("engagement_score", 0),
                "concepts_covered": [],  # Legacy field
                "concepts_mastered": [],  # Legacy field
                "objectives_covered": objectives_covered,
                # Enhanced progress fields
                "topic_title": topic_title,
                "learning_objectives": learning_objectives,
                "key_concepts": sample_concepts,
                "sub_topics": sample_subtopics
            }
        })
        logger.info("Successfully sent progress update")
    except Exception as e:
        logger.error(f"Error sending progress update: {e}")
        logger.exception("Progress update exception details:")


async def send_session_state_update(websocket: WebSocket, session: "EnhancedConversationSession"):
    """
    Send session state update with teaching strategy and learning phase information.

    This function provides detailed information about the current teaching session,
    including the AI tutor's teaching strategy, learning phase, and diagnostic information
    useful for debugging and understanding the learning process.

    Message Format Sent:
    {
        "type": "session_state",
        "state": {
            "phase": str,                      // Current learning phase: "introduction", "exploration", "practice", "assessment"
            "last_strategy": str,              // Last teaching strategy used
            "session_duration_minutes": int,   // How long the session has been active
            "confusion_level": int,            // 0-100 scale of student confusion
            "learning_velocity": int,          // 0-100 scale of learning speed
            "needs_encouragement": bool,       // Whether student needs motivation
            "strategy_confidence": int,        // 0-100 AI confidence in current strategy
            "strategy_reasoning": str,         // Why the AI chose this strategy
            "available_strategies": [str],     // List of available teaching strategies
            "performance_history": [dict]      // Historical performance data
        }
    }

    Available Teaching Strategies:
    - "direct_instruction": Clear explanations and information delivery
    - "socratic_inquiry": Question-based learning to guide discovery
    - "guided_practice": Hands-on exercises with support
    - "assessment": Testing understanding and knowledge
    - "encouragement": Motivation and confidence building

    Args:
        websocket (WebSocket): The WebSocket connection to send to
        session (EnhancedConversationSession): Current learning session

    Usage by Client:
    - Display current learning phase to user
    - Show teaching strategy information in debug panels
    - Adjust UI based on confusion level (offer help options)
    - Display encouragement messages when needed
    - Show session duration and learning velocity metrics
    - Provide strategy reasoning for educational transparency
    """
    from .server import conversation_engine

    try:
        logger.info("Starting session state update")
        session_info = None
        progress_info = {}

        if conversation_engine:
            try:
                logger.info("Getting session info from conversation engine")
                session_info = conversation_engine.get_session_info()
                logger.info(f"Got session info: {session_info}")
            except Exception as e:
                logger.error(f"Failed to get session info: {e}")
                session_info = None

            try:
                logger.info("Getting progress summary from conversation engine")
                progress_info = conversation_engine.get_progress_summary()
                logger.info(f"Got progress summary: {progress_info}")
            except Exception as e:
                logger.error(f"Failed to get progress summary for session state: {e}")
                progress_info = {}

        # Extract debug information from the teaching engine session with safe access
        debug_state = {
            "phase": session_info.get("current_phase", "introduction") if session_info else "introduction",
            "last_strategy": getattr(session, 'last_strategy', None) if session else None,
            "session_duration_minutes": session_info.get("session_duration", 0) if session_info else 0,
            "confusion_level": 0,  # Will be populated by teaching engine
            "learning_velocity": progress_info.get("learning_velocity", 0),
            "needs_encouragement": progress_info.get("needs_encouragement", False),
            "strategy_confidence": 0,  # Will be populated by teaching engine
            "strategy_reasoning": "",  # Will be populated by teaching engine
            "available_strategies": ["direct_instruction", "socratic_inquiry", "guided_practice", "assessment", "encouragement"],
            "performance_history": []  # Will be populated by teaching engine
        }

        logger.info("Sending session state JSON")
        await websocket.send_json({
            "type": "session_state",
            "state": debug_state
        })
        logger.info("Successfully sent session state update")
    except Exception as e:
        logger.error(f"Error sending session state update: {e}")
        logger.exception("Session state update exception details:")


def extract_debug_info(session, topic):
    """
    Extract debug information from session and topic for development debugging.

    This function extracts detailed diagnostic information from the current learning
    session and topic for debugging and development purposes. It provides insights
    into the AI tutor's decision-making process and student model state.

    Args:
        session: Current conversation session object
        topic: Topic object being learned

    Returns:
        dict: Comprehensive debug information including:
            - session_id: Unique session identifier
            - topic_title: Human-readable topic name
            - student_model_state: Current assessment of student
            - teaching_decisions: AI tutor's strategy decisions

    Usage:
        This function is primarily used for debugging and development purposes
        to understand how the AI tutor is making teaching decisions and
        assessing student progress.
    """
    return {
        "session_id": getattr(session, 'session_id', 'unknown'),
        "topic_title": getattr(topic, 'title', 'unknown'),
        "student_model_state": {
            "understanding_level": getattr(session, 'understanding_level', 0),
            "engagement_score": getattr(session, 'engagement_score', 0),
            "confusion_level": getattr(session, 'confusion_level', 0),
            "learning_velocity": getattr(session, 'learning_velocity', 0)
        },
        "teaching_decisions": {
            "current_strategy": getattr(session, 'last_strategy', None),
            "strategy_reasoning": getattr(session, 'strategy_reasoning', ''),
            "strategy_confidence": getattr(session, 'strategy_confidence', 0),
            "available_strategies": getattr(session, 'available_strategies', [])
        }
    }