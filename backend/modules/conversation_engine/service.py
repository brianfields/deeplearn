"""Service layer for conversation orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
import uuid

from ..llm_services.public import LLMMessage, LLMResponse, LLMServicesProvider
from .models import ConversationMessageModel, ConversationModel
from .repo import ConversationMessageRepo, ConversationRepo

__all__ = [
    "ConversationDetailDTO",
    "ConversationEngineService",
    "ConversationMessageDTO",
    "ConversationSummaryDTO",
    "PaginatedConversationsDTO",
]


@dataclass(slots=True)
class ConversationMessageDTO:
    """DTO representing a single conversation message."""

    id: str
    conversation_id: str
    role: str
    content: str
    message_order: int
    llm_request_id: str | None
    metadata: dict[str, Any] | None
    tokens_used: int | None
    cost_estimate: float | None
    created_at: datetime


@dataclass(slots=True)
class ConversationSummaryDTO:
    """DTO representing conversation metadata without messages."""

    id: str
    user_id: int | None
    conversation_type: str
    title: str | None
    status: str
    metadata: dict[str, Any] | None
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None


@dataclass(slots=True)
class ConversationDetailDTO(ConversationSummaryDTO):
    """DTO representing full conversation details including history."""

    messages: list[ConversationMessageDTO]


@dataclass(slots=True)
class PaginatedConversationsDTO:
    """DTO representing a paginated list of conversations with metadata."""

    conversations: list[ConversationSummaryDTO]
    total_count: int
    page: int
    page_size: int
    has_next: bool


class ConversationEngineService:
    """Application service that manages conversations and LLM interactions."""

    def __init__(
        self,
        conversation_repo: ConversationRepo,
        message_repo: ConversationMessageRepo,
        llm_services: LLMServicesProvider,
    ) -> None:
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.llm_services = llm_services

    async def create_conversation(
        self,
        *,
        conversation_type: str,
        user_id: int | None = None,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationSummaryDTO:
        """Create and persist a new conversation."""

        conversation = ConversationModel(
            user_id=user_id,
            conversation_type=conversation_type,
            title=title,
            conversation_metadata=dict(metadata or {}),
        )
        created = self.conversation_repo.create(conversation)
        return self._to_summary_dto(created)

    async def get_conversation(self, conversation_id: uuid.UUID) -> ConversationDetailDTO:
        """Return full conversation details including message history."""

        conversation = self._require_conversation(conversation_id)
        messages = self.message_repo.get_history(conversation_id, include_system=True)
        return self._to_detail_dto(conversation, messages)

    async def get_conversation_summary(self, conversation_id: uuid.UUID) -> ConversationSummaryDTO:
        """Return conversation metadata without loading message history."""

        conversation = self._require_conversation(conversation_id)
        return self._to_summary_dto(conversation)

    async def list_conversations_for_user(
        self,
        user_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
        conversation_type: str | None = None,
        status: str | None = None,
    ) -> list[ConversationSummaryDTO]:
        """Return paginated conversations for a user."""

        conversations = self.conversation_repo.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
            conversation_type=conversation_type,
            status=status,
        )
        return [self._to_summary_dto(conv) for conv in conversations]

    async def list_conversations_by_type(
        self,
        conversation_type: str,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[ConversationSummaryDTO]:
        """Return paginated conversations filtered solely by type."""

        conversations = self.conversation_repo.list_for_type(
            conversation_type,
            limit=limit,
            offset=offset,
            status=status,
        )
        return [self._to_summary_dto(conv) for conv in conversations]

    async def list_conversations_for_user_paginated(
        self,
        user_id: int,
        *,
        page: int = 1,
        page_size: int = 50,
        conversation_type: str | None = None,
        status: str | None = None,
    ) -> PaginatedConversationsDTO:
        """Return paginated conversations for a user with metadata."""

        # Calculate offset from page number
        offset = (page - 1) * page_size

        # Get conversations for this page
        conversations = self.conversation_repo.list_for_user(
            user_id,
            limit=page_size,
            offset=offset,
            conversation_type=conversation_type,
            status=status,
        )

        # Get total count
        total_count = self.conversation_repo.count_for_user(
            user_id,
            conversation_type=conversation_type,
            status=status,
        )

        # Calculate if there are more pages
        has_next = (offset + len(conversations)) < total_count

        return PaginatedConversationsDTO(
            conversations=[self._to_summary_dto(conv) for conv in conversations],
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )

    def count_assistant_conversations_since(self, since: datetime) -> int:
        """Count learning_coach and teaching_assistant conversations created since datetime. [ADMIN ONLY]"""
        from sqlalchemy import and_, select

        from .models import ConversationModel

        assistant_types = ["learning_coach", "teaching_assistant"]
        query = select(ConversationModel).where(
            and_(
                ConversationModel.conversation_type.in_(assistant_types),
                ConversationModel.created_at >= since,
            )
        )
        return len(list(self.conversation_repo.s.execute(query).scalars()))

    async def record_user_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessageDTO:
        """Record a user message."""

        return await self._add_message(conversation_id, "user", content, metadata=metadata)

    async def record_system_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessageDTO:
        """Record a system message."""

        return await self._add_message(conversation_id, "system", content, metadata=metadata)

    async def record_assistant_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        *,
        llm_request_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
        tokens_used: int | None = None,
        cost_estimate: float | None = None,
    ) -> ConversationMessageDTO:
        """Record an assistant message."""

        return await self._add_message(
            conversation_id,
            "assistant",
            content,
            metadata=metadata,
            llm_request_id=llm_request_id,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
        )

    async def get_message_history(
        self,
        conversation_id: uuid.UUID,
        *,
        limit: int | None = None,
        include_system: bool = True,
    ) -> list[ConversationMessageDTO]:
        """Return message history for the conversation."""

        messages = self.message_repo.get_history(conversation_id, limit=limit, include_system=include_system)
        return [self._to_message_dto(message) for message in messages]

    async def build_llm_messages(
        self,
        conversation_id: uuid.UUID,
        *,
        system_prompt: str | None = None,
        limit: int | None = None,
        include_system: bool = False,
    ) -> list[LLMMessage]:
        """Build ChatML-style messages for the LLM module."""

        llm_messages: list[LLMMessage] = []
        if system_prompt:
            llm_messages.append(LLMMessage(role="system", content=system_prompt))

        history = self.message_repo.get_history(conversation_id, limit=limit, include_system=include_system)
        for message in history:
            llm_messages.append(LLMMessage(role=message.role, content=message.content))

        return llm_messages

    async def generate_assistant_response(
        self,
        conversation_id: uuid.UUID,
        *,
        system_prompt: str | None = None,
        user_id: int | None = None,
        metadata: dict[str, Any] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        **kwargs: Any,
    ) -> tuple[ConversationMessageDTO, uuid.UUID, LLMResponse]:
        """Generate an assistant response via the LLM and persist it."""

        llm_messages = await self.build_llm_messages(
            conversation_id,
            system_prompt=system_prompt,
            include_system=False,
        )

        response, request_id = await self.llm_services.generate_response(
            messages=llm_messages,
            user_id=user_id,
            model=model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            **kwargs,
        )

        message_metadata = dict(metadata or {})
        message_metadata.setdefault("provider", response.provider)
        message_metadata.setdefault("model", response.model)

        message_dto = await self.record_assistant_message(
            conversation_id,
            response.content,
            llm_request_id=request_id,
            metadata=message_metadata,
            tokens_used=response.output_tokens or response.tokens_used,
            cost_estimate=response.cost_estimate,
        )

        return message_dto, request_id, response

    async def update_conversation_status(self, conversation_id: uuid.UUID, status: str) -> ConversationSummaryDTO:
        """Update and persist the conversation status."""

        conversation = self._require_conversation(conversation_id)
        conversation.status = status
        conversation.updated_at = datetime.now(UTC)
        self.conversation_repo.save(conversation)
        return self._to_summary_dto(conversation)

    async def update_conversation_metadata(
        self,
        conversation_id: uuid.UUID,
        metadata: dict[str, Any],
        *,
        merge: bool = True,
    ) -> ConversationSummaryDTO:
        """Update conversation metadata, optionally merging with existing values."""

        conversation = self._require_conversation(conversation_id)
        existing = dict(conversation.conversation_metadata or {}) if merge else {}
        existing.update(metadata)
        conversation.conversation_metadata = existing
        conversation.updated_at = datetime.now(UTC)
        self.conversation_repo.save(conversation)
        return self._to_summary_dto(conversation)

    async def update_conversation_title(
        self,
        conversation_id: uuid.UUID,
        title: str | None,
    ) -> ConversationSummaryDTO:
        """Update the stored conversation title."""

        conversation = self._require_conversation(conversation_id)
        conversation.title = title
        conversation.updated_at = datetime.now(UTC)
        self.conversation_repo.save(conversation)
        return self._to_summary_dto(conversation)

    def _require_conversation(self, conversation_id: uuid.UUID) -> ConversationModel:
        """Return the conversation or raise if it does not exist."""

        conversation = self.conversation_repo.by_id(conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation not found: {conversation_id}")
        return conversation

    async def _add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
        llm_request_id: uuid.UUID | None = None,
        tokens_used: int | None = None,
        cost_estimate: float | None = None,
    ) -> ConversationMessageDTO:
        """Internal helper for recording messages."""

        conversation = self._require_conversation(conversation_id)
        next_order = conversation.message_count + 1

        message = ConversationMessageModel(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_order=next_order,
            llm_request_id=llm_request_id,
            message_metadata=dict(metadata or {}),
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
        )

        created = self.message_repo.create(message)
        conversation.message_count = next_order
        conversation.mark_message_activity()
        self.conversation_repo.save(conversation)

        return self._to_message_dto(created)

    def _to_message_dto(self, message: ConversationMessageModel) -> ConversationMessageDTO:
        """Convert ORM message to DTO."""

        return ConversationMessageDTO(
            id=str(message.id),
            conversation_id=str(message.conversation_id),
            role=message.role,
            content=message.content,
            message_order=message.message_order,
            llm_request_id=str(message.llm_request_id) if message.llm_request_id else None,
            metadata=dict(message.message_metadata or {}),
            tokens_used=message.tokens_used,
            cost_estimate=message.cost_estimate,
            created_at=message.created_at,
        )

    def _to_summary_dto(self, conversation: ConversationModel) -> ConversationSummaryDTO:
        """Convert ORM conversation to DTO."""

        return ConversationSummaryDTO(
            id=str(conversation.id),
            user_id=conversation.user_id,
            conversation_type=conversation.conversation_type,
            title=conversation.title,
            status=conversation.status,
            metadata=dict(conversation.conversation_metadata or {}),
            message_count=conversation.message_count,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            last_message_at=conversation.last_message_at,
        )

    def _to_detail_dto(
        self,
        conversation: ConversationModel,
        messages: list[ConversationMessageModel],
    ) -> ConversationDetailDTO:
        """Convert ORM objects into a detail DTO."""

        return ConversationDetailDTO(
            **asdict(self._to_summary_dto(conversation)),
            messages=[self._to_message_dto(message) for message in messages],
        )
