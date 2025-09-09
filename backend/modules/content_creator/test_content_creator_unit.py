"""
Content Creator Module - Unit Tests

Tests for the content creator service layer.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from modules.content_creator.service import ContentCreatorService, CreateTopicRequest


class TestContentCreatorService:
    """Unit tests for ContentCreatorService."""

    @pytest.mark.asyncio
    @patch("modules.content_creator.service.TopicCreationFlow")
    async def test_create_topic_from_source_material(self, mock_flow_class):
        """Test creating a topic using flow engine."""
        # Arrange
        content = Mock()
        service = ContentCreatorService(content)

        request = CreateTopicRequest(title="Test Topic", core_concept="Test Concept", source_material="Test material content", user_level="beginner", domain="Testing")

        # Mock flow execution
        mock_flow = AsyncMock()
        mock_flow_class.return_value = mock_flow
        mock_flow.execute.return_value = {
            "learning_objectives": ["Learn X", "Understand Y"],
            "key_concepts": ["Concept A", "Concept B"],
            "refined_material": {"overview": "Test overview"},
            "didactic_snippet": {"explanation": "Test explanation", "key_points": ["Point 1"]},
            "glossary": {"terms": [{"term": "Test Term", "definition": "Test definition"}]},
            "mcqs": [{"question": "What is X?", "options": ["A", "B", "C", "D"], "correct_answer": 0}, {"question": "What is Y?", "options": ["A", "B", "C", "D"], "correct_answer": 1}],
        }

        # Mock content service responses
        from modules.content.service import TopicRead

        mock_topic = TopicRead(
            id="test-id", title="Test Topic", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Concept A"], created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00", components=[]
        )
        content.save_topic.return_value = mock_topic
        content.save_component.return_value = Mock()

        # Act
        result = await service.create_topic_from_source_material(request)

        # Assert
        assert result.title == "Test Topic"
        assert result.components_created == 4  # didactic_snippet, glossary, 2 MCQs (one per learning objective)
        content.save_topic.assert_called_once()
        assert content.save_component.call_count == 4

        # Verify flow was called with correct inputs
        mock_flow.execute.assert_called_once_with({"title": "Test Topic", "core_concept": "Test Concept", "source_material": "Test material content", "user_level": "beginner", "domain": "Testing"})

    # generate_component tests removed - method was unused and has been removed

    # Additional generate_component tests removed - method was unused and has been removed
