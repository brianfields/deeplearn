"""Public provider for the conversation engine module."""

from __future__ import annotations

from typing import Any, Protocol
import uuid

from sqlalchemy.orm import Session

from ..llm_services.public import LLMMessage, LLMResponse, LLMServicesProvider, llm_services_provider
from .repo import ConversationMessageRepo, ConversationRepo
from .service import (
    ConversationDetailDTO,
    ConversationEngineService,
    ConversationMessageDTO,
    ConversationSummaryDTO,
)

__all__ = [
    "ConversationDetailDTO",
    "ConversationEngineProvider",
    "ConversationMessageDTO",
    "ConversationSummaryDTO",
    "conversation_engine_provider",
]


class ConversationEngineProvider(Protocol):
    """Protocol describing the conversation engine service surface."""

    async def create_conversation(
        self,
        *,
        conversation_type: str,
        user_id: uuid.UUID | None = None,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationSummaryDTO: ...

    async def get_conversation(self, conversation_id: uuid.UUID) -> ConversationDetailDTO: ...

    async def list_conversations_for_user(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        conversation_type: str | None = None,
        status: str | None = None,
    ) -> list[ConversationSummaryDTO]: ...

    async def list_conversations_by_type(
        self,
        conversation_type: str,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[ConversationSummaryDTO]: ...

    async def record_user_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessageDTO: ...

    async def record_system_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessageDTO: ...

    async def record_assistant_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        *,
        llm_request_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
        tokens_used: int | None = None,
        cost_estimate: float | None = None,
    ) -> ConversationMessageDTO: ...

    async def get_message_history(
        self,
        conversation_id: uuid.UUID,
        *,
        limit: int | None = None,
        include_system: bool = True,
    ) -> list[ConversationMessageDTO]: ...

    async def build_llm_messages(
        self,
        conversation_id: uuid.UUID,
        *,
        system_prompt: str | None = None,
        limit: int | None = None,
        include_system: bool = False,
    ) -> list[LLMMessage]: ...

    async def generate_assistant_response(
        self,
        conversation_id: uuid.UUID,
        *,
        system_prompt: str | None = None,
        user_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        **kwargs: Any,
    ) -> tuple[ConversationMessageDTO, uuid.UUID, LLMResponse]: ...

    async def update_conversation_status(self, conversation_id: uuid.UUID, status: str) -> ConversationSummaryDTO: ...


def conversation_engine_provider(session: Session) -> ConversationEngineProvider:
    """Return a conversation engine service bound to the provided session."""

    llm_services: LLMServicesProvider = llm_services_provider()
    return ConversationEngineService(ConversationRepo(session), ConversationMessageRepo(session), llm_services)
