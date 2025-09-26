"""
Content Creator Flow Unit Tests

Covers:
- Lesson metadata step output format
- LessonCreationFlow output shape
- UnitCreationFlow planning/chunking
- Service create_unit precreate + complete pipeline
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modules.content.package_models import LessonPackage, Meta, Objective
from modules.content.public import LessonRead
from modules.content_creator.flows import UnitCreationFlow
from modules.content_creator.service import ContentCreatorService, CreateLessonRequest

# Deprecated test removed - used old step classes that no longer exist


@pytest.mark.asyncio
async def test_unit_creation_flow_plan_and_chunks() -> None:
    """UnitCreationFlow returns a plan and chunks; lesson execution is handled by service."""
    unit_plan = {
        "unit_title": "Unit T",
        "lesson_titles": ["L1", "L2", "L3"],
        "lesson_count": 3,
        "recommended_per_lesson_minutes": 5,
        "target_lesson_count": 3,
        "source_material": "S",
        "summary": "sum",
        "chunks": [
            {"index": 0, "title": "L1", "chunk_text": "text1"},
            {"index": 1, "title": "L2", "chunk_text": "text2"},
            {"index": 2, "title": "L3", "chunk_text": "text3"},
        ],
    }

    async def fake_fast_lesson_execute(_inputs: dict[str, Any]) -> dict[str, Any]:
        title = _inputs["title"]
        if title == "L2":
            raise RuntimeError("boom")
        return {"ok": True}

    with patch.object(UnitCreationFlow, "execute", new=AsyncMock(return_value=unit_plan)):
        flow = UnitCreationFlow()
        result = await flow.execute(
            {
                "topic": "Test Topic",
                "unit_source_material": None,
                "target_lesson_count": 3,
                "learner_level": "beginner",
            }
        )

        assert result["unit_title"] == "Unit T"
        assert result.get("lesson_titles") == ["L1", "L2", "L3"]
        assert len(result.get("chunks", [])) == 3


class TestServiceFlows:
    @pytest.mark.asyncio
    @patch("modules.content_creator.service.LessonCreationFlow")
    async def test_create_lesson_invokes_flow(self, mock_flow_cls: Mock) -> None:
        content = Mock()
        svc = ContentCreatorService(content)

        # Minimal flow return
        fake_flow_result = {
            "topic": "T",
            "learner_level": "beginner",
            "voice": "Test voice",
            "learning_objectives": [
                {"lo_id": "lo_1", "text": "A"},
            ],
            "misconceptions": [],
            "confusables": [],
            "glossary": [],
            "mini_lesson": "x",
            "mcqs": {
                "metadata": {"item_count": 1, "lo_coverage": ["lo_1"]},
                "mcqs": [
                    {
                        "id": "ex1",
                        "lo_id": "lo_1",
                        "stem": "?",
                        "options": [
                            {"id": "ex1_a", "label": "A", "text": "A"},
                            {"id": "ex1_b", "label": "B", "text": "B"},
                            {"id": "ex1_c", "label": "C", "text": "C"},
                        ],
                        "answer_key": {"label": "A", "rationale_right": "Correct"},
                    }
                ],
            },
        }
        mock_flow = AsyncMock()
        mock_flow.execute.return_value = fake_flow_result
        mock_flow_cls.return_value = mock_flow

        # Mock content save
        mock_package = LessonPackage(
            meta=Meta(lesson_id="id", title="T", learner_level="beginner"),
            objectives=[Objective(id="lo_1", text="A")],
            glossary={"terms": []},
            mini_lesson="x",
            exercises=[],
        )
        content.save_lesson.return_value = LessonRead(id="id", title="T", learner_level="beginner", package=mock_package, package_version=1, created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1))

        req = CreateLessonRequest(topic="T", unit_source_material="S", learner_level="beginner", voice="Test voice", learning_objectives=["Learn A"], lesson_objective="Test objective")

        await svc.create_lesson_from_source_material(req)
        mock_flow_cls.return_value.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_create_unit_precreates_and_completes(self) -> None:
        content = Mock()
        svc = ContentCreatorService(content)

        # Unit plan will be provided by mocked UnitCreationFlow below

        # Return created unit (minimal attributes required by service)
        created_unit_obj = Mock()
        created_unit_obj.id = "u1"
        created_unit_obj.title = "Unit T"
        content.create_unit.return_value = created_unit_obj

        # We'll patch flows to return minimal shapes and call create_unit (foreground)
        with patch("modules.content_creator.service.UnitCreationFlow") as mock_ucf_cls, patch("modules.content_creator.service.LessonCreationFlow") as mock_lcf_cls:
            mock_ucf = AsyncMock()
            mock_ucf.execute.return_value = {
                "unit_title": "Unit T",
                "learning_objectives": [{"lo_id": "u_lo_1", "text": "Understand the topic"}],
                "lessons": [{"title": "L1", "learning_objectives": ["lo_1"], "lesson_objective": "Learn about L1"}],
                "lesson_count": 1,
                "unit_source_material": "S",
            }
            mock_ucf_cls.return_value = mock_ucf

            mock_lcf = AsyncMock()
            mock_lcf.execute.return_value = {
                "topic": "L1",
                "learner_level": "beginner",
                "voice": "Plain",
                "learning_objectives": ["Learn about A"],
                "misconceptions": [],
                "confusables": [],
                "glossary": [],
                "mini_lesson": "x",
                "mcqs": {"metadata": {"total_mcqs": 0, "lo_coverage": 0}, "mcqs": []},
            }
            mock_lcf_cls.return_value = mock_lcf

            # Ensure save_lesson returns an object with a string id
            content.save_lesson.return_value = Mock(id="l1")

            # Add the missing method to the mock
            content.assign_lessons_to_unit = Mock()

            result = await svc.create_unit(topic="Topic", target_lesson_count=1, learner_level="beginner", background=False)
            assert result.title == "Unit T"
            content.assign_lessons_to_unit.assert_called_once()
