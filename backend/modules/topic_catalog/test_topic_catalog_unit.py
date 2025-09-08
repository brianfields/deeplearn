"""
Topic Catalog Module - Unit Tests

Tests for the topic catalog service layer.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

from modules.topic_catalog.service import TopicCatalogService


class TestTopicCatalogService:
    """Unit tests for TopicCatalogService."""

    def test_browse_topics_returns_summaries(self):
        """Test that browse_topics returns topic summaries."""
        # Arrange
        content = Mock()

        # Mock topics from content module
        from modules.content.service import ComponentRead, TopicRead

        mock_topics = [
            TopicRead(
                id="topic-1",
                title="Topic 1",
                core_concept="Concept 1",
                user_level="beginner",
                learning_objectives=["Learn A"],
                key_concepts=["Key A"],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                components=[ComponentRead(id="comp-1", topic_id="topic-1", component_type="mcq", title="MCQ 1", content={"question": "What is A?"}, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))],
            ),
            TopicRead(id="topic-2", title="Topic 2", core_concept="Concept 2", user_level="intermediate", learning_objectives=["Learn B"], key_concepts=["Key B"], created_at=datetime.now(UTC), updated_at=datetime.now(UTC), components=[]),
        ]

        content.search_topics.return_value = mock_topics
        service = TopicCatalogService(content)

        # Act
        result = service.browse_topics(user_level="beginner", limit=10)

        # Assert
        assert len(result.topics) == 2
        assert result.total == 2
        assert result.topics[0].id == "topic-1"
        assert result.topics[0].component_count == 1
        assert result.topics[1].component_count == 0

        content.search_topics.assert_called_once_with(user_level="beginner", limit=10)

    def test_get_topic_details_returns_details(self):
        """Test that get_topic_details returns topic details."""
        # Arrange
        content = Mock()

        from modules.content.service import ComponentRead, TopicRead

        mock_topic = TopicRead(
            id="topic-1",
            title="Topic 1",
            core_concept="Concept 1",
            user_level="beginner",
            learning_objectives=["Learn A"],
            key_concepts=["Key A"],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            components=[ComponentRead(id="comp-1", topic_id="topic-1", component_type="mcq", title="MCQ 1", content={"question": "What is A?"}, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))],
        )

        content.get_topic.return_value = mock_topic
        service = TopicCatalogService(content)

        # Act
        result = service.get_topic_details("topic-1")

        # Assert
        assert result is not None
        assert result.id == "topic-1"
        assert result.title == "Topic 1"
        assert result.component_count == 1
        assert len(result.components) == 1
        assert result.is_ready_for_learning() is True

        content.get_topic.assert_called_once_with("topic-1")

    def test_get_topic_details_returns_none_when_not_found(self):
        """Test that get_topic_details returns None when topic doesn't exist."""
        # Arrange
        content = Mock()
        content.get_topic.return_value = None
        service = TopicCatalogService(content)

        # Act
        result = service.get_topic_details("nonexistent")

        # Assert
        assert result is None
        content.get_topic.assert_called_once_with("nonexistent")

    def test_topic_summary_matches_user_level(self):
        """Test TopicSummary.matches_user_level method."""
        # Arrange
        from modules.topic_catalog.service import TopicSummary

        summary = TopicSummary(id="test-id", title="Test Topic", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Key X"], component_count=1)

        # Act & Assert
        assert summary.matches_user_level("beginner") is True
        assert summary.matches_user_level("intermediate") is False

    def test_topic_detail_is_ready_for_learning(self):
        """Test TopicDetail.is_ready_for_learning method."""
        # Arrange
        from modules.topic_catalog.service import TopicDetail

        # Topic with components
        detail_with_components = TopicDetail(
            id="test-id",
            title="Test Topic",
            core_concept="Test Concept",
            user_level="beginner",
            learning_objectives=["Learn X"],
            key_concepts=["Key X"],
            components=[{"type": "mcq", "content": "test"}],
            created_at="2024-01-01T00:00:00",
            component_count=1,
        )

        # Topic without components
        detail_without_components = TopicDetail(
            id="test-id-2", title="Test Topic 2", core_concept="Test Concept 2", user_level="beginner", learning_objectives=["Learn Y"], key_concepts=["Key Y"], components=[], created_at="2024-01-01T00:00:00", component_count=0
        )

        # Act & Assert
        assert detail_with_components.is_ready_for_learning() is True
        assert detail_without_components.is_ready_for_learning() is False
