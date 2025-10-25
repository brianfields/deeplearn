"""DTOs for the learning coach conversation module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class LearningCoachObjective:
    """Structured representation of a proposed learning objective."""

    id: str
    text: str


@dataclass(slots=True)
class LearningCoachMessage:
    """Serializable representation of a conversation message."""

    id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict[str, Any]


@dataclass(slots=True)
class LearningCoachSessionState:
    """Aggregate view of a learning coach conversation."""

    conversation_id: str
    messages: list[LearningCoachMessage]
    metadata: dict[str, Any]
    finalized_topic: str | None
    unit_title: str | None
    learning_objectives: list[LearningCoachObjective] | None
    suggested_lesson_count: int | None
    proposed_brief: dict[str, Any] | None  # Deprecated, will be removed
    accepted_brief: dict[str, Any] | None  # Deprecated, will be removed


@dataclass(slots=True)
class LearningCoachConversationSummary:
    """Summary information for listing learning coach conversations."""

    id: str
    user_id: int | None
    title: str | None
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None
    message_count: int
    metadata: dict[str, Any]
