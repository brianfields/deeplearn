"""
Content Creator Module - Unit Tests

Tests for the content creator service layer.
"""

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
