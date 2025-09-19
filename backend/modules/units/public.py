"""
Units Module - Public Interface (Shim)

Thin compatibility layer that forwards to the consolidated Content module.
This file exists temporarily during the migration away from a standalone
`units` module. Do not add functionality here.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from modules.content.public import ContentProvider, content_provider
from modules.content.service import ContentService


# Re-export DTOs from ContentService for response/request models
UnitRead = ContentService.UnitRead
UnitCreate = ContentService.UnitCreate


class SetLessonOrder(BaseModel):
    lesson_ids: list[str] = Field(default_factory=list)


class UnitsProvider(Protocol):
    def get(self, unit_id: str) -> UnitRead | None: ...
    def list(self, limit: int = 100, offset: int = 0) -> list[UnitRead]: ...
    def create(self, data: UnitCreate) -> UnitRead: ...
    def set_lesson_order(self, unit_id: str, order: SetLessonOrder) -> UnitRead: ...


class _UnitsShim:
    """Adapter that forwards unit operations to ContentProvider."""

    def __init__(self, content: ContentProvider) -> None:
        self._content = content

    def get(self, unit_id: str) -> UnitRead | None:
        return self._content.get_unit(unit_id)

    def list(self, limit: int = 100, offset: int = 0) -> list[UnitRead]:
        return self._content.list_units(limit=limit, offset=offset)

    def create(self, data: UnitCreate) -> UnitRead:
        return self._content.create_unit(data)

    def set_lesson_order(self, unit_id: str, order: SetLessonOrder) -> UnitRead:
        return self._content.set_unit_lesson_order(unit_id, order.lesson_ids)


def units_provider(session: Session) -> UnitsProvider:
    # Build and return the shim backed by the consolidated content service
    return _UnitsShim(content_provider(session))


__all__ = [
    "SetLessonOrder",
    "UnitCreate",
    "UnitRead",
    "UnitsProvider",
    "units_provider",
]
