from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Iterable
import uuid

from modules.flow_engine.public import FlowRunSummaryDTO

from ..models import LessonModel, UnitModel
from ..repo import ContentRepo
from .dtos import (
    UnitCreate,
    UnitDetailRead,
    UnitLessonSummary,
    UnitLearningObjective,
    UnitPodcastAudio,
    UnitRead,
    UnitSyncAsset,
)
from .lesson_handler import LessonHandler
from .media import MediaHelper

logger = logging.getLogger(__name__)


class UnitHandler:
    """Encapsulates unit-centric business logic and media orchestration."""

    def __init__(self, repo: ContentRepo, media: MediaHelper, lessons: LessonHandler) -> None:
        self.repo = repo
        self.media = media
        self.lessons = lessons

    # ------------------------------------------------------------------
    # Core transformation helpers
    # ------------------------------------------------------------------
    async def build_unit_read(
        self,
        unit: UnitModel,
        *,
        audio_meta: Any | None = None,
        include_art_presigned_url: bool = True,
        include_audio_metadata: bool = True,
    ) -> UnitRead:
        unit_read = UnitRead.model_validate(unit)
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

    async def build_unit_assets(
        self,
        unit: UnitModel,
        unit_read: UnitRead,
        *,
        allowed_types: set[str] | None = None,
        lessons: Iterable[LessonModel] | None = None,
    ) -> list[UnitSyncAsset]:
        assets: list[UnitSyncAsset] = []

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
                if include_audio:
                    metadata = await self.media.fetch_audio_metadata(
                        audio_uuid,
                        requesting_user_id=getattr(unit, "user_id", None),
                        include_presigned_url=True,
                    )
                    presigned_audio = getattr(metadata, "presigned_url", None) if metadata is not None else None

                assets.append(
                    UnitSyncAsset(
                        id=str(audio_uuid),
                        unit_id=unit.id,
                        type="audio",
                        object_id=audio_uuid,
                        remote_url=self.media.build_unit_podcast_audio_url(unit),
                        presigned_url=presigned_audio,
                        updated_at=getattr(unit, "podcast_generated_at", unit.updated_at),
                    )
                )

        if include_audio and lessons is not None:
            for lesson in lessons:
                audio_identifier = getattr(lesson, "podcast_audio_object_id", None)
                if not audio_identifier:
                    continue
                try:
                    audio_uuid = (
                        audio_identifier if isinstance(audio_identifier, uuid.UUID) else uuid.UUID(str(audio_identifier))
                    )
                except (TypeError, ValueError):  # pragma: no cover - defensive
                    logger.warning("🎧 Invalid lesson podcast id encountered: %s", audio_identifier)
                    continue

                metadata = await self.media.fetch_audio_metadata(
                    audio_uuid,
                    requesting_user_id=getattr(unit, "user_id", None),
                    include_presigned_url=True,
                )
                assets.append(
                    UnitSyncAsset(
                        id=str(audio_uuid),
                        unit_id=unit.id,
                        type="audio",
                        object_id=audio_uuid,
                        remote_url=self.media.build_lesson_podcast_audio_url(lesson),
                        presigned_url=getattr(metadata, "presigned_url", None) if metadata is not None else None,
                        updated_at=getattr(lesson, "podcast_generated_at", lesson.updated_at),
                    )
                )

        if include_image:
            art_identifier = getattr(unit, "art_image_id", None)
            if art_identifier:
                try:
                    art_uuid = art_identifier if isinstance(art_identifier, uuid.UUID) else uuid.UUID(str(art_identifier))
                except (TypeError, ValueError):  # pragma: no cover - defensive guard
                    logger.warning("🖼️ Invalid unit artwork id encountered: %s", art_identifier)
                else:
                    metadata = await self.media.fetch_image_metadata(
                        art_uuid,
                        requesting_user_id=getattr(unit, "user_id", None),
                        include_presigned_url=True,
                    )
                    assets.append(
                        UnitSyncAsset(
                            id=str(art_uuid),
                            unit_id=unit.id,
                            type="image",
                            object_id=art_uuid,
                            remote_url=getattr(metadata, "remote_url", None) if metadata is not None else None,
                            presigned_url=getattr(metadata, "presigned_url", None) if metadata is not None else None,
                            updated_at=getattr(metadata, "updated_at", unit.updated_at) if metadata is not None else unit.updated_at,
                        )
                    )

        return assets

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    async def get_unit(self, unit_id: str) -> UnitRead | None:
        unit = await self.repo.get_unit_by_id(unit_id)
        if unit is None:
            return None
        return await self.build_unit_read(unit)

    async def get_unit_detail(
        self,
        unit_id: str,
        *,
        include_art_presigned_url: bool = True,
    ) -> UnitDetailRead | None:
        unit = await self.repo.get_unit_by_id(unit_id)
        if unit is None:
            return None

        lesson_models = await self.repo.get_lessons_by_unit(unit_id=unit_id)
        lesson_summaries: dict[str, UnitLessonSummary] = {}
        unit_learning_objectives = self._parse_unit_learning_objectives(getattr(unit, "learning_objectives", None))
        lo_lookup = {lo.id: lo for lo in unit_learning_objectives}

        for lesson in lesson_models:
            package = self.lessons.lesson_to_read(lesson).package
            lesson_lo_ids = package.unit_learning_objective_ids or []
            objectives: list[str] = []
            for lo_id in lesson_lo_ids:
                lo = lo_lookup.get(lo_id)
                if lo is not None:
                    objectives.append(lo.title)
            if not objectives and package.meta and package.meta.title:
                objectives.append(package.meta.title)

            glossary_terms = package.glossary.get("terms", []) if package.glossary else []
            key_concepts: list[str] = []
            for term in glossary_terms:
                if hasattr(term, "term"):
                    key_concepts.append(str(term.term))
                elif isinstance(term, dict):
                    key_concepts.append(str(term.get("term") or term.get("label") or term))
                else:
                    key_concepts.append(str(term))

            podcast_meta = self.media.build_lesson_podcast_payload(lesson, include_transcript=False)
            summary = UnitLessonSummary(
                id=lesson.id,
                title=lesson.title,
                learner_level=lesson.learner_level,
                learning_objective_ids=lesson_lo_ids,
                learning_objectives=objectives,
                key_concepts=key_concepts,
                exercise_count=len(package.exercises),
                has_podcast=podcast_meta["has_podcast"],
                podcast_voice=podcast_meta["podcast_voice"],
                podcast_duration_seconds=podcast_meta["podcast_duration_seconds"],
                podcast_generated_at=podcast_meta["podcast_generated_at"],
                podcast_audio_url=podcast_meta["podcast_audio_url"],
            )
            lesson_summaries[lesson.id] = summary

        ordered_ids = list(unit.lesson_order or [])
        ordered_lessons: list[UnitLessonSummary] = []
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
            audio_meta = await self.media.fetch_audio_metadata(
                audio_object_id,
                requesting_user_id=getattr(unit, "user_id", None),
                include_presigned_url=True,
            )

        unit_summary = await self.build_unit_read(
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
        presigned_url = getattr(audio_meta, "presigned_url", None) if audio_meta is not None else None
        detail_dict["podcast_audio_url"] = presigned_url or self.media.build_unit_podcast_audio_url(unit)

        return UnitDetailRead.model_validate(detail_dict)

    async def list_units(self, limit: int = 100, offset: int = 0) -> list[UnitRead]:
        arr = await self.repo.list_units(limit=limit, offset=offset)
        results: list[UnitRead] = []
        for unit in arr:
            results.append(await self.build_unit_read(unit))
        return results

    async def list_units_for_user(self, user_id: int, *, limit: int = 100, offset: int = 0) -> list[UnitRead]:
        arr = await self.repo.list_units_for_user(user_id=user_id, limit=limit, offset=offset)
        results: list[UnitRead] = []
        for unit in arr:
            results.append(await self.build_unit_read(unit))
        return results

    async def list_units_for_user_including_my_units(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UnitRead]:
        arr = await self.repo.list_units_for_user_including_my_units(user_id=user_id, limit=limit, offset=offset)
        results: list[UnitRead] = []
        for unit in arr:
            results.append(await self.build_unit_read(unit))
        return results

    async def list_global_units(self, limit: int = 100, offset: int = 0) -> list[UnitRead]:
        arr = await self.repo.list_global_units(limit=limit, offset=offset)
        results: list[UnitRead] = []
        for unit in arr:
            results.append(await self.build_unit_read(unit))
        return results

    async def get_units_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[UnitRead]:
        arr = await self.repo.get_units_by_status(status=status, limit=limit, offset=offset)
        results: list[UnitRead] = []
        for unit in arr:
            results.append(await self.build_unit_read(unit))
        return results

    async def update_unit_status(
        self,
        unit_id: str,
        status: str,
        error_message: str | None = None,
        creation_progress: dict[str, Any] | None = None,
    ) -> UnitRead | None:
        updated = await self.repo.update_unit_status(
            unit_id=unit_id,
            status=status,
            error_message=error_message,
            creation_progress=creation_progress,
        )
        if updated is None:
            return None
        return await self.build_unit_read(updated)

    async def set_unit_task(self, unit_id: str, arq_task_id: str | None) -> UnitRead | None:
        updated = await self.repo.update_unit_arq_task(unit_id, arq_task_id)
        if updated is None:
            return None
        return await self.build_unit_read(updated)

    async def create_unit(self, data: UnitCreate) -> UnitRead:
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
        return await self.build_unit_read(created)

    async def get_unit_flow_runs(self, unit_id: str) -> list[FlowRunSummaryDTO]:
        from . import flow_engine_admin_provider, infrastructure_provider

        infra = infrastructure_provider()
        infra.initialize()
        with infra.get_session_context() as session:
            flow_service = flow_engine_admin_provider(session)
            return flow_service.list_flow_runs(unit_id=unit_id)

    async def set_unit_lesson_order(self, unit_id: str, lesson_ids: list[str]) -> UnitRead:
        updated = await self.repo.update_unit_lesson_order(unit_id, lesson_ids)
        if updated is None:
            raise ValueError("Unit not found")
        return await self.build_unit_read(updated)

    async def update_unit_metadata(
        self,
        unit_id: str,
        *,
        title: str | None = None,
        learning_objectives: list[UnitLearningObjective] | None = None,
    ) -> UnitRead | None:
        los_payload = [lo.model_dump() for lo in learning_objectives] if learning_objectives is not None else None
        updated = await self.repo.update_unit_metadata(
            unit_id,
            title=title,
            learning_objectives=los_payload,
        )
        if updated is None:
            return None
        return await self.build_unit_read(updated)

    async def assign_unit_owner(self, unit_id: str, *, owner_user_id: int | None) -> UnitRead:
        updated = await self.repo.set_unit_owner(unit_id, owner_user_id)
        if updated is None:
            raise ValueError("Unit not found")
        return await self.build_unit_read(updated)

    async def add_unit_to_my_units(self, user_id: int, unit_id: str) -> UnitRead:
        unit = await self.repo.get_unit_by_id(unit_id)
        if unit is None:
            raise LookupError("Unit not found")

        if getattr(unit, "user_id", None) == user_id:
            return await self.build_unit_read(unit)

        already_member = await self.repo.is_unit_in_my_units(user_id, unit_id)
        if already_member:
            return await self.build_unit_read(unit)

        if not getattr(unit, "is_global", False):
            raise PermissionError("Unit is not shared globally")

        await self.repo.add_unit_to_my_units(user_id, unit_id)
        return await self.build_unit_read(unit)

    async def remove_unit_from_my_units(self, user_id: int, unit_id: str) -> UnitRead:
        unit = await self.repo.get_unit_by_id(unit_id)
        if unit is None:
            raise LookupError("Unit not found")

        if getattr(unit, "user_id", None) == user_id:
            raise PermissionError("Cannot remove an owned unit")

        membership_exists = await self.repo.is_unit_in_my_units(user_id, unit_id)
        if not membership_exists:
            raise LookupError("Unit is not in My Units")

        await self.repo.remove_unit_from_my_units(user_id, unit_id)
        return await self.build_unit_read(unit)

    async def set_unit_sharing(
        self,
        unit_id: str,
        *,
        is_global: bool,
        acting_user_id: int | None = None,
    ) -> UnitRead:
        if acting_user_id is not None and not await self.repo.is_unit_owned_by_user(unit_id, acting_user_id):
            raise PermissionError("User does not own this unit")

        updated = await self.repo.set_unit_sharing(unit_id, is_global)
        if updated is None:
            raise ValueError("Unit not found")
        return await self.build_unit_read(updated)

    async def assign_lessons_to_unit(self, unit_id: str, lesson_ids: list[str]) -> UnitRead:
        updated = await self.repo.associate_lessons_with_unit(unit_id, lesson_ids)
        if updated is None:
            raise ValueError("Unit not found")
        return await self.build_unit_read(updated)

    async def set_unit_podcast(
        self,
        unit_id: str,
        *,
        transcript: str | None,
        audio_object_id: uuid.UUID | None,
        voice: str | None = None,
    ) -> UnitRead | None:
        self.media.clear_audio_cache()
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
            audio_meta = await self.media.fetch_audio_metadata(
                audio_object_id,
                requesting_user_id=getattr(updated, "user_id", None),
            )

        return await self.build_unit_read(updated, audio_meta=audio_meta)

    async def get_unit_podcast_audio(self, unit_id: str) -> UnitPodcastAudio | None:
        unit = await self.repo.get_unit_by_id(unit_id)
        if unit is None:
            return None

        audio_meta = await self.media.fetch_audio_metadata(
            getattr(unit, "podcast_audio_object_id", None),
            requesting_user_id=getattr(unit, "user_id", None),
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
                except Exception as exc:  # pragma: no cover - network/object store failures
                    logger.warning(
                        "🎧 Failed to generate presigned podcast URL for unit %s: %s",
                        unit_id,
                        exc,
                        exc_info=True,
                    )

        if presigned is None:
            return None

        return UnitPodcastAudio(
            unit_id=unit_id,
            mime_type=mime_type,
            presigned_url=presigned,
        )

    async def save_unit_art_from_bytes(
        self,
        unit_id: str,
        *,
        image_bytes: bytes,
        content_type: str,
        description: str | None,
        alt_text: str | None = None,
    ) -> UnitRead:
        if self.media.object_store is None:
            raise RuntimeError("Object store is not configured; cannot persist generated unit art.")

        unit_info = await self.repo.get_unit_by_id(unit_id)
        if unit_info is None:
            raise ValueError("Unit not found")

        owner_id = getattr(unit_info, "user_id", None)
        filename = self.media.build_unit_art_filename(unit_id, content_type)
        resolved_content_type = content_type or "image/png"

        upload = await self.media.upload_image(
            owner_id=owner_id,
            filename=filename,
            content_type=resolved_content_type,
            content=image_bytes,
            description=description,
            alt_text=alt_text,
            generate_presigned_url=True,
        )

        updated = await self.repo.set_unit_art(
            unit_id,
            image_object_id=upload.file.id,
            description=description,
        )
        if updated is None:
            raise ValueError("Failed to persist unit art metadata")

        self.media.clear_art_cache()
        return await self.build_unit_read(updated, include_art_presigned_url=True)

    async def save_unit_podcast_from_bytes(
        self,
        unit_id: str,
        *,
        transcript: str,
        audio_bytes: bytes,
        mime_type: str | None,
        voice: str | None,
    ) -> UnitRead:
        if self.media.object_store is None:
            raise RuntimeError("Object store is not configured; cannot persist generated podcast audio.")

        unit_info = await self.repo.get_unit_by_id(unit_id)
        if unit_info is None:
            raise ValueError("Unit not found")

        owner_id = getattr(unit_info, "user_id", None)
        filename = self.media.build_unit_podcast_filename(unit_id, mime_type)

        upload = await self.media.upload_audio(
            owner_id=owner_id,
            filename=filename,
            content_type=(mime_type or "audio/mpeg"),
            content=audio_bytes,
            transcript=transcript,
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

        return await self.build_unit_read(updated_model, audio_meta=upload.file)

    async def delete_unit(self, unit_id: str) -> bool:
        return await self.repo.delete_unit(unit_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_unit_learning_objectives(raw: list[Any] | None) -> list[UnitLearningObjective]:
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

    async def _apply_podcast_metadata(
        self,
        unit_read: UnitRead,
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
        unit_read.podcast_audio_url = self.media.build_unit_podcast_audio_url(unit) if audio_object_id else None

        if not include_metadata:
            resolved_meta = audio_meta if audio_meta is not None else None
        else:
            resolved_meta = audio_meta
            if resolved_meta is None and audio_object_id:
                resolved_meta = await self.media.fetch_audio_metadata(
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
        unit_read: UnitRead,
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
        metadata = await self.media.fetch_image_metadata(
            art_uuid,
            requesting_user_id=getattr(unit, "user_id", None),
            include_presigned_url=include_presigned_url,
        )

        if metadata is None:
            unit_read.art_image_url = None
            return

        unit_read.art_image_url = getattr(metadata, "presigned_url", None)


__all__ = ["UnitHandler"]
