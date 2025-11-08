from __future__ import annotations

"""
Content Module - Service Layer

Business logic layer that returns DTOs (Pydantic models).
Handles content operations and data transformation.
"""

# Import inside methods when needed to avoid circular imports with public/providers
from datetime import UTC, datetime
from enum import Enum
import logging
from typing import Any, Literal
import uuid

from pydantic import BaseModel, ConfigDict

from modules.flow_engine.public import FlowRunSummaryDTO, flow_engine_admin_provider
from modules.infrastructure.public import infrastructure_provider
from modules.object_store.public import AudioCreate, ImageCreate, ObjectStoreProvider

from .models import LessonModel, UnitModel
from .package_models import LessonPackage
from .repo import ContentRepo

logger = logging.getLogger(__name__)


# Enums for status validation
class UnitStatus(str, Enum):
    """Valid unit statuses for creation flow tracking."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# DTOs (Data Transfer Objects)
class LessonRead(BaseModel):
    """DTO for reading lesson data with embedded package."""

    id: str
    title: str
    learner_level: str
    core_concept: str | None = None  # For admin compatibility
    unit_id: str | None = None
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict[str, Any] | None = None
    package: LessonPackage
    package_version: int
    flow_run_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    schema_version: int = 1
    podcast_transcript: str | None = None
    podcast_voice: str | None = None
    podcast_duration_seconds: int | None = None
    podcast_generated_at: datetime | None = None
    podcast_audio_url: str | None = None
    has_podcast: bool = False

    model_config = ConfigDict(from_attributes=True)


class LessonCreate(BaseModel):
    """DTO for creating new lessons with package."""

    id: str
    title: str
    learner_level: str
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict[str, Any] | None = None
    package: LessonPackage
    package_version: int = 1
    flow_run_id: uuid.UUID | None = None


class UnitLearningObjective(BaseModel):
    """Structured representation of a unit-level learning objective."""

    id: str
    title: str
    description: str
    bloom_level: str | None = None
    evidence_of_mastery: str | None = None


class ContentService:
    """Service for content operations."""

    def __init__(self, repo: ContentRepo, object_store: ObjectStoreProvider | None = None) -> None:
        """Initialize service with repository."""
        self.repo = repo
        self._object_store = object_store
        self._audio_metadata_cache: dict[uuid.UUID, Any | None] = {}
        self._art_metadata_cache: dict[uuid.UUID, Any | None] = {}

    async def commit_session(self) -> None:
        """Commit pending changes to make them visible immediately in the admin dashboard."""
        await self.repo.s.commit()

    # Lesson operations
    def _lesson_model_to_read(self, lesson: LessonModel) -> LessonRead:
        """Convert an ORM lesson model into the LessonRead DTO."""

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

        lesson_dict = {
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

        lesson_dict.update(self._build_lesson_podcast_payload(lesson, include_transcript=True))

        return LessonRead.model_validate(lesson_dict)

    def _build_lesson_podcast_payload(
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
            "podcast_audio_url": self._build_lesson_podcast_audio_url(lesson) if audio_identifier else None,
        }

        if include_transcript:
            payload["podcast_transcript"] = transcript

        return payload

    async def get_lesson(self, lesson_id: str) -> LessonRead | None:
        """Get lesson with package by ID."""
        lesson = await self.repo.get_lesson_by_id(lesson_id)
        if not lesson:
            return None

        return self._lesson_model_to_read(lesson)

    async def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonRead]:
        """Get all lessons with packages."""
        lessons = await self.repo.get_all_lessons(limit, offset)
        result = []

        for lesson in lessons:
            try:
                result.append(self._lesson_model_to_read(lesson))
            except Exception as e:
                logger.warning(f"⚠️ Skipping lesson {lesson.id} ({lesson.title}) due to data validation error: {e}")
                continue

        return result

    async def search_lessons(
        self,
        query: str | None = None,
        learner_level: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LessonRead]:
        """Search lessons with optional filters."""
        lessons = await self.repo.search_lessons(query, learner_level, limit, offset)
        result = []

        for lesson in lessons:
            try:
                result.append(self._lesson_model_to_read(lesson))
            except Exception as e:
                logger.warning(f"⚠️ Skipping lesson {lesson.id} ({lesson.title}) due to data validation error: {e}")
                continue

        return result

    # New: Lessons by unit
    async def get_lessons_by_unit(self, unit_id: str, limit: int = 100, offset: int = 0) -> list[LessonRead]:
        """Return lessons that belong to the given unit."""
        lessons = await self.repo.get_lessons_by_unit(unit_id=unit_id, limit=limit, offset=offset)
        result: list[LessonRead] = []
        for lesson in lessons:
            try:
                result.append(self._lesson_model_to_read(lesson))
            except Exception as e:  # pragma: no cover - defensive
                logger.warning(f"⚠️ Skipping lesson {lesson.id} due to data validation error: {e}")
                continue
        return result

    async def save_lesson(self, lesson_data: LessonCreate) -> LessonRead:
        """Create new lesson with package."""
        package_dict = lesson_data.package.model_dump()

        lesson_model = LessonModel(
            id=lesson_data.id,
            title=lesson_data.title,
            learner_level=lesson_data.learner_level,
            source_material=lesson_data.source_material,
            package=package_dict,
            package_version=lesson_data.package_version,
            flow_run_id=lesson_data.flow_run_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        saved_lesson = await self.repo.save_lesson(lesson_model)

        saved_lesson.package = lesson_data.package.model_dump()  # ensure DTO uses validated package

        try:
            return self._lesson_model_to_read(saved_lesson)
        except Exception as e:
            logger.error(
                "❌ Failed to validate saved lesson %s (%s): %s",
                saved_lesson.id,
                getattr(saved_lesson, "title", "<unknown>"),
                e,
            )
            raise

    async def delete_lesson(self, lesson_id: str) -> bool:
        """Delete lesson by ID."""
        return await self.repo.delete_lesson(lesson_id)

    async def lesson_exists(self, lesson_id: str) -> bool:
        """Check if lesson exists."""
        return await self.repo.lesson_exists(lesson_id)

    # ======================
    # Unit operations (moved)
    # ======================
    PODCAST_AUDIO_ROUTE_TEMPLATE = "/api/v1/content/units/{unit_id}/podcast/audio"

    class UnitRead(BaseModel):
        id: str
        title: str
        description: str | None = None
        learner_level: str
        lesson_order: list[str]
        user_id: int | None = None
        is_global: bool = False
        arq_task_id: str | None = None
        # New fields
        learning_objectives: list[UnitLearningObjective] | None = None
        target_lesson_count: int | None = None
        source_material: str | None = None
        generated_from_topic: bool = False
        flow_type: str = "standard"
        # Status tracking fields
        status: str = "completed"
        creation_progress: dict[str, Any] | None = None
        error_message: str | None = None
        # Intro podcast metadata surfaced in summaries
        has_podcast: bool = False
        podcast_voice: str | None = None
        podcast_duration_seconds: int | None = None
        podcast_generated_at: datetime | None = None
        podcast_transcript: str | None = None
        podcast_audio_url: str | None = None
        art_image_id: uuid.UUID | None = None
        art_image_description: str | None = None
        art_image_url: str | None = None
        created_at: datetime
        updated_at: datetime
        schema_version: int = 1

        model_config = ConfigDict(from_attributes=True)

    class UnitLessonSummary(BaseModel):
        id: str
        title: str
        learner_level: str
        learning_objective_ids: list[str]
        learning_objectives: list[str]
        key_concepts: list[str]
        exercise_count: int
        has_podcast: bool = False
        podcast_voice: str | None = None
        podcast_duration_seconds: int | None = None
        podcast_generated_at: datetime | None = None
        podcast_audio_url: str | None = None

    class UnitDetailRead(UnitRead):
        """Full unit detail including intro podcast and ordered lessons."""

        learning_objectives: list[UnitLearningObjective] | None = None
        lessons: list[ContentService.UnitLessonSummary]
        podcast_transcript: str | None = None
        podcast_audio_url: str | None = None

        model_config = ConfigDict(from_attributes=True)

    class UnitSyncAsset(BaseModel):
        """Metadata describing a downloadable asset for an offline unit."""

        id: str
        unit_id: str
        type: Literal["audio", "image"]
        object_id: uuid.UUID | None = None
        remote_url: str | None = None
        presigned_url: str | None = None
        updated_at: datetime | None = None
        schema_version: int = 1

    class UnitSyncEntry(BaseModel):
        """Unit payload returned from the sync endpoint."""

        unit: ContentService.UnitRead
        lessons: list[LessonRead]
        assets: list[ContentService.UnitSyncAsset]

    class UnitSyncResponse(BaseModel):
        """Full sync response payload describing unit changes."""

        units: list[ContentService.UnitSyncEntry]
        deleted_unit_ids: list[str]
        deleted_lesson_ids: list[str]
        cursor: datetime

    UnitSyncPayload = Literal["full", "minimal"]

    class UnitCreate(BaseModel):
        id: str | None = None
        title: str
        description: str | None = None
        learner_level: str = "beginner"
        lesson_order: list[str] = []
        user_id: int | None = None
        is_global: bool = False
        learning_objectives: list[UnitLearningObjective] | None = None
        target_lesson_count: int | None = None
        source_material: str | None = None
        generated_from_topic: bool = False
        flow_type: str = "standard"

    class UnitPodcastAudio(BaseModel):
        unit_id: str
        mime_type: str
        audio_bytes: bytes | None = None
        presigned_url: str | None = None

    class LessonPodcastAudio(BaseModel):
        lesson_id: str
        mime_type: str
        audio_bytes: bytes | None = None
        presigned_url: str | None = None

    async def _build_unit_read(
        self,
        unit: UnitModel,
        *,
        audio_meta: Any | None = None,
        include_art_presigned_url: bool = True,
        include_audio_metadata: bool = True,
    ) -> ContentService.UnitRead:
        unit_read = self.UnitRead.model_validate(unit)
        parsed_learning_objectives = self._parse_unit_learning_objectives(getattr(unit, "learning_objectives", None))
        unit_read.learning_objectives = parsed_learning_objectives or None
        unit_read.schema_version = getattr(unit, "schema_version", 1)
        await self._apply_podcast_metadata(
            unit_read,
            unit,
            audio_meta=audio_meta,
            include_metadata=include_audio_metadata,
        )
        await self._apply_artwork_metadata(
            unit_read,
            unit,
            include_presigned_url=include_art_presigned_url,
        )
        return unit_read

    async def _apply_podcast_metadata(
        self,
        unit_read: ContentService.UnitRead,
        unit: UnitModel,
        *,
        audio_meta: Any | None = None,
        include_metadata: bool = True,
    ) -> None:
        audio_object_id = getattr(unit, "podcast_audio_object_id", None)
        unit_read.has_podcast = bool(audio_object_id)
        unit_read.podcast_voice = getattr(unit, "podcast_voice", None)
        unit_read.podcast_generated_at = getattr(unit, "podcast_generated_at", None)
        unit_read.podcast_transcript = getattr(unit, "podcast_transcript", None)
        unit_read.podcast_audio_url = self._build_podcast_audio_url(unit) if audio_object_id else None

        if not include_metadata:
            resolved_meta = audio_meta if audio_meta is not None else None
        else:
            resolved_meta = audio_meta
            if resolved_meta is None and audio_object_id and self._object_store is not None:
                resolved_meta = await self._fetch_audio_metadata(
                    audio_object_id,
                    requesting_user_id=getattr(unit, "user_id", None),
                )

        duration_value: Any | None = None if resolved_meta is None else getattr(resolved_meta, "duration_seconds", None)
        if isinstance(duration_value, int):
            unit_read.podcast_duration_seconds = duration_value
        elif isinstance(duration_value, float):
            unit_read.podcast_duration_seconds = round(duration_value)
        else:
            try:
                unit_read.podcast_duration_seconds = round(float(duration_value)) if duration_value is not None else None
            except (TypeError, ValueError):
                unit_read.podcast_duration_seconds = None

    async def _apply_artwork_metadata(
        self,
        unit_read: ContentService.UnitRead,
        unit: UnitModel,
        *,
        include_presigned_url: bool = True,
    ) -> None:
        unit_read.art_image_description = getattr(unit, "art_image_description", None)

        art_identifier = getattr(unit, "art_image_id", None)
        if not art_identifier:
            unit_read.art_image_id = None
            unit_read.art_image_url = None
            return

        try:
            art_uuid = art_identifier if isinstance(art_identifier, uuid.UUID) else uuid.UUID(str(art_identifier))
        except (TypeError, ValueError):  # pragma: no cover - defensive guard
            logger.warning("🖼️ Invalid unit artwork id encountered: %s", art_identifier)
            unit_read.art_image_id = None
            unit_read.art_image_url = None
            return

        unit_read.art_image_id = art_uuid
        if self._object_store is None:
            unit_read.art_image_url = None
            return

        metadata = await self._fetch_image_metadata(
            art_uuid,
            requesting_user_id=getattr(unit, "user_id", None),
            include_presigned_url=include_presigned_url,
        )

        if metadata is None:
            unit_read.art_image_url = None
            return

        unit_read.art_image_url = getattr(metadata, "presigned_url", None)

    async def _build_unit_assets(
        self,
        unit: UnitModel,
        unit_read: ContentService.UnitRead,
        *,
        allowed_types: set[str] | None = None,
        lessons: list[LessonModel] | None = None,
    ) -> list[ContentService.UnitSyncAsset]:
        """Construct asset metadata for the sync payload."""

        assets: list[ContentService.UnitSyncAsset] = []

        include_audio = allowed_types is None or "audio" in allowed_types
        include_image = allowed_types is None or "image" in allowed_types

        audio_identifier = getattr(unit, "podcast_audio_object_id", None)
        if include_audio and audio_identifier:
            try:
                audio_uuid = audio_identifier if isinstance(audio_identifier, uuid.UUID) else uuid.UUID(str(audio_identifier))
            except (TypeError, ValueError):  # pragma: no cover - defensive
                logger.warning("🎧 Invalid podcast audio id encountered: %s", audio_identifier)
            else:
                presigned_audio: str | None = None
                if self._object_store is not None:
                    metadata = await self._fetch_audio_metadata(
                        audio_uuid,
                        requesting_user_id=getattr(unit, "user_id", None),
                        include_presigned_url=True,
                    )
                    presigned_audio = getattr(metadata, "presigned_url", None)

                assets.append(
                    self.UnitSyncAsset(
                        id=str(audio_uuid),
                        unit_id=unit.id,
                        type="audio",
                        object_id=audio_uuid,
                        remote_url=self._build_podcast_audio_url(unit),
                        presigned_url=presigned_audio,
                        updated_at=getattr(unit, "podcast_generated_at", unit.updated_at),
                    )
                )

        # Include lesson podcast assets for offline download
        if include_audio and lessons:
            for lesson in lessons:
                lesson_audio_id = getattr(lesson, "podcast_audio_object_id", None)
                if lesson_audio_id:
                    try:
                        lesson_audio_uuid = lesson_audio_id if isinstance(lesson_audio_id, uuid.UUID) else uuid.UUID(str(lesson_audio_id))
                    except (TypeError, ValueError):  # pragma: no cover - defensive
                        logger.warning("🎧 Invalid lesson podcast audio id encountered: %s", lesson_audio_id)
                        continue

                    presigned_lesson_audio: str | None = None
                    if self._object_store is not None:
                        metadata = await self._fetch_audio_metadata(
                            lesson_audio_uuid,
                            requesting_user_id=getattr(unit, "user_id", None),
                            include_presigned_url=True,
                        )
                        presigned_lesson_audio = getattr(metadata, "presigned_url", None)

                    assets.append(
                        self.UnitSyncAsset(
                            id=f"lesson-podcast-{lesson.id}",
                            unit_id=unit.id,
                            type="audio",
                            object_id=lesson_audio_uuid,
                            remote_url=self._build_lesson_podcast_audio_url(lesson),
                            presigned_url=presigned_lesson_audio,
                            updated_at=getattr(lesson, "podcast_generated_at", lesson.updated_at),
                        )
                    )

        art_identifier = getattr(unit, "art_image_id", None)
        if include_image and art_identifier:
            try:
                art_uuid = art_identifier if isinstance(art_identifier, uuid.UUID) else uuid.UUID(str(art_identifier))
            except (TypeError, ValueError):  # pragma: no cover - defensive
                logger.warning("🖼️ Invalid unit artwork id encountered: %s", art_identifier)
            else:
                presigned_art: str | None = None
                if self._object_store is not None:
                    metadata = await self._fetch_image_metadata(
                        art_uuid,
                        requesting_user_id=getattr(unit, "user_id", None),
                        include_presigned_url=True,
                    )
                    presigned_art = getattr(metadata, "presigned_url", None)

                assets.append(
                    self.UnitSyncAsset(
                        id=str(art_uuid),
                        unit_id=unit.id,
                        type="image",
                        object_id=art_uuid,
                        remote_url=unit_read.art_image_url,
                        presigned_url=presigned_art or unit_read.art_image_url,
                        updated_at=unit.updated_at,
                    )
                )

        return assets

    async def _fetch_audio_metadata(
        self,
        audio_object_id: uuid.UUID | str | None,
        *,
        requesting_user_id: int | None,
        include_presigned_url: bool = False,
    ) -> Any | None:
        """Resolve audio metadata from the object store, caching non-URL lookups."""

        if not audio_object_id or self._object_store is None:
            return None

        try:
            audio_uuid = audio_object_id if isinstance(audio_object_id, uuid.UUID) else uuid.UUID(str(audio_object_id))
        except (TypeError, ValueError):  # pragma: no cover - defensive guard
            logger.warning("🎧 Invalid podcast audio id encountered: %s", audio_object_id)
            return None

        if not include_presigned_url and audio_uuid in self._audio_metadata_cache:
            return self._audio_metadata_cache[audio_uuid]

        try:
            metadata = await self._object_store.get_audio(  # type: ignore[func-returns-value]
                audio_uuid,
                requesting_user_id=requesting_user_id,
                include_presigned_url=include_presigned_url,
            )
        except Exception as exc:  # pragma: no cover - network/object store issues
            logger.warning(
                "🎧 Failed to retrieve podcast audio metadata %s: %s",
                audio_uuid,
                exc,
                exc_info=True,
            )
            metadata = None

        if not include_presigned_url:
            self._audio_metadata_cache[audio_uuid] = metadata

        return metadata

    async def _fetch_image_metadata(
        self,
        image_id: uuid.UUID,
        *,
        requesting_user_id: int | None,
        include_presigned_url: bool,
    ) -> Any | None:
        if self._object_store is None:
            return None

        cached = self._art_metadata_cache.get(image_id)
        if cached is not None:
            if include_presigned_url:
                cached_url = getattr(cached, "presigned_url", None)
                if cached_url:
                    return cached
            else:
                return cached

        try:
            metadata = await self._object_store.get_image(  # type: ignore[func-returns-value]
                image_id,
                requesting_user_id=requesting_user_id,
                include_presigned_url=include_presigned_url,
            )
        except Exception as exc:  # pragma: no cover - network/object store issues
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

    def _build_lesson_podcast_audio_url(self, lesson: LessonModel) -> str | None:
        audio_identifier = getattr(lesson, "podcast_audio_object_id", None)
        lesson_id = getattr(lesson, "id", None)
        if not audio_identifier or not lesson_id:
            return None
        return f"/api/v1/content/lessons/{lesson_id}/podcast/audio"

    def _build_podcast_audio_url(self, unit: UnitModel) -> str | None:
        if not getattr(unit, "podcast_audio_object_id", None):
            return None
        return self.PODCAST_AUDIO_ROUTE_TEMPLATE.format(unit_id=unit.id)

    def _build_lesson_podcast_filename(self, lesson_id: str, mime_type: str | None) -> str:
        """Construct a filename for uploaded lesson podcast audio."""

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

    def _build_podcast_filename(self, unit_id: str, mime_type: str | None) -> str:
        """Construct a filename for uploaded podcast audio for a unit."""
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

    def _build_unit_art_filename(self, unit_id: str, content_type: str | None) -> str:
        """Construct a deterministic filename for generated unit artwork."""

        extension_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp",
        }
        suffix = extension_map.get((content_type or "").lower(), ".png")
        return f"unit-art-{unit_id}{suffix}"

    async def save_unit_art_from_bytes(
        self,
        unit_id: str,
        *,
        image_bytes: bytes,
        content_type: str,
        description: str | None,
        alt_text: str | None = None,
    ) -> ContentService.UnitRead:
        """Upload generated art to the object store and persist metadata."""

        if self._object_store is None:
            raise RuntimeError("Object store is not configured; cannot persist generated unit art.")

        unit_info = await self.repo.get_unit_by_id(unit_id)
        if unit_info is None:
            raise ValueError("Unit not found")

        owner_id = getattr(unit_info, "user_id", None)
        filename = self._build_unit_art_filename(unit_id, content_type)
        resolved_content_type = content_type or "image/png"

        upload = await self._object_store.upload_image(  # type: ignore[func-returns-value]
            ImageCreate(
                user_id=owner_id,
                filename=filename,
                content_type=resolved_content_type,
                content=image_bytes,
                description=description,
                alt_text=alt_text,
            ),
            generate_presigned_url=True,
        )

        updated = await self.repo.set_unit_art(
            unit_id,
            image_object_id=upload.file.id,
            description=description,
        )
        if updated is None:
            raise ValueError("Failed to persist unit art metadata")

        self._art_metadata_cache.clear()
        return await self._build_unit_read(updated, include_art_presigned_url=True)

    async def save_unit_podcast_from_bytes(
        self,
        unit_id: str,
        *,
        transcript: str,
        audio_bytes: bytes,
        mime_type: str | None,
        voice: str | None,
    ) -> ContentService.UnitRead:
        """Upload podcast audio and persist metadata for a unit."""
        if self._object_store is None:
            raise RuntimeError("Object store is not configured; cannot persist generated podcast audio.")

        unit_info = await self.repo.get_unit_by_id(unit_id)
        if unit_info is None:
            raise ValueError("Unit not found")

        owner_id = getattr(unit_info, "user_id", None)
        filename = self._build_podcast_filename(unit_id, mime_type)

        upload = await self._object_store.upload_audio(  # type: ignore[func-returns-value]
            AudioCreate(
                user_id=owner_id,
                filename=filename,
                content_type=(mime_type or "audio/mpeg"),
                content=audio_bytes,
                transcript=transcript,
            )
        )

        audio_object_id = upload.file.id

        updated_model = await self.repo.set_unit_podcast(
            unit_id,
            transcript=transcript,
            audio_object_id=audio_object_id,
            voice=voice,
        )
        if updated_model is None:
            raise ValueError("Failed to persist intro podcast metadata")

        return await self._build_unit_read(updated_model, audio_meta=upload.file)

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
        """Upload lesson podcast audio and persist metadata."""

        if self._object_store is None:
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

        filename = self._build_lesson_podcast_filename(lesson_id, mime_type)

        upload = await self._object_store.upload_audio(  # type: ignore[func-returns-value]
            AudioCreate(
                user_id=owner_id,
                filename=filename,
                content_type=(mime_type or "audio/mpeg"),
                content=audio_bytes,
                transcript=transcript,
            )
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

        self._audio_metadata_cache.pop(audio_object_id, None)
        return self._lesson_model_to_read(updated_lesson)

    async def get_unit(self, unit_id: str) -> ContentService.UnitRead | None:
        u = await self.repo.get_unit_by_id(unit_id)
        if u is None:
            return None
        return await self._build_unit_read(u)

    async def get_unit_detail(
        self,
        unit_id: str,
        *,
        include_art_presigned_url: bool = True,
    ) -> ContentService.UnitDetailRead | None:
        unit = await self.repo.get_unit_by_id(unit_id)
        if unit is None:
            return None

        lesson_models = await self.repo.get_lessons_by_unit(unit_id=unit_id)
        lesson_summaries: dict[str, ContentService.UnitLessonSummary] = {}
        unit_learning_objectives = self._parse_unit_learning_objectives(getattr(unit, "learning_objectives", None))
        lo_lookup = {lo.id: lo for lo in unit_learning_objectives}

        for lesson in lesson_models:
            try:
                package = LessonPackage.model_validate(lesson.package)
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning(
                    "⚠️ Skipping lesson %s while building detail for unit %s due to package validation error: %s",
                    lesson.id,
                    unit.id,
                    exc,
                )
                continue

            lesson_lo_ids = list(package.unit_learning_objective_ids)
            if not lesson_lo_ids:
                lesson_lo_ids = sorted({exercise.aligned_learning_objective for exercise in package.exercise_bank if exercise.aligned_learning_objective})
            objectives = [(lo_obj.description if (lo_obj := lo_lookup.get(lo_id)) else lo_id) for lo_id in lesson_lo_ids]

            podcast_meta = self._build_lesson_podcast_payload(lesson, include_transcript=False)
            summary = self.UnitLessonSummary(
                id=lesson.id,
                title=lesson.title,
                learner_level=lesson.learner_level,
                learning_objective_ids=lesson_lo_ids,
                learning_objectives=objectives,
                key_concepts=[],
                exercise_count=len(package.quiz),
                has_podcast=podcast_meta["has_podcast"],
                podcast_voice=podcast_meta["podcast_voice"],
                podcast_duration_seconds=podcast_meta["podcast_duration_seconds"],
                podcast_generated_at=podcast_meta["podcast_generated_at"],
                podcast_audio_url=podcast_meta["podcast_audio_url"],
            )
            lesson_summaries[lesson.id] = summary

        ordered_ids = list(unit.lesson_order or [])
        ordered_lessons: list[ContentService.UnitLessonSummary] = []
        seen: set[str] = set()
        for lid in ordered_ids:
            summary = lesson_summaries.get(lid)
            if summary:
                ordered_lessons.append(summary)
                seen.add(lid)

        for lid, summary in lesson_summaries.items():
            if lid not in seen:
                ordered_lessons.append(summary)

        audio_meta: Any | None = None
        audio_object_id = getattr(unit, "podcast_audio_object_id", None)
        if audio_object_id:
            audio_meta = await self._fetch_audio_metadata(
                audio_object_id,
                requesting_user_id=getattr(unit, "user_id", None),
                include_presigned_url=True,
            )

        unit_summary = await self._build_unit_read(
            unit,
            audio_meta=audio_meta,
            include_art_presigned_url=include_art_presigned_url,
        )
        detail_dict = unit_summary.model_dump()
        detail_dict["lesson_order"] = ordered_ids
        detail_dict["lessons"] = [lesson.model_dump() for lesson in ordered_lessons]
        detail_dict["learning_objectives"] = [lo.model_dump() for lo in unit_learning_objectives] if unit_learning_objectives else None
        transcript = getattr(unit, "podcast_transcript", None)
        if not transcript and audio_meta is not None:
            transcript = getattr(audio_meta, "transcript", None)
        detail_dict["podcast_transcript"] = transcript
        # Prefer direct presigned URL if available, fallback to backend route
        presigned_url = getattr(audio_meta, "presigned_url", None) if audio_meta is not None else None
        detail_dict["podcast_audio_url"] = presigned_url or self._build_podcast_audio_url(unit)

        return self.UnitDetailRead.model_validate(detail_dict)

    async def list_units(self, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]:
        arr = await self.repo.list_units(limit=limit, offset=offset)
        results: list[ContentService.UnitRead] = []
        for unit in arr:
            results.append(await self._build_unit_read(unit))
        return results

    async def get_units_since(
        self,
        *,
        since: datetime | None,
        limit: int = 100,
        include_deleted: bool = False,
        payload: ContentService.UnitSyncPayload = "full",
        user_id: int | None = None,
    ) -> ContentService.UnitSyncResponse:
        """Return units and lessons that changed since the provided timestamp, filtered by user access."""

        if payload not in ("full", "minimal"):
            raise ValueError(f"Unsupported sync payload: {payload}")

        units = await self.repo.get_units_updated_since(since, limit=limit)

        memberships: set[str] = set()

        def _user_can_access(unit: UnitModel) -> bool:
            if user_id is None:
                return True
            if getattr(unit, "user_id", None) == user_id:
                return True
            return unit.id in memberships

        if user_id is not None:
            membership_ids = await self.repo.list_my_units_unit_ids(user_id)
            memberships = set(membership_ids)
            units = [unit for unit in units if _user_can_access(unit)]

        unit_by_id: dict[str, UnitModel] = {unit.id: unit for unit in units}

        lessons_by_unit: dict[str, dict[str, LessonModel]] = {}
        include_lessons = payload == "full"
        if include_lessons and unit_by_id:
            base_lessons = await self.repo.get_lessons_for_unit_ids(unit_by_id.keys())
            for lesson in base_lessons:
                if not lesson.unit_id:
                    continue
                bucket = lessons_by_unit.setdefault(lesson.unit_id, {})
                existing = bucket.get(lesson.id)
                if existing is None or existing.updated_at < lesson.updated_at:
                    bucket[lesson.id] = lesson

        if include_lessons and since is not None:
            recent_lessons = await self.repo.get_lessons_updated_since(since, limit=limit)
            for lesson in recent_lessons:
                if not lesson.unit_id:
                    continue
                if lesson.unit_id not in unit_by_id:
                    unit = await self.repo.get_unit_by_id(lesson.unit_id)
                    if unit is not None and _user_can_access(unit):
                        unit_by_id[unit.id] = unit
                        units.append(unit)
                    else:
                        continue
                bucket = lessons_by_unit.setdefault(lesson.unit_id, {})
                existing = bucket.get(lesson.id)
                if existing is None or existing.updated_at < lesson.updated_at:
                    bucket[lesson.id] = lesson

        entries: list[ContentService.UnitSyncEntry] = []
        cursor_candidates: list[datetime] = []

        allowed_asset_types = None if payload == "full" else {"image"}

        for unit in units:
            unit_read = await self._build_unit_read(
                unit,
                include_art_presigned_url=True,
                include_audio_metadata=payload == "full",
            )
            unit_read.schema_version = getattr(unit, "schema_version", 1)
            cursor_candidates.append(unit.updated_at)

            lesson_reads: list[LessonRead] = []
            if include_lessons:
                lesson_bucket = lessons_by_unit.get(unit.id, {})
                ordered_ids = list(getattr(unit, "lesson_order", []) or [])
                ordered_models: list[LessonModel] = []
                seen_ids: set[str] = set()

                for lesson_id in ordered_ids:
                    model = lesson_bucket.get(lesson_id)
                    if model is None:
                        continue
                    ordered_models.append(model)
                    seen_ids.add(model.id)

                remaining_models = [model for model_id, model in lesson_bucket.items() if model_id not in seen_ids]
                remaining_models.sort(key=lambda model: model.updated_at)
                ordered_models.extend(remaining_models)

                for model in ordered_models:
                    try:
                        lesson_read = self._lesson_model_to_read(model)
                    except Exception:  # pragma: no cover - helper already logged  # noqa: S112
                        continue
                    lesson_reads.append(lesson_read)
                    cursor_candidates.append(model.updated_at)

            assets = await self._build_unit_assets(
                unit,
                unit_read,
                allowed_types=allowed_asset_types,
                lessons=ordered_models if include_lessons else None,
            )

            entries.append(
                self.UnitSyncEntry(
                    unit=unit_read,
                    lessons=lesson_reads,
                    assets=assets,
                )
            )

        cursor = max(cursor_candidates) if cursor_candidates else (since if since is not None else datetime.now(tz=UTC))

        deleted_unit_ids: list[str] = []
        deleted_lesson_ids: list[str] = []
        if include_deleted:
            # Tombstones are not yet tracked; keep placeholders for forward compatibility.
            deleted_unit_ids = []
            deleted_lesson_ids = []

        return self.UnitSyncResponse(
            units=entries,
            deleted_unit_ids=deleted_unit_ids,
            deleted_lesson_ids=deleted_lesson_ids,
            cursor=cursor,
        )

    async def list_units_for_user(self, user_id: int, *, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]:
        """Return units owned by a specific user."""
        arr = await self.repo.list_units_for_user(user_id=user_id, limit=limit, offset=offset)
        results: list[ContentService.UnitRead] = []
        for unit in arr:
            results.append(await self._build_unit_read(unit))
        return results

    async def list_units_for_user_including_my_units(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ContentService.UnitRead]:
        """Return units owned by the user along with catalog units they have added."""

        arr = await self.repo.list_units_for_user_including_my_units(user_id=user_id, limit=limit, offset=offset)
        results: list[ContentService.UnitRead] = []
        for unit in arr:
            results.append(await self._build_unit_read(unit))
        return results

    async def list_global_units(self, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]:
        """Return units that have been shared globally."""
        arr = await self.repo.list_global_units(limit=limit, offset=offset)
        results: list[ContentService.UnitRead] = []
        for unit in arr:
            results.append(await self._build_unit_read(unit))
        return results

    async def get_units_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]:
        """Get units filtered by status."""
        arr = await self.repo.get_units_by_status(status=status, limit=limit, offset=offset)
        results: list[ContentService.UnitRead] = []
        for unit in arr:
            results.append(await self._build_unit_read(unit))
        return results

    async def update_unit_status(
        self,
        unit_id: str,
        status: str,
        error_message: str | None = None,
        creation_progress: dict[str, Any] | None = None,
    ) -> ContentService.UnitRead | None:
        """Update unit status and return the updated unit, or None if not found."""
        updated = await self.repo.update_unit_status(
            unit_id=unit_id,
            status=status,
            error_message=error_message,
            creation_progress=creation_progress,
        )
        if updated is None:
            return None
        return await self._build_unit_read(updated)

    async def set_unit_task(
        self,
        unit_id: str,
        arq_task_id: str | None,
    ) -> ContentService.UnitRead | None:
        """Update the ARQ task tracking identifier for a unit."""

        updated = await self.repo.update_unit_arq_task(unit_id, arq_task_id)
        if updated is None:
            return None
        return await self._build_unit_read(updated)

    async def create_unit(self, data: ContentService.UnitCreate) -> ContentService.UnitRead:
        unit_id = data.id or str(uuid.uuid4())
        los_payload = [lo.model_dump() for lo in data.learning_objectives] if data.learning_objectives is not None else []
        model = UnitModel(
            id=unit_id,
            title=data.title,
            description=data.description,
            learner_level=data.learner_level,
            lesson_order=list(data.lesson_order or []),
            user_id=data.user_id,
            is_global=bool(data.is_global),
            learning_objectives=los_payload,
            target_lesson_count=data.target_lesson_count,
            source_material=data.source_material,
            generated_from_topic=bool(data.generated_from_topic),
            flow_type=str(getattr(data, "flow_type", "standard") or "standard"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        created = await self.repo.add_unit(model)
        return await self._build_unit_read(created)

    async def get_unit_flow_runs(self, unit_id: str) -> list[FlowRunSummaryDTO]:
        """Retrieve flow runs associated with a unit for admin observability."""

        infra = infrastructure_provider()
        infra.initialize()
        with infra.get_session_context() as session:
            flow_service = flow_engine_admin_provider(session)
            return flow_service.list_flow_runs(unit_id=unit_id)

    async def set_unit_lesson_order(self, unit_id: str, lesson_ids: list[str]) -> ContentService.UnitRead:
        updated = await self.repo.update_unit_lesson_order(unit_id, lesson_ids)
        if updated is None:
            raise ValueError("Unit not found")
        return await self._build_unit_read(updated)

    async def update_unit_metadata(
        self,
        unit_id: str,
        *,
        title: str | None = None,
        learning_objectives: list[UnitLearningObjective] | None = None,
    ) -> ContentService.UnitRead | None:
        """Update unit metadata fields (title, learning_objectives)."""
        los_payload = [lo.model_dump() for lo in learning_objectives] if learning_objectives is not None else None
        updated = await self.repo.update_unit_metadata(
            unit_id,
            title=title,
            learning_objectives=los_payload,
        )
        if updated is None:
            return None
        return await self._build_unit_read(updated)

    async def assign_unit_owner(self, unit_id: str, *, owner_user_id: int | None) -> ContentService.UnitRead:
        """Assign or clear ownership of a unit."""
        updated = await self.repo.set_unit_owner(unit_id, owner_user_id)
        if updated is None:
            raise ValueError("Unit not found")
        return await self._build_unit_read(updated)

    async def add_unit_to_my_units(self, user_id: int, unit_id: str) -> ContentService.UnitRead:
        """Add a catalog unit to the user's My Units collection."""

        unit = await self.repo.get_unit_by_id(unit_id)
        if unit is None:
            raise LookupError("Unit not found")

        if getattr(unit, "user_id", None) == user_id:
            return await self._build_unit_read(unit)

        already_member = await self.repo.is_unit_in_my_units(user_id, unit_id)
        if already_member:
            return await self._build_unit_read(unit)

        if not getattr(unit, "is_global", False):
            raise PermissionError("Unit is not shared globally")

        await self.repo.add_unit_to_my_units(user_id, unit_id)
        return await self._build_unit_read(unit)

    async def remove_unit_from_my_units(self, user_id: int, unit_id: str) -> ContentService.UnitRead:
        """Remove a catalog unit from the user's My Units collection."""

        unit = await self.repo.get_unit_by_id(unit_id)
        if unit is None:
            raise LookupError("Unit not found")

        if getattr(unit, "user_id", None) == user_id:
            raise PermissionError("Cannot remove an owned unit")

        membership_exists = await self.repo.is_unit_in_my_units(user_id, unit_id)
        if not membership_exists:
            raise LookupError("Unit is not in My Units")

        await self.repo.remove_unit_from_my_units(user_id, unit_id)
        return await self._build_unit_read(unit)

    @staticmethod
    def _parse_unit_learning_objectives(
        raw: list[Any] | None,
    ) -> list[UnitLearningObjective]:
        if not raw:
            return []

        parsed: list[UnitLearningObjective] = []
        for item in raw:
            if isinstance(item, UnitLearningObjective):
                parsed.append(item)
                continue

            if isinstance(item, str):
                parsed.append(UnitLearningObjective(id=item, title=item, description=item))
                continue

            if isinstance(item, dict):
                payload = dict(item)
            else:
                payload = {
                    "id": getattr(item, "id", None) or getattr(item, "lo_id", None),
                    "title": getattr(item, "title", None) or getattr(item, "short_title", None),
                    "description": getattr(item, "description", None),
                    "bloom_level": getattr(item, "bloom_level", None),
                    "evidence_of_mastery": getattr(item, "evidence_of_mastery", None),
                }

            lo_id = payload.get("id") or payload.get("lo_id")
            if lo_id is None:
                raise ValueError("Unit learning objective is missing an id")

            title = payload.get("title") or payload.get("short_title")
            description = payload.get("description")
            if title is None:
                title = description or str(lo_id)
            if description is None:
                description = title

            bloom_level = payload.get("bloom_level")
            evidence_of_mastery = payload.get("evidence_of_mastery")
            parsed.append(
                UnitLearningObjective(
                    id=str(lo_id),
                    title=str(title),
                    description=str(description),
                    bloom_level=bloom_level if isinstance(bloom_level, str) else None,
                    evidence_of_mastery=evidence_of_mastery if isinstance(evidence_of_mastery, str) else None,
                )
            )

        return parsed

    async def set_unit_sharing(
        self,
        unit_id: str,
        *,
        is_global: bool,
        acting_user_id: int | None = None,
    ) -> ContentService.UnitRead:
        """Update whether a unit is shared globally, optionally enforcing ownership."""

        if acting_user_id is not None and not await self.repo.is_unit_owned_by_user(unit_id, acting_user_id):
            raise PermissionError("User does not own this unit")

        updated = await self.repo.set_unit_sharing(unit_id, is_global)
        if updated is None:
            raise ValueError("Unit not found")
        return await self._build_unit_read(updated)

    async def assign_lessons_to_unit(self, unit_id: str, lesson_ids: list[str]) -> ContentService.UnitRead:
        """Assign lessons to a unit and set ordering in one operation.

        Skips lesson IDs that don't exist. Removes lessons previously in the unit
        if they are not in the provided list.
        """
        updated = await self.repo.associate_lessons_with_unit(unit_id, lesson_ids)
        if updated is None:
            raise ValueError("Unit not found")
        return await self._build_unit_read(updated)

    async def set_unit_podcast(
        self,
        unit_id: str,
        *,
        transcript: str | None,
        audio_object_id: uuid.UUID | None,
        voice: str | None = None,
    ) -> ContentService.UnitRead | None:
        """Persist podcast transcript and object store reference for a unit."""

        self._audio_metadata_cache.clear()
        updated = await self.repo.set_unit_podcast(
            unit_id,
            transcript=transcript,
            audio_object_id=audio_object_id,
            voice=voice,
        )
        if updated is None:
            return None

        audio_meta: Any | None = None
        if audio_object_id is not None:
            audio_meta = await self._fetch_audio_metadata(
                audio_object_id,
                requesting_user_id=getattr(updated, "user_id", None),
            )

        return await self._build_unit_read(updated, audio_meta=audio_meta)

    async def get_unit_podcast_audio(self, unit_id: str) -> ContentService.UnitPodcastAudio | None:
        """Retrieve the stored podcast audio payload for streaming."""

        unit = await self.repo.get_unit_by_id(unit_id)
        if unit is None:
            return None

        audio_meta = await self._fetch_audio_metadata(
            getattr(unit, "podcast_audio_object_id", None),
            requesting_user_id=getattr(unit, "user_id", None),
            include_presigned_url=True,
        )
        if not audio_meta:
            return None

        mime_type = getattr(audio_meta, "content_type", None) or "audio/mpeg"
        presigned = getattr(audio_meta, "presigned_url", None)

        if presigned is None and self._object_store is not None:
            s3_key = getattr(audio_meta, "s3_key", None)
            if s3_key:
                try:
                    presigned = await self._object_store.generate_presigned_url(s3_key)
                except Exception as exc:  # pragma: no cover - network/object store issues
                    logger.warning(
                        "🎧 Failed to generate presigned podcast URL for unit %s: %s",
                        unit_id,
                        exc,
                        exc_info=True,
                    )

        if presigned is None:
            return None

        return self.UnitPodcastAudio(
            unit_id=unit_id,
            mime_type=mime_type,
            presigned_url=presigned,
        )

    async def get_lesson_podcast_audio(self, lesson_id: str) -> ContentService.LessonPodcastAudio | None:
        """Retrieve lesson podcast audio for streaming."""

        lesson = await self.repo.get_lesson_by_id(lesson_id)
        if lesson is None:
            return None

        audio_meta = await self._fetch_audio_metadata(
            getattr(lesson, "podcast_audio_object_id", None),
            requesting_user_id=None,
            include_presigned_url=True,
        )
        if not audio_meta:
            return None

        mime_type = getattr(audio_meta, "content_type", None) or "audio/mpeg"
        presigned = getattr(audio_meta, "presigned_url", None)

        if presigned is None and self._object_store is not None:
            s3_key = getattr(audio_meta, "s3_key", None)
            if s3_key:
                try:
                    presigned = await self._object_store.generate_presigned_url(s3_key)
                except Exception as exc:  # pragma: no cover - object store failures
                    logger.warning(
                        "🎧 Failed to generate presigned podcast URL for lesson %s: %s",
                        lesson_id,
                        exc,
                        exc_info=True,
                    )

        if presigned is None:
            return None

        return self.LessonPodcastAudio(
            lesson_id=lesson_id,
            mime_type=mime_type,
            presigned_url=presigned,
        )

    async def delete_unit(self, unit_id: str) -> bool:
        """Delete a unit by ID. Returns True if successful, False if not found."""
        return await self.repo.delete_unit(unit_id)

    # ======================
    # Unit session operations
    # ======================
    class UnitSessionRead(BaseModel):
        id: str
        unit_id: str
        user_id: str
        status: str
        progress_percentage: float
        last_lesson_id: str | None = None
        completed_lesson_ids: list[str]
        started_at: datetime
        completed_at: datetime | None = None
        updated_at: datetime

        model_config = ConfigDict(from_attributes=True)

    async def get_or_create_unit_session(self, user_id: str, unit_id: str) -> ContentService.UnitSessionRead:
        """Get existing unit session or create a new active one."""
        existing = await self.repo.get_unit_session(user_id=user_id, unit_id=unit_id)
        if existing:
            return self.UnitSessionRead.model_validate(existing)

        from ..learning_session.models import UnitSessionModel

        model = UnitSessionModel(
            id=str(uuid.uuid4()),
            unit_id=unit_id,
            user_id=user_id,
            status="active",
            progress_percentage=0.0,
            completed_lesson_ids=[],
            last_lesson_id=None,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        created = await self.repo.add_unit_session(model)
        return self.UnitSessionRead.model_validate(created)

    async def update_unit_session_progress(
        self,
        user_id: str,
        unit_id: str,
        *,
        last_lesson_id: str | None = None,
        completed_lesson_id: str | None = None,
        total_lessons: int | None = None,
        mark_completed: bool = False,
        progress_percentage: float | None = None,
    ) -> ContentService.UnitSessionRead:
        """Update progress for a unit session, creating one if needed."""
        model = await self.repo.get_unit_session(user_id=user_id, unit_id=unit_id)
        if not model:
            from ..learning_session.models import UnitSessionModel

            model = UnitSessionModel(
                id=str(uuid.uuid4()),
                unit_id=unit_id,
                user_id=user_id,
                status="active",
                progress_percentage=0.0,
                completed_lesson_ids=[],
                last_lesson_id=None,
                started_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            await self.repo.add_unit_session(model)

        # Update fields
        if last_lesson_id:
            model.last_lesson_id = last_lesson_id
        if completed_lesson_id:
            existing = set(model.completed_lesson_ids or [])
            existing.add(completed_lesson_id)
            model.completed_lesson_ids = list(existing)

        # Compute progress if total provided
        if total_lessons is not None:
            completed_count = len(model.completed_lesson_ids or [])
            pct = (completed_count / total_lessons * 100) if total_lessons > 0 else 0.0
            model.progress_percentage = float(min(pct, 100.0))

        if progress_percentage is not None:
            model.progress_percentage = float(progress_percentage)

        if mark_completed:
            model.status = "completed"
            model.completed_at = datetime.utcnow()

        model.updated_at = datetime.utcnow()
        await self.repo.save_unit_session(model)
        return self.UnitSessionRead.model_validate(model)
