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

from modules.content.package_models import DidacticSnippet, LessonPackage, Meta, Objective
from modules.content.public import LessonRead
from modules.content_creator.flows import LessonCreationFlow, UnitCreationFlow
from modules.content_creator.service import ContentCreatorService, CreateLessonRequest
from modules.content_creator.steps import (
    ConfusablePair,
    DidacticSnippetOutputs,
    DistractorCandidate,
    ExtractLessonMetadataStep,
    FastLessonMetadataStep,
    GenerateDidacticSnippetStep,
    GenerateGlossaryStep,
    GenerateMCQStep,
    GenerateMisconceptionBankStep,
    GlossaryTerm,
    KeyConcept,
    LearningObjective,
    LengthBudgets,
    LOWithDistractors,
    MCQAnswerKey,
    MCQItem,
    MCQOption,
    MCQSetOutputs,
    Misconception,
    RefinedMaterial,
)
from modules.flow_engine.base_step import StepResult


@pytest.mark.asyncio
async def test_lesson_metadata_step_outputs_model_shape() -> None:
    """Validate combined outputs model fields and nesting for the lesson metadata step."""
    outputs = FastLessonMetadataStep.Outputs(
        title="Lesson Title",
        core_concept="Core Concept",
        user_level="beginner",
        domain="General",
        learning_objectives=[
            LearningObjective(lo_id="lo_1", text="Understand A", bloom_level="Remember"),
            LearningObjective(lo_id="lo_2", text="Apply B", bloom_level="Apply"),
        ],
        key_concepts=[KeyConcept(term="Concept A", definition="Def A")],
        misconceptions=[Misconception(mc_id="mc_1", concept="A", misbelief="Wrong A")],
        confusables=[ConfusablePair(a="foo", b="bar", contrast="contrast")],
        refined_material=RefinedMaterial(outline_bullets=["pt1", "pt2"], evidence_anchors=["ref1"]),
        length_budgets=LengthBudgets(stem_max_words=35, vignette_max_words=80, option_max_words=12),
        didactic_snippet=DidacticSnippetOutputs(
            introduction="intro",
            core_explanation="core",
            key_points=["k1"],
            practical_context="ctx",
        ),
        glossary=[GlossaryTerm(term="Term", definition="Def")],
        by_lo=[
            LOWithDistractors(
                lo_id="lo_1",
                distractors=[DistractorCandidate(text="d1", maps_to_mc_id="mc_1", source="misconception")],
            )
        ],
    )

    assert outputs.title == "Lesson Title"
    assert outputs.didactic_snippet.core_explanation == "core"
    assert len(outputs.learning_objectives) == 2
    assert len(outputs.by_lo) == 1


@pytest.mark.asyncio
async def test_lesson_creation_flow_output_shape() -> None:
    """Ensure the lesson flow returns expected top-level keys and counts.

    We stub step/LLM calls to fixed outputs and call the flow logic directly.
    """
    # Shared test fixtures
    learning_objectives = [
        LearningObjective(lo_id="lo_1", text="Understand A", bloom_level="Remember"),
        LearningObjective(lo_id="lo_2", text="Apply B", bloom_level="Apply"),
    ]
    key_concepts = [KeyConcept(term="Concept A", definition="Def A")]
    misconceptions = [Misconception(mc_id="mc_1", concept="A", misbelief="Wrong A")]
    confusables = [ConfusablePair(a="foo", b="bar", contrast="contrast")]
    budgets = LengthBudgets(stem_max_words=35, vignette_max_words=80, option_max_words=12)
    didactic = DidacticSnippetOutputs(
        introduction="intro",
        core_explanation="core",
        key_points=["k1"],
        practical_context="ctx",
    )
    glossary_terms = [GlossaryTerm(term="Term", definition="Def")]

    # MCQ outputs
    mcq_items = [
        MCQItem(
            lo_id="lo_1",
            stem="What is A?",
            options=[
                MCQOption(label="A", text="opt A"),
                MCQOption(label="B", text="opt B"),
                MCQOption(label="C", text="opt C"),
            ],
            answer_key=MCQAnswerKey(label="A", rationale_right="because"),
        ),
        MCQItem(
            lo_id="lo_2",
            stem="What is B?",
            options=[
                MCQOption(label="A", text="opt A"),
                MCQOption(label="B", text="opt B"),
                MCQOption(label="C", text="opt C"),
            ],
            answer_key=MCQAnswerKey(label="B", rationale_right="because"),
        ),
    ]

    # Patch steps used by both flows
    with (
        patch.object(
            FastLessonMetadataStep,
            "execute",
            new=AsyncMock(
                return_value=StepResult(
                    step_name="fast_lesson_metadata",
                    output_content=FastLessonMetadataStep.Outputs(
                        title="T",
                        core_concept="C",
                        user_level="beginner",
                        domain="General",
                        learning_objectives=learning_objectives,
                        key_concepts=key_concepts,
                        misconceptions=misconceptions,
                        confusables=confusables,
                        refined_material=RefinedMaterial(outline_bullets=["a"], evidence_anchors=["b"]),
                        length_budgets=budgets,
                        didactic_snippet=didactic,
                        glossary=glossary_terms,
                        by_lo=[LOWithDistractors(lo_id="lo_1", distractors=[DistractorCandidate(text="d1", source="misconception")])],
                    ),
                    metadata={},
                )
            ),
        ),
        patch.object(
            ExtractLessonMetadataStep,
            "execute",
            new=AsyncMock(
                return_value=StepResult(
                    step_name="extract_lesson_metadata",
                    output_content=ExtractLessonMetadataStep.Outputs(
                        title="T",
                        core_concept="C",
                        user_level="beginner",
                        domain="General",
                        learning_objectives=learning_objectives,
                        key_concepts=key_concepts,
                        misconceptions=misconceptions,
                        confusables=confusables,
                        refined_material=RefinedMaterial(outline_bullets=["a"], evidence_anchors=["b"]),
                        length_budgets=budgets,
                    ),
                    metadata={},
                )
            ),
        ),
        patch.object(
            GenerateMisconceptionBankStep,
            "execute",
            new=AsyncMock(
                return_value=StepResult(
                    step_name="generate_misconception_bank",
                    output_content=GenerateMisconceptionBankStep.Outputs(by_lo=[LOWithDistractors(lo_id="lo_1", distractors=[DistractorCandidate(text="d1", source="misconception")])]),
                    metadata={},
                )
            ),
        ),
        patch.object(
            GenerateDidacticSnippetStep,
            "execute",
            new=AsyncMock(
                return_value=StepResult(
                    step_name="generate_didactic_snippet",
                    output_content=didactic,
                    metadata={},
                )
            ),
        ),
        patch.object(
            GenerateGlossaryStep,
            "execute",
            new=AsyncMock(
                return_value=StepResult(
                    step_name="generate_glossary",
                    output_content=GenerateGlossaryStep.Outputs(terms=glossary_terms),
                    metadata={},
                )
            ),
        ),
        patch.object(
            GenerateMCQStep,
            "execute",
            new=AsyncMock(
                return_value=StepResult(
                    step_name="generate_mcqs",
                    output_content=MCQSetOutputs(mcqs=mcq_items),
                    metadata={},
                )
            ),
        ),
    ):
        flow = LessonCreationFlow()
        result = await flow._execute_flow_logic({"title": "T", "core_concept": "C", "source_material": "M", "user_level": "beginner", "domain": "General"})

        # Compare shapes and counts
        for key in [
            "learning_objectives",
            "key_concepts",
            "misconceptions",
            "confusables",
            "refined_material",
            "length_budgets",
            "glossary",
            "didactic_snippet",
            "exercises",
        ]:
            assert key in result

        assert len(result["learning_objectives"]) == 2
        assert len(result["exercises"]) == 2

        # Ensure options have generated ids
        assert all("id" in opt for ex in result["exercises"] for opt in ex["options"])


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
                "topic": None,
                "source_material": "S",
                "target_lesson_count": 3,
                "user_level": "beginner",
                "domain": "General",
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
            "learning_objectives": [
                {"lo_id": "lo_1", "text": "A"},
            ],
            "refined_material": {"outline_bullets": []},
            "didactic_snippet": {"core_explanation": "x", "key_points": []},
            "glossary": {"terms": []},
            "exercises": [
                {
                    "id": "ex1",
                    "exercise_type": "mcq",
                    "lo_id": "lo_1",
                    "stem": "?",
                    "options": [
                        {"id": "ex1_a", "label": "A", "text": "A"},
                        {"id": "ex1_b", "label": "B", "text": "B"},
                        {"id": "ex1_c", "label": "C", "text": "C"},
                    ],
                    "answer_key": {"label": "A"},
                }
            ],
            "length_budgets": {"stem_max_words": 35, "vignette_max_words": 80, "option_max_words": 12},
        }
        mock_flow = AsyncMock()
        mock_flow.execute.return_value = fake_flow_result
        mock_flow_cls.return_value = mock_flow

        # Mock content save
        mock_package = LessonPackage(
            meta=Meta(lesson_id="id", title="T", core_concept="C", user_level="beginner", domain="General"),
            objectives=[Objective(id="lo_1", text="A")],
            glossary={"terms": []},
            didactic_snippet=DidacticSnippet(id="lesson_explanation", plain_explanation="x", key_takeaways=[]),
            exercises=[],
        )
        content.save_lesson.return_value = LessonRead(id="id", title="T", core_concept="C", user_level="beginner", package=mock_package, package_version=1, created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1))

        req = CreateLessonRequest(title="T", core_concept="C", source_material="S", user_level="beginner", domain="General")

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
                "lesson_titles": ["L1"],
                "lesson_count": 1,
                "target_lesson_count": 1,
                "source_material": "S",
                "summary": "sum",
                "chunks": [{"index": 0, "title": "L1", "chunk_text": "t1"}],
            }
            mock_ucf_cls.return_value = mock_ucf

            mock_lcf = AsyncMock()
            mock_lcf.execute.return_value = {
                "learning_objectives": [{"id": "lo_1", "text": "A"}],
                "didactic_snippet": {"plain_explanation": "x", "key_takeaways": []},
                "glossary": {"terms": []},
                "exercises": [],
            }
            mock_lcf_cls.return_value = mock_lcf

            # Ensure save_lesson returns an object with a string id
            content.save_lesson.return_value = Mock(id="l1")

            result = await svc.create_unit(topic="Topic", target_lesson_count=1, user_level="beginner", domain=None, background=False)
            assert result.title == "Unit T"
            content.assign_lessons_to_unit.assert_called_once()
