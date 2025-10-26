"""Service layer for the learning coach conversation module."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
import uuid

from modules.conversation_engine.public import conversation_engine_provider
from modules.infrastructure.public import InfrastructureProvider, infrastructure_provider

from .conversation import LearningCoachConversation
from .dtos import (
    LearningCoachConversationSummary,
    LearningCoachMessage,
    LearningCoachObjective,
    LearningCoachSessionState,
)


class LearningCoachService:
    """Coordinate learning coach conversations via the conversation engine."""

    def __init__(
        self,
        *,
        infrastructure: InfrastructureProvider | None = None,
        conversation_factory: Callable[[], LearningCoachConversation] | None = None,
    ) -> None:
        self._infrastructure = infrastructure
        self._conversation_factory = conversation_factory or LearningCoachConversation

    async def start_session(
        self,
        *,
        topic: str | None = None,
        user_id: int | None = None,
    ) -> LearningCoachSessionState:
        """Start a new learning coach conversation."""

        metadata = {"topic": topic} if topic else None
        conversation = self._conversation_factory()
        return await conversation.start_session(
            _user_id=user_id,
            topic=topic,
            _conversation_metadata=metadata,
        )

    async def submit_learner_turn(
        self,
        *,
        conversation_id: str,
        message: str,
        user_id: int | None = None,
    ) -> LearningCoachSessionState:
        """Append a learner turn and fetch the updated state."""

        conversation = self._conversation_factory()
        return await conversation.submit_learner_turn(
            _conversation_id=conversation_id,
            _user_id=user_id,
            message=message,
        )

    async def accept_brief(
        self,
        *,
        conversation_id: str,
        brief: dict[str, Any],
        user_id: int | None = None,
    ) -> LearningCoachSessionState:
        """Persist the accepted brief and return the refreshed session state."""

        conversation = self._conversation_factory()
        return await conversation.accept_brief(
            _conversation_id=conversation_id,
            _user_id=user_id,
            brief=brief,
        )

    async def restart_session(
        self,
        *,
        topic: str | None = None,
        user_id: int | None = None,
    ) -> LearningCoachSessionState:
        """Restart the conversation by creating a fresh session."""

        return await self.start_session(topic=topic, user_id=user_id)

    async def get_session_state(
        self,
        conversation_id: str,
        *,
        include_system_messages: bool = False,
    ) -> LearningCoachSessionState:
        """Return the conversation state for a given identifier."""

        infra = self._get_infrastructure()
        with infra.get_session_context() as session:
            engine = conversation_engine_provider(session)
            detail = await engine.get_conversation(uuid.UUID(conversation_id))

        metadata = dict(detail.metadata or {})
        messages = [
            LearningCoachMessage(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
                metadata=dict(message.metadata or {}),
            )
            for message in detail.messages
            if include_system_messages or message.role != "system"
        ]

        return LearningCoachSessionState(
            conversation_id=detail.id,
            messages=messages,
            metadata=metadata,
            finalized_topic=metadata.get("finalized_topic"),
            unit_title=metadata.get("unit_title"),
            learning_objectives=self._parse_learning_objectives(metadata.get("learning_objectives")),
            suggested_lesson_count=metadata.get("suggested_lesson_count"),
            proposed_brief=self._dict_or_none(metadata.get("proposed_brief")),
            accepted_brief=self._dict_or_none(metadata.get("accepted_brief")),
        )

    async def list_conversations(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[LearningCoachConversationSummary]:
        """Return paginated learning coach conversations for admin views."""

        infra = self._get_infrastructure()
        with infra.get_session_context() as session:
            engine = conversation_engine_provider(session)
            summaries = await engine.list_conversations_by_type(
                LearningCoachConversation.conversation_type,
                limit=limit,
                offset=offset,
                status=status,
            )

        return [
            LearningCoachConversationSummary(
                id=summary.id,
                user_id=summary.user_id,
                title=summary.title,
                created_at=summary.created_at,
                updated_at=summary.updated_at,
                last_message_at=summary.last_message_at,
                message_count=summary.message_count,
                metadata=dict(summary.metadata or {}),
            )
            for summary in summaries
        ]

    def _get_infrastructure(self) -> InfrastructureProvider:
        if self._infrastructure is None:
            self._infrastructure = infrastructure_provider()
        self._infrastructure.initialize()
        return self._infrastructure

    def _dict_or_none(self, value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            return value
        return None

    def _parse_learning_objectives(
        self,
        value: Any,
    ) -> list[LearningCoachObjective] | None:
        if not isinstance(value, list):
            return None

        objectives: list[LearningCoachObjective] = []
        for entry in value:
            if not isinstance(entry, dict):
                continue
            lo_id = str(entry.get("id") or "").strip()
            title = str(entry.get("title") or entry.get("short_title") or "").strip()
            description = str(entry.get("description") or entry.get("text") or title).strip()
            if not title and description:
                title = description[:50]
            if lo_id and title and description:
                objectives.append(
                    LearningCoachObjective(
                        id=lo_id,
                        title=title,
                        description=description,
                    )
                )

        return objectives or None


__all__ = [
    "LearningCoachConversationSummary",
    "LearningCoachMessage",
    "LearningCoachService",
    "LearningCoachSessionState",
]
