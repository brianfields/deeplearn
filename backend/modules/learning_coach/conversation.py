"""Learning coach conversation orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from modules.conversation_engine.public import (
    BaseConversation,
    ConversationContext,
    ConversationMessageDTO,
    conversation_session,
)

from .dtos import LearningCoachMessage, LearningCoachSessionState


class CoachResponse(BaseModel):
    """Structured response from the learning coach."""

    message: str = Field(description="The coach's response message to the learner (max ~100 words)")
    finalized_topic: str | None = Field(
        default=None,
        description=(
            "When you have clarity on both WHAT they want to learn and their current knowledge level, "
            "provide a detailed topic description including: specific topics/concepts, starting level "
            "(e.g., 'beginner', 'intermediate with Python basics'), focus areas, scope for 2-10 "
            "mini-lessons, and the learning objectives (listed out). Update this if they request changes. "
            "Leave null only while still gathering information."
        ),
    )
    unit_title: str | None = Field(
        default=None,
        description=(
            "When finalizing, provide a short, engaging unit title (1-6 words) that captures the essence "
            "of what they'll learn. Examples: 'React Native with Expo', 'Python Data Structures', "
            "'Web API Design Basics'. Update if the learner requests changes."
        ),
    )
    learning_objectives: list[str] | None = Field(
        default=None,
        description=(
            "When finalizing the topic, provide 3-8 clear, specific learning objectives. Each should be "
            "measurable, action-oriented, and appropriate for the learner's level. Examples: 'Explain how "
            "outliers affect mean and median differently', 'Apply decision rules to select appropriate "
            "measures of center'. Update if the learner requests changes."
        ),
    )
    suggested_lesson_count: int | None = Field(
        default=None,
        description=("When finalizing, suggest the number of lessons (2-10) to cover the learning objectives. Consider the breadth of objectives, the learner's level, and natural topic boundaries. Update if the learner requests changes."),
    )
    suggested_quick_replies: list[str] | None = Field(
        default=None,
        description=(
            "Provide 2-5 contextually relevant quick reply options based on the conversation state. "
            "These should be natural follow-ups to help guide the learner to the next step. "
            "Examples: 'Tell me more', 'Yes, that works', 'Can we adjust the focus?', 'I'm a beginner'. "
            "Keep each under 40 characters. Tailor to what you need to know next or what the learner might want to say."
        ),
    )


class LearningCoachConversation(BaseConversation):
    """High-level dialog handler for the learning coach experience."""

    conversation_type = "learning_coach"
    system_prompt_file = "prompts/system_prompt.md"

    @conversation_session
    async def start_session(
        self,
        *,
        _user_id: int | None = None,
        _conversation_id: str | None = None,
        topic: str | None = None,
        _conversation_metadata: dict[str, Any] | None = None,
        _conversation_title: str | None = None,
    ) -> LearningCoachSessionState:
        """Kick off a new learning coach conversation."""
        if topic:
            await self.record_user_message(f"I'd like to learn about {topic}.")
        await self._ensure_opening_assistant_turn()
        return await self._build_session_state()

    @conversation_session
    async def submit_learner_turn(
        self,
        *,
        _conversation_id: str | None = None,
        _user_id: int | None = None,
        message: str,
    ) -> LearningCoachSessionState:
        """Record a learner response and fetch the follow-up coach reply."""

        await self.record_user_message(message)
        await self._generate_structured_reply()
        return await self._build_session_state()

    @conversation_session
    async def accept_brief(
        self,
        *,
        _conversation_id: str | None = None,
        _user_id: int | None = None,
        brief: dict[str, Any],
    ) -> LearningCoachSessionState:
        """Mark the current proposal as accepted and return the refreshed state."""

        metadata_update = {
            "accepted_brief": brief,
            "accepted_at": datetime.now(UTC).isoformat(),
        }
        await self.update_conversation_metadata(metadata_update)
        return await self._build_session_state()

    async def _ensure_opening_assistant_turn(self) -> None:
        """Ensure the coach has produced an opening prompt."""

        ctx = ConversationContext.current()
        history = await ctx.service.get_message_history(ctx.conversation_id, include_system=False)
        if any(message.role == "assistant" for message in history):
            return
        # Start with a simple static greeting
        await self.record_assistant_message("What would you like to learn today?")

    async def _build_session_state(self) -> LearningCoachSessionState:
        """Assemble the latest session state for clients."""

        ctx = ConversationContext.current()
        history = await ctx.service.get_message_history(ctx.conversation_id, include_system=False)
        summary = await self.get_conversation_summary()
        metadata = dict(summary.metadata or {})

        return LearningCoachSessionState(
            conversation_id=str(ctx.conversation_id),
            messages=[self._to_message(message) for message in history],
            metadata=metadata,
            finalized_topic=metadata.get("finalized_topic"),
            unit_title=metadata.get("unit_title"),
            learning_objectives=metadata.get("learning_objectives"),
            suggested_lesson_count=metadata.get("suggested_lesson_count"),
            proposed_brief=self._dict_or_none(metadata.get("proposed_brief")),
            accepted_brief=self._dict_or_none(metadata.get("accepted_brief")),
        )

    def _to_message(self, message: ConversationMessageDTO) -> LearningCoachMessage:
        """Convert a conversation engine DTO into a learning coach message."""

        return LearningCoachMessage(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            metadata=dict(message.metadata or {}),
        )

    def _dict_or_none(self, value: Any) -> dict[str, Any] | None:
        """Return the provided value if it is a mapping."""

        if isinstance(value, dict):
            return value
        return None

    async def _generate_structured_reply(self) -> None:
        """Generate a structured coach response and persist it."""

        # Generate structured response using helper
        coach_response, request_id, raw_response = await self.generate_structured_reply(
            CoachResponse,
            model="claude-haiku-4-5",
        )

        # Record the assistant message
        message_metadata: dict[str, Any] = {
            "provider": raw_response.get("provider", "openai"),
        }
        if coach_response.suggested_quick_replies is not None:
            message_metadata["suggested_quick_replies"] = coach_response.suggested_quick_replies
        await self.record_assistant_message(
            coach_response.message,
            metadata=message_metadata,
            llm_request_id=request_id,
            tokens_used=raw_response.get("usage", {}).get("total_tokens"),
            cost_estimate=raw_response.get("cost_estimate"),
        )

        # If topic is finalized, update conversation metadata
        if coach_response.finalized_topic:
            metadata_update: dict[str, Any] = {
                "finalized_topic": coach_response.finalized_topic,
                "finalized_at": datetime.now(UTC).isoformat(),
            }
            if coach_response.unit_title is not None:
                metadata_update["unit_title"] = coach_response.unit_title
            if coach_response.learning_objectives is not None:
                metadata_update["learning_objectives"] = coach_response.learning_objectives
            if coach_response.suggested_lesson_count is not None:
                metadata_update["suggested_lesson_count"] = coach_response.suggested_lesson_count
            await self.update_conversation_metadata(metadata_update)
