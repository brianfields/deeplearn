"""
Content Creator Module - Unit Tests

Tests for the content creator service layer.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modules.content_creator.service import ContentCreatorService, CreateLessonRequest


class TestContentCreatorService:
    """Unit tests for ContentCreatorService."""

    @pytest.mark.asyncio
    @patch("modules.content_creator.service.LessonCreationFlow")
    async def test_create_lesson_from_source_material(self, mock_flow_class):
        """Test creating a lesson using flow engine."""
        # Arrange
        content = Mock()
        service = ContentCreatorService(content)

        request = CreateLessonRequest(title="Test Lesson", core_concept="Test Concept", source_material="Test material content", user_level="beginner", domain="Testing")

        # Mock flow execution
        mock_flow = AsyncMock()
        mock_flow_class.return_value = mock_flow
        mock_flow.execute.return_value = {
            "learning_objectives": ["Learn X", "Understand Y"],
            "key_concepts": ["Concept A", "Concept B"],
            "refined_material": {"overview": "Test overview"},
            "didactic_snippet": {"explanation": "Test explanation", "key_points": ["Point 1"]},
            "glossary": {"terms": [{"term": "Test Term", "definition": "Test definition"}]},
            "exercises": [
                {
                    "id": "ex1",
                    "exercise_type": "mcq",
                    "lo_id": "lo_1",
                    "stem": "What is X?",
                    "options": [{"id": "ex1_a", "label": "A", "text": "Option A"}, {"id": "ex1_b", "label": "B", "text": "Option B"}, {"id": "ex1_c", "label": "C", "text": "Option C"}],
                    "answer_key": {"label": "A"},
                },
                {
                    "id": "ex2",
                    "exercise_type": "mcq",
                    "lo_id": "lo_2",
                    "stem": "What is Y?",
                    "options": [{"id": "ex2_a", "label": "A", "text": "Option A"}, {"id": "ex2_b", "label": "B", "text": "Option B"}, {"id": "ex2_c", "label": "C", "text": "Option C"}],
                    "answer_key": {"label": "A"},
                },
            ],
        }

        # Mock content service responses
        from modules.content.package_models import DidacticSnippet, LessonPackage, Meta, Objective
        from modules.content.service import LessonRead

        # Create a mock package
        mock_package = LessonPackage(
            meta=Meta(lesson_id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", domain="Testing"),
            objectives=[Objective(id="lo_1", text="Learn X")],
            glossary={"terms": []},
            didactic_snippet=DidacticSnippet(id="lesson_explanation", plain_explanation="Test explanation", key_takeaways=[]),
            exercises=[],
        )

        mock_lesson = LessonRead(id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", package=mock_package, package_version=1, created_at=datetime(2024, 1, 1), updated_at=datetime(2024, 1, 1))
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
        mock_flow.execute.assert_called_once_with({"title": "Test Lesson", "core_concept": "Test Concept", "source_material": "Test material content", "user_level": "beginner", "domain": "Testing"})

    # generate_component tests removed - method was unused and has been removed

    # Additional generate_component tests removed - method was unused and has been removed
