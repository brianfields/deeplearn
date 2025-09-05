"""
Unit tests for Content Creation Catalog Repository.

These tests focus on the integration with the Content Creation module.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from modules.topic_catalog.infrastructure.persistence.content_creation_catalog_repository import (
    ContentCreationCatalogRepository,
)


class TestContentCreationCatalogRepository:
    """Test cases for ContentCreationCatalogRepository."""

    @pytest.fixture
    def mock_content_creation_service(self):
        """Create a mock content creation service."""
        service = AsyncMock()
        return service

    @pytest.fixture
    def catalog_repository(self, mock_content_creation_service):
        """Create catalog repository with mocked dependencies."""
        return ContentCreationCatalogRepository(content_creation_service=mock_content_creation_service)

    @pytest.fixture
    def sample_topic_responses(self):
        """Create sample topic responses from content creation service."""
        from modules.content_creation.module_api.types import TopicSummaryResponse

        return [
            TopicSummaryResponse(
                id="topic_1",
                title="Python Variables",
                core_concept="Understanding variable declaration",
                user_level="beginner",
                learning_objectives=["Declare variables", "Assign values"],
                key_concepts=["variable", "assignment"],
                estimated_duration=15,
                component_count=3,
                is_ready_for_learning=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            TopicSummaryResponse(
                id="topic_2",
                title="Python Functions",
                core_concept="Creating and using functions",
                user_level="intermediate",
                learning_objectives=["Define functions", "Call functions"],
                key_concepts=["function", "parameter", "return"],
                estimated_duration=25,
                component_count=5,
                is_ready_for_learning=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]

    @pytest.mark.asyncio
    async def test_get_catalog_success(self, catalog_repository, mock_content_creation_service, sample_topic_responses):
        """Test successful catalog retrieval."""
        # Arrange
        mock_content_creation_service.list_topics.return_value = sample_topic_responses

        # Act
        catalog = await catalog_repository.get_catalog()

        # Assert
        assert catalog is not None
        assert len(catalog.topics) == 2
        assert catalog.total_count == 2

        # Check first topic conversion
        first_topic = catalog.topics[0]
        assert first_topic.topic_id == "topic_1"
        assert first_topic.title == "Python Variables"
        assert first_topic.user_level == "beginner"
        assert first_topic.component_count == 3

        # Check second topic conversion
        second_topic = catalog.topics[1]
        assert second_topic.topic_id == "topic_2"
        assert second_topic.title == "Python Functions"
        assert second_topic.user_level == "intermediate"
        assert second_topic.component_count == 5

        mock_content_creation_service.list_topics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_catalog_empty_result(self, catalog_repository, mock_content_creation_service):
        """Test catalog retrieval with empty result."""
        # Arrange
        mock_content_creation_service.list_topics.return_value = []

        # Act
        catalog = await catalog_repository.get_catalog()

        # Assert
        assert catalog is not None
        assert len(catalog.topics) == 0
        assert catalog.total_count == 0

    @pytest.mark.asyncio
    async def test_get_catalog_service_error(self, catalog_repository, mock_content_creation_service):
        """Test catalog retrieval when content creation service fails."""
        # Arrange
        mock_content_creation_service.list_topics.side_effect = Exception("Service unavailable")

        # Act & Assert
        with pytest.raises(Exception, match="Service unavailable"):
            await catalog_repository.get_catalog()

    @pytest.mark.asyncio
    async def test_refresh_catalog_success(self, catalog_repository, mock_content_creation_service):
        """Test successful catalog refresh."""
        # Arrange
        expected_result = {
            "refreshed_topics": 10,
            "total_topics": 50,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        mock_content_creation_service.refresh_topic_cache.return_value = expected_result

        # Act
        result = await catalog_repository.refresh_catalog()

        # Assert
        assert result == expected_result
        mock_content_creation_service.refresh_topic_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_catalog_service_error(self, catalog_repository, mock_content_creation_service):
        """Test catalog refresh when content creation service fails."""
        # Arrange
        mock_content_creation_service.refresh_topic_cache.side_effect = Exception("Refresh failed")

        # Act & Assert
        with pytest.raises(Exception, match="Refresh failed"):
            await catalog_repository.refresh_catalog()

    def test_convert_topic_response_to_summary(self, catalog_repository):
        """Test conversion from TopicSummaryResponse to TopicSummary."""
        # Arrange
        from modules.content_creation.module_api.types import TopicSummaryResponse

        topic_response = TopicSummaryResponse(
            id="topic_123",
            title="Test Topic",
            core_concept="Test concept",
            user_level="beginner",
            learning_objectives=["Objective 1", "Objective 2"],
            key_concepts=["concept1", "concept2"],
            estimated_duration=30,
            component_count=4,
            is_ready_for_learning=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Act
        topic_summary = catalog_repository._convert_topic_response_to_summary(topic_response)

        # Assert
        assert topic_summary.topic_id == "topic_123"
        assert topic_summary.title == "Test Topic"
        assert topic_summary.core_concept == "Test concept"
        assert topic_summary.user_level == "beginner"
        assert topic_summary.learning_objectives == ["Objective 1", "Objective 2"]
        assert topic_summary.key_concepts == ["concept1", "concept2"]
        assert topic_summary.estimated_duration == 30
        assert topic_summary.component_count == 4
        assert topic_summary.is_ready_for_learning is True

    def test_convert_topic_response_minimal_data(self, catalog_repository):
        """Test conversion with minimal required data."""
        # Arrange
        from modules.content_creation.module_api.types import TopicSummaryResponse

        topic_response = TopicSummaryResponse(
            id="topic_min",
            title="Minimal Topic",
            core_concept="Minimal concept",
            user_level="intermediate",
            learning_objectives=["Single objective"],
            key_concepts=["single_concept"],
            estimated_duration=10,
            component_count=1,
            is_ready_for_learning=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Act
        topic_summary = catalog_repository._convert_topic_response_to_summary(topic_response)

        # Assert
        assert topic_summary.topic_id == "topic_min"
        assert topic_summary.title == "Minimal Topic"
        assert topic_summary.is_ready_for_learning is False
        assert topic_summary.component_count == 1

    @pytest.mark.asyncio
    async def test_get_catalog_caching_behavior(self, catalog_repository, mock_content_creation_service, sample_topic_responses):
        """Test that catalog retrieval doesn't implement caching at repository level."""
        # Arrange
        mock_content_creation_service.list_topics.return_value = sample_topic_responses

        # Act
        catalog1 = await catalog_repository.get_catalog()
        catalog2 = await catalog_repository.get_catalog()

        # Assert
        # Repository should call service each time (no caching at this level)
        assert mock_content_creation_service.list_topics.call_count == 2
        assert catalog1.total_count == catalog2.total_count

    @pytest.mark.asyncio
    async def test_get_catalog_with_different_topic_states(self, catalog_repository, mock_content_creation_service):
        """Test catalog retrieval with topics in different states."""
        # Arrange
        from modules.content_creation.module_api.types import TopicSummaryResponse

        mixed_topics = [
            TopicSummaryResponse(
                id="ready_topic",
                title="Ready Topic",
                core_concept="Ready concept",
                user_level="beginner",
                learning_objectives=["Learn ready"],
                key_concepts=["ready"],
                estimated_duration=15,
                component_count=3,
                is_ready_for_learning=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            TopicSummaryResponse(
                id="not_ready_topic",
                title="Not Ready Topic",
                core_concept="Not ready concept",
                user_level="advanced",
                learning_objectives=["Learn advanced"],
                key_concepts=["advanced"],
                estimated_duration=60,
                component_count=0,  # No components yet
                is_ready_for_learning=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]
        mock_content_creation_service.list_topics.return_value = mixed_topics

        # Act
        catalog = await catalog_repository.get_catalog()

        # Assert
        assert len(catalog.topics) == 2

        ready_topics = [t for t in catalog.topics if t.is_ready_for_learning]
        not_ready_topics = [t for t in catalog.topics if not t.is_ready_for_learning]

        assert len(ready_topics) == 1
        assert len(not_ready_topics) == 1
        assert ready_topics[0].component_count == 3
        assert not_ready_topics[0].component_count == 0
