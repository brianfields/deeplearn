#!/usr/bin/env python3
"""
Learning API Tests

Tests for the Learning API endpoints (/api/learning/*)
These endpoints handle the learning consumption experience and topic discovery.

Endpoints tested:
- GET /health
- GET /api/learning/topics
- GET /api/learning/topics/{id}
- GET /api/learning/topics/{id}/components
"""

import os
import sys
from contextlib import contextmanager
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.api.server import app


def create_mock_db_session():
    """Helper to create a properly mocked database session context manager."""
    mock_session = MagicMock()

    @contextmanager
    def mock_session_context():
        yield mock_session

    mock_db_service = MagicMock()
    mock_db_service.get_session = mock_session_context

    return mock_db_service, mock_session


class TestLearningAPI:
    """Test class for Learning API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_health_endpoint_success(self):
        """Test health check endpoint returns correct structure."""
        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert "database" in data["services"]
        assert data["status"] == "healthy"

    @patch('database_service.DatabaseService')
    @patch('data_structures.BiteSizedTopic')
    @patch('data_structures.BiteSizedComponent')
    def test_get_learning_topics_success(self, mock_component_class, mock_topic_class, mock_db_service_class):
        """Test successful retrieval of learning topics."""
        # Mock database setup
        mock_db_service, mock_session = create_mock_db_session()
        mock_db_service_class.return_value = mock_db_service

        # Mock topic data
        mock_topic = Mock()
        mock_topic.id = "topic-123"
        mock_topic.title = "Python Functions"
        mock_topic.core_concept = "Function definitions"
        mock_topic.user_level = "beginner"
        mock_topic.learning_objectives = ["Define functions", "Use parameters"]
        mock_topic.key_concepts = ["def keyword", "parameters"]
        mock_topic.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        # Mock query behavior
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = [mock_topic]
        mock_session.query.return_value = mock_query

        # Mock component count
        mock_session.query.return_value.filter.return_value.count.return_value = 3

        # Make request
        response = self.client.get("/api/learning/topics")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Python Functions"
        assert data[0]["component_count"] == 3
        assert data[0]["estimated_duration"] == 20  # 5 + (3 * 5)

    @patch('database_service.DatabaseService')
    @patch('data_structures.BiteSizedTopic')
    @patch('data_structures.BiteSizedComponent')
    def test_get_learning_topics_with_filter(self, mock_component_class, mock_topic_class, mock_db_service_class):
        """Test learning topics with user level filter."""
        # Mock database setup
        mock_db_service, mock_session = create_mock_db_session()
        mock_db_service_class.return_value = mock_db_service

        # Mock empty results
        mock_query = Mock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        # Make request with filter
        response = self.client.get("/api/learning/topics?user_level=advanced&limit=10&offset=0")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @patch('database_service.DatabaseService')
    @patch('data_structures.BiteSizedTopic')
    @patch('data_structures.BiteSizedComponent')
    def test_get_learning_topic_detail_success(self, mock_component_class, mock_topic_class, mock_db_service_class):
        """Test successful retrieval of learning topic detail."""
        # Mock database setup
        mock_db_service, mock_session = create_mock_db_session()
        mock_db_service_class.return_value = mock_db_service

        # Mock topic data
        mock_topic = Mock()
        mock_topic.id = "topic-123"
        mock_topic.title = "Python Functions"
        mock_topic.core_concept = "Function definitions"
        mock_topic.user_level = "beginner"
        mock_topic.learning_objectives = ["Define functions"]
        mock_topic.key_concepts = ["def keyword"]
        mock_topic.key_aspects = ["syntax"]
        mock_topic.target_insights = ["understanding functions"]
        mock_topic.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_topic.updated_at.isoformat.return_value = "2024-01-01T00:00:00"

        # Mock component data
        mock_component = Mock()
        mock_component.component_type = "mcq"
        mock_component.content = {"stem": "What is a function?", "options": ["A", "B", "C", "D"]}
        mock_component.title = "Function MCQ"
        mock_component.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_component.updated_at.isoformat.return_value = "2024-01-01T00:00:00"

        # Mock database queries
        mock_session.query.return_value.filter.return_value.first.return_value = mock_topic
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_component]

        # Make request
        response = self.client.get("/api/learning/topics/topic-123")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "topic-123"
        assert data["title"] == "Python Functions"
        assert len(data["components"]) == 1
        assert data["components"][0]["component_type"] == "mcq"
        assert data["estimated_duration"] == 10  # 5 + (1 * 5)

    @patch('database_service.DatabaseService')
    def test_get_learning_topic_not_found(self, mock_db_service_class):
        """Test learning topic detail when topic doesn't exist."""
        # Mock database setup
        mock_db_service, mock_session = create_mock_db_session()
        mock_db_service_class.return_value = mock_db_service

        # Mock topic not found
        mock_session.query.return_value.filter.return_value.first.return_value = None

        # Make request
        response = self.client.get("/api/learning/topics/non-existent-topic")

        # Verify response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch('database_service.DatabaseService')
    @patch('data_structures.BiteSizedTopic')
    @patch('data_structures.BiteSizedComponent')
    def test_get_learning_topic_components_success(self, mock_component_class, mock_topic_class, mock_db_service_class):
        """Test successful retrieval of learning topic components."""
        # Mock database setup
        mock_db_service, mock_session = create_mock_db_session()
        mock_db_service_class.return_value = mock_db_service

        # Mock topic exists
        mock_topic = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_topic

        # Mock component data
        mock_component1 = Mock()
        mock_component1.component_type = "mcq"
        mock_component1.content = {"stem": "Question 1"}
        mock_component1.title = "MCQ 1"
        mock_component1.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_component1.updated_at.isoformat.return_value = "2024-01-01T00:00:00"

        mock_component2 = Mock()
        mock_component2.component_type = "didactic_snippet"
        mock_component2.content = {"text": "Explanation"}
        mock_component2.title = "Explanation"
        mock_component2.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_component2.updated_at.isoformat.return_value = "2024-01-01T00:00:00"

        # Mock different query behaviors for topic check vs component retrieval
        def mock_query_side_effect(*args):
            query_mock = Mock()
            if args[0] == mock_topic_class:
                query_mock.filter.return_value.first.return_value = mock_topic
            else:  # BiteSizedComponent
                query_mock.filter.return_value.all.return_value = [mock_component1, mock_component2]
            return query_mock

        mock_session.query.side_effect = mock_query_side_effect

        # Make request
        response = self.client.get("/api/learning/topics/topic-123/components")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["component_type"] == "mcq"
        assert data[1]["component_type"] == "didactic_snippet"

    def test_get_learning_topic_components_topic_not_found(self):
        """Test learning topic components when topic doesn't exist."""
        with patch('database_service.DatabaseService') as mock_db_service_class:
            # Mock database setup
            mock_db_service, mock_session = create_mock_db_session()
            mock_db_service_class.return_value = mock_db_service

            # Mock topic not found
            mock_session.query.return_value.filter.return_value.first.return_value = None

            # Make request
            response = self.client.get("/api/learning/topics/non-existent-topic/components")

            # Verify response
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


class TestLearningAPIErrorHandling:
    """Test error handling for Learning API."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @patch('database_service.DatabaseService')
    def test_database_error_handling(self, mock_db_service_class):
        """Test handling of database errors."""
        # Mock database error
        mock_db_service_class.side_effect = Exception("Database connection failed")

        # Make request
        response = self.client.get("/api/learning/topics")

        # Verify error handling
        assert response.status_code == 500
        assert "Failed to get learning topics" in response.json()["detail"]

    def test_invalid_topic_id_format(self):
        """Test handling of invalid topic ID format."""
        # Make request with potentially problematic topic ID
        response = self.client.get("/api/learning/topics/invalid-topic-id-with-special-chars-@#$")

        # Should still attempt to process (404 is acceptable, 400 would indicate validation issue)
        assert response.status_code in [404, 500]  # Either not found or processing error is acceptable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])