"""Learning coach conversation orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid

from modules.conversation_engine.base_conversation import BaseConversation, conversation_session
from modules.conversation_engine.context import ConversationContext
from modules.conversation_engine.service import ConversationMessageDTO

from .dtos import LearningCoachMessage, LearningCoachSessionState


class LearningCoachConversation(BaseConversation):
    """High-level dialog handler for the learning coach experience."""

    conversation_type = "learning_coach"
    system_prompt_file = "learning_coach/system_prompt.md"

    @conversation_session
    async def start_session(
        self,
        *,
        _user_id: uuid.UUID | None = None,
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
        _user_id: uuid.UUID | None = None,
        message: str,
    ) -> LearningCoachSessionState:
        """Record a learner response and fetch the follow-up coach reply."""

        await self.record_user_message(message)
        await self.generate_assistant_reply(model="gpt-5-mini")
        return await self._build_session_state()

    @conversation_session
    async def accept_brief(
        self,
        *,
        _conversation_id: str | None = None,
        _user_id: uuid.UUID | None = None,
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
        await self.generate_assistant_reply(model="gpt-5-mini")

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
