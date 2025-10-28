from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..models import LessonModel, UnitModel
from ..repo import ContentRepo
from .dtos import LessonRead, UnitSyncEntry, UnitSyncPayload, UnitSyncResponse
from .lesson_handler import LessonHandler
from .unit_handler import UnitHandler


class SyncHandler:
    """Orchestrates unit/lesson synchronization payloads."""

    def __init__(
        self,
        repo: ContentRepo,
        unit_handler: UnitHandler,
        lesson_handler: LessonHandler,
    ) -> None:
        self.repo = repo
        self.unit_handler = unit_handler
        self.lesson_handler = lesson_handler

    async def get_units_since(
        self,
        *,
        since: datetime | None,
        limit: int = 100,
        include_deleted: bool = False,
        payload: UnitSyncPayload = "full",
        user_id: int | None = None,
    ) -> UnitSyncResponse:
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

        entries: list[UnitSyncEntry] = []
        cursor_candidates: list[datetime] = []

        allowed_asset_types = None if payload == "full" else {"image"}

        for unit in units:
            unit_read = await self.unit_handler.build_unit_read(
                unit,
                include_art_presigned_url=True,
                include_audio_metadata=payload == "full",
            )
            unit_read.schema_version = getattr(unit, "schema_version", 1)
            cursor_candidates.append(unit.updated_at)

            lesson_reads: list[LessonRead] = []
            ordered_models: list[LessonModel] = []
            if include_lessons:
                lesson_bucket = lessons_by_unit.get(unit.id, {})
                ordered_ids = list(getattr(unit, "lesson_order", []) or [])
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
                        lesson_read = self.lesson_handler.lesson_to_read(model)
                    except Exception:  # pragma: no cover - helper already logged
                        continue
                    lesson_reads.append(lesson_read)
                    cursor_candidates.append(model.updated_at)

            assets = await self.unit_handler.build_unit_assets(
                unit,
                unit_read,
                allowed_types=allowed_asset_types,
                lessons=ordered_models if include_lessons else None,
            )

            entries.append(
                UnitSyncEntry(
                    unit=unit_read,
                    lessons=lesson_reads,
                    assets=assets,
                )
            )

        cursor = max(cursor_candidates) if cursor_candidates else (since if since is not None else datetime.now(tz=UTC))

        deleted_unit_ids: list[str] = []
        deleted_lesson_ids: list[str] = []
        if include_deleted:
            deleted_unit_ids = []
            deleted_lesson_ids = []

        return UnitSyncResponse(
            units=entries,
            deleted_unit_ids=deleted_unit_ids,
            deleted_lesson_ids=deleted_lesson_ids,
            cursor=cursor,
        )


__all__ = ["SyncHandler"]
