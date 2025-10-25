"""Public provider for the learning coach module."""

from __future__ import annotations

from typing import Any, Protocol

from modules.infrastructure.public import InfrastructureProvider, infrastructure_provider

from .dtos import (
    LearningCoachConversationSummary,
    LearningCoachMessage,
    LearningCoachObjective,
    LearningCoachSessionState,
)
from .service import LearningCoachService


class LearningCoachProvider(Protocol):
    """Protocol describing the learning coach service surface."""

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


def learning_coach_provider(
    infrastructure: InfrastructureProvider | None = None,
) -> LearningCoachProvider:
    """Return a learning coach service bound to infrastructure."""

    infra = infrastructure or infrastructure_provider()
    return LearningCoachService(infrastructure=infra)


__all__ = [
    "LearningCoachConversationSummary",
    "LearningCoachMessage",
    "LearningCoachObjective",
    "LearningCoachProvider",
    "LearningCoachService",
    "LearningCoachSessionState",
    "learning_coach_provider",
]
