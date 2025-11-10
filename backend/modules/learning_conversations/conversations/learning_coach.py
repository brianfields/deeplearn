"""Learning coach conversation orchestration."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
import uuid

from pydantic import BaseModel, Field, field_validator

from modules.conversation_engine.public import (
    BaseConversation,
    ConversationContext,
    ConversationMessageDTO,
    conversation_session,
)
from modules.infrastructure.public import infrastructure_provider

from ..dtos import (
    UNSET,
    LearningCoachMessage,
    LearningCoachObjective,
    LearningCoachResource,
    LearningCoachSessionState,
    UncoveredLearningObjectiveIds,
)

if TYPE_CHECKING:
    from modules.resource.service import ResourceRead


RESOURCE_METADATA_KEY = "resource_ids"


async def _fetch_resources(resource_ids: Sequence[uuid.UUID]) -> list[ResourceRead]:
    """Load resource records for the provided identifiers."""

    if not resource_ids:
        return []

    from ..service import fetch_resources_for_ids

    infra = infrastructure_provider()
    infra.initialize()
    return await fetch_resources_for_ids(infra, resource_ids)


class CoachLearningObjective(BaseModel):
    """Learning objective emitted by finalization extraction."""

    id: str = Field(..., min_length=1, max_length=50, description="Stable identifier for the unit learning objective")
    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Short 3-8 word title that summarizes the learning objective",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Full explanation of the learning objective for learner-facing surfaces",
    )


class CoachResponse(BaseModel):
    """Structured response from the learning coach (conversational turn)."""

    text: str = Field(max_length=1000, description="The coach's response message to the learner (max ~100 words)")
    suggested_quick_replies: list[str] | None = Field(
        default=None,
        max_length=5,
        description=(
            "Provide 2-5 contextually relevant quick reply options based on the conversation state. "
            "These should be natural follow-ups to help guide the learner to the next step. "
            "Examples: 'Tell me more', 'Yes, that works', 'Can we adjust the focus?', 'I'm a beginner'. "
            "Keep each under 40 characters. Tailor to what you need to know next or what the learner might want to say."
        ),
    )
    ready_to_finalize: bool = Field(
        description=(
            "REQUIRED: Set to true when you have clarity on BOTH what they want to learn AND their current knowledge level. "
            "When true, a separate extraction step will gather detailed metadata (topic, title, objectives, etc.). "
            "Set to false while still gathering information or clarifying their needs. "
            "IMPORTANT: You MUST explicitly include this field in every response (true or false)."
        ),
    )
    uncovered_learning_objective_ids: list[str] | None = Field(
        default=None,
        description=("Learning objective identifiers that are not adequately covered by the learner's shared resources. Return an empty list when resources cover every objective and null when no resources are available to evaluate."),
    )


class FinalizationExtraction(BaseModel):
    """Metadata extracted when ready to finalize the learning unit."""

    finalized_topic: str = Field(
        max_length=2000,
        description=("A detailed topic description including: specific topics/concepts, starting level (e.g., 'beginner', 'intermediate with Python basics'), focus areas, scope for 2-10 mini-lessons, and the learning objectives (listed out)."),
    )
    unit_title: str = Field(
        max_length=80,
        description=(
            "A short, engaging unit title (3-10 words max, 80 chars max) that captures "
            "the essence of what they'll learn. Examples: 'React Native with Expo', 'Python Data Structures', "
            "'Web API Design Basics', 'Introduction to Roman Republic'. Keep it concise!"
        ),
    )
    learning_objectives: list[CoachLearningObjective] = Field(
        description=(
            "3-8 clear, specific learning objectives. Each must include a stable identifier (e.g., 'lo_1'), a short 3-8 word title, and a full description. Objectives should be measurable, action-oriented, and appropriate for the learner's level."
        ),
    )
    suggested_lesson_count: int = Field(
        ge=2,
        le=10,
        description=("The number of lessons (2-10) to cover the learning objectives. Consider the breadth of objectives, the learner's level, and natural topic boundaries."),
    )
    learner_desires: str = Field(
        max_length=2000,
        description=(
            "A comprehensive synthesis of the learner's goals, prior knowledge, "
            "learning style preferences, and constraints. Include: specific topic, difficulty level, prior exposure, "
            "presentation preferences, voice/tone, time constraints, and any other relevant context. "
            "Write this for AI systems to read (not learners)."
        ),
    )

    @field_validator("unit_title", mode="before")
    @classmethod
    def truncate_unit_title(cls, v: str | None) -> str | None:
        """Truncate unit_title if it exceeds the limit."""
        if v and len(v) > 80:
            return v[:77] + "..."
        return v


class LearningCoachConversation(BaseConversation):
    """High-level dialog handler for the learning coach experience."""

    conversation_type = "learning_coach"
    system_prompt_file = "../prompts/system_prompt.md"
    finalization_prompt_file = "../prompts/finalization_extraction.md"

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

        resource = resources[0]
        print(f"[DEBUG] add_resource: resource.user_id={resource.user_id}, _user_id={_user_id}, resource_id={resource_id}")
        if _user_id is None or resource.user_id != _user_id:
            raise PermissionError("Resource does not belong to the active learner")

        summary = await self.get_conversation_summary()
        existing_ids = self._extract_resource_ids(summary.metadata)
        stored_ids = [str(item) for item in existing_ids]
        resource_id_str = str(resource_uuid)
        print(f"[DEBUG] add_resource: existing_ids={existing_ids}, resource_id_str={resource_id_str}")
        if resource_id_str not in stored_ids:
            stored_ids.append(resource_id_str)
            await self.update_conversation_metadata({RESOURCE_METADATA_KEY: stored_ids})
            print(f"[DEBUG] add_resource: Updated metadata with resource_ids={stored_ids}")

            # Inject a user message showing what was shared
            resource_name = resource.filename or resource.source_url or resource.resource_type
            await self.record_user_message(f"[shared {resource_name}]")

            # Generate coach acknowledgment with resource context
            await self._generate_structured_reply()

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
        uncovered_ids = self._parse_uncovered_learning_objective_ids(metadata.get("uncovered_learning_objective_ids")) if "uncovered_learning_objective_ids" in metadata else UNSET

        return LearningCoachSessionState(
            conversation_id=str(ctx.conversation_id),
            messages=[self._to_message(message) for message in history],
            metadata=metadata,
            finalized_topic=metadata.get("finalized_topic"),
            learner_desires=metadata.get("learner_desires"),
            unit_title=metadata.get("unit_title"),
            learning_objectives=self._parse_learning_objectives(metadata.get("learning_objectives")),
            suggested_lesson_count=metadata.get("suggested_lesson_count"),
            proposed_brief=self._dict_or_none(metadata.get("proposed_brief")),
            accepted_brief=self._dict_or_none(metadata.get("accepted_brief")),
            resources=[self._to_resource_summary(resource) for resource in resources],
            uncovered_learning_objective_ids=uncovered_ids,
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

    def _parse_uncovered_learning_objective_ids(self, value: Any) -> UncoveredLearningObjectiveIds:
        """Normalize uncovered learning objective identifiers from metadata."""

        if value is None:
            return None

        if not isinstance(value, list):
            return []

        normalized = [str(item) for item in value if isinstance(item, str) and item.strip()]

        return normalized

    async def _generate_structured_reply(self) -> None:
        """Generate a structured coach response and persist it."""

        resources = await self._load_conversation_resources()
        from ..service import build_resource_context_prompt

        base_prompt = self.get_system_prompt()
        resource_context = build_resource_context_prompt(resources)
        system_prompt = self._merge_system_prompt(base_prompt, resource_context)

        # Step 1: Generate conversational response with ready_to_finalize flag
        coach_response, request_id, raw_response = await self.generate_structured_reply(
            CoachResponse,
            model="gemini-2.5-flash",
            system_prompt=system_prompt,
        )

        # Record the assistant message
        message_metadata: dict[str, Any] = {
            "provider": raw_response.get("provider", "openai"),
        }
        if coach_response.suggested_quick_replies is not None:
            message_metadata["suggested_quick_replies"] = coach_response.suggested_quick_replies
        await self.record_assistant_message(
            coach_response.text,
            metadata=message_metadata,
            llm_request_id=request_id,
            tokens_used=raw_response.get("usage", {}).get("total_tokens"),
            cost_estimate=raw_response.get("cost_estimate"),
        )

        # Update uncovered_learning_objective_ids if present
        metadata_update: dict[str, Any] = {}
        if coach_response.uncovered_learning_objective_ids is not None:
            metadata_update["uncovered_learning_objective_ids"] = coach_response.uncovered_learning_objective_ids

        # Step 2: If ready to finalize, extract detailed metadata using a separate LLM call
        if coach_response.ready_to_finalize:
            finalization_data = await self._extract_finalization_metadata(system_prompt)

            # Update conversation metadata with finalization data
            metadata_update.update(
                {
                    "finalized_topic": finalization_data.finalized_topic,
                    "unit_title": finalization_data.unit_title,
                    "learning_objectives": [obj.model_dump() for obj in finalization_data.learning_objectives],
                    "suggested_lesson_count": finalization_data.suggested_lesson_count,
                    "learner_desires": finalization_data.learner_desires,
                    "finalized_at": datetime.now(UTC).isoformat(),
                }
            )

            # Inject finalization into conversation history for context
            await self._inject_finalization_into_history(finalization_data)

        if metadata_update:
            await self.update_conversation_metadata(metadata_update)

    async def _extract_finalization_metadata(self, conversation_context: str | None) -> FinalizationExtraction:
        """Extract finalization metadata using a separate LLM call with gemini-2.5-pro."""

        # Load finalization prompt
        finalization_prompt = self._load_prompt_file(self.finalization_prompt_file)

        # Build system prompt with conversation context
        system_prompt = finalization_prompt
        if conversation_context:
            system_prompt = f"{finalization_prompt}\n\n## Conversation Context\n\n{conversation_context}"

        # Use gemini-2.5-pro for better reasoning on metadata extraction
        extraction_result, _request_id, _raw = await self.generate_structured_reply(
            FinalizationExtraction,
            model="gemini-2.5-pro",
            system_prompt=system_prompt,
        )

        return extraction_result

    async def _inject_finalization_into_history(self, finalization_data: FinalizationExtraction) -> None:
        """Inject finalization metadata into conversation history for context."""

        # Format learning objectives for display
        objectives_text = "\n".join([f"  - {obj.id}: {obj.title} - {obj.description}" for obj in finalization_data.learning_objectives])

        # Create a system message documenting the finalization
        finalization_message = f"""[FINALIZATION EXTRACTED]

Unit Title: {finalization_data.unit_title}
Suggested Lesson Count: {finalization_data.suggested_lesson_count}

Topic Description:
{finalization_data.finalized_topic}

Learning Objectives:
{objectives_text}

Learner Context:
{finalization_data.learner_desires}"""

        # Record as a system message
        await self.record_system_message(finalization_message)

    def _load_prompt_file(self, relative_path: str) -> str:
        """Load a prompt file relative to this module."""
        from pathlib import Path

        # Get the directory containing this file
        current_dir = Path(__file__).parent
        prompt_path = (current_dir / relative_path).resolve()

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        return prompt_path.read_text(encoding="utf-8")

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
