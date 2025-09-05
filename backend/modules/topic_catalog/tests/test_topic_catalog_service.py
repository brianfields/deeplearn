"""
Unit tests for Topic Catalog Service.

These tests use mocks and focus on the service orchestration logic.
"""

from unittest.mock import AsyncMock

import pytest

from modules.topic_catalog.domain.entities.topic_summary import TopicSummary
from modules.topic_catalog.module_api import (
    SearchTopicsRequest,
    SearchTopicsResponse,
    TopicCatalogError,
    TopicCatalogService,
    TopicSummaryResponse,
)


class TestTopicCatalogService:
    """Test cases for TopicCatalogService."""

    @pytest.fixture
    def mock_catalog_repository(self):
        """Create a mock catalog repository."""
        repository = AsyncMock()
        return repository

    @pytest.fixture
    def topic_catalog_service(self, mock_catalog_repository):
        """Create topic catalog service with mocked dependencies."""
        return TopicCatalogService(catalog_repository=mock_catalog_repository)

    @pytest.fixture
    def sample_topic_summary(self):
        """Create a sample topic summary for testing."""
        return TopicSummary(
            topic_id="topic_123",
            title="Python Variables",
            core_concept="Understanding variable declaration and usage",
            user_level="beginner",
            learning_objectives=["Declare variables", "Assign values"],
            key_concepts=["variable", "assignment"],
            estimated_duration=15,
            component_count=3,
            is_ready_for_learning=True,
        )

    @pytest.mark.asyncio
    async def test_search_topics_success(self, topic_catalog_service, mock_catalog_repository, sample_topic_summary):
        """Test successful topic search."""
        # Arrange
        request = SearchTopicsRequest(query="Python", user_level="beginner", limit=10, offset=0)

        # Mock the topic discovery service
        mock_discovery = AsyncMock()
        mock_discovery.discover_topics.return_value = [sample_topic_summary]
        topic_catalog_service._topic_discovery_service = mock_discovery

        # Act
        result = await topic_catalog_service.search_topics(request)

        # Assert
        assert isinstance(result, SearchTopicsResponse)
        assert len(result.topics) == 1
        assert result.topics[0].title == "Python Variables"
        assert result.query == "Python"
        mock_discovery.discover_topics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_topic_by_id_success(self, topic_catalog_service, mock_catalog_repository, sample_topic_summary):
        """Test successful topic retrieval by ID."""
        # Arrange
        topic_id = "topic_123"

        # Mock the topic discovery service
        mock_discovery = AsyncMock()
        mock_discovery.get_topic_by_id.return_value = sample_topic_summary
        topic_catalog_service._topic_discovery_service = mock_discovery

        # Act
        result = await topic_catalog_service.get_topic_by_id(topic_id)

        # Assert
        assert isinstance(result, TopicSummaryResponse)
        assert result.id == topic_id
        assert result.title == "Python Variables"
        mock_discovery.get_topic_by_id.assert_called_once_with(topic_id)

    @pytest.mark.asyncio
    async def test_get_popular_topics_success(self, topic_catalog_service, mock_catalog_repository, sample_topic_summary):
        """Test successful popular topics retrieval."""
        # Arrange
        limit = 5

        # Mock the topic discovery service
        mock_discovery = AsyncMock()
        mock_discovery.get_popular_topics.return_value = [sample_topic_summary]
        topic_catalog_service._topic_discovery_service = mock_discovery

        # Act
        result = await topic_catalog_service.get_popular_topics(limit=limit)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TopicSummaryResponse)
        assert result[0].title == "Python Variables"
        mock_discovery.get_popular_topics.assert_called_once_with(limit=limit)

    @pytest.mark.asyncio
    async def test_get_catalog_statistics_success(self, topic_catalog_service, mock_catalog_repository):
        """Test successful catalog statistics retrieval."""
        # Arrange
        mock_stats = {
            "total_topics": 100,
            "topics_by_user_level": {"beginner": 40, "intermediate": 50, "advanced": 10},
            "topics_by_readiness": {"ready": 80, "not_ready": 20},
            "average_duration": 22.5,
            "duration_distribution": {"0-15": 30, "16-30": 50, "31-60": 15, "60+": 5},
        }

        # Mock the topic discovery service
        mock_discovery = AsyncMock()
        mock_discovery.get_catalog_statistics.return_value = mock_stats
        topic_catalog_service._topic_discovery_service = mock_discovery

        # Act
        result = await topic_catalog_service.get_catalog_statistics()

        # Assert
        assert result.total_topics == 100
        assert result.topics_by_user_level["beginner"] == 40
        assert result.average_duration == 22.5
        mock_discovery.get_catalog_statistics.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_topics_discovery_error(self, topic_catalog_service, mock_catalog_repository):
        """Test topic search with discovery error."""
        # Arrange
        request = SearchTopicsRequest(query="Python", limit=10, offset=0)

        # Mock the topic discovery service to raise error
        from modules.topic_catalog.application.topic_discovery_service import TopicDiscoveryError

        mock_discovery = AsyncMock()
        mock_discovery.discover_topics.side_effect = TopicDiscoveryError("Discovery failed")
        topic_catalog_service._topic_discovery_service = mock_discovery

        # Act & Assert
        with pytest.raises(TopicCatalogError):
            await topic_catalog_service.search_topics(request)

    @pytest.mark.asyncio
    async def test_get_topic_not_found(self, topic_catalog_service, mock_catalog_repository):
        """Test topic retrieval when topic not found."""
        # Arrange
        from modules.topic_catalog.application.topic_discovery_service import TopicDiscoveryError

        mock_discovery = AsyncMock()
        mock_discovery.get_topic_by_id.side_effect = TopicDiscoveryError("Topic not found")
        topic_catalog_service._topic_discovery_service = mock_discovery

        # Act & Assert
        with pytest.raises(TopicCatalogError):
            await topic_catalog_service.get_topic_by_id("nonexistent_id")

    @pytest.mark.asyncio
    async def test_refresh_catalog_success(self, topic_catalog_service, mock_catalog_repository):
        """Test successful catalog refresh."""
        # Arrange
        mock_result = {"refreshed_topics": 50, "total_topics": 100, "timestamp": "2024-01-01T12:00:00Z"}

        # Mock the topic discovery service
        mock_discovery = AsyncMock()
        mock_discovery.refresh_catalog.return_value = mock_result
        topic_catalog_service._topic_discovery_service = mock_discovery

        # Act
        result = await topic_catalog_service.refresh_catalog()

        # Assert
        assert result["refreshed_topics"] == 50
        assert result["total_topics"] == 100
        mock_discovery.refresh_catalog.assert_called_once()

    def test_lazy_initialization_of_discovery_service(self, topic_catalog_service):
        """Test that topic discovery service is lazily initialized."""
        # Initially, the service should be None
        assert topic_catalog_service._topic_discovery_service is None

        # Accessing the property should initialize it
        discovery_service = topic_catalog_service.topic_discovery_service
        assert discovery_service is not None
        assert topic_catalog_service._topic_discovery_service is discovery_service

        # Subsequent access should return the same instance
        same_service = topic_catalog_service.topic_discovery_service
        assert same_service is discovery_service
