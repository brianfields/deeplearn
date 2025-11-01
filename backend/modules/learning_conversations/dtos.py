"""DTOs for the learning coach conversation module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Final


class _UnsetType:
    """Sentinel value representing an intentionally omitted field."""

    __slots__ = ()


UNSET: Final[_UnsetType] = _UnsetType()

UncoveredLearningObjectiveIds = list[str] | None


@dataclass(slots=True)
class LearningCoachObjective:
    """Structured representation of a proposed learning objective."""

    id: str
    title: str
    description: str


@dataclass(slots=True)
class LearningCoachMessage:
    """Serializable representation of a conversation message."""

    id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict[str, Any]


@dataclass(slots=True)
class LearningCoachResource:
    """Summary view of a resource associated with the conversation."""

    id: str
    resource_type: str
    filename: str | None
    source_url: str | None
    file_size: int | None
    created_at: datetime
    preview_text: str


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
    resources: list[LearningCoachResource]
    uncovered_learning_objective_ids: UncoveredLearningObjectiveIds | _UnsetType = UNSET


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


@dataclass(slots=True)
class TeachingAssistantMessage:
    """Message structure for teaching assistant conversations."""

    id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict[str, Any]
    suggested_quick_replies: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TeachingAssistantContext:
    """Structured context passed to the teaching assistant."""

    unit_id: str
    lesson_id: str | None
    session_id: str | None
    session: dict[str, Any] | None
    exercise_attempt_history: list[dict[str, Any]] = field(default_factory=list)
    lesson: dict[str, Any] | None = None
    unit: dict[str, Any] | None = None
    unit_session: dict[str, Any] | None = None
    unit_resources: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class TeachingAssistantSessionState:
    """Aggregate state returned to clients for teaching assistant conversations."""

    conversation_id: str
    unit_id: str
    lesson_id: str | None
    session_id: str | None
    messages: list[TeachingAssistantMessage]
    suggested_quick_replies: list[str]
    metadata: dict[str, Any]
    context: TeachingAssistantContext
