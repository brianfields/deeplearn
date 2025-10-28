"""Media generation helpers for the content creator service."""

from __future__ import annotations

import logging
from typing import Any, Iterable

import httpx

from modules.content.public import ContentProvider, UnitRead

from ..flows import UnitArtCreationFlow
from ..podcast import (
    LessonPodcastGenerator,
    LessonPodcastResult,
    PodcastLesson,
    UnitPodcast,
    UnitPodcastGenerator,
)
from .prompt_handler import PromptHandler

logger = logging.getLogger(__name__)


class MediaHandler:
    """Coordinate audio and artwork generation for units and lessons."""

    def __init__(
        self,
        content: ContentProvider,
        prompt_handler: PromptHandler,
        podcast_generator: UnitPodcastGenerator | None = None,
        lesson_podcast_generator: LessonPodcastGenerator | None = None,
    ) -> None:
        self._content = content
        self._prompt_handler = prompt_handler
        self._podcast_generator = podcast_generator
        self._lesson_podcast_generator = lesson_podcast_generator

    async def create_unit_art(self, unit_id: str, *, arq_task_id: str | None = None) -> UnitRead:
        """Generate and persist hero artwork for the specified unit."""

        unit_detail = await self._content.get_unit_detail(unit_id, include_art_presigned_url=False)
        if unit_detail is None:
            raise ValueError("Unit not found")

        raw_learning_objectives = list(getattr(unit_detail, "learning_objectives", []) or [])
        learning_objectives: list[str] = []
        for lo in raw_learning_objectives:
            description = (
                lo.get("description")
                or lo.get("title")
                if isinstance(lo, dict)
                else getattr(lo, "description", None)
                or getattr(lo, "title", None)
                or str(lo)
            )
            learning_objectives.append(str(description or ""))
        key_concepts = self._prompt_handler.extract_key_concepts(unit_detail)

        flow_inputs = {
            "unit_title": unit_detail.title,
            "unit_description": unit_detail.description or "",
            "learning_objectives": learning_objectives,
            "key_concepts": key_concepts,
        }

        flow = UnitArtCreationFlow()
        attempts = 0
        art_payload: dict[str, Any] | None = None
        last_exc: Exception | None = None

        while attempts < 2:
            try:
                art_payload = await flow.execute(flow_inputs, arq_task_id=arq_task_id)
                break
            except Exception as exc:  # pragma: no cover - LLM/network issues
                attempts += 1
                last_exc = exc
                logger.warning(
                    "🖼️ Unit art attempt %s failed for unit %s: %s",
                    attempts,
                    unit_id,
                    exc,
                    exc_info=True,
                )
        if art_payload is None:
            raise RuntimeError("Unit art generation failed") from last_exc

        description_info = art_payload.get("art_description") or {}
        prompt_text = str(description_info.get("prompt", "")).strip()
        alt_text = str(description_info.get("alt_text", "")).strip()

        image_info = art_payload.get("image") or {}
        image_url = image_info.get("image_url")
        if not image_url:
            raise RuntimeError("Image generation returned no URL")

        image_bytes, content_type = await self._download_image(image_url)

        return await self._content.save_unit_art_from_bytes(
            unit_id,
            image_bytes=image_bytes,
            content_type=content_type or "image/png",
            description=prompt_text or None,
            alt_text=alt_text or None,
        )

    async def generate_lesson_podcast(
        self,
        *,
        lesson_index: int,
        lesson_title: str,
        lesson_objective: str,
        mini_lesson: str,
        voice_label: str,
        arq_task_id: str | None = None,
    ) -> tuple[PodcastLesson, LessonPodcastResult]:
        """Create a narrated podcast for a single lesson."""

        generator = self._lesson_podcast_generator or LessonPodcastGenerator()
        self._lesson_podcast_generator = generator
        podcast = await generator.create_podcast(
            lesson_index=lesson_index,
            lesson_title=lesson_title,
            lesson_objective=lesson_objective,
            mini_lesson=mini_lesson,
            voice_label=voice_label,
            arq_task_id=arq_task_id,
        )
        podcast_lesson = PodcastLesson(title=lesson_title, mini_lesson=mini_lesson)
        return podcast_lesson, podcast

    async def generate_unit_podcast(
        self,
        *,
        unit_title: str,
        voice_label: str,
        unit_summary: str,
        lessons: Iterable[PodcastLesson],
        arq_task_id: str | None = None,
    ) -> UnitPodcast:
        """Generate a podcast summarising the unit."""

        generator = self._podcast_generator or UnitPodcastGenerator()
        self._podcast_generator = generator
        return await generator.create_podcast(
            unit_title=unit_title,
            voice_label=voice_label,
            unit_summary=unit_summary,
            lessons=list(lessons),
            arq_task_id=arq_task_id,
        )

    async def save_unit_podcast(self, unit_id: str, podcast: UnitPodcast) -> None:
        """Persist the generated unit podcast if audio is available."""

        if getattr(podcast, "audio_bytes", None):
            await self._content.save_unit_podcast_from_bytes(
                unit_id,
                transcript=podcast.transcript,
                audio_bytes=podcast.audio_bytes,
                mime_type=podcast.mime_type,
                voice=podcast.voice,
            )

    async def save_lesson_podcast(
        self,
        content_service: ContentProvider,
        lesson_id: str,
        podcast: LessonPodcastResult,
    ) -> None:
        """Persist lesson podcast audio for the provided lesson identifier."""

        await content_service.save_lesson_podcast_from_bytes(
            lesson_id,
            transcript=podcast.transcript,
            audio_bytes=podcast.audio_bytes,
            mime_type=podcast.mime_type,
            voice=podcast.voice,
            duration_seconds=podcast.duration_seconds,
        )

    async def _download_image(self, url: str) -> tuple[bytes, str | None]:
        """Fetch binary image data from the generated image URL."""

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content, response.headers.get("content-type")
