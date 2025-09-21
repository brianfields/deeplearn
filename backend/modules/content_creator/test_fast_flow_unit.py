"""
Fast Flow Unit Tests

Covers:
- FastLessonMetadataStep output format
- FastLessonCreationFlow output shape parity with LessonCreationFlow
- FastUnitCreationFlow parallelization and error handling
- Service methods selecting fast vs standard flow via use_fast_flow
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modules.content.package_models import DidacticSnippet, LessonPackage, Meta, Objective
from modules.content.public import LessonRead
from modules.content_creator.service import ContentCreatorService, CreateLessonRequest, LessonCreationResult


@pytest.mark.asyncio
async def test_fast_lesson_metadata_step_outputs_model_shape() -> None:
    """Validate combined outputs model fields and nesting for FastLessonMetadataStep."""
    from modules.content_creator.steps import (
        ConfusablePair,
        DistractorCandidate,
        FastLessonMetadataStep,
        GlossaryTerm,
        KeyConcept,
        LearningObjective,
        LOWithDistractors,
        Misconception,
        RefinedMaterial,
        LengthBudgets,
        DidacticSnippetOutputs,
    )

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
async def test_fast_lesson_creation_flow_output_shape_matches_standard_flow() -> None:
    """Ensure fast and standard flows return comparable top-level keys and counts.

    We stub step/LLM calls to fixed outputs and call the flow logic directly.
    """
    from modules.content_creator.flows import FastLessonCreationFlow, LessonCreationFlow
    from modules.content_creator.steps import (
        FastLessonMetadataStep,
        ExtractLessonMetadataStep,
        GenerateMisconceptionBankStep,
        GenerateDidacticSnippetStep,
        GenerateGlossaryStep,
        GenerateMCQStep,
        LengthBudgets,
        LearningObjective,
        KeyConcept,
        Misconception,
        ConfusablePair,
        RefinedMaterial,
        GlossaryTerm,
        DidacticSnippetOutputs,
        LOWithDistractors,
        DistractorCandidate,
        MCQItem,
        MCQOption,
        MCQAnswerKey,
        MCQSetOutputs,
    )
    from modules.flow_engine.base_step import StepResult

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
                    output_content=GenerateMisconceptionBankStep.Outputs(
                        by_lo=[LOWithDistractors(lo_id="lo_1", distractors=[DistractorCandidate(text="d1", source="misconception")])]
                    ),
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
        fast_flow = FastLessonCreationFlow()
        std_flow = LessonCreationFlow()

        fast_result = await fast_flow._execute_flow_logic(
            {"title": "T", "core_concept": "C", "source_material": "M", "user_level": "beginner", "domain": "General"}
        )
        std_result = await std_flow._execute_flow_logic(
            {"title": "T", "core_concept": "C", "source_material": "M", "user_level": "beginner", "domain": "General"}
        )

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
            assert key in fast_result
            assert key in std_result

        assert len(fast_result["learning_objectives"]) == len(std_result["learning_objectives"]) == 2
        assert len(fast_result["exercises"]) == len(std_result["exercises"]) == 2

        # Ensure options have generated ids in both flows
        assert all("id" in opt for ex in fast_result["exercises"] for opt in ex["options"])  # type: ignore[call-arg]
        assert all("id" in opt for ex in std_result["exercises"] for opt in ex["options"])  # type: ignore[call-arg]


@pytest.mark.asyncio
async def test_fast_unit_creation_flow_parallel_and_error_handling() -> None:
    """FastUnitCreationFlow should continue on individual lesson failures and preserve order."""
    from modules.content_creator.flows import FastUnitCreationFlow, UnitCreationFlow, FastLessonCreationFlow

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

    with (
        patch.object(UnitCreationFlow, "execute", new=AsyncMock(return_value=unit_plan)),
        patch.object(FastLessonCreationFlow, "execute", new=AsyncMock(side_effect=fake_fast_lesson_execute)),
    ):
        flow = FastUnitCreationFlow()
        result = await flow._execute_flow_logic({
            "topic": None,
            "source_material": "S",
            "target_lesson_count": 3,
            "user_level": "beginner",
            "domain": "General",
            "max_parallel_lessons": 2,
        })

        assert result["unit_title"] == "Unit T"
        lessons = result.get("lessons", [])
        # One failure => only 2 lessons produced
        assert len(lessons) == 2
        # Order preserved by index
        assert [l["title"] for l in lessons] == ["L1", "L3"]


class TestServiceFastFlag:
    @pytest.mark.asyncio
    @patch("modules.content_creator.service.FastLessonCreationFlow")
    @patch("modules.content_creator.service.LessonCreationFlow")
    async def test_create_lesson_respects_use_fast_flow_flag(
        self, mock_std_flow_cls: Mock, mock_fast_flow_cls: Mock
    ) -> None:
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
                {"id": "ex1", "exercise_type": "mcq", "lo_id": "lo_1", "stem": "?", "options": [
                    {"id": "ex1_a", "label": "A", "text": "A"},
                    {"id": "ex1_b", "label": "B", "text": "B"},
                    {"id": "ex1_c", "label": "C", "text": "C"},
                ], "answer_key": {"label": "A"}}
            ],
            "length_budgets": {"stem_max_words": 35, "vignette_max_words": 80, "option_max_words": 12},
        }
        mock_fast_flow = AsyncMock()
        mock_fast_flow.execute.return_value = fake_flow_result
        mock_fast_flow_cls.return_value = mock_fast_flow

        mock_std_flow = AsyncMock()
        mock_std_flow.execute.return_value = fake_flow_result
        mock_std_flow_cls.return_value = mock_std_flow

        # Mock content save
        mock_package = LessonPackage(
            meta=Meta(lesson_id="id", title="T", core_concept="C", user_level="beginner", domain="General"),
            objectives=[Objective(id="lo_1", text="A")],
            glossary={"terms": []},
            didactic_snippet=DidacticSnippet(id="lesson_explanation", plain_explanation="x", key_takeaways=[]),
            exercises=[],
        )
        content.save_lesson.return_value = LessonRead(
            id="id", title="T", core_concept="C", user_level="beginner", package=mock_package, package_version=1,
            created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1)
        )

        req = CreateLessonRequest(title="T", core_concept="C", source_material="S", user_level="beginner", domain="General")

        # Fast path
        await svc.create_lesson_from_source_material(req, use_fast_flow=True)
        mock_fast_flow.execute.assert_awaited()
        mock_std_flow.execute.assert_not_called()

        # Standard path
        mock_fast_flow.execute.reset_mock()
        mock_std_flow.execute.reset_mock()
        await svc.create_lesson_from_source_material(req, use_fast_flow=False)
        mock_std_flow.execute.assert_awaited()
        mock_fast_flow.execute.assert_not_called()

    @pytest.mark.asyncio
    @patch("modules.content_creator.service.UnitCreationFlow")
    async def test_create_unit_sets_flow_type_and_parallelizes(self, mock_unit_flow_cls: Mock) -> None:
        content = Mock()
        svc = ContentCreatorService(content)

        # Unit plan with 3 chunks
        mock_unit_flow = AsyncMock()
        mock_unit_flow.execute.return_value = {
            "unit_title": "Unit T",
            "lesson_titles": ["L1", "L2", "L3"],
            "lesson_count": 3,
            "target_lesson_count": 3,
            "source_material": "S",
            "summary": "sum",
            "chunks": [
                {"index": 0, "title": "L1", "chunk_text": "t1"},
                {"index": 1, "title": "L2", "chunk_text": "t2"},
                {"index": 2, "title": "L3", "chunk_text": "t3"},
            ],
        }
        mock_unit_flow_cls.return_value = mock_unit_flow

        # Return created unit (minimal attributes required by service)
        created_unit_obj = Mock()
        created_unit_obj.id = "u1"
        created_unit_obj.title = "Unit T"
        content.create_unit.return_value = created_unit_obj

        # Stub lesson creation to simulate parallel workers
        async def fake_create_lesson(_req: CreateLessonRequest, *, use_fast_flow: bool = False) -> LessonCreationResult:  # noqa: FBT002
            return LessonCreationResult(
                lesson_id=f"lesson-{_req.title}",
                title=_req.title,
                package_version=1,
                objectives_count=1,
                glossary_terms_count=0,
                mcqs_count=1,
            )

        svc.create_lesson_from_source_material = AsyncMock(side_effect=fake_create_lesson)  # type: ignore[method-assign]

        # Fast flow: sets flow_type fast and parallelizes
        topic_req = ContentCreatorService.CreateUnitFromTopicRequest(topic="Topic", target_lesson_count=3, user_level="beginner", use_fast_flow=True)
        result_fast = await svc.create_unit_from_topic(topic_req)
        assert result_fast.title == "Unit T"
        # flow_type passed to content.create_unit
        args, _ = content.create_unit.call_args
        assert args[0].flow_type == "fast"  # type: ignore[index]
        # lessons assigned
        content.assign_lessons_to_unit.assert_called_once()

        content.create_unit.reset_mock()
        content.assign_lessons_to_unit.reset_mock()

        # Standard flow: sets flow_type standard
        topic_req_std = ContentCreatorService.CreateUnitFromTopicRequest(topic="Topic", target_lesson_count=3, user_level="beginner", use_fast_flow=False)
        result_std = await svc.create_unit_from_topic(topic_req_std)
        assert result_std.title == "Unit T"
        args2, _ = content.create_unit.call_args
        assert args2[0].flow_type == "standard"  # type: ignore[index]
