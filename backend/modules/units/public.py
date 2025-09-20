"""
Units Module - Public Interface (Shim)

Thin compatibility layer that forwards to the consolidated Content module.
This file exists temporarily during the migration away from a standalone
`units` module. Do not add functionality here.
"""

from __future__ import annotations

from typing import Protocol, cast

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from modules.content.public import UnitCreate, UnitRead, content_provider

from .service import UnitsService

# DTOs imported directly from content.public


class SetLessonOrder(BaseModel):
    lesson_ids: list[str] = Field(default_factory=list)


class UnitsProvider(Protocol):
    def get(self, unit_id: str) -> UnitRead | None: ...
    def list(self, limit: int = 100, offset: int = 0) -> list[UnitRead]: ...
    def create(self, data: UnitCreate) -> UnitRead: ...
    def set_lesson_order(self, unit_id: str, order: SetLessonOrder) -> UnitRead: ...


def units_provider(session: Session) -> UnitsProvider:
    # Build and return the service backed by the consolidated content service
    return cast(UnitsProvider, UnitsService(content_provider(session)))  # type: ignore[return-value]


__all__ = [
    "SetLessonOrder",
    "UnitCreate",
    "UnitRead",
    "UnitsProvider",
    "units_provider",
]
