"""Service layer for the learning coach conversation module."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any
import uuid

from modules.conversation_engine.public import conversation_engine_provider
from modules.infrastructure.public import InfrastructureProvider, infrastructure_provider
from modules.resource.public import ResourceRead, resource_provider

from .conversation import LearningCoachConversation
from .dtos import (
    UNSET,
    LearningCoachConversationSummary,
    LearningCoachMessage,
    LearningCoachObjective,
    LearningCoachResource,
    LearningCoachSessionState,
    UncoveredLearningObjectiveIds,
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

    async def attach_resource(
        self,
        *,
        conversation_id: str,
        resource_id: uuid.UUID,
        user_id: int | None = None,
    ) -> LearningCoachSessionState:
        """Associate an uploaded resource with the specified conversation."""

        conversation = self._conversation_factory()
        return await conversation.add_resource(
            _conversation_id=conversation_id,
            _user_id=user_id,
            resource_id=str(resource_id),
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

        resources = await self.get_conversation_resources(conversation_id)
        uncovered_ids = self._parse_uncovered_learning_objective_ids(metadata.get("uncovered_learning_objective_ids")) if "uncovered_learning_objective_ids" in metadata else UNSET

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
            resources=[
                LearningCoachResource(
                    id=str(resource.id),
                    resource_type=resource.resource_type,
                    filename=resource.filename,
                    source_url=resource.source_url,
                    file_size=resource.file_size,
                    created_at=resource.created_at,
                    preview_text=_build_preview_text(resource),
                )
                for resource in resources
            ],
            uncovered_learning_objective_ids=uncovered_ids,
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
            payload = dict(entry)

            lo_id = str(payload.get("id") or "").strip()
            title = str(payload.get("title") or payload.get("short_title") or payload.get("description") or "").strip()
            description = str(payload.get("description") or title).strip()
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

    def _parse_uncovered_learning_objective_ids(self, value: Any) -> UncoveredLearningObjectiveIds:
        if value is None:
            return None

        if not isinstance(value, list):
            return []

        normalized = [str(item) for item in value if isinstance(item, str) and item.strip()]

        return normalized

    async def get_conversation_resources(self, conversation_id: str) -> list[ResourceRead]:
        """Return resources linked to a conversation via metadata."""

        infra = self._get_infrastructure()
        with infra.get_session_context() as session:
            engine = conversation_engine_provider(session)
            detail = await engine.get_conversation(uuid.UUID(conversation_id))

        resource_ids = _extract_resource_ids(detail.metadata)
        return await fetch_resources_for_ids(infra, resource_ids)


RESOURCE_METADATA_KEY = "resource_ids"


def _extract_resource_ids(metadata: dict[str, Any] | None) -> list[uuid.UUID]:
    """Parse stored resource identifiers from the provided metadata."""

    if not metadata:
        return []
    return _coerce_resource_ids(metadata.get(RESOURCE_METADATA_KEY))


def _coerce_resource_ids(value: Any) -> list[uuid.UUID]:
    """Convert stored identifier values into UUID objects."""

    if value is None:
        return []
    if isinstance(value, str | uuid.UUID):
        try:
            return [uuid.UUID(str(value))]
        except ValueError:
            return []
    if isinstance(value, list | tuple | set):
        result: list[uuid.UUID] = []
        for item in value:
            try:
                result.append(uuid.UUID(str(item)))
            except ValueError:
                continue
        return result
    return []


async def fetch_resources_for_ids(
    infrastructure: InfrastructureProvider,
    resource_ids: Sequence[uuid.UUID],
) -> list[ResourceRead]:
    """Load resources by identifier using the resource provider."""

    if not resource_ids:
        return []

    infrastructure.initialize()
    async with infrastructure.get_async_session_context() as session:
        provider = await resource_provider(session)
        results: list[ResourceRead] = []
        for resource_id in resource_ids:
            record = await provider.get_resource(resource_id)
            if record is not None:
                results.append(record)
        return results


def _build_preview_text(resource: ResourceRead) -> str:
    """Return a short preview of the extracted resource text for API summaries."""

    text = resource.extracted_text.strip()
    if len(text) <= 200:
        return text
    return text[:200]


def _build_context_excerpt(resource: ResourceRead) -> str:
    """Return the first 500 words of the extracted text for prompt context."""

    text = resource.extracted_text.strip()
    if not text:
        return ""
    words = text.split()
    if len(words) <= 500:
        return text
    excerpt = " ".join(words[:500])
    return excerpt


def build_resource_context_prompt(resources: Sequence[ResourceRead]) -> str | None:
    """Generate the resource context block appended to the system prompt."""

    if not resources:
        return None

    lines = [
        "## Source Materials Provided",
        "",
        "The learner has provided the following materials for context:",
        "",
    ]

    for index, resource in enumerate(resources, start=1):
        label = resource.filename or resource.source_url or f"Resource {index}"
        uploaded = resource.created_at.strftime("%B %d, %Y")
        lines.append(f"{index}. {label} (uploaded on {uploaded})")
        lines.append("   Extracted content:")
        excerpt = _build_context_excerpt(resource)
        if excerpt:
            indented = excerpt.replace("\n", "\n   ")
            lines.append(f"   {indented}")
        else:
            lines.append("   (no extracted text available)")
        lines.append("")

    return "\n".join(lines).strip()


__all__ = [
    "LearningCoachConversationSummary",
    "LearningCoachMessage",
    "LearningCoachService",
    "LearningCoachSessionState",
]
