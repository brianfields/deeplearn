"""
Unit tests for Topic Catalog HTTP API.

These tests focus on HTTP request/response handling and routing.
"""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
import pytest

from modules.topic_catalog.http_api.routes import create_topic_catalog_router
from modules.topic_catalog.module_api import (
    SearchTopicsRequest,
    SearchTopicsResponse,
    TopicCatalogError,
    TopicSummaryResponse,
)


class TestTopicCatalogHTTPAPI:
    """Test cases for Topic Catalog HTTP API routes."""

    @pytest.fixture
    def mock_topic_catalog_service(self):
        """Create a mock topic catalog service."""
        service = AsyncMock()
        return service

    @pytest.fixture
    def client(self, mock_topic_catalog_service):
        """Create test client with mocked service."""
        from fastapi import FastAPI

        app = FastAPI()
        router = create_topic_catalog_router(topic_catalog_service=mock_topic_catalog_service)
        app.include_router(router, prefix="/api/v1/catalog")

        return TestClient(app)

    @pytest.fixture
    def sample_topic_summary_response(self):
        """Create a sample topic summary response."""
        from datetime import UTC, datetime

        return TopicSummaryResponse(
            id="topic_123",
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
        )

    def test_search_topics_success(self, client, mock_topic_catalog_service, sample_topic_summary_response):
        """Test successful topic search."""
        # Arrange
        search_response = SearchTopicsResponse(
            topics=[sample_topic_summary_response],
            total_count=1,
            query="Python",
            user_level="beginner",
            limit=10,
            offset=0,
        )
        mock_topic_catalog_service.search_topics.return_value = search_response

        # Act
        response = client.get("/api/v1/catalog/topics/search?query=Python&user_level=beginner&limit=10&offset=0")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["query"] == "Python"
        assert len(data["topics"]) == 1
        assert data["topics"][0]["title"] == "Python Variables"

        # Verify service was called with correct parameters
        mock_topic_catalog_service.search_topics.assert_called_once()
        call_args = mock_topic_catalog_service.search_topics.call_args[0][0]
        assert isinstance(call_args, SearchTopicsRequest)
        assert call_args.query == "Python"
        assert call_args.user_level == "beginner"

    def test_search_topics_minimal_params(self, client, mock_topic_catalog_service, sample_topic_summary_response):
        """Test topic search with minimal parameters."""
        # Arrange
        search_response = SearchTopicsResponse(
            topics=[sample_topic_summary_response],
            total_count=1,
            query=None,
            user_level=None,
            limit=20,
            offset=0,
        )
        mock_topic_catalog_service.search_topics.return_value = search_response

        # Act
        response = client.get("/api/v1/catalog/topics/search")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["query"] is None
        assert data["user_level"] is None

    def test_search_topics_service_error(self, client, mock_topic_catalog_service):
        """Test topic search when service raises error."""
        # Arrange
        mock_topic_catalog_service.search_topics.side_effect = TopicCatalogError("Search failed")

        # Act
        response = client.get("/api/v1/catalog/topics/search?query=Python")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Search failed" in data["detail"]

    def test_get_topic_by_id_success(self, client, mock_topic_catalog_service, sample_topic_summary_response):
        """Test successful topic retrieval by ID."""
        # Arrange
        mock_topic_catalog_service.get_topic_by_id.return_value = sample_topic_summary_response

        # Act
        response = client.get("/api/v1/catalog/topics/topic_123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "topic_123"
        assert data["title"] == "Python Variables"
        mock_topic_catalog_service.get_topic_by_id.assert_called_once_with("topic_123")

    def test_get_topic_by_id_not_found(self, client, mock_topic_catalog_service):
        """Test topic retrieval when topic not found."""
        # Arrange
        mock_topic_catalog_service.get_topic_by_id.side_effect = TopicCatalogError("Topic not found")

        # Act
        response = client.get("/api/v1/catalog/topics/nonexistent")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Topic not found" in data["detail"]

    def test_get_popular_topics_success(self, client, mock_topic_catalog_service, sample_topic_summary_response):
        """Test successful popular topics retrieval."""
        # Arrange
        mock_topic_catalog_service.get_popular_topics.return_value = [sample_topic_summary_response]

        # Act
        response = client.get("/api/v1/catalog/topics/popular?limit=5")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Python Variables"
        mock_topic_catalog_service.get_popular_topics.assert_called_once_with(limit=5)

    def test_get_popular_topics_default_limit(self, client, mock_topic_catalog_service, sample_topic_summary_response):
        """Test popular topics retrieval with default limit."""
        # Arrange
        mock_topic_catalog_service.get_popular_topics.return_value = [sample_topic_summary_response]

        # Act
        response = client.get("/api/v1/catalog/topics/popular")

        # Assert
        assert response.status_code == 200
        mock_topic_catalog_service.get_popular_topics.assert_called_once_with(limit=10)

    def test_get_catalog_statistics_success(self, client, mock_topic_catalog_service):
        """Test successful catalog statistics retrieval."""
        # Arrange
        from modules.topic_catalog.module_api.types import CatalogStatisticsResponse

        stats_response = CatalogStatisticsResponse(
            total_topics=100,
            topics_by_user_level={"beginner": 40, "intermediate": 50, "advanced": 10},
            topics_by_readiness={"ready": 80, "not_ready": 20},
            average_duration=22.5,
            duration_distribution={"0-15": 30, "16-30": 50, "31-60": 15, "60+": 5},
        )
        mock_topic_catalog_service.get_catalog_statistics.return_value = stats_response

        # Act
        response = client.get("/api/v1/catalog/statistics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_topics"] == 100
        assert data["topics_by_user_level"]["beginner"] == 40
        assert data["average_duration"] == 22.5

    def test_refresh_catalog_success(self, client, mock_topic_catalog_service):
        """Test successful catalog refresh."""
        # Arrange
        refresh_result = {
            "refreshed_topics": 25,
            "total_topics": 100,
            "timestamp": "2024-01-01T12:00:00Z",
        }
        mock_topic_catalog_service.refresh_catalog.return_value = refresh_result

        # Act
        response = client.post("/api/v1/catalog/refresh")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["refreshed_topics"] == 25
        assert data["total_topics"] == 100
        mock_topic_catalog_service.refresh_catalog.assert_called_once()

    def test_refresh_catalog_service_error(self, client, mock_topic_catalog_service):
        """Test catalog refresh when service fails."""
        # Arrange
        mock_topic_catalog_service.refresh_catalog.side_effect = TopicCatalogError("Refresh failed")

        # Act
        response = client.post("/api/v1/catalog/refresh")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Refresh failed" in data["detail"]

    def test_search_topics_invalid_user_level(self, client, mock_topic_catalog_service):
        """Test topic search with invalid user level."""
        # Act
        response = client.get("/api/v1/catalog/topics/search?user_level=expert")

        # Assert
        # FastAPI should validate the enum and return 422 for invalid values
        assert response.status_code == 422
        data = response.json()
        assert "validation error" in data["detail"][0]["type"]

    def test_search_topics_negative_limit(self, client, mock_topic_catalog_service):
        """Test topic search with negative limit."""
        # Act
        response = client.get("/api/v1/catalog/topics/search?limit=-1")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "greater than 0" in str(data["detail"])

    def test_search_topics_negative_offset(self, client, mock_topic_catalog_service):
        """Test topic search with negative offset."""
        # Act
        response = client.get("/api/v1/catalog/topics/search?offset=-1")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "greater than or equal to 0" in str(data["detail"])

    def test_get_popular_topics_invalid_limit(self, client, mock_topic_catalog_service):
        """Test popular topics with invalid limit."""
        # Act
        response = client.get("/api/v1/catalog/topics/popular?limit=0")

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "greater than 0" in str(data["detail"])

    def test_search_topics_large_limit(self, client, mock_topic_catalog_service):
        """Test topic search with large limit (should be capped)."""
        # Arrange
        search_response = SearchTopicsResponse(
            topics=[],
            total_count=0,
            query=None,
            user_level=None,
            limit=100,  # Capped at max
            offset=0,
        )
        mock_topic_catalog_service.search_topics.return_value = search_response

        # Act
        response = client.get("/api/v1/catalog/topics/search?limit=1000")

        # Assert
        assert response.status_code == 200
        # The service should receive the capped limit
        call_args = mock_topic_catalog_service.search_topics.call_args[0][0]
        assert call_args.limit == 100  # Should be capped at max limit

    def test_api_response_format_consistency(self, client, mock_topic_catalog_service, sample_topic_summary_response):
        """Test that API responses follow consistent format."""
        # Arrange
        search_response = SearchTopicsResponse(
            topics=[sample_topic_summary_response],
            total_count=1,
            query="test",
            user_level="beginner",
            limit=10,
            offset=0,
        )
        mock_topic_catalog_service.search_topics.return_value = search_response
        mock_topic_catalog_service.get_topic_by_id.return_value = sample_topic_summary_response

        # Act
        search_resp = client.get("/api/v1/catalog/topics/search?query=test")
        topic_resp = client.get("/api/v1/catalog/topics/topic_123")

        # Assert
        search_data = search_resp.json()
        topic_data = topic_resp.json()

        # Both should have consistent topic format
        search_topic = search_data["topics"][0]
        assert search_topic["id"] == topic_data["id"]
        assert search_topic["title"] == topic_data["title"]
        assert search_topic["user_level"] == topic_data["user_level"]

        # Check required fields are present
        required_fields = ["id", "title", "core_concept", "user_level", "learning_objectives", "key_concepts", "estimated_duration", "component_count", "is_ready_for_learning"]
        for field in required_fields:
            assert field in search_topic
            assert field in topic_data
