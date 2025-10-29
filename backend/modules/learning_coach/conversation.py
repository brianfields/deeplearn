"""Learning coach conversation orchestration."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
import uuid

from pydantic import BaseModel, Field

from modules.conversation_engine.public import (
    BaseConversation,
    ConversationContext,
    ConversationMessageDTO,
    conversation_session,
)
from modules.infrastructure.public import infrastructure_provider

from .dtos import (
    LearningCoachMessage,
    LearningCoachObjective,
    LearningCoachResource,
    LearningCoachSessionState,
)

if TYPE_CHECKING:
    from modules.resource.service import ResourceRead


RESOURCE_METADATA_KEY = "resource_ids"


async def _fetch_resources(resource_ids: Sequence[uuid.UUID]) -> list[ResourceRead]:
    """Load resource records for the provided identifiers."""

    if not resource_ids:
        return []

    from .service import fetch_resources_for_ids

    infra = infrastructure_provider()
    infra.initialize()
    return await fetch_resources_for_ids(infra, resource_ids)


class CoachLearningObjective(BaseModel):
    """Learning objective emitted by the structured coach response."""

    id: str = Field(..., min_length=1, description="Stable identifier for the unit learning objective")
    title: str = Field(
        ...,
        min_length=3,
        description="Short 3-8 word title that summarizes the learning objective",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Full explanation of the learning objective for learner-facing surfaces",
    )


class CoachResponse(BaseModel):
    """Structured response from the learning coach."""

    message: str = Field(description="The coach's response message to the learner (max ~100 words)")
    finalized_topic: str | None = Field(
        default=None,
        description=(
            "When you have clarity on both WHAT they want to learn and their current knowledge level, "
            "provide a detailed topic description including: specific topics/concepts, starting level "
            "(e.g., 'beginner', 'intermediate with Python basics'), focus areas, scope for 2-10 "
            "mini-lessons, and the learning objectives (listed out). Update this if they request changes. "
            "Leave null only while still gathering information."
        ),
    )
    unit_title: str | None = Field(
        default=None,
        description=(
            "When finalizing, provide a short, engaging unit title (1-6 words) that captures the essence "
            "of what they'll learn. Examples: 'React Native with Expo', 'Python Data Structures', "
            "'Web API Design Basics'. Update if the learner requests changes."
        ),
    )
    learning_objectives: list[CoachLearningObjective] | None = Field(
        default=None,
        description=(
            "When finalizing the topic, provide 3-8 clear, specific learning objectives. Each must include "
            "a stable identifier (e.g., 'lo_1'), a short 3-8 word title, and a full description. Objectives "
            "should be measurable, action-oriented, and appropriate for the learner's level. Update if the learner requests changes."
        ),
    )
    suggested_lesson_count: int | None = Field(
        default=None,
        description=("When finalizing, suggest the number of lessons (2-10) to cover the learning objectives. Consider the breadth of objectives, the learner's level, and natural topic boundaries. Update if the learner requests changes."),
    )
    suggested_quick_replies: list[str] | None = Field(
        default=None,
        description=(
            "Provide 2-5 contextually relevant quick reply options based on the conversation state. "
            "These should be natural follow-ups to help guide the learner to the next step. "
            "Examples: 'Tell me more', 'Yes, that works', 'Can we adjust the focus?', 'I'm a beginner'. "
            "Keep each under 40 characters. Tailor to what you need to know next or what the learner might want to say."
        ),
    )


class LearningCoachConversation(BaseConversation):
    """High-level dialog handler for the learning coach experience."""

    conversation_type = "learning_coach"
    system_prompt_file = "prompts/system_prompt.md"

    @conversation_session
    async def add_resource(
        self,
        *,
        _conversation_id: str | None = None,
        _user_id: int | None = None,
        resource_id: str,
    ) -> LearningCoachSessionState:
        """Attach a learner resource to the active conversation."""

        resource_uuid = uuid.UUID(str(resource_id))

        resources = await _fetch_resources([resource_uuid])
        if not resources:
            raise LookupError("Resource not found")

        summary = await self.get_conversation_summary()
        existing_ids = self._extract_resource_ids(summary.metadata)
        stored_ids = [str(item) for item in existing_ids]
        resource_id_str = str(resource_uuid)
        if resource_id_str not in stored_ids:
            stored_ids.append(resource_id_str)
            await self.update_conversation_metadata({RESOURCE_METADATA_KEY: stored_ids})

        return await self._build_session_state()

    @conversation_session
    async def start_session(
        self,
        *,
        _user_id: int | None = None,
        _conversation_id: str | None = None,
        topic: str | None = None,
        _conversation_metadata: dict[str, Any] | None = None,
        _conversation_title: str | None = None,
    ) -> LearningCoachSessionState:
        """Kick off a new learning coach conversation."""
        if topic:
            await self.record_user_message(f"I'd like to learn about {topic}.")
        await self._ensure_opening_assistant_turn()
        return await self._build_session_state()

    @conversation_session
    async def submit_learner_turn(
        self,
        *,
        _conversation_id: str | None = None,
        _user_id: int | None = None,
        message: str,
    ) -> LearningCoachSessionState:
        """Record a learner response and fetch the follow-up coach reply."""

        await self.record_user_message(message)
        await self._generate_structured_reply()
        return await self._build_session_state()

    @conversation_session
    async def accept_brief(
        self,
        *,
        _conversation_id: str | None = None,
        _user_id: int | None = None,
        brief: dict[str, Any],
    ) -> LearningCoachSessionState:
        """Mark the current proposal as accepted and return the refreshed state."""

        metadata_update = {
            "accepted_brief": brief,
            "accepted_at": datetime.now(UTC).isoformat(),
        }
        await self.update_conversation_metadata(metadata_update)
        return await self._build_session_state()

    async def _ensure_opening_assistant_turn(self) -> None:
        """Ensure the coach has produced an opening prompt."""

        ctx = ConversationContext.current()
        history = await ctx.service.get_message_history(ctx.conversation_id, include_system=False)
        if any(message.role == "assistant" for message in history):
            return
        # Start with a simple static greeting
        await self.record_assistant_message("What would you like to learn today?")

    async def _build_session_state(self) -> LearningCoachSessionState:
        """Assemble the latest session state for clients."""

        ctx = ConversationContext.current()
        history = await ctx.service.get_message_history(ctx.conversation_id, include_system=False)
        summary = await self.get_conversation_summary()
        metadata = dict(summary.metadata or {})
        resources = await self._load_conversation_resources()

        return LearningCoachSessionState(
            conversation_id=str(ctx.conversation_id),
            messages=[self._to_message(message) for message in history],
            metadata=metadata,
            finalized_topic=metadata.get("finalized_topic"),
            unit_title=metadata.get("unit_title"),
            learning_objectives=self._parse_learning_objectives(metadata.get("learning_objectives")),
            suggested_lesson_count=metadata.get("suggested_lesson_count"),
            proposed_brief=self._dict_or_none(metadata.get("proposed_brief")),
            accepted_brief=self._dict_or_none(metadata.get("accepted_brief")),
            resources=[self._to_resource_summary(resource) for resource in resources],
        )

    def _to_message(self, message: ConversationMessageDTO) -> LearningCoachMessage:
        """Convert a conversation engine DTO into a learning coach message."""

        return LearningCoachMessage(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            metadata=dict(message.metadata or {}),
        )

    def _dict_or_none(self, value: Any) -> dict[str, Any] | None:
        """Return the provided value if it is a mapping."""

        if isinstance(value, dict):
            return value
        return None

    def _parse_learning_objectives(
        self,
        value: Any,
    ) -> list[LearningCoachObjective] | None:
        """Convert stored metadata into typed learning objectives."""

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

    async def _generate_structured_reply(self) -> None:
        """Generate a structured coach response and persist it."""

        resources = await self._load_conversation_resources()
        from .service import build_resource_context_prompt

        base_prompt = self.get_system_prompt()
        resource_context = build_resource_context_prompt(resources)
        system_prompt = self._merge_system_prompt(base_prompt, resource_context)

        coach_response, request_id, raw_response = await self.generate_structured_reply(
            CoachResponse,
            model="claude-haiku-4-5",
            system_prompt=system_prompt,
        )

        # Record the assistant message
        message_metadata: dict[str, Any] = {
            "provider": raw_response.get("provider", "openai"),
        }
        if coach_response.suggested_quick_replies is not None:
            message_metadata["suggested_quick_replies"] = coach_response.suggested_quick_replies
        await self.record_assistant_message(
            coach_response.message,
            metadata=message_metadata,
            llm_request_id=request_id,
            tokens_used=raw_response.get("usage", {}).get("total_tokens"),
            cost_estimate=raw_response.get("cost_estimate"),
        )

        # If topic is finalized, update conversation metadata
        if coach_response.finalized_topic:
            metadata_update: dict[str, Any] = {
                "finalized_topic": coach_response.finalized_topic,
                "finalized_at": datetime.now(UTC).isoformat(),
            }
            if coach_response.unit_title is not None:
                metadata_update["unit_title"] = coach_response.unit_title
            if coach_response.learning_objectives is not None:
                metadata_update["learning_objectives"] = [objective.model_dump() for objective in coach_response.learning_objectives]
            if coach_response.suggested_lesson_count is not None:
                metadata_update["suggested_lesson_count"] = coach_response.suggested_lesson_count
            await self.update_conversation_metadata(metadata_update)

    async def _load_conversation_resources(self) -> list[ResourceRead]:
        """Return resources referenced by the current conversation metadata."""

        metadata = ConversationContext.current().metadata or {}
        resource_ids = self._coerce_resource_ids(metadata.get(RESOURCE_METADATA_KEY))
        return await _fetch_resources(resource_ids)

    def _extract_resource_ids(self, metadata: Any) -> list[uuid.UUID]:
        """Parse stored resource identifiers from conversation metadata."""

        if not isinstance(metadata, dict):
            return []
        return self._coerce_resource_ids(metadata.get(RESOURCE_METADATA_KEY))

    def _coerce_resource_ids(self, value: Any) -> list[uuid.UUID]:
        """Convert stored identifier values into UUID instances."""

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

    def _to_resource_summary(self, resource: ResourceRead) -> LearningCoachResource:
        """Convert a resource record into the conversation DTO format."""

        preview = resource.extracted_text.strip()
        if len(preview) > 200:
            preview = preview[:200]
        return LearningCoachResource(
            id=str(resource.id),
            resource_type=resource.resource_type,
            filename=resource.filename,
            source_url=resource.source_url,
            file_size=resource.file_size,
            created_at=resource.created_at,
            preview_text=preview,
        )

    def _merge_system_prompt(self, base_prompt: str | None, resource_context: str | None) -> str | None:
        """Combine the static system prompt with dynamic resource context."""

        if base_prompt and resource_context:
            return f"{base_prompt}\n\n{resource_context}"
        return resource_context or base_prompt
