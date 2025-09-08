"""
Content Module - Unit Tests

Tests for the content module service layer.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

from modules.content.models import ComponentModel, TopicModel
from modules.content.repo import ContentRepo
from modules.content.service import ComponentCreate, ContentService, TopicCreate


class TestContentService:
    """Unit tests for ContentService."""

    def test_get_topic_returns_none_when_not_found(self):
        """Test that get_topic returns None when topic doesn't exist."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        repo.get_topic_by_id.return_value = None
        service = ContentService(repo)

        # Act
        result = service.get_topic("nonexistent")

        # Assert
        assert result is None
        repo.get_topic_by_id.assert_called_once_with("nonexistent")

    def test_get_topic_returns_topic_with_components(self):
        """Test that get_topic returns topic with components when found."""
        # Arrange
        repo = Mock(spec=ContentRepo)

        # Mock topic
        mock_topic = TopicModel(id="test-id", title="Test Topic", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Concept A"], created_at=datetime.now(UTC), updated_at=datetime.now(UTC))

        # Mock components
        mock_component = ComponentModel(id="comp-id", topic_id="test-id", component_type="mcq", title="Test MCQ", content={"question": "What is X?"}, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))

        repo.get_topic_by_id.return_value = mock_topic
        repo.get_components_by_topic_id.return_value = [mock_component]

        service = ContentService(repo)

        # Act
        result = service.get_topic("test-id")

        # Assert
        assert result is not None
        assert result.id == "test-id"
        assert result.title == "Test Topic"
        assert len(result.components) == 1
        assert result.components[0].id == "comp-id"

        repo.get_topic_by_id.assert_called_once_with("test-id")
        repo.get_components_by_topic_id.assert_called_once_with("test-id")

    def test_save_topic_creates_new_topic(self):
        """Test that save_topic creates a new topic."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        service = ContentService(repo)

        topic_data = TopicCreate(id="test-id", title="Test Topic", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Concept A"])

        # Mock the saved topic
        mock_saved_topic = TopicModel(id="test-id", title="Test Topic", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Concept A"], created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        repo.save_topic.return_value = mock_saved_topic

        # Act
        result = service.save_topic(topic_data)

        # Assert
        assert result.id == "test-id"
        assert result.title == "Test Topic"
        assert len(result.components) == 0  # New topic has no components
        repo.save_topic.assert_called_once()

    def test_save_component_creates_new_component(self):
        """Test that save_component creates a new component."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        service = ContentService(repo)

        component_data = ComponentCreate(id="comp-id", topic_id="test-id", component_type="mcq", title="Test MCQ", content={"question": "What is X?"}, learning_objective="Learn X")

        # Mock the saved component
        mock_saved_component = ComponentModel(id="comp-id", topic_id="test-id", component_type="mcq", title="Test MCQ", content={"question": "What is X?"}, learning_objective="Learn X", created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        repo.save_component.return_value = mock_saved_component

        # Act
        result = service.save_component(component_data)

        # Assert
        assert result.id == "comp-id"
        assert result.topic_id == "test-id"
        assert result.component_type == "mcq"
        repo.save_component.assert_called_once()

    def test_topic_exists_returns_true_when_exists(self):
        """Test that topic_exists returns True when topic exists."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        repo.topic_exists.return_value = True
        service = ContentService(repo)

        # Act
        result = service.topic_exists("test-id")

        # Assert
        assert result is True
        repo.topic_exists.assert_called_once_with("test-id")

    def test_delete_topic_returns_true_when_deleted(self):
        """Test that delete_topic returns True when topic is deleted."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        repo.delete_topic.return_value = True
        service = ContentService(repo)

        # Act
        result = service.delete_topic("test-id")

        # Assert
        assert result is True
        repo.delete_topic.assert_called_once_with("test-id")
