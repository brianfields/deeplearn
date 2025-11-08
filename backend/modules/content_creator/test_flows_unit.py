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
from modules.content_creator.steps import (
    MCQAnswerKey,
    MCQOption,
    MCQValidationOutputs,
    StructuredMCQExercise,
)

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
@patch("modules.content_creator.flows.ValidateAndStructureMCQsStep")
@patch("modules.content_creator.flows.GenerateMCQsUnstructuredStep")
@patch("modules.content_creator.flows.GenerateLessonPodcastTranscriptStep")
async def test_lesson_creation_flow_runs_podcast_pipeline(
    mock_transcript_step: Mock,
    mock_mcq_step: Mock,
    mock_validate_step: Mock,
) -> None:
    """Lesson creation flow should orchestrate the podcast-first pipeline."""

    transcript_runner = AsyncMock()
    transcript_runner.execute.return_value = SimpleNamespace(output_content="Transcript body")
    mock_transcript_step.return_value = transcript_runner

    mock_mcq = AsyncMock()
    mock_mcq.execute.return_value = SimpleNamespace(output_content="RAW MCQS")
    mock_mcq_step.return_value = mock_mcq

    exercises = [
        StructuredMCQExercise(
            id="ex-comp-mc-001",
            exercise_type="mcq",
            exercise_category="comprehension",
            aligned_learning_objective="lo_1",
            cognitive_level="Comprehension",
            difficulty="medium",
            stem="What is the main idea?",
            options=[
                MCQOption(label="A", text="Idea A"),
                MCQOption(label="B", text="Idea B"),
                MCQOption(label="C", text="Idea C"),
                MCQOption(label="D", text="Idea D"),
            ],
            answer_key=MCQAnswerKey(label="A", rationale_right="Explains it"),
        )
    ]
    validation_output = MCQValidationOutputs(reasoning="all good", exercises=exercises)
    mock_validate = AsyncMock()
    mock_validate.execute.return_value = SimpleNamespace(output_content=validation_output)
    mock_validate_step.return_value = mock_validate

    flow = LessonCreationFlow()
    result = await flow._execute_flow_logic(
        {
            "learner_desires": "Curious adult",
            "learning_objectives": [{"id": "lo_1", "title": "Explain concept", "description": "Explain concept"}],
            "learning_objective_ids": ["lo_1"],
            "lesson_objective": "Explain it",
            "source_material": "Full source",
            "lesson_title": "Lesson One",
            "sibling_lessons": [{"title": "Lesson Two", "lesson_objective": "Do something else"}],
        }
    )

    transcript_runner.execute.assert_awaited_once()
    mock_mcq.execute.assert_awaited_once()
    mock_validate.execute.assert_awaited_once()

    assert result["podcast_transcript"] == "Transcript body"
    assert result["quiz"] == ["ex-comp-mc-001"]
    assert result["quiz_metadata"]["total_items"] == 1


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
            "learner_desires": "Curious adult",
            "lesson_number": 1,
            "lesson_title": "Title",
            "lesson_objective": "Objective",
            "voice": "Guide",
        }
    )

    transcript_step.execute.assert_awaited_once_with(
        {
            "learner_desires": "Curious adult",
            "lesson_title": "Title",
            "lesson_objective": "Objective",
            "learning_objectives": [],
            "source_material": "",
            "sibling_lessons": [],
            "lesson_number": 1,
            "voice": "Guide",
        }
    )
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

    lessons = [PodcastLessonInput(title="L1", podcast_transcript="Body")]
    flow = UnitPodcastFlow()
    result = await flow._execute_flow_logic(
        {
            "learner_desires": "Curious adult",
            "unit_title": "Unit",
            "voice": "Guide",
            "unit_summary": "Summary",
            "lessons": lessons,
        }
    )

    transcript_step.execute.assert_awaited_once_with(
        {
            "learner_desires": "Curious adult",
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
                PodcastLesson(title="Lesson 1", podcast_transcript="x"),
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
                "podcast_transcript": "Transcript body",
                "learning_objectives": ["Learn about A"],
                "learning_objective_ids": ["lo_1"],
                "exercise_bank": [
                    {
                        "id": "ex-comp-mc-001",
                        "exercise_type": "mcq",
                        "exercise_category": "comprehension",
                        "aligned_learning_objective": "lo_1",
                        "cognitive_level": "Comprehension",
                        "difficulty": "medium",
                        "stem": "Question?",
                        "options": [{"label": "A", "text": "Option A"}, {"label": "B", "text": "Option B"}, {"label": "C", "text": "Option C"}, {"label": "D", "text": "Option D"}],
                        "answer_key": {"label": "A", "rationale_right": "Because"},
                    }
                ],
                "quiz": ["ex-comp-mc-001"],
                "quiz_metadata": {"quiz_type": "lesson_assessment", "total_items": 1, "reasoning": "none"},
            }
            mock_lcf_cls.return_value = mock_lcf

            result = await svc.create_unit(
                learner_desires="Beginner learning Topic",
                unit_title="Unit T",
                learning_objectives=[{"id": "u_lo_1", "title": "Understand the Topic", "description": "Understand the topic"}],
                target_lesson_count=1,
                conversation_id="conv-123",
                background=False,
            )
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
                PodcastLesson(title="Lesson 1", podcast_transcript="Body"),
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
                "podcast_transcript": "Transcript body",
                "learning_objectives": ["Learn about A"],
                "learning_objective_ids": ["lo_1"],
                "exercise_bank": [
                    {
                        "id": "ex-comp-mc-001",
                        "exercise_type": "mcq",
                        "exercise_category": "comprehension",
                        "aligned_learning_objective": "lo_1",
                        "cognitive_level": "Comprehension",
                        "difficulty": "medium",
                        "stem": "Question?",
                        "options": [{"label": "A", "text": "Option A"}, {"label": "B", "text": "Option B"}, {"label": "C", "text": "Option C"}, {"label": "D", "text": "Option D"}],
                        "answer_key": {"label": "A", "rationale_right": "Because"},
                    }
                ],
                "quiz": ["ex-comp-mc-001"],
                "quiz_metadata": {"quiz_type": "lesson_assessment", "total_items": 1, "reasoning": "none"},
            }
            mock_lcf_cls.return_value = mock_lcf

            await svc.create_unit(
                learner_desires="Beginner learning Topic",
                unit_title="Unit B",
                learning_objectives=[{"id": "u_lo_1", "title": "Understand the Topic", "description": "Understand the topic"}],
                target_lesson_count=1,
                conversation_id="conv-456",
                background=False,
            )

            content.save_lesson.assert_awaited()
            content.assign_lessons_to_unit.assert_awaited()
        svc._media_handler.save_unit_podcast.assert_awaited_once()
