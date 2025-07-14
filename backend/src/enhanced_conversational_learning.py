"""
Enhanced Conversational Learning - Integrates with Teaching Engine
Uses rule-based strategy selection for adaptive teaching
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from llm_interface import LLMProvider, LLMMessage, MessageRole
from database_service import DatabaseService
from teaching_engine import (
    TeachingEngine, TopicMetadata, TeachingStrategy, LearningPhase,
    StudentModel, LearningSession
)

logger = logging.getLogger(__name__)

class ConversationState(str, Enum):
    """States of the learning conversation"""
    STARTING = "starting"
    EXPLORING = "exploring"
    PRACTICING = "practicing"
    DEEPENING = "deepening"
    ASSESSING = "assessing"
    TRANSITIONING = "transitioning"
    COMPLETED = "completed"

@dataclass
class EnhancedConversationSession:
    """Enhanced conversation session that includes teaching engine data"""
    learning_path_id: str
    topic_id: str
    topic_title: str
    learning_objectives: List[str]
    teaching_session_id: str  # Links to TeachingEngine session
    conversation_state: ConversationState = ConversationState.STARTING
    messages: List[LLMMessage] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

class EnhancedConversationalLearningEngine:
    """
    Enhanced conversational learning engine using TeachingEngine for strategy selection
    """

    def __init__(self, llm_provider: LLMProvider, storage: DatabaseService):
        self.llm_provider = llm_provider
        self.storage = storage
        self.teaching_engine = TeachingEngine(llm_provider)
        self.current_session: Optional[EnhancedConversationSession] = None

        # Configuration
        self.session_storage: Dict[str, EnhancedConversationSession] = {}

    def start_conversation(self, learning_path_id: str, topic_id: str) -> EnhancedConversationSession:
        """Start a new learning conversation with teaching engine integration"""

        # Load learning path and topic
        learning_path = self.storage.get_learning_path(learning_path_id)
        if not learning_path:
            raise ValueError(f"Learning path {learning_path_id} not found")

        topic = next((t for t in learning_path.topics if t.get('id') == topic_id), None)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")

        # Create topic metadata for teaching engine
        topic_metadata = self._create_topic_metadata(topic, learning_path)

        # Create teaching engine session
        teaching_session_id = self.teaching_engine.create_session(
            student_id="user",  # For now, using generic user ID
            topic_id=topic_id,
            topic_metadata=topic_metadata
        )

        # Create enhanced conversation session
        session = EnhancedConversationSession(
            learning_path_id=learning_path_id,
            topic_id=topic_id,
            topic_title=topic.get('title', 'Unknown Topic'),
            learning_objectives=topic.get('learning_objectives', []),
            teaching_session_id=teaching_session_id
        )

        # Generate initial greeting using teaching engine
        initial_response = self._generate_initial_greeting(session, topic_metadata)
        session.messages.append(LLMMessage(
            role=MessageRole.ASSISTANT,
            content=initial_response,
            timestamp=datetime.utcnow()
        ))

        self.current_session = session
        self.session_storage[f"{learning_path_id}_{topic_id}"] = session

        logger.info(f"Started conversation for {topic.get('title', 'Unknown Topic')}")
        return session

    def continue_conversation(self, learning_path_id: str, topic_id: str) -> Optional[EnhancedConversationSession]:
        """Continue an existing conversation"""

        session_key = f"{learning_path_id}_{topic_id}"
        session = self.session_storage.get(session_key)

        if session:
            self.current_session = session
            logger.info(f"Continuing conversation for {session.topic_title}")

        return session

    async def process_user_message(self, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Process user message using teaching engine for strategy selection"""

        if not self.current_session:
            raise ValueError("No active conversation session")

        session = self.current_session

        # Add user message to session
        user_msg = LLMMessage(
            role=MessageRole.USER,
            content=user_message,
            timestamp=datetime.utcnow()
        )
        session.messages.append(user_msg)

        try:
            # Process through teaching engine
            teaching_response = await self.teaching_engine.process_student_interaction(
                message=user_message,
                session_id=session.teaching_session_id
            )

            # Add AI response to conversation
            ai_msg = LLMMessage(
                role=MessageRole.ASSISTANT,
                content=teaching_response.content,
                timestamp=datetime.utcnow()
            )
            session.messages.append(ai_msg)

            # Update session state
            session.last_updated = datetime.utcnow()
            self._update_conversation_state(session, teaching_response)

            # Get progress information
            teaching_session = self.teaching_engine.get_session(session.teaching_session_id)
            student_model = self.teaching_engine.get_student_model("user")

            progress_info = self._build_progress_info(teaching_session, student_model, teaching_response)

            logger.info(f"Processed message using strategy: {teaching_response.strategy_used.value}")

            return teaching_response.content, progress_info

        except Exception as e:
            logger.error(f"Error processing user message: {e}")
            # Fallback response
            fallback_response = "I'm having trouble processing that right now. Could you try rephrasing your question?"

            ai_msg = LLMMessage(
                role=MessageRole.ASSISTANT,
                content=fallback_response,
                timestamp=datetime.utcnow()
            )
            session.messages.append(ai_msg)

            return fallback_response, {"error": str(e)}

    def _create_topic_metadata(self, topic, learning_path) -> TopicMetadata:
        """Create topic metadata for the teaching engine"""

        # Determine recommended strategies based on topic characteristics
        recommended_strategies = []

        # If topic title suggests it's introductory, start with direct instruction
        if any(word in topic.title.lower() for word in ['introduction', 'basics', 'overview', 'fundamentals']):
            recommended_strategies.extend([TeachingStrategy.DIRECT_INSTRUCTION, TeachingStrategy.SOCRATIC_INQUIRY])

        # If it's about application or practice, use guided practice
        if any(word in topic.title.lower() for word in ['application', 'practice', 'implementation', 'example']):
            recommended_strategies.extend([TeachingStrategy.GUIDED_PRACTICE, TeachingStrategy.SOCRATIC_INQUIRY])

        # Default to socratic inquiry for engagement
        if not recommended_strategies:
            recommended_strategies = [TeachingStrategy.SOCRATIC_INQUIRY, TeachingStrategy.DIRECT_INSTRUCTION]

        # Estimate difficulty based on position in learning path
        topic_position = next((i for i, t in enumerate(learning_path.topics) if t.id == topic.id), 0)
        difficulty_level = min(5, max(1, (topic_position // 2) + 1))  # 1-5 scale

        return TopicMetadata(
            topic_id=topic.id,
            topic_name=topic.title,
            difficulty_level=difficulty_level,
            recommended_strategies=recommended_strategies,
            requires_visual_aids=False,  # Could be enhanced with topic analysis
            prerequisite_topics=[],  # Could be derived from learning path structure
            common_misconceptions=[],  # Could be enhanced with domain knowledge
            estimated_duration_minutes=15
        )

    def _generate_initial_greeting(self, session: EnhancedConversationSession, topic_metadata: TopicMetadata) -> str:
        """Generate initial greeting that sets the right tone for the topic"""

        # Use direct instruction strategy for introduction phase
        teaching_session = self.teaching_engine.get_session(session.teaching_session_id)

        if topic_metadata.difficulty_level <= 2:
            # Beginner-friendly introduction
            return f"""Hi! I'm excited to explore {session.topic_title} with you today.

This is a foundational topic that will give you a solid understanding of key concepts. Don't worry if it's completely new - we'll take it step by step.

To start, what's your experience with this area? Have you encountered {session.topic_title.lower()} before, or is this your first time learning about it?"""

        elif topic_metadata.difficulty_level >= 4:
            # Advanced topic introduction
            return f"""Welcome! Today we're diving into {session.topic_title} - an important and somewhat advanced topic.

This builds on concepts you've likely encountered before, so I'm curious about your background. What's your experience with related topics, and what specifically interests you about {session.topic_title.lower()}?"""

        else:
            # Intermediate topic introduction
            return f"""Hey there! Ready to explore {session.topic_title}?

This is an interesting topic that bridges foundational concepts with more practical applications. I'd love to know where you're coming from - what sparked your interest in learning about {session.topic_title.lower()}?"""

    def _update_conversation_state(self, session: EnhancedConversationSession, teaching_response):
        """Update conversation state based on teaching engine response"""

        # Map teaching engine phases to conversation states
        phase_to_state = {
            LearningPhase.INTRODUCTION: ConversationState.STARTING,
            LearningPhase.EXPLORATION: ConversationState.EXPLORING,
            LearningPhase.PRACTICE: ConversationState.PRACTICING,
            LearningPhase.ASSESSMENT: ConversationState.ASSESSING,
            LearningPhase.CONSOLIDATION: ConversationState.TRANSITIONING
        }

        new_state = phase_to_state.get(teaching_response.phase_used, session.conversation_state)

        if new_state != session.conversation_state:
            logger.info(f"Conversation state transition: {session.conversation_state.value} -> {new_state.value}")
            session.conversation_state = new_state

    def _build_progress_info(self, teaching_session: Optional[LearningSession],
                           student_model: Optional[StudentModel],
                           teaching_response) -> Dict[str, Any]:
        """Build progress information for the frontend"""

        if not teaching_session or not student_model:
            return {
                "understanding_level": 0.5,
                "engagement_score": 0.5,
                "message_count": 0,
                "concepts_covered": [],
                "concepts_mastered": [],
                "current_phase": "introduction",
                "strategy_used": "socratic_inquiry"
            }

        current_performance = student_model.get_current_performance()

        return {
            "understanding_level": current_performance.understanding_score,
            "engagement_score": current_performance.engagement_score,
            "message_count": teaching_session.interaction_count,
            "concepts_covered": teaching_session.objectives_covered,
            "concepts_mastered": [],  # Could be enhanced with mastery tracking
            "current_phase": teaching_session.current_phase.value,
            "strategy_used": teaching_response.strategy_used.value,
            "confusion_level": current_performance.confusion_level,
            "learning_velocity": student_model.learning_velocity,
            "session_duration": teaching_session.total_session_time().total_seconds() / 60
        }

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get overall progress summary across all sessions"""

        if not self.current_session:
            return {}

        student_model = self.teaching_engine.get_student_model("user")
        if not student_model:
            return {}

        current_performance = student_model.get_current_performance()

        return {
            "understanding_level": current_performance.understanding_score,
            "engagement_score": current_performance.engagement_score,
            "total_interactions": current_performance.total_interactions,
            "correct_responses": current_performance.correct_responses,
            "concepts_mastered": 0,  # Placeholder
            "learning_velocity": student_model.learning_velocity,
            "needs_encouragement": student_model.needs_encouragement
        }

    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get current session information"""

        if not self.current_session:
            return None

        teaching_session = self.teaching_engine.get_session(self.current_session.teaching_session_id)

        return {
            "topic_title": self.current_session.topic_title,
            "learning_objectives": self.current_session.learning_objectives,
            "conversation_state": self.current_session.conversation_state.value,
            "current_phase": teaching_session.current_phase.value if teaching_session else "unknown",
            "message_count": len(self.current_session.messages),
            "session_duration": (datetime.utcnow() - self.current_session.started_at).total_seconds() / 60
        }

    def end_conversation(self, learning_path_id: str) -> Dict[str, Any]:
        """End the current conversation and return summary"""

        if not self.current_session:
            return {"error": "No active session"}

        session = self.current_session
        student_model = self.teaching_engine.get_student_model("user")

        summary = {
            "topic_title": session.topic_title,
            "duration_minutes": (datetime.utcnow() - session.started_at).total_seconds() / 60,
            "message_count": len(session.messages),
            "final_understanding": student_model.get_current_performance().understanding_score if student_model else 0.5,
            "objectives_covered": session.learning_objectives
        }

        # Mark session as completed
        session.conversation_state = ConversationState.COMPLETED
        session.last_updated = datetime.utcnow()

        self.current_session = None

        logger.info(f"Ended conversation for {session.topic_title}")
        return summary