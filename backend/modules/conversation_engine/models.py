"""Database models for the conversation engine module."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.shared_models import Base, PostgresUUID

__all__ = ["ConversationMessageModel", "ConversationModel"]


class ConversationModel(Base):
    """Stores metadata about a single conversational thread."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(PostgresUUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    conversation_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    conversation_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, default=dict)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    messages: Mapped[list[ConversationMessageModel]] = relationship(
        "ConversationMessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessageModel.message_order",
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if self.status is None:
            self.status = "active"
        if self.message_count is None:
            self.message_count = 0
        if self.conversation_metadata is None:
            self.conversation_metadata = {}

    def mark_message_activity(self) -> None:
        """Update timestamps when a message is recorded."""

        now = datetime.now(UTC)
        self.last_message_at = now
        self.updated_at = now


class ConversationMessageModel(Base):
    """Stores an individual message that belongs to a conversation."""

    __tablename__ = "conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(PostgresUUID(), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(PostgresUUID(), ForeignKey("conversations.id"), nullable=False, index=True)
    llm_request_id: Mapped[uuid.UUID | None] = mapped_column(PostgresUUID(), ForeignKey("llm_requests.id"), nullable=True, index=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_order: Mapped[int] = mapped_column(Integer, nullable=False)

    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    message_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    conversation: Mapped[ConversationModel] = relationship("ConversationModel", back_populates="messages")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if self.message_metadata is None:
            self.message_metadata = {}

    @property
    def is_system(self) -> bool:
        """Return True when the message is a system turn."""

        return self.role == "system"
