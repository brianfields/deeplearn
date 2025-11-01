"""Public provider for the learning conversations module."""

from __future__ import annotations

from typing import Any, Protocol

from modules.infrastructure.public import InfrastructureProvider, infrastructure_provider
from modules.resource.public import ResourceRead

from .dtos import (
    LearningCoachConversationSummary,
    LearningCoachMessage,
    LearningCoachObjective,
    LearningCoachSessionState,
    TeachingAssistantContext,
    TeachingAssistantSessionState,
)
from .service import LearningCoachService


class LearningConversationsProvider(Protocol):
    """Protocol describing the learning conversations service surface."""

    async def start_session(
        self,
        *,
        topic: str | None = None,
        user_id: int | None = None,
    ) -> LearningCoachSessionState: ...

    async def submit_learner_turn(
        self,
        *,
        conversation_id: str,
        message: str,
        user_id: int | None = None,
    ) -> LearningCoachSessionState: ...

    async def accept_brief(
        self,
        *,
        conversation_id: str,
        brief: dict[str, Any],
        user_id: int | None = None,
    ) -> LearningCoachSessionState: ...

    async def restart_session(
        self,
        *,
        topic: str | None = None,
        user_id: int | None = None,
    ) -> LearningCoachSessionState: ...

    async def get_session_state(
        self,
        conversation_id: str,
        *,
        include_system_messages: bool = False,
    ) -> LearningCoachSessionState: ...

    async def list_conversations(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[LearningCoachConversationSummary]: ...

    async def get_conversation_resources(self, conversation_id: str) -> list[ResourceRead]: ...

    async def start_teaching_assistant_session(
        self,
        *,
        unit_id: str,
        lesson_id: str | None,
        session_id: str | None,
        user_id: int | None = None,
    ) -> TeachingAssistantSessionState: ...

    async def submit_teaching_assistant_question(
        self,
        *,
        conversation_id: str,
        message: str,
        unit_id: str,
        lesson_id: str | None,
        session_id: str | None,
        user_id: int | None = None,
    ) -> TeachingAssistantSessionState: ...

    async def get_teaching_assistant_session_state(
        self,
        *,
        conversation_id: str,
        unit_id: str,
        lesson_id: str | None,
        session_id: str | None,
        user_id: int | None = None,
    ) -> TeachingAssistantSessionState: ...


def learning_conversations_provider(
    infrastructure: InfrastructureProvider | None = None,
) -> LearningConversationsProvider:
    """Return a learning conversations service bound to infrastructure."""

    infra = infrastructure or infrastructure_provider()
    return LearningCoachService(infrastructure=infra)


__all__ = [
    "LearningCoachConversationSummary",
    "LearningCoachMessage",
    "LearningCoachObjective",
    "LearningCoachService",
    "LearningCoachSessionState",
    "LearningConversationsProvider",
    "TeachingAssistantContext",
    "TeachingAssistantSessionState",
    "learning_conversations_provider",
]
