"""
Content Creator Module - Unit Tests

Tests for the content creator service layer.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modules.content.package_models import LessonPackage, Meta, Objective
from modules.content.public import LessonRead
from modules.content_creator.service import ContentCreatorService, CreateLessonRequest


class TestContentCreatorService:
    """Unit tests for ContentCreatorService."""

    @pytest.mark.asyncio
    @patch("modules.content_creator.service.LessonCreationFlow")
    async def test_create_lesson_from_source_material(self, mock_flow_class: Mock) -> None:
        """Test creating a lesson using flow engine."""
        # Arrange
        content = Mock()
        service = ContentCreatorService(content)

        request = CreateLessonRequest(topic="Test Lesson", unit_source_material="Test material content", learner_level="beginner", voice="Test voice", learning_objectives=["Learn X"], lesson_objective="Test objective")

        # Mock flow execution
        mock_flow = AsyncMock()
        mock_flow_class.return_value = mock_flow
        mock_flow.execute.return_value = {
            "topic": "Test Lesson",
            "learner_level": "beginner",
            "voice": "Test voice",
            "learning_objectives": ["Learn X", "Understand Y"],
            "misconceptions": [{"mc_id": "mc_1", "concept": "Test", "misbelief": "Wrong"}],
            "confusables": [{"concept_a": "A", "concept_b": "B", "distinction": "Different"}],
            "glossary": [{"id": "term_1", "term": "Test Term", "definition": "Test definition"}],
            "mini_lesson": "Test explanation",
            "mcqs": {
                "metadata": {},
                "mcqs": [
                    {
                        "id": "ex1",
                        "lo_id": "lo_1",
                        "stem": "What is X?",
                        "options": [{"id": "ex1_a", "label": "A", "text": "Option A"}, {"id": "ex1_b", "label": "B", "text": "Option B"}, {"id": "ex1_c", "label": "C", "text": "Option C"}],
                        "answer_key": {"label": "A", "rationale_right": "Correct"},
                    },
                    {
                        "id": "ex2",
                        "lo_id": "lo_2",
                        "stem": "What is Y?",
                        "options": [{"id": "ex2_a", "label": "A", "text": "Option A"}, {"id": "ex2_b", "label": "B", "text": "Option B"}, {"id": "ex2_c", "label": "C", "text": "Option C"}],
                        "answer_key": {"label": "B", "rationale_right": "Correct"},
                    },
                ],
            },
        }

        # Mock content service responses

        # Create a mock package
        mock_package = LessonPackage(
            meta=Meta(lesson_id="test-id", title="Test Lesson", learner_level="beginner"),
            objectives=[Objective(id="lo_1", text="Learn X")],
            glossary={"terms": []},
            mini_lesson="Test explanation",
            exercises=[],
        )

        mock_lesson = LessonRead(id="test-id", title="Test Lesson", learner_level="beginner", package=mock_package, package_version=1, created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1))
        content.save_lesson.return_value = mock_lesson

        # Act
        result = await service.create_lesson_from_source_material(request)

        # Assert
        assert result.title == "Test Lesson"
        assert result.package_version == 1
        assert result.objectives_count > 0
        assert result.mcqs_count > 0
        content.save_lesson.assert_called_once()
        # No more component calls - everything is in the package now

        # Verify flow was called with correct inputs
        mock_flow.execute.assert_called_once_with({"topic": "Test Lesson", "unit_source_material": "Test material content", "learner_level": "beginner", "voice": "Test voice", "learning_objectives": ["Learn X"], "lesson_objective": "Test objective"})

    @pytest.mark.asyncio
    async def test_retry_unit_creation_success(self) -> None:
        """Test successfully retrying a failed unit."""
        # Arrange
        content = Mock()
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
        content.get_unit.return_value = mock_unit

        # Mock update status call
        content.update_unit_status.return_value = mock_unit

        # Mock task queue provider to avoid infrastructure initialization
        with patch("modules.content_creator.service.task_queue_provider") as mock_provider:
            tq = AsyncMock()
            mock_provider.return_value = tq

            # Act
            result = await service.retry_unit_creation(valid_unit_id)

        # Assert
        assert result is not None
        assert result.unit_id == valid_unit_id
        assert result.title == "Test Unit"
        assert result.status == "in_progress"

        # Verify status was updated to in_progress
        content.update_unit_status.assert_called_once_with(unit_id=valid_unit_id, status="in_progress", error_message=None, creation_progress={"stage": "retrying", "message": "Retrying unit creation..."})

    @pytest.mark.asyncio
    async def test_retry_unit_creation_unit_not_found(self) -> None:
        """Test retrying a non-existent unit returns None."""
        # Arrange
        content = Mock()
        service = ContentCreatorService(content)
        content.get_unit.return_value = None

        # Act
        result = await service.retry_unit_creation("nonexistent-unit")

        # Assert
        assert result is None
        content.get_unit.assert_called_once_with("nonexistent-unit")

    @pytest.mark.asyncio
    async def test_retry_unit_creation_not_failed_raises_error(self) -> None:
        """Test retrying a unit that's not failed raises ValueError."""
        # Arrange
        content = Mock()
        service = ContentCreatorService(content)

        mock_unit = Mock()
        mock_unit.status = "completed"  # Not failed
        content.get_unit.return_value = mock_unit

        # Act & Assert
        with pytest.raises(ValueError, match="not in failed state"):
            await service.retry_unit_creation("unit-123")

    def test_dismiss_unit_success(self) -> None:
        """Test successfully dismissing a unit."""
        # Arrange
        content = Mock()
        service = ContentCreatorService(content)

        mock_unit = Mock()
        mock_unit.id = "unit-123"
        content.get_unit.return_value = mock_unit
        content.delete_unit.return_value = True

        # Act
        result = service.dismiss_unit("unit-123")

        # Assert
        assert result is True
        content.get_unit.assert_called_once_with("unit-123")
        content.delete_unit.assert_called_once_with("unit-123")

    def test_dismiss_unit_not_found(self) -> None:
        """Test dismissing a non-existent unit returns False."""
        # Arrange
        content = Mock()
        service = ContentCreatorService(content)
        content.get_unit.return_value = None

        # Act
        result = service.dismiss_unit("nonexistent-unit")

        # Assert
        assert result is False
        content.get_unit.assert_called_once_with("nonexistent-unit")
