"""
Content Creator Module - Unit Tests

Tests for the content creator service layer.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from modules.content_creator.service import ContentCreatorService, CreateComponentRequest, CreateTopicRequest


class TestContentCreatorService:
    """Unit tests for ContentCreatorService."""

    @pytest.mark.asyncio
    async def test_create_topic_from_source_material(self):
        """Test creating a topic from source material."""
        # Arrange
        content = Mock()
        llm = Mock()
        service = ContentCreatorService(content, llm)

        request = CreateTopicRequest(title="Test Topic", core_concept="Test Concept", source_material="Test material content", user_level="beginner", domain="Testing")

        # Mock the LLM response and content saving
        service._extract_topic_content = AsyncMock(
            return_value={
                "learning_objectives": ["Learn X", "Understand Y"],
                "key_concepts": ["Concept A", "Concept B"],
                "refined_material": {"overview": "Test overview"},
                "didactic_snippet": {"explanation": "Test explanation", "key_points": ["Point 1"]},
                "glossary": {"terms": [{"term": "Test Term", "definition": "Test definition"}]},
                "mcqs": [{"question": "What is X?", "options": ["A", "B", "C", "D"], "correct_answer": 0}],
            }
        )

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
        assert result.components_created == 3  # didactic_snippet, glossary, 1 MCQ
        content.save_topic.assert_called_once()
        assert content.save_component.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_component_mcq(self):
        """Test generating an MCQ component for existing topic."""
        # Arrange
        content = Mock()
        llm = Mock()
        service = ContentCreatorService(content, llm)

        # Mock existing topic
        from modules.content.service import TopicRead

        mock_topic = TopicRead(
            id="test-id", title="Test Topic", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Concept A"], created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00", components=[]
        )
        content.get_topic.return_value = mock_topic
        content.save_component.return_value = Mock()

        # Mock LLM generation
        service._generate_mcq = AsyncMock(return_value={"question": "What is X?", "options": ["A", "B", "C", "D"], "correct_answer": 0})

        request = CreateComponentRequest(component_type="mcq", learning_objective="Learn about X")

        # Act
        result = await service.generate_component("test-id", request)

        # Assert
        assert isinstance(result, str)  # Returns component ID
        content.get_topic.assert_called_once_with("test-id")
        content.save_component.assert_called_once()
        service._generate_mcq.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_component_topic_not_found(self):
        """Test that generate_component raises error when topic doesn't exist."""
        # Arrange
        content = Mock()
        llm = Mock()
        service = ContentCreatorService(content, llm)

        content.get_topic.return_value = None

        request = CreateComponentRequest(component_type="mcq", learning_objective="Learn about X")

        # Act & Assert
        with pytest.raises(ValueError, match="Topic nonexistent not found"):
            await service.generate_component("nonexistent", request)

    @pytest.mark.asyncio
    async def test_generate_component_unsupported_type(self):
        """Test that generate_component raises error for unsupported component type."""
        # Arrange
        content = Mock()
        llm = Mock()
        service = ContentCreatorService(content, llm)

        # Mock existing topic
        from modules.content.service import TopicRead

        mock_topic = TopicRead(
            id="test-id", title="Test Topic", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Concept A"], created_at="2024-01-01T00:00:00", updated_at="2024-01-01T00:00:00", components=[]
        )
        content.get_topic.return_value = mock_topic

        request = CreateComponentRequest(component_type="unsupported_type", learning_objective="Learn about X")

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported component type: unsupported_type"):
            await service.generate_component("test-id", request)
