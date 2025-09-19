"""
Units Module - Repository Layer (Deprecated)

Deprecated shim kept temporarily for backward compatibility during migration.
All unit data access has been consolidated into `modules.content.repo`.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from modules.content.models import UnitModel
from modules.content.repo import ContentRepo


class UnitsRepo:
    """Thin adapter over ContentRepo for backward compatibility."""

    def __init__(self, session: Session) -> None:
        self._content = ContentRepo(session)

    # Basic CRUD
    def by_id(self, unit_id: str) -> UnitModel | None:
        return self._content.get_unit_by_id(unit_id)

    def list(self, limit: int = 100, offset: int = 0) -> list[UnitModel]:
        return self._content.list_units(limit=limit, offset=offset)

    def add(self, unit: UnitModel) -> UnitModel:
        return self._content.add_unit(unit)

    def save(self, unit: UnitModel) -> None:
        self._content.save_unit(unit)

    def delete(self, unit_id: str) -> bool:
        return self._content.delete_unit(unit_id)

    # Ordering helpers
    def update_lesson_order(self, unit_id: str, lesson_ids: Iterable[str]) -> UnitModel | None:
        return self._content.update_unit_lesson_order(unit_id, list(lesson_ids))
