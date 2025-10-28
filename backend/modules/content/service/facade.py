from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from modules.flow_engine.public import FlowRunSummaryDTO
from modules.object_store.public import ObjectStoreProvider

from ..repo import ContentRepo
from .dtos import (
    LessonCreate,
    LessonPodcastAudio,
    LessonRead,
    UnitCreate,
    UnitDetailRead,
    UnitLearningObjective,
    UnitLessonSummary,
    UnitPodcastAudio,
    UnitRead,
    UnitSessionRead,
    UnitStatus,
    UnitSyncAsset,
    UnitSyncEntry,
    UnitSyncPayload,
    UnitSyncResponse,
)
from .lesson_handler import LessonHandler
from .media import MediaHelper
from .session_handler import SessionHandler
from .sync_handler import SyncHandler
from .unit_handler import UnitHandler


class ContentService:
    """Facade that composes specialized handlers for content operations."""

    UnitStatus = UnitStatus
    LessonRead = LessonRead
    LessonCreate = LessonCreate
    LessonPodcastAudio = LessonPodcastAudio
    UnitRead = UnitRead
    UnitDetailRead = UnitDetailRead
    UnitLessonSummary = UnitLessonSummary
    UnitLearningObjective = UnitLearningObjective
    UnitPodcastAudio = UnitPodcastAudio
    UnitSyncAsset = UnitSyncAsset
    UnitSyncEntry = UnitSyncEntry
    UnitSyncResponse = UnitSyncResponse
    UnitSessionRead = UnitSessionRead
    UnitSyncPayload = UnitSyncPayload
    UnitCreate = UnitCreate

    def __init__(self, repo: ContentRepo, object_store: ObjectStoreProvider | None = None) -> None:
        self.repo = repo
        self._media = MediaHelper(object_store)
        self._lessons = LessonHandler(repo, self._media)
        self._units = UnitHandler(repo, self._media, self._lessons)
        self._sync = SyncHandler(repo, self._units, self._lessons)
        self._sessions = SessionHandler(repo)

    async def commit_session(self) -> None:
        await self.repo.s.commit()

    # ------------------------------------------------------------------
    # Lesson façade methods
    # ------------------------------------------------------------------
    async def get_lesson(self, lesson_id: str) -> LessonRead | None:
        return await self._lessons.get_lesson(lesson_id)

    async def search_lessons(
        self,
        query: str | None = None,
        learner_level: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LessonRead]:
        return await self._lessons.search_lessons(
            query=query,
            learner_level=learner_level,
            limit=limit,
            offset=offset,
        )

    async def get_lessons_by_unit(self, unit_id: str, limit: int = 100, offset: int = 0) -> list[LessonRead]:
        return await self._lessons.get_lessons_by_unit(unit_id, limit=limit, offset=offset)

    async def save_lesson(self, lesson_data: LessonCreate) -> LessonRead:
        return await self._lessons.save_lesson(lesson_data)

    async def delete_lesson(self, lesson_id: str) -> bool:
        return await self._lessons.delete_lesson(lesson_id)

    async def lesson_exists(self, lesson_id: str) -> bool:
        return await self._lessons.lesson_exists(lesson_id)

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
        return await self._lessons.save_lesson_podcast_from_bytes(
            lesson_id,
            transcript=transcript,
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            voice=voice,
            duration_seconds=duration_seconds,
        )

    async def get_lesson_podcast_audio(self, lesson_id: str) -> LessonPodcastAudio | None:
        return await self._lessons.get_lesson_podcast_audio(lesson_id)

    # ------------------------------------------------------------------
    # Unit façade methods
    # ------------------------------------------------------------------
    async def save_unit_art_from_bytes(
        self,
        unit_id: str,
        *,
        image_bytes: bytes,
        content_type: str,
        description: str | None,
        alt_text: str | None = None,
    ) -> UnitRead:
        return await self._units.save_unit_art_from_bytes(
            unit_id,
            image_bytes=image_bytes,
            content_type=content_type,
            description=description,
            alt_text=alt_text,
        )

    async def save_unit_podcast_from_bytes(
        self,
        unit_id: str,
        *,
        transcript: str,
        audio_bytes: bytes,
        mime_type: str | None,
        voice: str | None,
    ) -> UnitRead:
        return await self._units.save_unit_podcast_from_bytes(
            unit_id,
            transcript=transcript,
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            voice=voice,
        )

    async def get_unit(self, unit_id: str) -> UnitRead | None:
        return await self._units.get_unit(unit_id)

    async def get_unit_detail(
        self,
        unit_id: str,
        *,
        include_art_presigned_url: bool = True,
    ) -> UnitDetailRead | None:
        return await self._units.get_unit_detail(unit_id, include_art_presigned_url=include_art_presigned_url)

    async def list_units(self, limit: int = 100, offset: int = 0) -> list[UnitRead]:
        return await self._units.list_units(limit=limit, offset=offset)

    async def get_units_since(
        self,
        *,
        since: datetime | None,
        limit: int = 100,
        include_deleted: bool = False,
        payload: UnitSyncPayload = "full",
        user_id: int | None = None,
    ) -> UnitSyncResponse:
        return await self._sync.get_units_since(
            since=since,
            limit=limit,
            include_deleted=include_deleted,
            payload=payload,
            user_id=user_id,
        )

    async def list_units_for_user(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UnitRead]:
        return await self._units.list_units_for_user(user_id, limit=limit, offset=offset)

    async def list_units_for_user_including_my_units(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UnitRead]:
        return await self._units.list_units_for_user_including_my_units(user_id, limit=limit, offset=offset)

    async def list_global_units(self, limit: int = 100, offset: int = 0) -> list[UnitRead]:
        return await self._units.list_global_units(limit=limit, offset=offset)

    async def get_units_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[UnitRead]:
        return await self._units.get_units_by_status(status, limit=limit, offset=offset)

    async def update_unit_status(
        self,
        unit_id: str,
        status: str,
        error_message: str | None = None,
        creation_progress: dict[str, Any] | None = None,
    ) -> UnitRead | None:
        return await self._units.update_unit_status(
            unit_id,
            status,
            error_message=error_message,
            creation_progress=creation_progress,
        )

    async def set_unit_task(self, unit_id: str, arq_task_id: str | None) -> UnitRead | None:
        return await self._units.set_unit_task(unit_id, arq_task_id)

    async def create_unit(self, data: UnitCreate) -> UnitRead:
        return await self._units.create_unit(data)

    async def get_unit_flow_runs(self, unit_id: str) -> list[FlowRunSummaryDTO]:
        return await self._units.get_unit_flow_runs(unit_id)

    async def set_unit_lesson_order(self, unit_id: str, lesson_ids: list[str]) -> UnitRead:
        return await self._units.set_unit_lesson_order(unit_id, lesson_ids)

    async def update_unit_metadata(
        self,
        unit_id: str,
        *,
        title: str | None = None,
        learning_objectives: list[UnitLearningObjective] | None = None,
    ) -> UnitRead | None:
        return await self._units.update_unit_metadata(
            unit_id,
            title=title,
            learning_objectives=learning_objectives,
        )

    async def assign_unit_owner(self, unit_id: str, *, owner_user_id: int | None) -> UnitRead:
        return await self._units.assign_unit_owner(unit_id, owner_user_id=owner_user_id)

    async def add_unit_to_my_units(self, user_id: int, unit_id: str) -> UnitRead:
        return await self._units.add_unit_to_my_units(user_id, unit_id)

    async def remove_unit_from_my_units(self, user_id: int, unit_id: str) -> UnitRead:
        return await self._units.remove_unit_from_my_units(user_id, unit_id)

    async def set_unit_sharing(
        self,
        unit_id: str,
        *,
        is_global: bool,
        acting_user_id: int | None = None,
    ) -> UnitRead:
        return await self._units.set_unit_sharing(
            unit_id,
            is_global=is_global,
            acting_user_id=acting_user_id,
        )

    async def assign_lessons_to_unit(self, unit_id: str, lesson_ids: list[str]) -> UnitRead:
        return await self._units.assign_lessons_to_unit(unit_id, lesson_ids)

    async def set_unit_podcast(
        self,
        unit_id: str,
        *,
        transcript: str | None,
        audio_object_id: uuid.UUID | None,
        voice: str | None = None,
    ) -> UnitRead | None:
        return await self._units.set_unit_podcast(
            unit_id,
            transcript=transcript,
            audio_object_id=audio_object_id,
            voice=voice,
        )

    async def get_unit_podcast_audio(self, unit_id: str) -> UnitPodcastAudio | None:
        return await self._units.get_unit_podcast_audio(unit_id)

    async def delete_unit(self, unit_id: str) -> bool:
        return await self._units.delete_unit(unit_id)

    # ------------------------------------------------------------------
    # Session façade methods
    # ------------------------------------------------------------------
    async def get_or_create_unit_session(self, user_id: str, unit_id: str) -> UnitSessionRead:
        return await self._sessions.get_or_create_unit_session(user_id, unit_id)

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
    ) -> UnitSessionRead:
        return await self._sessions.update_unit_session_progress(
            user_id,
            unit_id,
            last_lesson_id=last_lesson_id,
            completed_lesson_id=completed_lesson_id,
            total_lessons=total_lessons,
            mark_completed=mark_completed,
            progress_percentage=progress_percentage,
        )


__all__ = [
    "ContentService",
    "LessonCreate",
    "LessonPodcastAudio",
    "LessonRead",
    "UnitCreate",
    "UnitDetailRead",
    "UnitLearningObjective",
    "UnitLessonSummary",
    "UnitPodcastAudio",
    "UnitRead",
    "UnitSessionRead",
    "UnitStatus",
    "UnitSyncAsset",
    "UnitSyncEntry",
    "UnitSyncPayload",
    "UnitSyncResponse",
]
