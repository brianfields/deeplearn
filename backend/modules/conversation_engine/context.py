"""Conversation execution context management."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
import uuid

if TYPE_CHECKING:
    from .service import ConversationEngineService

__all__ = ["ConversationContext"]


_conversation_context: ContextVar["ConversationContext | None"] = ContextVar("conversation_context", default=None)


@dataclass
class ConversationContext:
    """Stores infrastructure required during a conversation turn."""

    service: "ConversationEngineService"
    conversation_id: uuid.UUID
    user_id: uuid.UUID | None = None
    metadata: dict[str, Any] | None = None

    @classmethod
    def set(cls, **kwargs: Any) -> "ConversationContext":
        """Attach a context to the current task."""

        ctx = cls(**kwargs)
        _conversation_context.set(ctx)
        return ctx

    @classmethod
    def current(cls) -> "ConversationContext":
        """Return the current context or raise if missing."""

        ctx = _conversation_context.get()
        if ctx is None:
            raise RuntimeError("Conversation context is not available; ensure conversation_session is applied.")
        return ctx

    @classmethod
    def clear(cls) -> None:
        """Clear the active context."""

        _conversation_context.set(None)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation of the context."""

        return {
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "metadata_keys": sorted(list(self.metadata.keys())) if self.metadata else [],
        }

