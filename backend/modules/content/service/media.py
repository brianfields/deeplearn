from __future__ import annotations

import logging
from typing import Any
import uuid

from modules.object_store.public import AudioCreate, ImageCreate, ObjectStoreProvider

from ..models import LessonModel, UnitModel

logger = logging.getLogger(__name__)


class MediaHelper:
    """Shared helper for audio and artwork media interactions."""

    PODCAST_AUDIO_ROUTE_TEMPLATE = "/api/v1/content/units/{unit_id}/podcast/audio"

    def __init__(self, object_store: ObjectStoreProvider | None) -> None:
        self._object_store = object_store
        self._audio_metadata_cache: dict[uuid.UUID, Any | None] = {}
        self._art_metadata_cache: dict[uuid.UUID, Any | None] = {}

    @property
    def object_store(self) -> ObjectStoreProvider | None:
        """Expose the configured object store for callers that need direct access."""

        return self._object_store

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------
    def clear_audio_cache(self, audio_id: uuid.UUID | None = None) -> None:
        """Clear cached audio metadata, optionally scoping to a specific file."""

        if audio_id is None:
            self._audio_metadata_cache.clear()
        else:
            self._audio_metadata_cache.pop(audio_id, None)

    def clear_art_cache(self) -> None:
        """Clear cached artwork metadata."""

        self._art_metadata_cache.clear()

    # ------------------------------------------------------------------
    # Metadata retrieval
    # ------------------------------------------------------------------
    async def fetch_audio_metadata(
        self,
        audio_id: uuid.UUID | None,
        *,
        requesting_user_id: int | None,
        include_presigned_url: bool = False,
    ) -> Any | None:
        """Retrieve audio metadata, leveraging an in-memory cache when possible."""

        if audio_id is None:
            return None

        cached = self._audio_metadata_cache.get(audio_id)
        if cached is not None and (include_presigned_url or getattr(cached, "presigned_url", None) is not None):
            return cached

        if self._object_store is None:
            return None

        try:
            metadata = await self._object_store.get_audio(  # type: ignore[func-returns-value]
                audio_id,
                requesting_user_id=requesting_user_id,
                include_presigned_url=include_presigned_url,
            )
        except Exception as exc:  # pragma: no cover - network/object store failures
            logger.warning(
                "🎧 Failed to retrieve podcast metadata %s: %s",
                audio_id,
                exc,
                exc_info=True,
            )
            metadata = None

        if metadata is not None:
            self._audio_metadata_cache[audio_id] = metadata

        return metadata

    async def fetch_image_metadata(
        self,
        image_id: uuid.UUID | None,
        *,
        requesting_user_id: int | None,
        include_presigned_url: bool = False,
    ) -> Any | None:
        """Retrieve artwork metadata with caching."""

        if image_id is None:
            return None

        cached = self._art_metadata_cache.get(image_id)
        if cached is not None:
            has_presigned = getattr(cached, "presigned_url", None)
            if include_presigned_url:
                if has_presigned is not None:
                    return cached
            else:
                return cached

        if self._object_store is None:
            return None

        try:
            metadata = await self._object_store.get_image(  # type: ignore[func-returns-value]
                image_id,
                requesting_user_id=requesting_user_id,
                include_presigned_url=include_presigned_url,
            )
        except Exception as exc:  # pragma: no cover - network/object store failures
            logger.warning(
                "🖼️ Failed to retrieve unit artwork metadata %s: %s",
                image_id,
                exc,
                exc_info=True,
            )
            metadata = None

        if metadata is not None:
            self._art_metadata_cache[image_id] = metadata

        return metadata

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------
    @staticmethod
    def build_lesson_podcast_audio_url(lesson: LessonModel) -> str | None:
        audio_identifier = getattr(lesson, "podcast_audio_object_id", None)
        lesson_id = getattr(lesson, "id", None)
        if not audio_identifier or not lesson_id:
            return None
        return f"/api/v1/content/lessons/{lesson_id}/podcast/audio"

    def build_unit_podcast_audio_url(self, unit: UnitModel) -> str | None:
        if not getattr(unit, "podcast_audio_object_id", None):
            return None
        return self.PODCAST_AUDIO_ROUTE_TEMPLATE.format(unit_id=unit.id)

    # ------------------------------------------------------------------
    # Filename helpers
    # ------------------------------------------------------------------
    @staticmethod
    def build_lesson_podcast_filename(lesson_id: str, mime_type: str | None) -> str:
        extension_map = {
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/flac": ".flac",
            "audio/x-flac": ".flac",
            "audio/mp4": ".mp4",
            "audio/m4a": ".m4a",
        }
        suffix = extension_map.get((mime_type or "").lower(), ".bin")
        return f"lesson-{lesson_id}{suffix}"

    @staticmethod
    def build_unit_podcast_filename(unit_id: str, mime_type: str | None) -> str:
        extension_map = {
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/flac": ".flac",
            "audio/x-flac": ".flac",
            "audio/mp4": ".mp4",
            "audio/m4a": ".m4a",
        }
        suffix = extension_map.get((mime_type or "").lower(), ".bin")
        return f"unit-{unit_id}{suffix}"

    @staticmethod
    def build_unit_art_filename(unit_id: str, content_type: str | None) -> str:
        extension_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp",
        }
        suffix = extension_map.get((content_type or "").lower(), ".png")
        return f"unit-art-{unit_id}{suffix}"

    # ------------------------------------------------------------------
    # Upload helpers
    # ------------------------------------------------------------------
    async def upload_audio(
        self,
        *,
        owner_id: int | None,
        filename: str,
        content_type: str,
        content: bytes,
        transcript: str | None = None,
    ) -> Any:
        if self._object_store is None:
            raise RuntimeError("Object store is not configured; cannot persist generated podcast audio.")

        return await self._object_store.upload_audio(  # type: ignore[func-returns-value]
            AudioCreate(
                user_id=owner_id,
                filename=filename,
                content_type=content_type,
                content=content,
                transcript=transcript,
            )
        )

    async def upload_image(
        self,
        *,
        owner_id: int | None,
        filename: str,
        content_type: str,
        content: bytes,
        description: str | None,
        alt_text: str | None = None,
        generate_presigned_url: bool = False,
    ) -> Any:
        if self._object_store is None:
            raise RuntimeError("Object store is not configured; cannot persist generated unit art.")

        return await self._object_store.upload_image(  # type: ignore[func-returns-value]
            ImageCreate(
                user_id=owner_id,
                filename=filename,
                content_type=content_type,
                content=content,
                description=description,
                alt_text=alt_text,
            ),
            generate_presigned_url=generate_presigned_url,
        )

    # ------------------------------------------------------------------
    # Payload helpers
    # ------------------------------------------------------------------
    def build_lesson_podcast_payload(
        self,
        lesson: LessonModel,
        *,
        include_transcript: bool,
    ) -> dict[str, Any]:
        audio_identifier = getattr(lesson, "podcast_audio_object_id", None)
        transcript = getattr(lesson, "podcast_transcript", None)
        payload: dict[str, Any] = {
            "has_podcast": bool(audio_identifier or transcript),
            "podcast_voice": getattr(lesson, "podcast_voice", None),
            "podcast_duration_seconds": getattr(lesson, "podcast_duration_seconds", None),
            "podcast_generated_at": getattr(lesson, "podcast_generated_at", None),
            "podcast_audio_url": self.build_lesson_podcast_audio_url(lesson) if audio_identifier else None,
        }

        if include_transcript:
            payload["podcast_transcript"] = transcript

        return payload


__all__ = ["MediaHelper"]
