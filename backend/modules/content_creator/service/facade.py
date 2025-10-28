"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

from __future__ import annotations

import logging

from modules.content.public import ContentProvider, UnitCreate, UnitRead, UnitStatus

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
    ) -> None:
        """Initialize with content storage only - flows handle LLM interactions."""

        self.content = content
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
        topic: str,
        source_material: str | None = None,
        background: bool = False,
        target_lesson_count: int | None = None,
        learner_level: str = "beginner",
        user_id: int | None = None,
        unit_title: str | None = None,
    ) -> UnitCreationResult | MobileUnitCreationResult:
        """Create a learning unit (foreground or background)."""

        provisional_title = self._truncate_title(unit_title if unit_title else topic, max_length=200)
        unit = await self.content.create_unit(
            UnitCreate(
                title=provisional_title,
                description=topic,
                learner_level=learner_level,
                lesson_order=[],
                user_id=user_id,
                learning_objectives=None,
                target_lesson_count=target_lesson_count,
                source_material=source_material,
                generated_from_topic=(source_material is None),
                flow_type="standard",
            )
        )
        await self.content.update_unit_status(
            unit_id=unit.id,
            status=UnitStatus.IN_PROGRESS.value,
            creation_progress={"stage": "starting", "message": "Initialization"},
        )

        if background:
            await self._status_handler.enqueue_unit_creation(
                unit_id=unit.id,
                topic=topic,
                source_material=source_material,
                target_lesson_count=target_lesson_count,
                learner_level=learner_level,
            )
            return MobileUnitCreationResult(unit_id=unit.id, title=unit.title, status=UnitStatus.IN_PROGRESS.value)

        return await self._flow_handler.execute_unit_creation_pipeline(
            unit_id=unit.id,
            topic=topic,
            source_material=source_material,
            target_lesson_count=target_lesson_count,
            learner_level=learner_level,
            arq_task_id=None,
        )

    async def _execute_unit_creation_pipeline(
        self,
        *,
        unit_id: str,
        topic: str,
        source_material: str | None,
        target_lesson_count: int | None,
        learner_level: str,
        arq_task_id: str | None = None,
    ) -> UnitCreationResult:
        """Delegate to the flow handler for unit creation."""

        return await self._flow_handler.execute_unit_creation_pipeline(
            unit_id=unit_id,
            topic=topic,
            source_material=source_material,
            target_lesson_count=target_lesson_count,
            learner_level=learner_level,
            arq_task_id=arq_task_id,
        )

    async def retry_unit_creation(self, unit_id: str) -> MobileUnitCreationResult | None:
        """Retry failed unit creation."""

        return await self._status_handler.retry_unit_creation(unit_id)

    async def dismiss_unit(self, unit_id: str) -> bool:
        """Dismiss (delete) a unit."""

        return await self._status_handler.dismiss_unit(unit_id)

    async def check_and_timeout_stale_units(self, timeout_seconds: int = 3600) -> int:
        """Check for units stuck in 'in_progress' status and mark them as failed."""

        return await self._status_handler.check_and_timeout_stale_units(timeout_seconds)


__all__ = ["ContentCreatorService", "MobileUnitCreationResult", "UnitCreationResult"]
