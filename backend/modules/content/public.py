"""Protocol definition and dependency injection provider for the content module."""

from typing import Any, Protocol
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from modules.object_store.public import object_store_provider

from .repo import ContentRepo
from .service import (
    ContentService,
    LessonCreate,
    LessonRead,
    UnitStatus,
)


class ContentProvider(Protocol):
    """Protocol defining the content module's public async interface."""

    async def get_lesson(self, lesson_id: str) -> LessonRead | None: ...
    async def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonRead]: ...
    async def search_lessons(
        self,
        query: str | None = None,
        learner_level: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LessonRead]: ...
    async def save_lesson(self, lesson_data: LessonCreate) -> LessonRead: ...
    async def delete_lesson(self, lesson_id: str) -> bool: ...
    async def lesson_exists(self, lesson_id: str) -> bool: ...
    async def get_lessons_by_unit(self, unit_id: str, limit: int = 100, offset: int = 0) -> list[LessonRead]: ...
    async def get_unit(self, unit_id: str) -> ContentService.UnitRead | None: ...
    async def get_unit_detail(self, unit_id: str) -> ContentService.UnitDetailRead | None: ...
    async def list_units(self, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]: ...
    async def list_units_for_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ContentService.UnitRead]: ...
    async def list_global_units(self, limit: int = 100, offset: int = 0) -> list[ContentService.UnitRead]: ...
    async def get_units_by_status(
        self,
        status: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ContentService.UnitRead]: ...
    async def update_unit_status(
        self,
        unit_id: str,
        status: str,
        error_message: str | None = None,
        creation_progress: dict[str, Any] | None = None,
    ) -> ContentService.UnitRead | None: ...
    async def create_unit(self, data: ContentService.UnitCreate) -> ContentService.UnitRead: ...
    async def set_unit_lesson_order(self, unit_id: str, lesson_ids: list[str]) -> ContentService.UnitRead: ...
    async def assign_lessons_to_unit(self, unit_id: str, lesson_ids: list[str]) -> ContentService.UnitRead: ...
    async def assign_unit_owner(self, unit_id: str, owner_user_id: int | None) -> ContentService.UnitRead: ...
    async def set_unit_sharing(
        self,
        unit_id: str,
        is_global: bool,
        acting_user_id: int | None = None,
    ) -> ContentService.UnitRead: ...
    async def set_unit_podcast(
        self,
        unit_id: str,
        *,
        transcript: str | None,
        audio_object_id: uuid.UUID | None,
        voice: str | None = None,
    ) -> ContentService.UnitRead | None: ...
    async def get_unit_podcast_audio(self, unit_id: str) -> ContentService.UnitPodcastAudio | None: ...
    async def save_unit_podcast_from_bytes(
        self,
        unit_id: str,
        *,
        transcript: str,
        audio_bytes: bytes,
        mime_type: str | None,
        voice: str | None,
    ) -> ContentService.UnitRead: ...
    async def delete_unit(self, unit_id: str) -> bool: ...
    async def get_or_create_unit_session(self, user_id: str, unit_id: str) -> ContentService.UnitSessionRead: ...
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
    ) -> ContentService.UnitSessionRead: ...


def content_provider(session: AsyncSession) -> ContentProvider:
    """Create a content service backed by the provided async session."""

    object_store = object_store_provider(session)
    return ContentService(ContentRepo(session), object_store=object_store)


# Create aliases for nested classes to maintain backward compatibility
UnitCreate = ContentService.UnitCreate
UnitRead = ContentService.UnitRead
UnitDetailRead = ContentService.UnitDetailRead
UnitPodcastAudio = ContentService.UnitPodcastAudio
UnitSessionRead = ContentService.UnitSessionRead

__all__ = [
    "ContentProvider",
    "LessonCreate",
    "LessonRead",
    "UnitCreate",
    "UnitDetailRead",
    "UnitPodcastAudio",
    "UnitRead",
    "UnitSessionRead",
    "UnitStatus",
    "content_provider",
]
