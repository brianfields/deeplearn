"""
Units Module - Service Layer (Deprecated)

Deprecated shim that forwards to the consolidated Content module.
Prefer using `modules.content.public` from other modules.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from modules.content.public import ContentProvider


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

    def __init__(self, content: ContentProvider) -> None:
        self.content = content

    def get(self, unit_id: str) -> UnitRead | None:
        return self.content.get_unit(unit_id)  # type: ignore[return-value]

    def list(self, limit: int = 100, offset: int = 0) -> list[UnitRead]:
        return self.content.list_units(limit=limit, offset=offset)  # type: ignore[return-value]

    def create(self, data: UnitCreate) -> UnitRead:
        return self.content.create_unit(data)  # type: ignore[return-value,arg-type]

    def set_lesson_order(self, unit_id: str, order: SetLessonOrder) -> UnitRead:
        return self.content.set_unit_lesson_order(unit_id, order.lesson_ids)  # type: ignore[return-value]
