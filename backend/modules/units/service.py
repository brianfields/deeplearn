"""
Units Module - Service Layer (Deprecated)

Deprecated shim that forwards to the consolidated Content module.
Prefer using `modules.content.public` from other modules.
"""

from __future__ import annotations

from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from modules.content.service import ContentService
from .repo import UnitsRepo


class UnitRead(BaseModel):
    id: str
    title: str
    description: str | None = None
    difficulty: str
    lesson_order: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnitCreate(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    difficulty: str = "beginner"
    lesson_order: list[str] = Field(default_factory=list)


class SetLessonOrder(BaseModel):
    lesson_ids: list[str] = Field(default_factory=list)


class UnitsService:
    """Adapter service forwarding to consolidated content service via repo shim."""

    def __init__(self, repo: UnitsRepo) -> None:
        self.repo = repo

    def get(self, unit_id: str) -> UnitRead | None:
        u = self.repo.by_id(unit_id)
        return UnitRead.model_validate(u) if u else None

    def list(self, limit: int = 100, offset: int = 0) -> list[UnitRead]:
        arr = self.repo.list(limit=limit, offset=offset)
        return [UnitRead.model_validate(u) for u in arr]

    def create(self, data: UnitCreate) -> UnitRead:
        # Delegate creation to content model via repo shim
        # Reuse ContentService semantics for timestamps, id generation handled here
        unit_id = data.id or str(uuid.uuid4())
        created = self.repo.add(
            # Create a light-weight object compatible with repo.add (UnitModel in content)
            # We cannot import UnitModel directly here to keep shim minimal
            # The repo shim handles actual persistence
            type(
                "UnitModelProxy",
                (),
                {
                    "id": unit_id,
                    "title": data.title,
                    "description": data.description,
                    "difficulty": data.difficulty,
                    "lesson_order": list(data.lesson_order or []),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )()
        )
        return UnitRead.model_validate(created)

    def set_lesson_order(self, unit_id: str, order: SetLessonOrder) -> UnitRead:
        updated = self.repo.update_lesson_order(unit_id, order.lesson_ids)
        if not updated:
            raise ValueError("Unit not found")
        return UnitRead.model_validate(updated)
