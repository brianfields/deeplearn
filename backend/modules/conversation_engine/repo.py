"""Repository helpers for the conversation engine module."""

from __future__ import annotations

from collections.abc import Sequence
import uuid

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from .models import ConversationMessageModel, ConversationModel

__all__ = ["ConversationMessageRepo", "ConversationRepo"]


class ConversationRepo:
    """Data access helpers for conversation records."""

    def __init__(self, session: Session) -> None:
        self.s = session

    def by_id(self, conversation_id: uuid.UUID) -> ConversationModel | None:
        """Return a conversation by its identifier."""

        return self.s.get(ConversationModel, conversation_id)

    def create(self, conversation: ConversationModel) -> ConversationModel:
        """Persist a new conversation record."""

        self.s.add(conversation)
        self.s.flush()
        return conversation

    def save(self, conversation: ConversationModel) -> ConversationModel:
        """Persist changes to an existing conversation."""

        self.s.add(conversation)
        return conversation

    def list_for_user(
        self,
        user_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
        conversation_type: str | None = None,
        status: str | None = None,
    ) -> list[ConversationModel]:
        """Return paginated conversations for a given user."""

        query: Select[tuple[ConversationModel]] = select(ConversationModel).where(ConversationModel.user_id == user_id)

        if conversation_type:
            query = query.where(ConversationModel.conversation_type == conversation_type)
        if status:
            query = query.where(ConversationModel.status == status)

        query = query.order_by(desc(ConversationModel.last_message_at), desc(ConversationModel.created_at)).limit(limit).offset(offset)
        return list(self.s.execute(query).scalars())

    def list_for_type(
        self,
        conversation_type: str,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[ConversationModel]:
        """Return paginated conversations filtered by type."""

        query: Select[tuple[ConversationModel]] = select(ConversationModel).where(ConversationModel.conversation_type == conversation_type)

        if status:
            query = query.where(ConversationModel.status == status)

        query = query.order_by(desc(ConversationModel.last_message_at), desc(ConversationModel.created_at)).limit(limit).offset(offset)
        return list(self.s.execute(query).scalars())


class ConversationMessageRepo:
    """Data access helpers for conversation messages."""

    def __init__(self, session: Session) -> None:
        self.s = session

    def create(self, message: ConversationMessageModel) -> ConversationMessageModel:
        """Persist a new conversation message."""

        self.s.add(message)
        self.s.flush()
        return message

    def save(self, message: ConversationMessageModel) -> ConversationMessageModel:
        """Persist changes to a conversation message."""

        self.s.add(message)
        return message

    def get_history(
        self,
        conversation_id: uuid.UUID,
        *,
        limit: int | None = None,
        include_system: bool = True,
    ) -> list[ConversationMessageModel]:
        """Return ordered message history for a conversation."""

        query: Select[tuple[ConversationMessageModel]] = select(ConversationMessageModel).where(ConversationMessageModel.conversation_id == conversation_id)

        if not include_system:
            query = query.where(ConversationMessageModel.role != "system")

        query = query.order_by(ConversationMessageModel.message_order)

        if limit is not None:
            query = query.limit(limit)

        result: Sequence[ConversationMessageModel] = self.s.execute(query).scalars().all()
        return list(result)

    def count_for_conversation(self, conversation_id: uuid.UUID) -> int:
        """Return total messages stored for the conversation."""

        query = select(ConversationMessageModel.id).where(ConversationMessageModel.conversation_id == conversation_id)
        return len(list(self.s.execute(query).scalars()))
