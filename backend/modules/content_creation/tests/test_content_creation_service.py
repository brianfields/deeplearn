"""
Unit tests for Content Creation Service.

These tests use mocks and focus on the service orchestration logic.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.content_creation.domain.entities.component import Component
from modules.content_creation.domain.entities.topic import Topic
from modules.content_creation.module_api import (
    ComponentResponse,
    ContentCreationError,
    ContentCreationService,
    CreateComponentRequest,
    CreateTopicRequest,
    TopicResponse,
)


class TestContentCreationService:
    """Test cases for ContentCreationService."""

    @pytest.fixture
    def mock_topic_repository(self):
        """Create a mock topic repository."""
        repository = AsyncMock()
        return repository

    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service."""
        service = AsyncMock()
        return service

    @pytest.fixture
    def content_creation_service(self, mock_topic_repository, mock_llm_service):
        """Create content creation service with mocked dependencies."""
        return ContentCreationService(topic_repository=mock_topic_repository, llm_service=mock_llm_service)

    @pytest.fixture
    def sample_topic(self):
        """Create a sample topic for testing."""
        return Topic(
            title="Python Variables",
            core_concept="Understanding variable declaration and usage",
            user_level="beginner",
            learning_objectives=["Declare variables", "Assign values"],
            key_concepts=["variable", "assignment"],
            source_material="Variables in Python are used to store data...",
            refined_material={"topics": [{"learning_objectives": ["Declare variables"], "key_facts": ["variable"]}]},
        )

    @pytest.fixture
    def sample_component(self, sample_topic):
        """Create a sample component for testing."""
        return Component(
            topic_id=sample_topic.id,
            component_type="mcq",
            title="MCQ: Variable Declaration",
            content={"question": "How do you declare a variable?", "choices": {"A": "var x", "B": "x = 5", "C": "int x", "D": "declare x"}, "correct_answer": "B", "explanation": "In Python, you assign a value to create a variable."},
            learning_objective="Declare variables",
        )

    @pytest.mark.asyncio
    async def test_create_topic_from_source_material_success(self, content_creation_service, mock_topic_repository, sample_topic):
        """Test successful topic creation from source material."""
        # Arrange
        request = CreateTopicRequest(
            title="Python Variables",
            core_concept="Understanding variables",
            source_material="Variables in Python are used to store data values. A variable is created the moment you first assign a value to it. Python has no command for declaring a variable. You can use variables to store different types of data.",
            user_level="beginner",
        )

        # Mock the material extraction service by setting the private attribute
        mock_extraction = AsyncMock()
        mock_extraction.extract_topic_from_source_material.return_value = sample_topic
        content_creation_service._material_extraction_service = mock_extraction
        mock_topic_repository.save.return_value = sample_topic

        # Act
        result = await content_creation_service.create_topic_from_source_material(request)

        # Assert
        assert isinstance(result, TopicResponse)
        assert result.title == "Python Variables"
        assert result.user_level == "beginner"
        mock_extraction.extract_topic_from_source_material.assert_called_once()
        mock_topic_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_topic_success(self, content_creation_service, mock_topic_repository, sample_topic, sample_component):
        """Test successful topic retrieval."""
        # Arrange
        topic_id = sample_topic.id
        mock_topic_repository.get_by_id.return_value = sample_topic
        mock_topic_repository.get_components_by_topic_id.return_value = [sample_component]

        # Act
        result = await content_creation_service.get_topic(topic_id)

        # Assert
        assert isinstance(result, TopicResponse)
        assert result.id == topic_id
        assert len(result.components) == 1
        mock_topic_repository.get_by_id.assert_called_once_with(topic_id)
        mock_topic_repository.get_components_by_topic_id.assert_called_once_with(topic_id)

    @pytest.mark.asyncio
    async def test_create_mcq_component_success(self, content_creation_service, mock_topic_repository, sample_topic, sample_component):
        """Test successful MCQ component creation."""
        # Arrange
        request = CreateComponentRequest(component_type="mcq", learning_objective="Declare variables")

        mock_topic_repository.get_by_id.return_value = sample_topic
        mock_topic_repository.save_component.return_value = sample_component
        mock_topic_repository.save.return_value = sample_topic

        # Mock the MCQ generation service by patching the property
        mock_mcq_gen = AsyncMock()
        mock_mcq_gen.generate_mcq_for_topic.return_value = sample_component
        content_creation_service._mcq_generation_service = mock_mcq_gen

        # Act
        result = await content_creation_service.create_component(sample_topic.id, request)

        # Assert
        assert isinstance(result, ComponentResponse)
        assert result.component_type == "mcq"
        assert result.learning_objective == "Declare variables"
        mock_mcq_gen.generate_mcq_for_topic.assert_called_once()
        mock_topic_repository.save_component.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_placeholder_component_success(self, content_creation_service, mock_topic_repository, sample_topic):
        """Test successful placeholder component creation."""
        # Arrange
        request = CreateComponentRequest(component_type="didactic_snippet", learning_objective="Understand concepts")

        mock_topic_repository.get_by_id.return_value = sample_topic
        mock_topic_repository.save_component.return_value = MagicMock()
        mock_topic_repository.save.return_value = sample_topic

        # Mock the save_component to return a component with the expected attributes
        placeholder_component = Component(
            topic_id=sample_topic.id,
            component_type="didactic_snippet",
            title="Didactic Snippet",
            content={"type": "didactic_snippet", "learning_objective": "Understand concepts", "placeholder": True, "explanation": "This is a placeholder explanation", "key_points": ["Point 1", "Point 2"]},
            learning_objective="Understand concepts",
        )
        mock_topic_repository.save_component.return_value = placeholder_component

        # Act
        result = await content_creation_service.create_component(sample_topic.id, request)

        # Assert
        assert isinstance(result, ComponentResponse)
        assert result.component_type == "didactic_snippet"
        assert result.content["placeholder"] is True
        mock_topic_repository.save_component.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_component_success(self, content_creation_service, mock_topic_repository, sample_topic):
        """Test successful component deletion."""
        # Arrange
        component_id = "comp_123"
        mock_topic_repository.get_by_id.return_value = sample_topic
        mock_topic_repository.delete_component.return_value = True
        mock_topic_repository.save.return_value = sample_topic

        # Act
        result = await content_creation_service.delete_component(sample_topic.id, component_id)

        # Assert
        assert result is True
        mock_topic_repository.delete_component.assert_called_once_with(component_id)

    @pytest.mark.asyncio
    async def test_delete_topic_success(self, content_creation_service, mock_topic_repository, sample_topic):
        """Test successful topic deletion."""
        # Arrange
        topic_id = sample_topic.id
        mock_topic_repository.delete.return_value = True

        # Act
        result = await content_creation_service.delete_topic(topic_id)

        # Assert
        assert result is True
        mock_topic_repository.delete.assert_called_once_with(topic_id)

    @pytest.mark.asyncio
    async def test_generate_all_components_success(self, content_creation_service, mock_topic_repository, sample_topic, sample_component):
        """Test successful generation of all components."""
        # Arrange
        mock_topic_repository.get_by_id.return_value = sample_topic
        mock_topic_repository.save_component.return_value = sample_component
        mock_topic_repository.save.return_value = sample_topic

        # Mock the MCQ generation service by setting the private attribute
        mock_mcq_gen = AsyncMock()
        mock_mcq_gen.generate_mcqs_for_all_objectives.return_value = [sample_component]
        content_creation_service._mcq_generation_service = mock_mcq_gen

        # Act
        result = await content_creation_service.generate_all_components_for_topic(sample_topic.id)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ComponentResponse)
        mock_mcq_gen.generate_mcqs_for_all_objectives.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_topics_success(self, content_creation_service, mock_topic_repository, sample_topic):
        """Test successful retrieval of all topics."""
        # Arrange
        mock_topic_repository.get_all.return_value = [sample_topic]
        mock_topic_repository.get_components_by_topic_id.return_value = []

        # Act
        result = await content_creation_service.get_all_topics(limit=10, offset=0)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TopicResponse)
        mock_topic_repository.get_all.assert_called_once_with(limit=10, offset=0)

    @pytest.mark.asyncio
    async def test_search_topics_success(self, content_creation_service, mock_topic_repository, sample_topic):
        """Test successful topic search."""
        # Arrange
        mock_topic_repository.search.return_value = [sample_topic]
        mock_topic_repository.get_components_by_topic_id.return_value = []

        # Act
        result = await content_creation_service.search_topics(query="Python", user_level="beginner", limit=10, offset=0)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TopicResponse)
        mock_topic_repository.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_topic_validation_error(self, content_creation_service, mock_topic_repository):
        """Test topic creation with validation error."""
        # Arrange
        # This test should check service-level validation, not Pydantic validation
        # So we'll create a valid request but mock the service to raise an error
        request = CreateTopicRequest(title="Valid Title", core_concept="Test concept", source_material="This is a longer source material that meets the minimum length requirement of 100 characters for the validation to pass.", user_level="beginner")

        # Mock the material extraction service to raise validation error
        mock_extraction = AsyncMock()
        from modules.content_creation.domain.entities.topic import InvalidTopicError

        mock_extraction.extract_topic_from_source_material.side_effect = InvalidTopicError("Invalid title")
        content_creation_service._material_extraction_service = mock_extraction

        # Act & Assert
        with pytest.raises(ContentCreationError):
            await content_creation_service.create_topic_from_source_material(request)

    @pytest.mark.asyncio
    async def test_get_topic_not_found(self, content_creation_service, mock_topic_repository):
        """Test topic retrieval when topic not found."""
        # Arrange
        from modules.content_creation.domain.repositories.topic_repository import TopicNotFoundError

        mock_topic_repository.get_by_id.side_effect = TopicNotFoundError("Topic not found")

        # Act & Assert
        with pytest.raises(ContentCreationError):
            await content_creation_service.get_topic("nonexistent_id")

    def test_service_without_llm_service(self, mock_topic_repository):
        """Test service initialization without LLM service."""
        # Arrange & Act
        service = ContentCreationService(topic_repository=mock_topic_repository, llm_service=None)

        # Assert
        assert service.llm_service is None

        # Accessing application services should raise error
        with pytest.raises(ContentCreationError):
            _ = service.material_extraction_service

        with pytest.raises(ContentCreationError):
            _ = service.mcq_generation_service
