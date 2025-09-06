"""
Unit tests for Topic Catalog module.

These tests focus on domain entities and service logic in isolation.
They use mocks and don't require external dependencies.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from modules.topic_catalog.domain.entities import TopicDetail, TopicSummary
from modules.topic_catalog.module_api import (
    BrowseTopicsRequest,
    TopicCatalogError,
    TopicCatalogService,
)


class TestTopicSummary:
    """Test TopicSummary domain entity."""

    def test_create_topic_summary(self) -> None:
        """Test creating a topic summary."""
        summary = TopicSummary(
            id="test-id",
            title="Test Topic",
            core_concept="Testing concepts",
            user_level="beginner",
            learning_objectives=["Learn testing"],
            key_concepts=["Unit tests"],
            created_at=datetime.now(UTC),
            component_count=3,
        )

        assert summary.id == "test-id"
        assert summary.title == "Test Topic"
        assert summary.component_count == 3

    def test_matches_user_level(self) -> None:
        """Test user level matching."""
        summary = TopicSummary(
            id="test-id",
            title="Test Topic",
            core_concept="Testing",
            user_level="beginner",
            learning_objectives=[],
            key_concepts=[],
            created_at=datetime.now(UTC),
        )

        assert summary.matches_user_level("beginner") is True
        assert summary.matches_user_level("advanced") is False


class TestTopicDetail:
    """Test TopicDetail domain entity."""

    def test_create_topic_detail(self) -> None:
        """Test creating topic details."""
        detail = TopicDetail(
            id="test-id",
            title="Test Topic",
            core_concept="Testing",
            user_level="beginner",
            learning_objectives=["Learn testing"],
            key_concepts=["Unit tests"],
            key_aspects=["Testing aspects"],
            target_insights=["Testing insights"],
            source_material="Test material",
            refined_material={"content": "refined"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            components=[{"type": "mcq", "question": "Test?"}],
        )

        assert detail.id == "test-id"
        assert detail.component_count == 1
        assert detail.is_ready_for_learning() is True

    def test_empty_components(self) -> None:
        """Test topic with no components."""
        detail = TopicDetail(
            id="test-id",
            title="Test Topic",
            core_concept="Testing",
            user_level="beginner",
            learning_objectives=[],
            key_concepts=[],
            key_aspects=[],
            target_insights=[],
            source_material=None,
            refined_material=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            components=[],
        )

        assert detail.component_count == 0
        assert detail.is_ready_for_learning() is False


class TestTopicCatalogService:
    """Test TopicCatalogService."""

    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Create a mock repository."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repository: AsyncMock) -> TopicCatalogService:
        """Create service with mock repository."""
        return TopicCatalogService(mock_repository)

    @pytest.mark.asyncio
    async def test_browse_topics_success(self, service: TopicCatalogService, mock_repository: AsyncMock) -> None:
        """Test successful topic browsing."""
        # Setup mock
        mock_topics = [
            TopicSummary(
                id="topic-1",
                title="Topic 1",
                core_concept="Concept 1",
                user_level="beginner",
                learning_objectives=["Objective 1"],
                key_concepts=["Concept 1"],
                created_at=datetime.now(UTC),
                component_count=2,
            )
        ]
        mock_repository.list_topics.return_value = mock_topics

        # Execute
        request = BrowseTopicsRequest(user_level="beginner", limit=10)
        response = await service.browse_topics(request)

        # Verify
        assert len(response.topics) == 1
        assert response.topics[0].id == "topic-1"
        assert response.topics[0].title == "Topic 1"
        assert response.total_count == 1
        mock_repository.list_topics.assert_called_once_with(user_level="beginner", limit=10)

    @pytest.mark.asyncio
    async def test_browse_topics_error(self, service: TopicCatalogService, mock_repository: AsyncMock) -> None:
        """Test topic browsing with repository error."""
        # Setup mock to raise exception
        mock_repository.list_topics.side_effect = Exception("Repository error")

        # Execute and verify
        request = BrowseTopicsRequest()
        with pytest.raises(TopicCatalogError, match="Failed to browse topics"):
            await service.browse_topics(request)

    @pytest.mark.asyncio
    async def test_get_topic_by_id_success(self, service: TopicCatalogService, mock_repository: AsyncMock) -> None:
        """Test successful topic retrieval."""
        # Setup mock
        mock_topic = TopicDetail(
            id="topic-1",
            title="Topic 1",
            core_concept="Concept 1",
            user_level="beginner",
            learning_objectives=["Objective 1"],
            key_concepts=["Concept 1"],
            key_aspects=["Aspect 1"],
            target_insights=["Insight 1"],
            source_material="Source",
            refined_material={"content": "refined"},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            components=[{"type": "mcq"}],
        )
        mock_repository.get_topic_by_id.return_value = mock_topic

        # Execute
        response = await service.get_topic_by_id("topic-1")

        # Verify
        assert response.id == "topic-1"
        assert response.title == "Topic 1"
        assert response.component_count == 1
        assert response.is_ready_for_learning is True
        mock_repository.get_topic_by_id.assert_called_once_with("topic-1")

    @pytest.mark.asyncio
    async def test_get_topic_by_id_not_found(self, service: TopicCatalogService, mock_repository: AsyncMock) -> None:
        """Test topic retrieval when topic not found."""
        # Setup mock to return None
        mock_repository.get_topic_by_id.return_value = None

        # Execute and verify
        with pytest.raises(TopicCatalogError, match="Topic not found"):
            await service.get_topic_by_id("nonexistent")

    @pytest.mark.asyncio
    async def test_get_topic_by_id_error(self, service: TopicCatalogService, mock_repository: AsyncMock) -> None:
        """Test topic retrieval with repository error."""
        # Setup mock to raise exception
        mock_repository.get_topic_by_id.side_effect = Exception("Repository error")

        # Execute and verify
        with pytest.raises(TopicCatalogError, match="Failed to get topic"):
            await service.get_topic_by_id("topic-1")
