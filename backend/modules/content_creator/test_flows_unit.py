"""
Content Creator Flow Unit Tests

Covers:
- Lesson metadata step output format
- LessonCreationFlow output shape
- UnitCreationFlow planning/chunking
- Service create_unit precreate + complete pipeline
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any
from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest

from modules.content_creator.flows import (
    LessonCreationFlow,
    LessonPodcastFlow,
    PodcastLessonInput,
    UnitCreationFlow,
    UnitPodcastFlow,
)
from modules.content_creator.podcast import PodcastLesson, UnitPodcast
from modules.content_creator.service import ContentCreatorService

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
                "source_material": None,
                "target_lesson_count": 3,
                "learner_level": "beginner",
            }
        )

        assert result["unit_title"] == "Unit T"
        assert result.get("lesson_titles") == ["L1", "L2", "L3"]
        assert len(result.get("chunks", [])) == 3


@pytest.mark.asyncio
@patch("modules.content_creator.flows.GenerateQuizFromExercisesStep")
@patch("modules.content_creator.flows.GenerateTransferExercisesStep")
@patch("modules.content_creator.flows.GenerateComprehensionExercisesStep")
@patch("modules.content_creator.flows.AnnotateConceptGlossaryStep")
@patch("modules.content_creator.flows.ExtractConceptGlossaryStep")
@patch("modules.content_creator.flows.ExtractLessonMetadataStep")
async def test_lesson_creation_flow_runs_concept_pipeline(
    mock_extract_lesson_step: Mock,
    mock_extract_concepts_step: Mock,
    mock_annotate_step: Mock,
    mock_comprehension_step: Mock,
    mock_transfer_step: Mock,
    mock_quiz_step: Mock,
) -> None:
    """Lesson creation flow should orchestrate the concept-driven pipeline."""

    class _FakeModel:
        def __init__(self, **payload: Any) -> None:
            self.__dict__.update(payload)

        def model_dump(self) -> dict[str, Any]:
            return dict(self.__dict__)

    lesson_md = _FakeModel(
        topic="Lesson",
        learner_level="beginner",
        voice="Guide",
        learning_objectives=["Explain"],
        learning_objective_ids=["lo_1"],
        lesson_source_material="Scaffolded excerpt",
        mini_lesson="Body",
    )
    mock_extract_lesson_step.return_value.execute = AsyncMock(
        return_value=SimpleNamespace(output_content=lesson_md)
    )

    concept_items = [_FakeModel(id="c1", term="Mean", slug="mean", definition="Avg", aliases=[], example_from_source=None, source_span=None, related_terms=[], aligned_learning_objectives=["lo_1"])]
    mock_extract_concepts_step.return_value.execute = AsyncMock(
        return_value=SimpleNamespace(output_content=_FakeModel(concepts=concept_items, meta=_FakeModel(total_concepts=1)))
    )

    refined_concepts = [
        _FakeModel(
            id="c1",
            term="Mean",
            slug="mean",
            aliases=[],
            definition="Average",
            example_from_source=None,
            source_span=None,
            category="Technical",
            centrality=5,
            distinctiveness=4,
            transferability=4,
            clarity=5,
            assessment_potential=5,
            cognitive_domain="Knowledge",
            difficulty_potential={"min_level": "Recall", "max_level": "Comprehension"},
            learning_role="Core",
            aligned_learning_objectives=["lo_1"],
            canonical_answer="Mean",
            accepted_phrases=["average"],
            answer_type="closed",
            closed_answer=True,
            example_exercise_stem="Define mean",
            plausible_distractors=["median"],
            misconception_note=None,
            contrast_with=["median"],
            related_concepts=["median"],
            review_notes=None,
            source_reference=None,
            version="v1",
        )
    ]
    mock_annotate_step.return_value.execute = AsyncMock(
        return_value=SimpleNamespace(output_content=_FakeModel(refined_concepts=refined_concepts, meta=_FakeModel(total_retained=1)))
    )

    comprehension_exercises = [
        _FakeModel(
            id="ex-comp-sa-001",
            exercise_category="comprehension",
            type="short-answer",
            concept_slug="mean",
            concept_term="Mean",
            stem="Define the mean",
            canonical_answer="Mean",
            acceptable_answers=["average"],
            rationale_right="Explains the concept",
            wrong_answers=[{"answer": "Median", "rationale_wrong": "Different measure"}],
            answer_type="closed",
            cognitive_level="Recall",
            difficulty="easy",
            aligned_learning_objective="lo_1",
        )
    ]
    mock_comprehension_step.return_value.execute = AsyncMock(
        return_value=SimpleNamespace(output_content=_FakeModel(exercises=comprehension_exercises, meta=_FakeModel(exercise_category="comprehension")))
    )

    transfer_exercises = [
        _FakeModel(
            id="ex-trans-mc-001",
            exercise_category="transfer",
            type="multiple-choice",
            concept_slug="mean",
            concept_term="Mean",
            stem="Which concept fits?",
            options=[{"label": "A", "text": "Mean", "rationale_wrong": None}],
            answer_key={"label": "A", "rationale_right": "Matches scenario"},
            cognitive_level="Application",
            difficulty="medium",
            aligned_learning_objective="lo_1",
        )
    ]
    mock_transfer_step.return_value.execute = AsyncMock(
        return_value=SimpleNamespace(output_content=_FakeModel(exercises=transfer_exercises, meta=_FakeModel(exercise_category="transfer")))
    )

    quiz_meta = _FakeModel(
        quiz_type="Formative",
        total_items=2,
        difficulty_distribution_target={"easy": 0.5, "medium": 0.5, "hard": 0.0},
        difficulty_distribution_actual={"easy": 0.5, "medium": 0.5, "hard": 0.0},
        cognitive_mix_target={"Recall": 0.5, "Application": 0.5},
        cognitive_mix_actual={"Recall": 0.5, "Application": 0.5},
        coverage_by_LO={"lo_1": {"exercise_ids": ["ex-comp-sa-001"], "concepts": ["mean"]}},
        coverage_by_concept={"mean": {"exercise_ids": ["ex-comp-sa-001"], "types": ["short-answer"]}},
        normalizations_applied=[],
        selection_rationale=[],
        gaps_identified=[],
    )
    mock_quiz_step.return_value.execute = AsyncMock(
        return_value=SimpleNamespace(output_content=_FakeModel(quiz=["ex-comp-sa-001", "ex-trans-mc-001"], meta=quiz_meta))
    )

    flow = LessonCreationFlow()
    result = await flow._execute_flow_logic(
        {
            "topic": "Lesson",
            "learner_level": "beginner",
            "voice": "Guide",
            "learning_objectives": ["Explain"],
            "learning_objective_ids": ["lo_1"],
            "lesson_objective": "Explain it",
            "source_material": "Body",
        }
    )

    mock_extract_concepts_step.return_value.execute.assert_awaited_once()
    mock_annotate_step.return_value.execute.assert_awaited_once()
    mock_comprehension_step.return_value.execute.assert_awaited_once()
    mock_transfer_step.return_value.execute.assert_awaited_once()
    mock_quiz_step.return_value.execute.assert_awaited_once()

    assert result["concept_glossary"][0]["term"] == "Mean"
    assert len(result["exercise_bank"]) == 2
    assert result["quiz"] == ["ex-comp-sa-001", "ex-trans-mc-001"]
    assert result["quiz_metadata"]["total_items"] == 2


@pytest.mark.asyncio
@patch("modules.content_creator.flows.GenerateLessonPodcastTranscriptStep")
@patch("modules.content_creator.flows.SynthesizePodcastAudioStep")
async def test_lesson_podcast_flow_orchestrates_steps(
    mock_audio_step_cls: Mock,
    mock_transcript_step_cls: Mock,
) -> None:
    transcript_step = AsyncMock()
    transcript_step.execute.return_value = SimpleNamespace(output_content="Lesson 1. Title")
    mock_transcript_step_cls.return_value = transcript_step

    audio_step = AsyncMock()
    audio_step.execute.return_value = SimpleNamespace(output_content={"id": "audio-1"})
    mock_audio_step_cls.return_value = audio_step

    flow = LessonPodcastFlow()
    result = await flow._execute_flow_logic(
        {
            "lesson_number": 1,
            "lesson_title": "Title",
            "lesson_objective": "Objective",
            "mini_lesson": "Mini lesson content",
            "voice": "Guide",
        }
    )

    transcript_step.execute.assert_awaited_once()
    audio_step.execute.assert_awaited_once()
    assert result["transcript"] == "Lesson 1. Title"
    assert result["audio"] == {"id": "audio-1"}


@pytest.mark.asyncio
@patch("modules.content_creator.flows.GenerateUnitPodcastTranscriptStep")
@patch("modules.content_creator.flows.SynthesizePodcastAudioStep")
async def test_unit_podcast_flow_uses_intro_prompt(
    mock_audio_step_cls: Mock,
    mock_transcript_step_cls: Mock,
) -> None:
    transcript_step = AsyncMock()
    transcript_step.execute.return_value = SimpleNamespace(output_content="Intro transcript")
    mock_transcript_step_cls.return_value = transcript_step

    audio_step = AsyncMock()
    audio_step.execute.return_value = SimpleNamespace(output_content={"id": "audio-2"})
    mock_audio_step_cls.return_value = audio_step

    lessons = [PodcastLessonInput(title="L1", mini_lesson="Body")]
    flow = UnitPodcastFlow()
    result = await flow._execute_flow_logic(
        {
            "unit_title": "Unit",
            "voice": "Guide",
            "unit_summary": "Summary",
            "lessons": lessons,
        }
    )

    transcript_step.execute.assert_awaited_once_with(
        {
            "unit_title": "Unit",
            "voice": "Guide",
            "unit_summary": "Summary",
            "lessons": lessons,
        }
    )
    audio_step.execute.assert_awaited_once()
    assert result["transcript"] == "Intro transcript"
    assert result["audio"] == {"id": "audio-2"}


class TestServiceFlows:
    @pytest.mark.asyncio
    async def test_create_unit_precreates_and_completes(self) -> None:
        content = AsyncMock()
        podcast_generator = AsyncMock()
        podcast_generator.create_podcast.return_value = UnitPodcast(
            transcript="Narration",
            audio_bytes=b"audio",
            mime_type="audio/mpeg",
            voice="Plain",
            duration_seconds=120,
        )

        # Return created unit (minimal attributes required by service)
        created_unit_obj = Mock()
        created_unit_obj.id = "u1"
        created_unit_obj.title = "Unit T"
        content.create_unit.return_value = created_unit_obj

        # Set up all async mocks before creating service
        content.save_lesson = AsyncMock(return_value=Mock(id="l1"))
        content.assign_lessons_to_unit = AsyncMock()
        content.update_unit_metadata = AsyncMock()
        content.update_unit_status = AsyncMock()
        content.save_unit_podcast_from_bytes = AsyncMock()
        content.save_lesson_podcast_from_bytes = AsyncMock()
        # Mock get_unit_detail with iterable lessons to avoid TypeError in art generation
        mock_lesson = Mock()
        mock_lesson.key_concepts = ["concept1", "concept2"]
        content.get_unit_detail = AsyncMock(return_value=Mock(title="Unit T", description="Description", learning_objectives=[], lessons=[mock_lesson]))
        # Mock create_unit_art to avoid LLM calls

        svc = ContentCreatorService(content, podcast_generator=podcast_generator)
        svc._media_handler.generate_lesson_podcast = AsyncMock(
            return_value=(
                PodcastLesson(title="Lesson 1", mini_lesson="x"),
                SimpleNamespace(
                    transcript="Lesson 1. L1",
                    audio_bytes=b"lesson-audio",
                    mime_type="audio/mpeg",
                    voice="Plain",
                    duration_seconds=150,
                ),
            )
        )
        svc._media_handler.save_lesson_podcast = AsyncMock()
        svc._media_handler.generate_unit_podcast = AsyncMock(
            return_value=SimpleNamespace(
                transcript="Narration",
                audio_bytes=b"audio",
                mime_type="audio/mpeg",
                voice="Plain",
                duration_seconds=120,
            )
        )
        svc._media_handler.save_unit_podcast = AsyncMock()

        # We'll patch flows to return minimal shapes and call create_unit (foreground)
        with (
            patch("modules.content_creator.service.flow_handler.UnitCreationFlow") as mock_ucf_cls,
            patch("modules.content_creator.service.flow_handler.LessonCreationFlow") as mock_lcf_cls,
            patch.object(svc._media_handler, "create_unit_art", new=AsyncMock()),
            patch("modules.content_creator.service.flow_handler.content_provider", return_value=content),
            patch("modules.content_creator.service.flow_handler.infrastructure_provider") as mock_infra_prov,
        ):
            # Mock infrastructure provider with proper async context manager
            mock_infra = Mock()
            mock_infra.initialize = Mock()

            @asynccontextmanager
            async def mock_session_context():
                yield AsyncMock()

            mock_infra.get_async_session_context = mock_session_context
            mock_infra_prov.return_value = mock_infra
            mock_ucf = AsyncMock()
            mock_ucf.execute.return_value = {
                "unit_title": "Unit T",
                "learning_objectives": [
                    {
                        "id": "u_lo_1",
                        "title": "Understand the Topic",
                        "description": "Understand the topic",
                    }
                ],
                "lessons": [
                    {
                        "title": "L1",
                        "learning_objective_ids": ["lo_1"],
                        "lesson_objective": "Learn about L1",
                    }
                ],
                "lesson_count": 1,
                "source_material": "S",
            }
            mock_ucf_cls.return_value = mock_ucf

            mock_lcf = AsyncMock()
            mock_lcf.execute.return_value = {
                "topic": "L1",
                "learner_level": "beginner",
                "voice": "Plain",
                "learning_objectives": ["Learn about A"],
                "learning_objective_ids": ["lo_1"],
                "misconceptions": [],
                "confusables": [],
                "glossary": [],
                "mini_lesson": "x",
                "mcqs": [],
                "short_answers": [],
            }
            mock_lcf_cls.return_value = mock_lcf

            result = await svc.create_unit(topic="Topic", target_lesson_count=1, learner_level="beginner", background=False)
        assert result.title == "Unit T"
        content.save_lesson.assert_awaited()
        content.assign_lessons_to_unit.assert_awaited_once()
        svc._media_handler.generate_unit_podcast.assert_awaited_once()
        svc._media_handler.save_unit_podcast.assert_awaited_once_with(created_unit_obj.id, ANY)

    @pytest.mark.asyncio
    async def test_podcast_audio_uploads_to_object_store(self) -> None:
        content = AsyncMock()
        podcast_generator = AsyncMock()
        podcast_generator.create_podcast.return_value = UnitPodcast(
            transcript="Narration",
            audio_bytes=b"audio",
            mime_type="audio/mpeg",
            voice="Plain",
            duration_seconds=120,
        )

        # Set up all mocks before creating service
        created_unit_obj = Mock()
        created_unit_obj.id = "u2"
        created_unit_obj.title = "Unit B"
        content.create_unit.return_value = created_unit_obj
        content.get_unit.return_value = Mock(user_id=42)
        content.save_lesson = AsyncMock(return_value=Mock(id="lesson-1"))
        content.assign_lessons_to_unit = AsyncMock()
        content.update_unit_metadata = AsyncMock()
        content.update_unit_status = AsyncMock()
        content.save_unit_podcast_from_bytes = AsyncMock()
        content.save_lesson_podcast_from_bytes = AsyncMock()
        # Mock get_unit_detail with iterable lessons to avoid TypeError in art generation
        mock_lesson = Mock()
        mock_lesson.key_concepts = ["concept1", "concept2"]
        content.get_unit_detail = AsyncMock(return_value=Mock(title="Unit B", description="Description", learning_objectives=[], lessons=[mock_lesson]))

        svc = ContentCreatorService(content, podcast_generator=podcast_generator)
        svc._media_handler.generate_lesson_podcast = AsyncMock(
            return_value=(
                PodcastLesson(title="Lesson 1", mini_lesson="Body"),
                SimpleNamespace(
                    transcript="Lesson 1. L1",
                    audio_bytes=b"lesson-audio",
                    mime_type="audio/mpeg",
                    voice="Plain",
                    duration_seconds=150,
                ),
            )
        )
        svc._media_handler.save_lesson_podcast = AsyncMock()
        svc._media_handler.generate_unit_podcast = AsyncMock(
            return_value=UnitPodcast(
                transcript="Narration",
                audio_bytes=b"audio",
                mime_type="audio/mpeg",
                voice="Plain",
                duration_seconds=120,
            )
        )
        svc._media_handler.save_unit_podcast = AsyncMock()

        with (
            patch("modules.content_creator.service.flow_handler.UnitCreationFlow") as mock_ucf_cls,
            patch("modules.content_creator.service.flow_handler.LessonCreationFlow") as mock_lcf_cls,
            patch.object(svc._media_handler, "create_unit_art", new=AsyncMock()),
            patch("modules.content_creator.service.flow_handler.content_provider", return_value=content),
            patch("modules.content_creator.service.flow_handler.infrastructure_provider") as mock_infra_prov,
        ):
            # Mock infrastructure provider with proper async context manager
            mock_infra = Mock()
            mock_infra.initialize = Mock()

            @asynccontextmanager
            async def mock_session_context():
                yield AsyncMock()

            mock_infra.get_async_session_context = mock_session_context
            mock_infra_prov.return_value = mock_infra
            mock_ucf = AsyncMock()
            mock_ucf.execute.return_value = {
                "unit_title": "Unit B",
                "learning_objectives": [
                    {
                        "id": "u_lo_1",
                        "title": "Understand the Topic",
                        "description": "Understand the topic",
                    }
                ],
                "lessons": [
                    {
                        "title": "L1",
                        "learning_objective_ids": ["lo_1"],
                        "lesson_objective": "Learn about L1",
                    }
                ],
            }
            mock_ucf_cls.return_value = mock_ucf

            mock_lcf = AsyncMock()
            mock_lcf.execute.return_value = {
                "topic": "L1",
                "learner_level": "beginner",
                "voice": "Plain",
                "learning_objectives": ["Learn about A"],
                "learning_objective_ids": ["lo_1"],
                "misconceptions": [],
                "confusables": [],
                "glossary": [],
                "mini_lesson": "x",
                "mcqs": [],
                "short_answers": [],
            }
            mock_lcf_cls.return_value = mock_lcf

            await svc.create_unit(topic="Topic", target_lesson_count=1, learner_level="beginner", background=False)

            content.save_lesson.assert_awaited()
            content.assign_lessons_to_unit.assert_awaited()
        svc._media_handler.save_unit_podcast.assert_awaited_once()
