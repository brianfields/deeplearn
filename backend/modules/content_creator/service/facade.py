"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
import logging

from modules.content.public import ContentProvider, UnitCreate, UnitRead, UnitStatus
from modules.learning_conversations.public import (
    LearningCoachSessionState,
    LearningConversationsProvider,
    learning_conversations_provider,
)
from modules.resource.public import ResourceProvider, ResourceRead

from ..podcast import LessonPodcastGenerator, UnitPodcastGenerator
from .dtos import MobileUnitCreationResult, UnitCreationResult
from .flow_handler import FlowHandler
from .media_handler import MediaHandler
from .prompt_handler import PromptHandler
from .status_handler import StatusHandler

logger = logging.getLogger(__name__)


class ContentCreatorService:
    """Service for AI-powered content creation."""

    UnitCreationResult = UnitCreationResult
    MobileUnitCreationResult = MobileUnitCreationResult

    def __init__(
        self,
        content: ContentProvider,
        podcast_generator: UnitPodcastGenerator | None = None,
        lesson_podcast_generator: LessonPodcastGenerator | None = None,
        learning_coach_factory: Callable[[], LearningConversationsProvider] | None = None,
        resource_factory: Callable[[], Awaitable[ResourceProvider]] | None = None,
    ) -> None:
        """Initialize with content storage only - flows handle LLM interactions."""

        self.content = content
        self._learning_coach_factory = learning_coach_factory or learning_conversations_provider
        self._resource_factory = resource_factory
        self._resource_service: ResourceProvider | None = None
        self._prompt_handler = PromptHandler()
        self._media_handler = MediaHandler(
            content,
            self._prompt_handler,
            podcast_generator=podcast_generator,
            lesson_podcast_generator=lesson_podcast_generator,
        )
        self._flow_handler = FlowHandler(content, self._prompt_handler, self._media_handler)
        self._status_handler = StatusHandler(content)

    @property
    def podcast_generator(self) -> UnitPodcastGenerator | None:
        """Expose the cached unit podcast generator for compatibility with tests."""

        return self._media_handler._podcast_generator

    @podcast_generator.setter
    def podcast_generator(self, value: UnitPodcastGenerator | None) -> None:
        self._media_handler._podcast_generator = value

    @property
    def lesson_podcast_generator(self) -> LessonPodcastGenerator | None:
        """Expose the cached lesson podcast generator for compatibility with tests."""

        return self._media_handler._lesson_podcast_generator

    @lesson_podcast_generator.setter
    def lesson_podcast_generator(self, value: LessonPodcastGenerator | None) -> None:
        self._media_handler._lesson_podcast_generator = value

    def _truncate_title(self, title: str, max_length: int = 255) -> str:
        """Truncate title to fit database constraint."""

        if len(title) <= max_length:
            return title
        return title[: max_length - 3] + "..."

    async def create_unit_art(self, unit_id: str, arq_task_id: str | None = None) -> UnitRead:
        """Generate and persist Weimar Edge artwork for the specified unit."""

        return await self._media_handler.create_unit_art(unit_id, arq_task_id=arq_task_id)

    async def create_unit(
        self,
        *,
        learner_desires: str,
        learning_objectives: list,
        unit_title: str | None = None,
        target_lesson_count: int | None = None,
        conversation_id: str | None = None,
        source_material: str | None = None,
        background: bool = False,
        user_id: int | None = None,
    ) -> UnitCreationResult | MobileUnitCreationResult:
        """Create a learning unit from coach-driven context (required).

        All parameters are required because the coach conversation must finalize them.
        """
        if not learning_objectives:
            raise ValueError("learning_objectives must be provided")

        # Use coach title if provided, otherwise generate from learner_desires
        title_source = unit_title if unit_title else learner_desires
        provisional_title = self._truncate_title(title_source, max_length=200)

        combined_source_material = source_material
        conversation_resources: list[ResourceRead] = []
        uncovered_lo_ids: list[str] | None = None
        session_state: LearningCoachSessionState | None = None
        supplemental_text: str | None = None

        if conversation_id is not None:
            conversation_resources = await self._fetch_conversation_resources(conversation_id)
            uncovered_lo_ids, session_state = await self._fetch_uncovered_lo_ids(conversation_id)

            if conversation_resources:
                resource_text = self._combine_resource_texts(conversation_resources)
                if resource_text.strip():
                    combined_source_material = resource_text

                    if uncovered_lo_ids:
                        supplemental_text = await self._generate_supplemental_source_material(
                            learner_desires=learner_desires,
                            target_lesson_count=target_lesson_count,
                            uncovered_lo_ids=uncovered_lo_ids,
                            session_state=session_state,
                        )
                        if supplemental_text:
                            combined_source_material = self._combine_resource_and_supplemental_text(
                                resource_text,
                                supplemental_text,
                            )

        # Convert learning_objectives to dicts early (for UnitCreate, background queue, and flow handler)
        lo_list = []
        for lo in learning_objectives:
            if hasattr(lo, "model_dump"):
                lo_list.append(lo.model_dump())
            elif isinstance(lo, dict):
                lo_list.append(lo)
            else:
                # Handle plain objects with attributes
                lo_list.append(
                    {
                        "id": getattr(lo, "id", str(lo)),
                        "title": getattr(lo, "title", ""),
                        "description": getattr(lo, "description", ""),
                        "bloom_level": getattr(lo, "bloom_level", None),
                        "evidence_of_mastery": getattr(lo, "evidence_of_mastery", None),
                    }
                )

        # Create unit with coach LOs
        unit = await self.content.create_unit(
            UnitCreate(
                title=provisional_title,
                description=learner_desires,
                learner_level="beginner",  # Default for coach-driven units
                lesson_order=[],
                user_id=user_id,
                learning_objectives=lo_list,
                target_lesson_count=target_lesson_count,
                source_material=combined_source_material,
                generated_from_topic=False,  # Coach-driven units don't generate from topic
                flow_type="standard",
            )
        )
        await self.content.update_unit_status(
            unit_id=unit.id,
            status=UnitStatus.IN_PROGRESS.value,
            creation_progress={"stage": "starting", "message": "Initialization"},
        )

        if conversation_id is not None:
            owner_id = user_id
            if owner_id is None and conversation_resources:
                owner_id = conversation_resources[0].user_id
            await self._link_resources_and_save_generated_source(
                unit_id=unit.id,
                resources=conversation_resources,
                user_id=owner_id,
                supplemental_text=supplemental_text,
                uncovered_learning_objective_ids=uncovered_lo_ids,
            )

        if background:
            await self._status_handler.enqueue_unit_creation(
                unit_id=unit.id,
                learner_desires=learner_desires,
                learning_objectives=lo_list,
                source_material=combined_source_material,
                target_lesson_count=target_lesson_count,
            )
            return MobileUnitCreationResult(unit_id=unit.id, title=unit.title, status=UnitStatus.IN_PROGRESS.value)

        result = await self._flow_handler.execute_unit_creation_pipeline(
            unit_id=unit.id,
            learner_desires=learner_desires,
            learning_objectives=lo_list,
            source_material=combined_source_material,
            target_lesson_count=target_lesson_count,
            arq_task_id=None,
        )

        return result

    async def retry_unit_creation(self, unit_id: str) -> MobileUnitCreationResult | None:
        """Retry failed unit creation."""

        return await self._status_handler.retry_unit_creation(unit_id)

    async def dismiss_unit(self, unit_id: str) -> bool:
        """Dismiss (delete) a unit."""

        return await self._status_handler.dismiss_unit(unit_id)

    async def check_and_timeout_stale_units(self, timeout_seconds: int = 3600) -> int:
        """Check for units stuck in 'in_progress' status and mark them as failed."""

        return await self._status_handler.check_and_timeout_stale_units(timeout_seconds)

    async def _fetch_conversation_resources(self, conversation_id: str) -> list[ResourceRead]:
        """Return resources associated with a learning coach conversation."""

        try:
            coach = self._learning_coach_factory()
            resources = await coach.get_conversation_resources(conversation_id)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to load conversation resources for conversation_id=%s: %s", conversation_id, exc)
            return []

        return list(resources)

    async def _fetch_uncovered_lo_ids(self, conversation_id: str) -> tuple[list[str] | None, LearningCoachSessionState | None]:
        """Fetch uncovered learning objective identifiers from conversation metadata."""

        try:
            coach = self._learning_coach_factory()
            session_state = await coach.get_session_state(conversation_id)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to load conversation metadata for conversation_id=%s: %s", conversation_id, exc)
            return None, None

        metadata = session_state.metadata or {}
        value = metadata.get("uncovered_learning_objective_ids")
        if not isinstance(value, list):
            return None, session_state

        uncovered: list[str] = []
        for entry in value:
            item = str(entry).strip()
            if item:
                uncovered.append(item)

        return (uncovered or [], session_state)

    def _combine_resource_texts(
        self,
        resources: list[ResourceRead],
        *,
        max_bytes: int = 200_000,
    ) -> str:
        """Combine resource texts into a single prompt-friendly block respecting byte limits."""

        parts: list[str] = []
        current_bytes = 0

        for index, resource in enumerate(resources, start=1):
            content = resource.extracted_text or ""
            if not content.strip():
                continue

            label = resource.filename or resource.source_url or f"Resource {index}"
            header = f"\n\n## Source: {label}\n\n"

            header_bytes = len(header.encode("utf-8"))
            content_bytes = len(content.encode("utf-8"))

            if current_bytes + header_bytes + content_bytes > max_bytes:
                remaining = max_bytes - current_bytes - header_bytes
                if remaining > 100:
                    truncated_bytes = content.encode("utf-8")[: max(0, remaining)]
                    truncated = truncated_bytes.decode("utf-8", errors="ignore")
                    if truncated:
                        parts.append(header + truncated)
                break

            parts.append(header + content)
            current_bytes += header_bytes + content_bytes

        return "".join(parts)

    async def _get_resource_service(self) -> ResourceProvider | None:
        """Lazily resolve the resource provider for cross-module coordination."""

        if self._resource_service is not None:
            return self._resource_service

        if self._resource_factory is None:
            return None

        try:
            resource_service = await self._resource_factory()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to initialize resource provider: %s", exc)
            return None

        self._resource_service = resource_service
        return resource_service

    async def _generate_supplemental_source_material(
        self,
        *,
        learner_desires: str,
        target_lesson_count: int | None = None,
        uncovered_lo_ids: list[str] | None = None,
        session_state: LearningCoachSessionState | None = None,
    ) -> str | None:
        """Generate supplemental source material focused on uncovered learning objectives."""

        if not uncovered_lo_ids:
            return None

        if session_state is None or not session_state.learning_objectives:
            return None

        objective_lookup = {obj.id: obj for obj in session_state.learning_objectives}
        selected_objectives = [objective_lookup.get(lo_id) for lo_id in uncovered_lo_ids]
        filtered_objectives = [obj for obj in selected_objectives if obj is not None]
        if not filtered_objectives:
            return None

        try:
            from ..steps import GenerateSupplementalSourceMaterialStep
        except ImportError:  # pragma: no cover - defensive guard
            logger.warning("Supplemental generation step unavailable")
            return None

        objectives_outline = "\n".join(f"- {obj.id}: {obj.title} — {obj.description}" for obj in filtered_objectives)

        inputs = GenerateSupplementalSourceMaterialStep.Inputs(
            learner_desires=learner_desires,
            target_lesson_count=(target_lesson_count if target_lesson_count is not None else getattr(session_state, "suggested_lesson_count", None)),
            objectives_outline=objectives_outline,
        )

        try:
            result = await GenerateSupplementalSourceMaterialStep().execute(inputs.model_dump())
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Failed to generate supplemental source material for uncovered LOs %s: %s",
                uncovered_lo_ids,
                exc,
            )
            return None

        output_text = str(result.output_content or "").strip()
        return output_text or None

    def _combine_resource_and_supplemental_text(self, resource_text: str, supplemental_text: str) -> str:
        """Merge learner-provided resource text with supplemental generated content."""

        resource_section = resource_text.strip()
        supplemental_section = supplemental_text.strip()

        parts: list[str] = []
        if resource_section:
            parts.append("## Learner-Provided Materials\n\n" + resource_section)
        if supplemental_section:
            parts.append("## Supplemental Generated Content\n\n" + supplemental_section)

        return "\n\n".join(parts)

    async def _link_resources_and_save_generated_source(
        self,
        *,
        unit_id: str,
        resources: list[ResourceRead],
        user_id: int | None,
        supplemental_text: str | None,
        uncovered_learning_objective_ids: list[str] | None,
    ) -> None:
        """Associate learner resources and supplemental material with the created unit."""

        resource_service = await self._get_resource_service()
        if resource_service is None:
            return

        resource_ids = [resource.id for resource in resources if getattr(resource, "id", None) is not None]
        if resource_ids:
            try:
                await resource_service.attach_resources_to_unit(unit_id=unit_id, resource_ids=resource_ids)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Failed to link resources to unit_id=%s: %s", unit_id, exc)

        if supplemental_text is None or not supplemental_text.strip():
            return

        owner_id = user_id
        if owner_id is None and resources:
            owner_id = getattr(resources[0], "user_id", None)
        if owner_id is None:
            logger.warning("Unable to persist supplemental material for unit_id=%s without user context", unit_id)
            return

        metadata = {
            "generated_at": datetime.now(UTC).isoformat(),
            "method": "ai_supplemental",
            "uncovered_lo_ids": uncovered_learning_objective_ids or [],
        }

        try:
            generated_resource = await resource_service.create_generated_source_resource(
                user_id=owner_id,
                unit_id=unit_id,
                source_text=supplemental_text,
                metadata=metadata,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to persist supplemental source for unit_id=%s: %s", unit_id, exc)
            return

        try:
            await resource_service.attach_resources_to_unit(
                unit_id=unit_id,
                resource_ids=[generated_resource.id],
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Failed to link generated supplemental resource to unit_id=%s: %s",
                unit_id,
                exc,
            )


__all__ = ["ContentCreatorService", "MobileUnitCreationResult", "UnitCreationResult"]
