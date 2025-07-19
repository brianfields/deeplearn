#!/usr/bin/env python3
"""
Content Creation API Tests

Tests for the Content Creation API endpoints (/api/content/*)
These endpoints handle the database-first content creation workflow.

New endpoints tested:
- POST /api/content/topics - Create topic with refined material
- GET  /api/content/topics/{topic_id} - Get topic with components
- POST /api/content/topics/{topic_id}/components - Create MCQ component
- DELETE /api/content/topics/{topic_id}/components/{component_id} - Delete component
- DELETE /api/content/topics/{topic_id} - Delete topic
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from src.api.content_creation_routes import get_database_service, get_mcq_service, get_refined_material_service
from src.api.server import app


def create_mock_db_service():
    """Helper to create a properly mocked database service."""
    mock_db_service = MagicMock()

    # Mock topic result
    mock_topic = MagicMock()
    mock_topic.id = "test-topic-id"
    mock_topic.title = "Python Functions"
    mock_topic.core_concept = "Function Definition"
    mock_topic.user_level = "intermediate"
    mock_topic.learning_objectives = ["Define functions", "Use parameters"]
    mock_topic.key_concepts = ["Use def keyword", "Functions can return values"]
    mock_topic.source_material = "Functions in Python..."
    mock_topic.source_domain = "Programming"
    mock_topic.source_level = "intermediate"
    mock_topic.refined_material = {"topics": [{"topic": "Function Basics"}]}
    mock_topic.created_at = MagicMock()
    mock_topic.created_at.isoformat.return_value = "2024-01-01T12:00:00Z"
    mock_topic.updated_at = MagicMock()
    mock_topic.updated_at.isoformat.return_value = "2024-01-01T12:00:00Z"

    mock_db_service.get_bite_sized_topic.return_value = mock_topic
    mock_db_service.save_bite_sized_topic.return_value = True
    mock_db_service.delete_bite_sized_topic.return_value = True
    mock_db_service.get_topic_components.return_value = []

    return mock_db_service


def create_mock_mcq_service():
    """Helper to create a properly mocked MCQ service."""
    mock_mcq_service = MagicMock()

    # Mock MCQ creation
    mock_mcq_service._create_single_mcq = AsyncMock(
        return_value={
            "stem": "What keyword defines a function?",
            "options": ["def", "function", "define", "func"],
            "correct_answer": "def",
            "rationale": "The 'def' keyword is used to define functions in Python",
        }
    )

    # Mock MCQ evaluation
    mock_mcq_service._evaluate_mcq = AsyncMock(return_value={"overall": "High quality"})

    return mock_mcq_service


def create_mock_refined_material_service():
    """Helper to create a properly mocked refined material service."""
    mock_service = MagicMock()

    mock_service.extract_refined_material = AsyncMock(
        return_value={
            "topics": [
                {
                    "topic": "Python Function Basics",
                    "learning_objectives": ["Define functions", "Use parameters"],
                    "key_facts": ["Use def keyword", "Functions can return values"],
                    "common_misconceptions": [],
                    "assessment_angles": ["Syntax knowledge"],
                }
            ]
        }
    )

    return mock_service


class TestContentCreationAPI:
    """Test class for Content Creation API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

        # Sample data for testing - updated for new API
        self.sample_topic_request = {
            "title": "Python Functions",
            "source_material": "Functions in Python are defined using the def keyword...",
            "source_domain": "Programming",
            "source_level": "intermediate",
        }

        self.sample_component_request = {"component_type": "mcq", "learning_objective": "Define Python functions"}

    def test_create_topic_from_material_success(self):
        """Test successful creation of topic with refined material."""
        # Override dependencies
        mock_db_service = create_mock_db_service()
        mock_refined_service = create_mock_refined_material_service()

        app.dependency_overrides[get_database_service] = lambda: mock_db_service
        app.dependency_overrides[get_refined_material_service] = lambda: mock_refined_service

        try:
            # Make request to new endpoint
            response = self.client.post("/api/content/topics", json=self.sample_topic_request)

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "refined_material" in data
            assert data["title"] == "Python Functions"
            assert data["user_level"] == "intermediate"
            assert len(data["learning_objectives"]) >= 1
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_create_mcq_component_success(self):
        """Test successful MCQ component creation for a topic."""
        # Override dependencies
        mock_db_service = create_mock_db_service()
        mock_mcq_service = create_mock_mcq_service()

        app.dependency_overrides[get_database_service] = lambda: mock_db_service
        app.dependency_overrides[get_mcq_service] = lambda: mock_mcq_service

        try:
            topic_id = "test-topic-id"

            # Make request to create MCQ component
            response = self.client.post(f"/api/content/topics/{topic_id}/components", json=self.sample_component_request)

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["component_type"] == "mcq"
            assert data["topic_id"] == topic_id
            assert "content" in data
            assert "mcq" in data["content"]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_create_mcq_topic_not_found(self):
        """Test MCQ creation with non-existent topic."""
        # Override dependency with None return
        mock_db_service = MagicMock()
        mock_db_service.get_bite_sized_topic.return_value = None
        mock_mcq_service = create_mock_mcq_service()

        app.dependency_overrides[get_database_service] = lambda: mock_db_service
        app.dependency_overrides[get_mcq_service] = lambda: mock_mcq_service

        try:
            topic_id = "non-existent-topic"
            response = self.client.post(f"/api/content/topics/{topic_id}/components", json=self.sample_component_request)

            assert response.status_code == 404
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_get_topic_success(self):
        """Test getting a topic with components."""
        # Override dependency
        mock_db_service = create_mock_db_service()

        # Add mock component
        mock_component = MagicMock()
        mock_component.dict.return_value = {
            "id": "component-1",
            "topic_id": "test-topic-id",
            "component_type": "mcq",
            "title": "Test MCQ",
            "content": {"mcq": {"stem": "Test question?"}},
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
        }
        mock_db_service.get_topic_components.return_value = [mock_component]

        app.dependency_overrides[get_database_service] = lambda: mock_db_service

        try:
            topic_id = "test-topic-id"
            response = self.client.get(f"/api/content/topics/{topic_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == topic_id
            assert data["title"] == "Python Functions"
            assert len(data["components"]) == 1
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_get_topic_not_found(self):
        """Test getting a topic that doesn't exist."""
        # Override dependency with None return
        mock_db_service = MagicMock()
        mock_db_service.get_bite_sized_topic.return_value = None

        app.dependency_overrides[get_database_service] = lambda: mock_db_service

        try:
            response = self.client.get("/api/content/topics/non-existent-topic")
            assert response.status_code == 404
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_delete_topic_success(self):
        """Test successful topic deletion."""
        # Override dependency
        mock_db_service = MagicMock()
        mock_db_service.delete_bite_sized_topic.return_value = True

        app.dependency_overrides[get_database_service] = lambda: mock_db_service

        try:
            topic_id = "test-topic-id"
            response = self.client.delete(f"/api/content/topics/{topic_id}")

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_delete_topic_not_found(self):
        """Test deleting a topic that doesn't exist."""
        # Override dependency with False return (not found)
        mock_db_service = MagicMock()
        mock_db_service.delete_bite_sized_topic.return_value = False

        app.dependency_overrides[get_database_service] = lambda: mock_db_service

        try:
            response = self.client.delete("/api/content/topics/non-existent-topic")
            assert response.status_code == 404
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()


class TestContentCreationValidation:
    """Test validation for content creation endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_create_topic_missing_required_fields(self):
        """Test topic creation with missing required fields."""
        invalid_request = {
            "source_material": "Some text"
            # Missing title, which is required
        }

        response = self.client.post("/api/content/topics", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_create_component_missing_required_fields(self):
        """Test component creation with missing required fields."""
        invalid_request = {
            "component_type": "mcq"
            # Missing learning_objective, which is required
        }

        topic_id = "test-topic-id"
        response = self.client.post(f"/api/content/topics/{topic_id}/components", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_create_component_invalid_type(self):
        """Test component creation with invalid component type."""
        # Override dependency first
        mock_db_service = create_mock_db_service()
        app.dependency_overrides[get_database_service] = lambda: mock_db_service

        try:
            invalid_request = {"component_type": "invalid_type", "learning_objective": "Some objective"}

            topic_id = "test-topic-id"
            response = self.client.post(f"/api/content/topics/{topic_id}/components", json=invalid_request)
            # This should either return 422 for validation or 200 with placeholder content
            # depending on implementation
            assert response.status_code in [200, 422]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()


class TestContentCreationErrors:
    """Test error handling for content creation endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_database_error_handling(self):
        """Test handling of database errors."""

        # Override dependency to raise exception
        def mock_db_service_error():
            mock_db_service = MagicMock()
            mock_db_service.get_bite_sized_topic.side_effect = Exception("Database error")
            return mock_db_service

        app.dependency_overrides[get_database_service] = mock_db_service_error

        try:
            response = self.client.get("/api/content/topics/test-topic-id")
            assert response.status_code == 500
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_llm_service_error_handling(self):
        """Test handling of LLM service errors."""
        # Override dependencies
        mock_db_service = create_mock_db_service()

        def mock_refined_service_error():
            mock_service = MagicMock()
            mock_service.extract_refined_material = AsyncMock(side_effect=Exception("LLM error"))
            return mock_service

        app.dependency_overrides[get_database_service] = lambda: mock_db_service
        app.dependency_overrides[get_refined_material_service] = mock_refined_service_error

        try:
            topic_request = {"title": "Test Topic", "source_material": "Test material", "source_domain": "Test", "source_level": "beginner"}

            response = self.client.post("/api/content/topics", json=topic_request)
            assert response.status_code == 500
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
