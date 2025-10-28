from __future__ import annotations

from datetime import datetime
import uuid

from ..repo import ContentRepo
from .dtos import UnitSessionRead


class SessionHandler:
    """Handles unit session lifecycle events."""

    def __init__(self, repo: ContentRepo) -> None:
        self.repo = repo

    async def get_or_create_unit_session(self, user_id: str, unit_id: str) -> UnitSessionRead:
        existing = await self.repo.get_unit_session(user_id=user_id, unit_id=unit_id)
        if existing:
            return UnitSessionRead.model_validate(existing)

        from ..learning_session.models import UnitSessionModel  # noqa: PLC0415

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
        return UnitSessionRead.model_validate(created)

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
        model = await self.repo.get_unit_session(user_id=user_id, unit_id=unit_id)
        if not model:
            from ..learning_session.models import UnitSessionModel  # noqa: PLC0415

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

        if last_lesson_id:
            model.last_lesson_id = last_lesson_id
        if completed_lesson_id:
            existing = set(model.completed_lesson_ids or [])
            existing.add(completed_lesson_id)
            model.completed_lesson_ids = list(existing)

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
        return UnitSessionRead.model_validate(model)


__all__ = ["SessionHandler"]
