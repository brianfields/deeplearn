"""
Units Module - Unit Tests

Tests for UnitsService behavior.
"""

from datetime import datetime
from unittest.mock import Mock

from modules.units.service import SetLessonOrder, UnitCreate, UnitsService


class TestUnitsService:
    def test_create_and_get_unit(self) -> None:
        repo = Mock()
        # Simulate repo.add returning a model-like object
        repo.add.side_effect = lambda m: m
        repo.by_id.side_effect = lambda uid: type("M", (), {"id": uid, "title": "T", "description": None, "difficulty": "beginner", "lesson_order": [], "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()})()

        svc = UnitsService(repo)
        created = svc.create(UnitCreate(title="My Unit"))
        assert created.title == "My Unit"
        assert created.difficulty == "beginner"

        got = svc.get(created.id)
        assert got is not None
        assert got.id == created.id

    def test_set_lesson_order(self) -> None:
        repo = Mock()
        # Simulate update returning an updated model-like object
        repo.update_lesson_order.return_value = type("M", (), {"id": "u1", "title": "T", "description": None, "difficulty": "beginner", "lesson_order": ["l1", "l2"], "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()})()

        svc = UnitsService(repo)
        updated = svc.set_lesson_order("u1", SetLessonOrder(lesson_ids=["l1", "l2"]))
        assert updated.lesson_order == ["l1", "l2"]
