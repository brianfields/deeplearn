from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from ..models import LessonModel
from ..repo import ContentRepo
from .dtos import LessonCreate, LessonPodcastAudio, LessonRead
from .media import MediaHelper

logger = logging.getLogger(__name__)


class LessonHandler:
    """Encapsulates lesson-centric business logic."""

    def __init__(self, repo: ContentRepo, media: MediaHelper) -> None:
        self.repo = repo
        self.media = media

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------
    def lesson_to_read(self, lesson: LessonModel) -> LessonRead:
        """Convert an ORM lesson model into the LessonRead DTO."""

        from ..package_models import LessonPackage

        try:
            package = LessonPackage.model_validate(lesson.package)
        except Exception as exc:  # pragma: no cover - invalid persisted data
            logger.error(
                "❌ Failed to validate lesson %s (%s): %s",
                lesson.id,
                getattr(lesson, "title", "<unknown>"),
                exc,
            )
            raise

        lesson_dict: dict[str, Any] = {
            "id": lesson.id,
            "title": lesson.title,
            "learner_level": lesson.learner_level,
            "unit_id": getattr(lesson, "unit_id", None),
            "source_material": lesson.source_material,
            "source_domain": getattr(lesson, "source_domain", None),
            "source_level": getattr(lesson, "source_level", None),
            "refined_material": getattr(lesson, "refined_material", None),
            "package": package,
            "package_version": lesson.package_version,
            "flow_run_id": lesson.flow_run_id,
            "created_at": lesson.created_at,
            "updated_at": lesson.updated_at,
            "schema_version": getattr(lesson, "schema_version", 1),
        }

        lesson_dict.update(self.media.build_lesson_podcast_payload(lesson, include_transcript=True))

        return LessonRead.model_validate(lesson_dict)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    async def get_lesson(self, lesson_id: str) -> LessonRead | None:
        lesson = await self.repo.get_lesson_by_id(lesson_id)
        if lesson is None:
            return None
        return self.lesson_to_read(lesson)

    async def search_lessons(
        self,
        *,
        query: str | None = None,
        learner_level: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LessonRead]:
        lessons = await self.repo.search_lessons(query, learner_level, limit, offset)
        result: list[LessonRead] = []
        for lesson in lessons:
            try:
                result.append(self.lesson_to_read(lesson))
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning(
                    "⚠️ Skipping lesson %s (%s) due to data validation error: %s",
                    getattr(lesson, "id", "<unknown>"),
                    getattr(lesson, "title", "<unknown>"),
                    exc,
                )
        return result

    async def get_lessons_by_unit(self, unit_id: str, *, limit: int = 100, offset: int = 0) -> list[LessonRead]:
        lessons = await self.repo.get_lessons_by_unit(unit_id=unit_id, limit=limit, offset=offset)
        result: list[LessonRead] = []
        for lesson in lessons:
            try:
                result.append(self.lesson_to_read(lesson))
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning(
                    "⚠️ Skipping lesson %s due to data validation error: %s",
                    getattr(lesson, "id", "<unknown>"),
                    exc,
                )
        return result

    async def save_lesson(self, lesson_data: LessonCreate) -> LessonRead:
        from ..models import LessonModel

        package_dict = lesson_data.package.model_dump()
        now = datetime.utcnow()
        lesson_model = LessonModel(
            id=lesson_data.id,
            title=lesson_data.title,
            learner_level=lesson_data.learner_level,
            source_material=lesson_data.source_material,
            package=package_dict,
            package_version=lesson_data.package_version,
            flow_run_id=lesson_data.flow_run_id,
            created_at=now,
            updated_at=now,
        )

        saved_lesson = await self.repo.save_lesson(lesson_model)
        saved_lesson.package = lesson_data.package.model_dump()  # ensure DTO uses validated package

        try:
            return self.lesson_to_read(saved_lesson)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(
                "❌ Failed to validate saved lesson %s (%s): %s",
                saved_lesson.id,
                getattr(saved_lesson, "title", "<unknown>"),
                exc,
            )
            raise

    async def delete_lesson(self, lesson_id: str) -> bool:
        return await self.repo.delete_lesson(lesson_id)

    async def lesson_exists(self, lesson_id: str) -> bool:
        return await self.repo.lesson_exists(lesson_id)

    # ------------------------------------------------------------------
    # Podcast helpers
    # ------------------------------------------------------------------
    async def save_lesson_podcast_from_bytes(
        self,
        lesson_id: str,
        *,
        transcript: str,
        audio_bytes: bytes,
        mime_type: str | None,
        voice: str | None,
        duration_seconds: int | None = None,
    ) -> LessonRead:
        if self.media.object_store is None:
            raise RuntimeError("Object store is not configured; cannot persist lesson podcast audio.")

        lesson = await self.repo.get_lesson_by_id(lesson_id)
        if lesson is None:
            raise ValueError("Lesson not found")

        owner_id: int | None = None
        unit_id = getattr(lesson, "unit_id", None)
        if unit_id:
            unit = await self.repo.get_unit_by_id(unit_id)
            if unit is not None:
                owner_id = getattr(unit, "user_id", None)

        filename = self.media.build_lesson_podcast_filename(lesson_id, mime_type)
        upload = await self.media.upload_audio(
            owner_id=owner_id,
            filename=filename,
            content_type=(mime_type or "audio/mpeg"),
            content=audio_bytes,
            transcript=transcript,
        )

        audio_file = upload.file
        audio_object_id = audio_file.id
        resolved_duration = duration_seconds if duration_seconds is not None else getattr(audio_file, "duration_seconds", None)
        resolved_voice = voice if voice is not None else getattr(audio_file, "voice", None)

        updated_lesson = await self.repo.set_lesson_podcast(
            lesson_id,
            transcript=transcript,
            audio_object_id=audio_object_id,
            voice=resolved_voice,
            duration_seconds=resolved_duration,
        )
        if updated_lesson is None:
            raise ValueError("Failed to persist lesson podcast metadata")

        self.media.clear_audio_cache(audio_object_id)
        return self.lesson_to_read(updated_lesson)

    async def get_lesson_podcast_audio(self, lesson_id: str) -> LessonPodcastAudio | None:
        lesson = await self.repo.get_lesson_by_id(lesson_id)
        if lesson is None:
            return None

        audio_meta = await self.media.fetch_audio_metadata(
            getattr(lesson, "podcast_audio_object_id", None),
            requesting_user_id=None,
            include_presigned_url=True,
        )
        if not audio_meta:
            return None

        mime_type = getattr(audio_meta, "content_type", None) or "audio/mpeg"
        presigned = getattr(audio_meta, "presigned_url", None)

        object_store = self.media.object_store
        if presigned is None and object_store is not None:
            s3_key = getattr(audio_meta, "s3_key", None)
            if s3_key:
                try:
                    presigned = await object_store.generate_presigned_url(s3_key)
                except Exception as exc:  # pragma: no cover - object store failures
                    logger.warning(
                        "🎧 Failed to generate presigned podcast URL for lesson %s: %s",
                        lesson_id,
                        exc,
                        exc_info=True,
                    )

        if presigned is None:
            return None

        return LessonPodcastAudio(
            lesson_id=lesson_id,
            mime_type=mime_type,
            presigned_url=presigned,
        )


__all__ = ["LessonHandler"]
