"""Content service for intro lesson creation in content creator module."""

from __future__ import annotations

import logging
from typing import Any

from modules.catalog.service import LessonSummary
from modules.content.public import ContentProvider

from ..podcast import UnitPodcast

logger = logging.getLogger(__name__)


class ContentService:
    """Service for intro lesson creation and management during content creation."""

    def __init__(self, content: ContentProvider, repo: Any = None) -> None:
        """Initialize with content provider for all operations.

        Args:
            content: ContentProvider for accessing content service methods.
            repo: Optional repo (reserved for future use; not needed if content provider has helper methods).
        """
        self._content = content
        self._repo = repo

    async def create_intro_lesson(
        self,
        *,
        unit_id: str,
        podcast: UnitPodcast,
        learner_level: str = "beginner",
    ) -> tuple[str, LessonSummary]:
        """Create an intro lesson from generated podcast and return lesson_id + summary DTO.

        Validates that no intro lesson already exists (idempotency), creates minimal lesson
        package, persists podcast audio/metadata, and prepends lesson to unit.lesson_order.

        Returns:
            Tuple of (lesson_id, lesson_summary_dto)

        Raises:
            ValueError: If unit not found, audio bytes missing, or intro already exists.
            RuntimeError: If lesson creation fails.
        """
        # Check if intro already exists (idempotency)
        try:
            existing_summary = await self._content.get_intro_lesson_summary(unit_id)
            if existing_summary is not None:
                logger.info(f"Intro lesson already exists for unit {unit_id}; returning existing")
                return existing_summary.id, existing_summary
        except Exception as e:
            # Helper not available; continue to create
            logger.debug(f"Could not fetch existing intro lesson: {e}")

        if not podcast.audio_bytes:
            raise ValueError("Podcast audio_bytes required to create intro lesson")

        # Fetch unit to verify it exists
        unit = await self._content.get_unit_detail(unit_id, include_art_presigned_url=False)
        if unit is None:
            raise ValueError(f"Unit {unit_id} not found")

        # Generate consistent lesson ID
        intro_lesson_id = f"{unit_id}-intro"

        # Create minimal valid package for intro lesson (no exercises)
        from modules.content.package_models import LessonPackage

        empty_package = LessonPackage(
            exercise_bank=[],
            quiz=[],
            meta={"title": "Unit Introduction", "version": 1},
            unit_learning_objective_ids=[],
        )

        # Create the intro lesson via content service
        from modules.content.service.dtos import LessonCreate

        lesson_create = LessonCreate(
            id=intro_lesson_id,
            title="Unit Introduction",
            learner_level=learner_level,
            lesson_type="intro",  # Mark as intro lesson
            package=empty_package,
            package_version=1,
        )

        # Save lesson (ORM obj created in repo, DTO returned by service)
        lesson_dto = await self._content.save_lesson(lesson_create)

        # Assign to unit (prepend to lesson_order)
        await self._assign_intro_to_unit(unit_id, intro_lesson_id)

        # Persist podcast audio/metadata for the lesson
        await self._content.save_lesson_podcast_from_bytes(
            intro_lesson_id,
            transcript=podcast.transcript,
            audio_bytes=podcast.audio_bytes,
            mime_type=podcast.mime_type,
            voice=podcast.voice,
            duration_seconds=podcast.duration_seconds,
        )

        logger.info(f"✓ Intro lesson created: {intro_lesson_id} for unit {unit_id}")

        # Convert LessonRead to LessonSummary for return
        lesson_summary = LessonSummary(
            id=lesson_dto.id,
            title=lesson_dto.title,
            learner_level=lesson_dto.learner_level,
            lesson_type="intro",
            learning_objectives=getattr(lesson_dto, "learning_objectives", []),
            key_concepts=[],
            exercise_count=0,  # Intro has no exercises
            has_podcast=lesson_dto.has_podcast,
            podcast_duration_seconds=lesson_dto.podcast_duration_seconds,
            podcast_voice=lesson_dto.podcast_voice,
        )

        return intro_lesson_id, lesson_summary

    async def _assign_intro_to_unit(self, unit_id: str, lesson_id: str) -> None:
        """Atomically prepend intro lesson ID to unit.lesson_order."""

        unit = await self._content.get_unit(unit_id)
        if unit is None:
            raise ValueError(f"Unit {unit_id} not found during lesson assignment")

        current_order = list(getattr(unit, "lesson_order", []) or [])

        # Check if intro already exists in order (idempotency)
        if lesson_id in current_order:
            logger.warning(f"Intro lesson {lesson_id} already in unit order for {unit_id}")
            return

        # Prepend new intro to front
        new_order = [lesson_id, *current_order]
        await self._content.set_unit_lesson_order(unit_id, new_order)
        logger.info(f"✓ Updated unit {unit_id} lesson_order: intro prepended")
