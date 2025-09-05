"""
Unit tests for Topic Discovery Service.

These tests focus on the application logic for topic discovery and filtering.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from modules.topic_catalog.application.topic_discovery_service import (
    TopicDiscoveryError,
    TopicDiscoveryService,
)
from modules.topic_catalog.domain.entities.catalog import Catalog
from modules.topic_catalog.domain.entities.topic_summary import TopicSummary
from modules.topic_catalog.domain.policies.search_policy import SearchPolicy


class TestTopicDiscoveryService:
    """Test cases for TopicDiscoveryService."""

    @pytest.fixture
    def mock_catalog_repository(self):
        """Create a mock catalog repository."""
        repository = AsyncMock()
        return repository

    @pytest.fixture
    def topic_discovery_service(self, mock_catalog_repository):
        """Create topic discovery service with mocked dependencies."""
        return TopicDiscoveryService(catalog_repository=mock_catalog_repository)

    @pytest.fixture
    def sample_topic_summaries(self):
        """Create sample topic summaries for testing."""
        return [
            TopicSummary(
                topic_id="topic_1",
                title="Python Variables",
                core_concept="Understanding variable declaration",
                user_level="beginner",
                learning_objectives=["Declare variables"],
                key_concepts=["variable", "assignment"],
                estimated_duration=15,
                component_count=3,
                is_ready_for_learning=True,
            ),
            TopicSummary(
                topic_id="topic_2",
                title="Python Functions",
                core_concept="Creating and using functions",
                user_level="intermediate",
                learning_objectives=["Define functions", "Call functions"],
                key_concepts=["function", "parameter", "return"],
                estimated_duration=25,
                component_count=5,
                is_ready_for_learning=True,
            ),
            TopicSummary(
                topic_id="topic_3",
                title="Advanced Python Decorators",
                core_concept="Understanding decorators",
                user_level="advanced",
                learning_objectives=["Create decorators"],
                key_concepts=["decorator", "wrapper"],
                estimated_duration=45,
                component_count=7,
                is_ready_for_learning=False,
            ),
        ]

    @pytest.fixture
    def sample_catalog(self, sample_topic_summaries):
        """Create a sample catalog for testing."""
        return Catalog(
            topics=sample_topic_summaries,
            last_updated=datetime.now(UTC),
            total_count=len(sample_topic_summaries),
        )

    @pytest.mark.asyncio
    async def test_discover_topics_with_query(self, topic_discovery_service, mock_catalog_repository, sample_catalog):
        """Test topic discovery with search query."""
        # Arrange
        mock_catalog_repository.get_catalog.return_value = sample_catalog

        # Act
        result = await topic_discovery_service.discover_topics(query="Python", user_level=None, limit=10, offset=0)

        # Assert
        assert len(result) == 3  # All topics match "Python"
        assert all("Python" in topic.title for topic in result)
        mock_catalog_repository.get_catalog.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_topics_with_user_level_filter(self, topic_discovery_service, mock_catalog_repository, sample_catalog):
        """Test topic discovery with user level filter."""
        # Arrange
        mock_catalog_repository.get_catalog.return_value = sample_catalog

        # Act
        result = await topic_discovery_service.discover_topics(query=None, user_level="beginner", limit=10, offset=0)

        # Assert
        assert len(result) == 1
        assert result[0].user_level == "beginner"
        assert result[0].title == "Python Variables"

    @pytest.mark.asyncio
    async def test_discover_topics_with_pagination(self, topic_discovery_service, mock_catalog_repository, sample_catalog):
        """Test topic discovery with pagination."""
        # Arrange
        mock_catalog_repository.get_catalog.return_value = sample_catalog

        # Act
        result = await topic_discovery_service.discover_topics(query=None, limit=2, offset=1)

        # Assert
        assert len(result) == 2
        # Should skip the first topic and return the next 2
        assert result[0].title == "Python Functions"
        assert result[1].title == "Advanced Python Decorators"

    @pytest.mark.asyncio
    async def test_discover_topics_ready_only_filter(self, topic_discovery_service, mock_catalog_repository, sample_catalog):
        """Test topic discovery filtering for ready topics only."""
        # Arrange
        mock_catalog_repository.get_catalog.return_value = sample_catalog

        # Act
        result = await topic_discovery_service.discover_topics(query=None, ready_only=True, limit=10, offset=0)

        # Assert
        assert len(result) == 2  # Only 2 topics are ready
        assert all(topic.is_ready_for_learning for topic in result)

    @pytest.mark.asyncio
    async def test_get_topic_by_id_success(self, topic_discovery_service, mock_catalog_repository, sample_catalog):
        """Test successful topic retrieval by ID."""
        # Arrange
        mock_catalog_repository.get_catalog.return_value = sample_catalog

        # Act
        result = await topic_discovery_service.get_topic_by_id("topic_1")

        # Assert
        assert result.topic_id == "topic_1"
        assert result.title == "Python Variables"

    @pytest.mark.asyncio
    async def test_get_topic_by_id_not_found(self, topic_discovery_service, mock_catalog_repository, sample_catalog):
        """Test topic retrieval when topic not found."""
        # Arrange
        mock_catalog_repository.get_catalog.return_value = sample_catalog

        # Act & Assert
        with pytest.raises(TopicDiscoveryError, match="Topic not found"):
            await topic_discovery_service.get_topic_by_id("nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_popular_topics(self, topic_discovery_service, mock_catalog_repository, sample_catalog):
        """Test popular topics retrieval."""
        # Arrange
        mock_catalog_repository.get_catalog.return_value = sample_catalog

        # Act
        result = await topic_discovery_service.get_popular_topics(limit=2)

        # Assert
        assert len(result) == 2
        # Should return ready topics first, sorted by component count (descending)
        assert result[0].component_count >= result[1].component_count

    @pytest.mark.asyncio
    async def test_get_catalog_statistics(self, topic_discovery_service, mock_catalog_repository, sample_catalog):
        """Test catalog statistics generation."""
        # Arrange
        mock_catalog_repository.get_catalog.return_value = sample_catalog

        # Act
        result = await topic_discovery_service.get_catalog_statistics()

        # Assert
        assert result["total_topics"] == 3
        assert result["topics_by_user_level"]["beginner"] == 1
        assert result["topics_by_user_level"]["intermediate"] == 1
        assert result["topics_by_user_level"]["advanced"] == 1
        assert result["topics_by_readiness"]["ready"] == 2
        assert result["topics_by_readiness"]["not_ready"] == 1
        assert result["average_duration"] == (15 + 25 + 45) / 3

    @pytest.mark.asyncio
    async def test_refresh_catalog(self, topic_discovery_service, mock_catalog_repository):
        """Test catalog refresh."""
        # Arrange
        mock_catalog_repository.refresh_catalog.return_value = {
            "refreshed_topics": 10,
            "total_topics": 50,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Act
        result = await topic_discovery_service.refresh_catalog()

        # Assert
        assert result["refreshed_topics"] == 10
        assert result["total_topics"] == 50
        assert "timestamp" in result
        mock_catalog_repository.refresh_catalog.assert_called_once()

    @pytest.mark.asyncio
    async def test_repository_error_handling(self, topic_discovery_service, mock_catalog_repository):
        """Test error handling when repository fails."""
        # Arrange
        mock_catalog_repository.get_catalog.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(TopicDiscoveryError, match="Failed to retrieve catalog"):
            await topic_discovery_service.discover_topics()

    def test_search_policy_integration(self, topic_discovery_service, sample_topic_summaries):
        """Test that search policy is properly applied."""
        # Arrange
        policy = SearchPolicy()

        # Act
        filtered_topics = policy.apply_filters(topics=sample_topic_summaries, query="Functions", user_level="intermediate", ready_only=True)

        # Assert
        assert len(filtered_topics) == 1
        assert filtered_topics[0].title == "Python Functions"

    def test_search_policy_sorting(self, topic_discovery_service, sample_topic_summaries):
        """Test that search policy sorting works correctly."""
        # Arrange
        policy = SearchPolicy()

        # Act - sort by relevance (component count descending)
        sorted_topics = policy.sort_by_relevance(sample_topic_summaries)

        # Assert
        assert sorted_topics[0].component_count == 7  # Advanced Python Decorators
        assert sorted_topics[1].component_count == 5  # Python Functions
        assert sorted_topics[2].component_count == 3  # Python Variables
