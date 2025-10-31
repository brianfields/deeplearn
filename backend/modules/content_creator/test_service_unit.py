"""
Content Creator Module - Unit Tests

Tests for the content creator service layer.
"""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
import uuid

import pytest

from modules.content.public import UnitStatus
from modules.content_creator.podcast import PodcastLesson
from modules.content_creator.service import ContentCreatorService


class TestContentCreatorService:
    """Unit tests for ContentCreatorService."""

    @pytest.mark.asyncio
    @patch("modules.content_creator.service.flow_handler.UnitCreationFlow")
    async def test_execute_unit_creation_removes_uncovered_los(
        self,
        mock_flow_class: Mock,
    ) -> None:
        """Learning objectives without exercises should be removed after lesson generation."""

        content = AsyncMock()
        content.update_unit_metadata = AsyncMock()
        content.update_unit_status = AsyncMock()
        content.assign_lessons_to_unit = AsyncMock()
        content.save_unit_podcast_from_bytes = AsyncMock()

        service = ContentCreatorService(content)
        service._media_handler.create_unit_art = AsyncMock()
        service._media_handler.generate_unit_podcast = AsyncMock(
            return_value=SimpleNamespace(
                transcript="Transcript",
                audio_bytes=b"",
                mime_type="audio/mpeg",
                voice="Plain",
                duration_seconds=120,
            )
        )
        service._media_handler.save_unit_podcast = AsyncMock()

        unit_plan = {
            "unit_title": "Test Unit",
            "learning_objectives": [
                {
                    "id": "UO1",
                    "title": "Covered Objective",
                    "description": "Learner will cover UO1",
                },
                {
                    "id": "UO2",
                    "title": "Uncovered Objective",
                    "description": "Learner will skip UO2",
                },
            ],
            "lessons": [
                {
                    "title": "Lesson 1",
                    "lesson_objective": "Do something",
                    "learning_objectives": ["UO1"],
                }
            ],
            "lesson_count": 1,
        }

        mock_flow = AsyncMock()
        mock_flow.execute.return_value = unit_plan
        mock_flow_class.return_value = mock_flow

        podcast_generator = Mock()
        podcast_generator.create_podcast = AsyncMock(
            return_value=SimpleNamespace(
                transcript="Transcript",
                audio_bytes=b"",
                mime_type="audio/mpeg",
                voice="Plain",
            )
        )
        service.podcast_generator = podcast_generator

        service._flow_handler._create_single_lesson = AsyncMock(
            return_value=(
                "lesson-1",
                PodcastLesson(title="Lesson 1", mini_lesson="Body"),
                "Plain",
                {"UO1"},
            )
        )

        result = await service._execute_unit_creation_pipeline(
            unit_id="unit-1",
            topic="Topic",
            source_material="Source",
            target_lesson_count=None,
            learner_level="beginner",
        )

        assert result.unit_id == "unit-1"
        assert result.lesson_count == 1

        # First call persists original objectives; second call removes uncovered ones
        assert content.update_unit_metadata.await_count >= 2
        first_call = content.update_unit_metadata.await_args_list[0]
        second_call = content.update_unit_metadata.await_args_list[-1]

        original_los = first_call.kwargs.get("learning_objectives")
        filtered_los = second_call.kwargs.get("learning_objectives")

        assert original_los is not None and len(original_los) == 2
        assert filtered_los is not None and len(filtered_los) == 1
        assert filtered_los[0].id == "UO1"

    @pytest.mark.asyncio
    async def test_retry_unit_creation_success(self) -> None:
        """Test successfully retrying a failed unit."""
        # Arrange
        content = AsyncMock()
        service = ContentCreatorService(content)

        # Mock a failed unit that can be retried
        mock_unit = Mock()
        valid_unit_id = "123e4567-e89b-12d3-a456-426614174000"
        mock_unit.id = valid_unit_id
        mock_unit.title = "Test Unit"
        mock_unit.status = "failed"
        mock_unit.generated_from_topic = True
        mock_unit.learner_level = "beginner"
        mock_unit.target_lesson_count = 3
        mock_unit.source_material = "Original"
        content.get_unit.return_value = mock_unit

        # Mock update status call
        content.update_unit_status.return_value = mock_unit
        content.set_unit_task = AsyncMock()

        # Mock task queue provider to avoid infrastructure initialization
        tq = AsyncMock()
        service._status_handler._task_queue_factory = Mock(return_value=tq)
        tq.submit_flow_task.return_value = SimpleNamespace(
            task_id="task-789",
            flow_run_id=uuid.UUID(valid_unit_id),
        )

        # Act
        result = await service.retry_unit_creation(valid_unit_id)

        # Assert
        assert result is not None
        assert result.unit_id == valid_unit_id
        assert result.title == "Test Unit"
        assert result.status == "in_progress"

        # Verify status was updated to in_progress
        content.update_unit_status.assert_awaited_once_with(unit_id=valid_unit_id, status="in_progress", error_message=None, creation_progress={"stage": "retrying", "message": "Retrying unit creation..."})
        content.set_unit_task.assert_awaited_once_with(valid_unit_id, "task-789")
        tq.submit_flow_task.assert_awaited_once_with(
            flow_name="content_creator.unit_creation",
            flow_run_id=uuid.UUID(valid_unit_id),
            inputs={
                "unit_id": valid_unit_id,
                "topic": "Test Unit",
                "source_material": mock_unit.source_material,
                "target_lesson_count": mock_unit.target_lesson_count,
                "learner_level": mock_unit.learner_level,
            },
        )

    @pytest.mark.asyncio
    @patch("modules.content_creator.service.flow_handler.LessonCreationFlow")
    @patch("modules.content_creator.service.flow_handler.content_provider")
    @patch("modules.content_creator.service.flow_handler.infrastructure_provider")
    async def test_create_single_lesson_includes_short_answers(
        self,
        mock_infra_provider: Mock,
        mock_content_provider: Mock,
        mock_lesson_flow_cls: Mock,
    ) -> None:
        """Flow handler should persist short-answer exercises in the saved lesson package."""

        content = AsyncMock()
        content.save_lesson = AsyncMock(return_value=Mock(id="lesson-123"))
        mock_content_provider.return_value = content

        service = ContentCreatorService(content)
        service._media_handler.generate_lesson_podcast = AsyncMock(
            return_value=(
                PodcastLesson(title="Lesson", mini_lesson="Body"),
                SimpleNamespace(
                    transcript="Transcript",
                    audio_bytes=b"audio",
                    mime_type="audio/mpeg",
                    voice="Guide",
                    duration_seconds=90,
                ),
            )
        )
        service._media_handler.save_lesson_podcast = AsyncMock()

        mock_flow = AsyncMock()
        mock_flow.execute.return_value = {
            "topic": "Lesson",
            "learner_level": "beginner",
            "voice": "Guide",
            "learning_objectives": ["Explain"],
            "learning_objective_ids": ["lo_1"],
            "misconceptions": [],
            "confusables": [],
            "glossary": [],
            "mini_lesson": "Body",
            "mcqs": [
                {
                    "stem": "What is it?",
                    "options": [
                        {"label": "A", "text": "Answer"},
                        {"label": "B", "text": "Other"},
                        {"label": "C", "text": "Another"},
                    ],
                    "answer_key": {"label": "A"},
                    "learning_objectives_covered": ["lo_1"],
                    "misconceptions_used": [],
                    "glossary_terms_used": [],
                }
            ],
            "short_answers": [
                {
                    "stem": "Name it",
                    "canonical_answer": "term",
                    "acceptable_answers": ["the term"],
                    "wrong_answers": [
                        {
                            "answer": "mistake",
                            "explanation": "Not exact",
                            "misconception_ids": ["m1"],
                        }
                    ],
                    "learning_objectives_covered": ["lo_1"],
                    "misconceptions_used": ["m1"],
                    "glossary_terms_used": [],
                    "cognitive_level": "remember",
                    "explanation_correct": "Yes",
                }
            ],
        }
        mock_lesson_flow_cls.return_value = mock_flow

        mock_infra = Mock()
        mock_infra.initialize = Mock()

        @asynccontextmanager
        async def _session_ctx() -> AsyncMock:
            yield AsyncMock()

        mock_infra.get_async_session_context = _session_ctx
        mock_infra_provider.return_value = mock_infra

        await service._flow_handler._create_single_lesson(
            lesson_plan={"title": "Lesson", "learning_objective_ids": ["lo_1"], "lesson_objective": "Explain"},
            lesson_index=0,
            unit_los={"lo_1": "Explain"},
            unit_material="Body",
            learner_level="beginner",
            arq_task_id=None,
        )

        assert content.save_lesson.await_count == 1
        saved_package = content.save_lesson.await_args.args[0].package
        short_answers = [ex for ex in saved_package.exercises if ex.exercise_type == "short_answer"]
        assert len(short_answers) == 1
        assert short_answers[0].canonical_answer == "term"

    @pytest.mark.asyncio
    async def test_create_unit_with_conversation_resources(self) -> None:
        """Conversation resources should populate the unit source material."""

        content = AsyncMock()
        content.create_unit.return_value = SimpleNamespace(id="unit-123", title="Draft Unit")
        content.update_unit_status = AsyncMock()

        service = ContentCreatorService(content)
        service._status_handler.enqueue_unit_creation = AsyncMock()
        service._fetch_conversation_resources = AsyncMock(return_value=[SimpleNamespace(user_id=101)])
        service._combine_resource_texts = Mock(return_value="Combined content")
        session_state = SimpleNamespace(
            learning_objectives=None,
            suggested_lesson_count=None,
            metadata={"uncovered_learning_objective_ids": []},
        )
        service._fetch_uncovered_lo_ids = AsyncMock(return_value=([], session_state))
        service._link_resources_and_save_generated_source = AsyncMock()

        result = await service.create_unit(
            topic="Interesting Topic",
            background=True,
            learner_level="beginner",
            conversation_id="conversation-1",
        )

        assert result.unit_id == "unit-123"
        service._fetch_conversation_resources.assert_awaited_once_with("conversation-1")
        service._combine_resource_texts.assert_called_once()
        service._link_resources_and_save_generated_source.assert_awaited_once()

        unit_create = content.create_unit.await_args.args[0]
        assert unit_create.source_material == "Combined content"
        assert unit_create.generated_from_topic is False

    @pytest.mark.asyncio
    async def test_create_unit_ignores_empty_conversation_resources(self) -> None:
        """Empty or missing conversation resources fall back to topic generation."""

        content = AsyncMock()
        content.create_unit.return_value = SimpleNamespace(id="unit-456", title="Draft Unit")
        content.update_unit_status = AsyncMock()

        service = ContentCreatorService(content)
        service._status_handler.enqueue_unit_creation = AsyncMock()
        service._fetch_conversation_resources = AsyncMock(return_value=[])
        service._combine_resource_texts = Mock(return_value="")
        service._fetch_uncovered_lo_ids = AsyncMock(return_value=(None, None))
        service._link_resources_and_save_generated_source = AsyncMock()

        result = await service.create_unit(
            topic="Fallback Topic",
            background=True,
            learner_level="beginner",
            conversation_id="conversation-2",
        )

        assert result.unit_id == "unit-456"
        service._fetch_conversation_resources.assert_awaited_once_with("conversation-2")
        service._combine_resource_texts.assert_not_called()
        service._link_resources_and_save_generated_source.assert_awaited_once()

        unit_create = content.create_unit.await_args.args[0]
        assert unit_create.source_material is None
        assert unit_create.generated_from_topic is True

    @pytest.mark.asyncio
    async def test_create_unit_with_partial_coverage_generates_supplemental(self) -> None:
        """Uncovered learning objectives should trigger supplemental generation."""

        content = AsyncMock()
        content.create_unit.return_value = SimpleNamespace(id="unit-789", title="Draft Unit")
        content.update_unit_status = AsyncMock()

        service = ContentCreatorService(content)
        service._status_handler.enqueue_unit_creation = AsyncMock()

        resource = SimpleNamespace(id=uuid.uuid4(), user_id=42, extracted_text="primary")
        session_state = SimpleNamespace(
            learning_objectives=[SimpleNamespace(id="lo_1", title="Objective", description="Details")],
            suggested_lesson_count=5,
            metadata={"uncovered_learning_objective_ids": ["lo_1"]},
        )

        service._fetch_conversation_resources = AsyncMock(return_value=[resource])
        service._combine_resource_texts = Mock(return_value="Resource text")
        service._fetch_uncovered_lo_ids = AsyncMock(return_value=(["lo_1"], session_state))
        service._generate_supplemental_source_material = AsyncMock(return_value="Supplement text")
        service._combine_resource_and_supplemental_text = Mock(return_value="Combined output")
        service._link_resources_and_save_generated_source = AsyncMock()

        result = await service.create_unit(
            topic="Interesting Topic",
            background=True,
            learner_level="intermediate",
            conversation_id="conversation-3",
        )

        assert result.unit_id == "unit-789"
        service._generate_supplemental_source_material.assert_awaited_once_with(
            topic="Interesting Topic",
            learner_level="intermediate",
            target_lesson_count=None,
            uncovered_lo_ids=["lo_1"],
            session_state=session_state,
        )
        service._combine_resource_and_supplemental_text.assert_called_once_with(
            "Resource text",
            "Supplement text",
        )

        unit_create = content.create_unit.await_args.args[0]
        assert unit_create.source_material == "Combined output"
        service._link_resources_and_save_generated_source.assert_awaited_once_with(
            unit_id="unit-789",
            resources=[resource],
            user_id=42,
            supplemental_text="Supplement text",
            uncovered_learning_objective_ids=["lo_1"],
        )

    @pytest.mark.asyncio
    async def test_create_unit_background_records_task(self) -> None:
        """Background unit creation should persist the ARQ task identifier."""

        content = AsyncMock()
        content.set_unit_task = AsyncMock()
        created_unit_id = str(uuid.uuid4())
        content.create_unit.return_value = SimpleNamespace(id=created_unit_id, title="Draft Unit")

        service = ContentCreatorService(content)

        task_service = AsyncMock()
        service._status_handler._task_queue_factory = Mock(return_value=task_service)
        task_service.submit_flow_task.return_value = SimpleNamespace(
            task_id="task-123",
            flow_run_id=uuid.UUID(created_unit_id),
        )

        result = await service.create_unit(
            topic="Interesting Topic",
            source_material="source",
            background=True,
            target_lesson_count=2,
            learner_level="advanced",
            user_id=9,
            unit_title="Draft Unit",
        )

        # Type narrowing: background=True returns MobileUnitCreationResult
        assert isinstance(result, ContentCreatorService.MobileUnitCreationResult)
        assert result.unit_id == created_unit_id
        assert result.status == UnitStatus.IN_PROGRESS.value
        content.set_unit_task.assert_awaited_once_with(created_unit_id, "task-123")
        task_service.submit_flow_task.assert_awaited_once_with(
            flow_name="content_creator.unit_creation",
            flow_run_id=uuid.UUID(created_unit_id),
            inputs={
                "unit_id": created_unit_id,
                "topic": "Interesting Topic",
                "source_material": "source",
                "target_lesson_count": 2,
                "learner_level": "advanced",
            },
        )

    @pytest.mark.asyncio
    async def test_retry_unit_creation_unit_not_found(self) -> None:
        """Test retrying a non-existent unit returns None."""
        # Arrange
        content = AsyncMock()
        service = ContentCreatorService(content)
        content.get_unit.return_value = None

        # Act
        result = await service.retry_unit_creation("nonexistent-unit")

        # Assert
        assert result is None
        content.get_unit.assert_awaited_once_with("nonexistent-unit")

    @pytest.mark.asyncio
    async def test_retry_unit_creation_not_failed_raises_error(self) -> None:
        """Test retrying a unit that's not failed raises ValueError."""
        # Arrange
        content = AsyncMock()
        service = ContentCreatorService(content)

        mock_unit = Mock()
        mock_unit.status = "completed"  # Not failed
        content.get_unit.return_value = mock_unit

        # Act & Assert
        with pytest.raises(ValueError, match="not in failed state"):
            await service.retry_unit_creation("unit-123")

    @pytest.mark.asyncio
    async def test_dismiss_unit_success(self) -> None:
        """Test successfully dismissing a unit."""
        # Arrange
        content = AsyncMock()
        service = ContentCreatorService(content)

        mock_unit = Mock()
        mock_unit.id = "unit-123"
        content.get_unit.return_value = mock_unit
        content.delete_unit.return_value = True

        # Act
        result = await service.dismiss_unit("unit-123")

        # Assert
        assert result is True
        content.get_unit.assert_awaited_once_with("unit-123")
        content.delete_unit.assert_awaited_once_with("unit-123")

    @pytest.mark.asyncio
    async def test_dismiss_unit_not_found(self) -> None:
        """Test dismissing a non-existent unit returns False."""
        # Arrange
        content = AsyncMock()
        service = ContentCreatorService(content)
        content.get_unit.return_value = None

        # Act
        result = await service.dismiss_unit("nonexistent-unit")

        # Assert
        assert result is False
        content.get_unit.assert_awaited_once_with("nonexistent-unit")

    @pytest.mark.asyncio
    async def test_link_resources_and_save_generated_source_persists_supplemental(self) -> None:
        """Helper should link learner resources and persist supplemental text."""

        content = AsyncMock()
        service = ContentCreatorService(content)

        resource_service = AsyncMock()
        generated_id = uuid.uuid4()
        resource_service.create_generated_source_resource.return_value = SimpleNamespace(id=generated_id)
        service._resource_service = resource_service

        resource_a = SimpleNamespace(id=uuid.uuid4(), user_id=51)
        await service._link_resources_and_save_generated_source(
            unit_id="unit-xyz",
            resources=[resource_a],
            user_id=None,
            supplemental_text=" Supplemental text ",
            uncovered_learning_objective_ids=["lo_2"],
        )

        resource_service.create_generated_source_resource.assert_awaited_once()
        metadata = resource_service.create_generated_source_resource.await_args.kwargs["metadata"]
        assert metadata["method"] == "ai_supplemental"
        assert metadata["uncovered_lo_ids"] == ["lo_2"]

        attach_calls = resource_service.attach_resources_to_unit.await_args_list
        assert attach_calls[0].kwargs == {"unit_id": "unit-xyz", "resource_ids": [resource_a.id]}
        assert attach_calls[1].kwargs == {"unit_id": "unit-xyz", "resource_ids": [generated_id]}

    @pytest.mark.asyncio
    async def test_link_resources_and_save_generated_source_skips_when_no_text(self) -> None:
        """Helper should exit early when supplemental text is missing."""

        content = AsyncMock()
        service = ContentCreatorService(content)
        resource_service = AsyncMock()
        service._resource_service = resource_service

        resource = SimpleNamespace(id=uuid.uuid4(), user_id=99)
        await service._link_resources_and_save_generated_source(
            unit_id="unit-empty",
            resources=[resource],
            user_id=77,
            supplemental_text="   ",
            uncovered_learning_objective_ids=None,
        )

        resource_service.attach_resources_to_unit.assert_awaited_once_with(
            unit_id="unit-empty",
            resource_ids=[resource.id],
        )
        resource_service.create_generated_source_resource.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("modules.content_creator.service.media_handler.UnitArtCreationFlow")
    async def test_create_unit_art_uploads_generated_image(self, mock_flow_class: Mock) -> None:
        """Art generation flow output should be downloaded and saved via content service."""

        content = AsyncMock()
        service = ContentCreatorService(content)

        unit_detail = SimpleNamespace(
            title="Quantum Jazz",
            description="Explore improvisation through qubits",
            learning_objectives=["Understand qubits"],
            lessons=[SimpleNamespace(key_concepts=["Qubit", "Superposition"])],
        )
        content.get_unit_detail.return_value = unit_detail

        mock_flow = AsyncMock()
        mock_flow.execute.return_value = {
            "art_description": {"prompt": "Petrol blue jazz club with qubits", "alt_text": "Art Deco jazz trio"},
            "image": {"image_url": "https://example.com/art.png"},
        }
        mock_flow_class.return_value = mock_flow

        download_mock = AsyncMock(return_value=(b"image-bytes", "image/png"))
        content.save_unit_art_from_bytes.return_value = SimpleNamespace(id="unit-1")

        with patch.object(service._media_handler, "_download_image", download_mock):
            result = await service.create_unit_art("unit-1")

        content.get_unit_detail.assert_awaited_once_with("unit-1", include_art_presigned_url=False)
        mock_flow.execute.assert_awaited_once()
        download_mock.assert_awaited_once_with("https://example.com/art.png")
        content.save_unit_art_from_bytes.assert_awaited_once_with(
            "unit-1",
            image_bytes=b"image-bytes",
            content_type="image/png",
            description="Petrol blue jazz club with qubits",
            alt_text="Art Deco jazz trio",
        )
        assert result == content.save_unit_art_from_bytes.return_value

    @pytest.mark.asyncio
    @patch("modules.content_creator.service.media_handler.UnitArtCreationFlow")
    async def test_create_unit_art_retries_on_failure(self, mock_flow_class: Mock) -> None:
        """The service should retry the art flow once before raising."""

        content = AsyncMock()
        service = ContentCreatorService(content)

        unit_detail = SimpleNamespace(
            title="Cyber History",
            description=None,
            learning_objectives=[],
            lessons=[],
        )
        content.get_unit_detail.return_value = unit_detail

        mock_flow = AsyncMock()
        mock_flow.execute.side_effect = [
            RuntimeError("boom"),
            {
                "art_description": {"prompt": "Prompt", "alt_text": "Alt"},
                "image": {"image_url": "https://example.com/art.png"},
            },
        ]
        mock_flow_class.return_value = mock_flow

        download_mock = AsyncMock(return_value=(b"img", "image/png"))
        content.save_unit_art_from_bytes.return_value = SimpleNamespace(id="unit-2")

        with patch.object(service._media_handler, "_download_image", download_mock):
            result = await service.create_unit_art("unit-2")

        assert mock_flow.execute.await_count == 2
        download_mock.assert_awaited_once()
        assert result == content.save_unit_art_from_bytes.return_value

    @pytest.mark.asyncio
    @patch("modules.content_creator.service.media_handler.UnitArtCreationFlow")
    async def test_create_unit_art_raises_after_retries(self, mock_flow_class: Mock) -> None:
        """Two consecutive flow failures should bubble up as a runtime error."""

        content = AsyncMock()
        service = ContentCreatorService(content)

        content.get_unit_detail.return_value = SimpleNamespace(
            title="Unit",
            description=None,
            learning_objectives=[],
            lessons=[],
        )

        mock_flow = AsyncMock()
        mock_flow.execute.side_effect = RuntimeError("nope")
        mock_flow_class.return_value = mock_flow

        with pytest.raises(RuntimeError):
            await service.create_unit_art("unit-3")

        assert mock_flow.execute.await_count == 2
