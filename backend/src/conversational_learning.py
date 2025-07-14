"""
Conversational Learning Engine

This module provides a ChatGPT-like conversational learning experience
with Socratic dialogue and real-time progress tracking.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from llm_interface import LLMMessage, MessageRole, LLMProvider
from prompt_engineering import PromptFactory, PromptType, PromptContext
from database_service import DatabaseService
from data_structures import SimpleLearningPath, ProgressStatus

logger = logging.getLogger(__name__)

class ConversationState(str, Enum):
    """States of the learning conversation"""
    STARTING = "starting"              # Beginning of topic
    EXPLORING = "exploring"            # Learning new concepts
    PRACTICING = "practicing"          # Applying knowledge
    DEEPENING = "deepening"           # Going deeper into concepts
    ASSESSING = "assessing"           # Checking understanding
    TRANSITIONING = "transitioning"   # Moving to next topic
    COMPLETED = "completed"           # Topic finished

@dataclass
class ConversationProgress:
    """Track progress within a conversation"""
    concepts_covered: List[str] = field(default_factory=list)
    concepts_mastered: List[str] = field(default_factory=list)
    current_concept: Optional[str] = None
    understanding_level: float = 0.0  # 0.0 to 1.0
    engagement_score: float = 0.0     # 0.0 to 1.0
    time_spent: int = 0               # minutes
    message_count: int = 0
    last_assessment: Optional[Dict[str, Any]] = None

@dataclass
class ConversationSession:
    """A learning conversation session"""
    topic_id: str
    topic_title: str
    learning_objectives: List[str]
    state: ConversationState = ConversationState.STARTING
    progress: ConversationProgress = field(default_factory=ConversationProgress)
    messages: List[LLMMessage] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

class ConversationalLearningEngine:
    """
    Main engine for conversational learning experiences.

    Provides ChatGPT-like interaction with proactive Socratic dialogue
    and real-time progress tracking.
    """

    def __init__(self, llm_provider: LLMProvider, storage: DatabaseService):
        self.llm_provider = llm_provider
        self.storage = storage
        self.current_session: Optional[ConversationSession] = None

        # Configuration
        self.progress_check_interval = 5  # Check progress every 5 messages
        self.concept_mastery_threshold = 0.8
        self.engagement_threshold = 0.6

    def start_conversation(self, learning_path_id: str, topic_id: str) -> ConversationSession:
        """Start a new learning conversation"""

                # Load learning path and topic
        learning_path = self.storage.get_learning_path(learning_path_id)
        if not learning_path:
            raise ValueError(f"Learning path {learning_path_id} not found")

        topic = next((t for t in learning_path.topics if t.get('id') == topic_id), None)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")

        # Create conversation session
        session = ConversationSession(
            topic_id=topic_id,
            topic_title=topic.get('title', 'Unknown Topic'),
            learning_objectives=topic.get('learning_objectives', [])
        )

        # Add system message
        system_message = self._create_system_message(session)
        session.messages.append(system_message)

        # Add initial greeting
        greeting = self._create_initial_greeting(session)
        session.messages.append(greeting)

        self.current_session = session

        # Save session
        self._save_session(learning_path_id, session)

        return session

    def continue_conversation(self, learning_path_id: str, topic_id: str) -> Optional[ConversationSession]:
        """Continue an existing conversation"""

        session = self._load_session(learning_path_id, topic_id)
        if session:
            self.current_session = session

        return session

    async def process_user_message(self, user_message: str) -> Tuple[str, ConversationProgress]:
        """Process user message and generate AI response"""

        if not self.current_session:
            raise ValueError("No active conversation session")

        session = self.current_session

        # Add user message
        user_msg = LLMMessage(
            role=MessageRole.USER,
            content=user_message,
            timestamp=datetime.now()
        )
        session.messages.append(user_msg)
        session.progress.message_count += 1

        # Update engagement score based on message length and content
        self._update_engagement_score(user_message)

        # Check if we need to assess progress
        should_assess = session.progress.message_count % self.progress_check_interval == 0

        # Generate AI response
        ai_response = await self._generate_ai_response(session, should_assess)

        # Add AI message
        ai_msg = LLMMessage(
            role=MessageRole.ASSISTANT,
            content=ai_response,
            timestamp=datetime.now()
        )
        session.messages.append(ai_msg)

        # Update session
        session.last_updated = datetime.now()

        # Save session
        learning_path = self._get_learning_path_from_session(session)
        self._save_session(learning_path, session)

        return ai_response, session.progress

    def _create_system_message(self, session: ConversationSession) -> LLMMessage:
        """Create system message for the conversation"""

        system_prompt = f"""You are an expert Socratic tutor teaching about "{session.topic_title}".

Your role is to guide the student through learning using conversational dialogue, not traditional Q&A.

LEARNING OBJECTIVES:
{chr(10).join(f"- {obj}" for obj in session.learning_objectives)}

CONVERSATION GUIDELINES:
1. Be conversational and engaging like ChatGPT
2. Use Socratic questioning to guide discovery
3. Ask probing questions that help students think deeper
4. Provide explanations when needed, but encourage thinking first
5. Use real-world examples and analogies
6. Adapt to the student's responses and understanding level
7. Be encouraging and supportive
8. Keep responses focused but conversational (not lecture-like)

PROGRESS TRACKING:
- Track concepts the student understands vs struggles with
- Note when they demonstrate mastery of learning objectives
- Adjust difficulty based on their responses

CONVERSATION FLOW:
- Start with engaging introduction and connection to prior knowledge
- Guide through concepts using questions and examples
- Check understanding through dialogue, not formal tests
- Encourage questions and curiosity
- Help them connect new knowledge to what they already know

Remember: This is a conversation, not a lesson plan. Be responsive to what the student says and guide them naturally through the learning objectives."""

        return LLMMessage(
            role=MessageRole.SYSTEM,
            content=system_prompt,
            timestamp=datetime.now()
        )

    def _create_initial_greeting(self, session: ConversationSession) -> LLMMessage:
        """Create initial greeting message"""

        greeting = f"""Hey there! I'm excited to explore {session.topic_title} with you today.

Instead of diving straight into definitions, let me ask you this: What comes to mind when you think about {session.topic_title.lower()}? Have you encountered this concept before, maybe in your work or daily life?

I'm curious about your perspective before we start our journey together! 🤔"""

        return LLMMessage(
            role=MessageRole.ASSISTANT,
            content=greeting,
            timestamp=datetime.now()
        )

    async def _generate_ai_response(self, session: ConversationSession, should_assess: bool = False) -> str:
        """Generate AI response using the conversation history"""

        # Prepare context for assessment if needed
        assessment_context = ""
        if should_assess:
            assessment_context = f"""

PROGRESS CHECK: Based on the conversation so far, assess:
1. Which concepts has the student grasped well?
2. What areas need more exploration?
3. Are they ready to move to the next concept or need more practice?
4. Adjust your teaching approach based on their responses.

Current progress: {session.progress.understanding_level:.1%} understanding
"""

        # Create conversation context
        conversation_context = f"""
CURRENT TOPIC: {session.topic_title}
CONVERSATION STATE: {session.state.value}
CONCEPTS COVERED: {', '.join(session.progress.concepts_covered) if session.progress.concepts_covered else 'None yet'}
CURRENT CONCEPT: {session.progress.current_concept or 'Getting started'}

{assessment_context}

Continue the Socratic dialogue naturally. Ask thoughtful questions, provide insights, and guide the student's discovery. Be conversational and engaging.
"""

        # Add context as system message (temporarily)
        context_msg = LLMMessage(
            role=MessageRole.SYSTEM,
            content=conversation_context,
            timestamp=datetime.now()
        )

        # Prepare messages for LLM
        messages = session.messages + [context_msg]

        # Generate response
        response = await self.llm_provider.generate_response(messages)

        # Update progress based on response
        self._update_progress_from_response(session, response.content)

        return response.content

    def _update_engagement_score(self, user_message: str) -> None:
        """Update engagement score based on user message"""

        if not self.current_session:
            return

        session = self.current_session

        # Simple engagement scoring based on message length and content
        message_length = len(user_message.split())

        # Score based on length (longer messages = more engagement)
        length_score = min(message_length / 20, 1.0)  # Normalize to 1.0

        # Score based on content indicators
        content_score = 0.5
        engagement_indicators = [
            "why", "how", "what if", "i think", "my experience",
            "interesting", "question", "example", "because"
        ]

        for indicator in engagement_indicators:
            if indicator in user_message.lower():
                content_score += 0.1

        content_score = min(content_score, 1.0)

        # Update running average
        new_score = (length_score + content_score) / 2
        session.progress.engagement_score = (
            session.progress.engagement_score * 0.8 + new_score * 0.2
        )

    def _update_progress_from_response(self, session: ConversationSession, ai_response: str) -> None:
        """Update progress tracking based on AI response"""

        # Simple heuristics to track progress
        # In a more sophisticated version, this could use NLP to analyze understanding

        # Check for concept introduction
        concept_keywords = ["concept", "principle", "idea", "theory", "approach"]
        if any(keyword in ai_response.lower() for keyword in concept_keywords):
            if session.progress.current_concept:
                if session.progress.current_concept not in session.progress.concepts_covered:
                    session.progress.concepts_covered.append(session.progress.current_concept)

        # Check for mastery indicators
        mastery_keywords = ["excellent", "exactly", "perfect", "great understanding", "you've got it"]
        if any(keyword in ai_response.lower() for keyword in mastery_keywords):
            if session.progress.current_concept and session.progress.current_concept not in session.progress.concepts_mastered:
                session.progress.concepts_mastered.append(session.progress.current_concept)

        # Update understanding level
        total_objectives = len(session.learning_objectives)
        if total_objectives > 0:
            mastered_count = len(session.progress.concepts_mastered)
            session.progress.understanding_level = min(mastered_count / total_objectives, 1.0)

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary"""

        if not self.current_session:
            return {}

        session = self.current_session
        progress = session.progress

        return {
            "topic_title": session.topic_title,
            "conversation_state": session.state.value,
            "understanding_level": progress.understanding_level,
            "engagement_score": progress.engagement_score,
            "concepts_covered": progress.concepts_covered,
            "concepts_mastered": progress.concepts_mastered,
            "current_concept": progress.current_concept,
            "message_count": progress.message_count,
            "time_spent": progress.time_spent,
            "objectives_completed": f"{len(progress.concepts_mastered)}/{len(session.learning_objectives)}"
        }

    def _save_session(self, learning_path_id: str, session: ConversationSession) -> None:
        """Save conversation session to storage"""

        session_data = {
            "topic_id": session.topic_id,
            "topic_title": session.topic_title,
            "learning_objectives": session.learning_objectives,
            "state": session.state.value,
            "progress": {
                "concepts_covered": session.progress.concepts_covered,
                "concepts_mastered": session.progress.concepts_mastered,
                "current_concept": session.progress.current_concept,
                "understanding_level": session.progress.understanding_level,
                "engagement_score": session.progress.engagement_score,
                "time_spent": session.progress.time_spent,
                "message_count": session.progress.message_count,
                "last_assessment": session.progress.last_assessment
            },
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in session.messages
            ],
            "started_at": session.started_at.isoformat(),
            "last_updated": session.last_updated.isoformat()
        }

        # Save to storage
        self.storage.save_current_session(session_data)

    def _load_session(self, learning_path_id: str, topic_id: str) -> Optional[ConversationSession]:
        """Load conversation session from storage"""

        try:
            session_data = self.storage.get_current_session()

            if not session_data or session_data.get("topic_id") != topic_id:
                return None

            # Reconstruct session
            progress = ConversationProgress(
                concepts_covered=session_data["progress"]["concepts_covered"],
                concepts_mastered=session_data["progress"]["concepts_mastered"],
                current_concept=session_data["progress"]["current_concept"],
                understanding_level=session_data["progress"]["understanding_level"],
                engagement_score=session_data["progress"]["engagement_score"],
                time_spent=session_data["progress"]["time_spent"],
                message_count=session_data["progress"]["message_count"],
                last_assessment=session_data["progress"]["last_assessment"]
            )

            messages = []
            for msg_data in session_data["messages"]:
                timestamp = datetime.fromisoformat(msg_data["timestamp"]) if msg_data["timestamp"] else None
                messages.append(LLMMessage(
                    role=MessageRole(msg_data["role"]),
                    content=msg_data["content"],
                    timestamp=timestamp
                ))

            session = ConversationSession(
                topic_id=session_data["topic_id"],
                topic_title=session_data["topic_title"],
                learning_objectives=session_data["learning_objectives"],
                state=ConversationState(session_data["state"]),
                progress=progress,
                messages=messages,
                started_at=datetime.fromisoformat(session_data["started_at"]),
                last_updated=datetime.fromisoformat(session_data["last_updated"])
            )

            return session

        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return None

    def _get_learning_path_from_session(self, session: ConversationSession) -> str:
        """Get learning path ID from session (simplified for now)"""
        # In a real implementation, this would be stored in the session
        # For now, we'll use a simple approach
        return "current_path"

    def end_conversation(self, learning_path_id: str) -> Dict[str, Any]:
        """End the current conversation and return summary"""

        if not self.current_session:
            return {}

        session = self.current_session

        # Update final progress
        session.state = ConversationState.COMPLETED
        session.progress.time_spent = int(
            (datetime.now() - session.started_at).total_seconds() / 60
        )

        # Save final session
        self._save_session(learning_path_id, session)

        # Get summary
        summary = self.get_progress_summary()

        # Clear current session
        self.current_session = None

        return summary

# Example usage
if __name__ == "__main__":
    import asyncio
    from llm_interface import create_llm_provider, LLMConfig, LLMProviderType

    async def test_conversation():
        # Setup
        config = LLMConfig(
            provider=LLMProviderType.OPENAI,
            model="gpt-3.5-turbo",
            api_key="your-api-key"
        )
        llm_provider = create_llm_provider(config)
        storage = DatabaseService()

        # Create engine
        engine = ConversationalLearningEngine(llm_provider, storage)

        # Start conversation
        session = engine.start_conversation("path_1", "topic_1")
        print(f"Started conversation: {session.topic_title}")

        # Simulate conversation
        response, progress = await engine.process_user_message("I'm not sure what this means")
        print(f"AI: {response}")
        print(f"Progress: {progress}")

    # Run test
    # asyncio.run(test_conversation())