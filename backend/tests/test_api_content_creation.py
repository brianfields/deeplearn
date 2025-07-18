#!/usr/bin/env python3
"""
Content Creation API Tests

Tests for the Content Creation API endpoints (/api/content/*)
These endpoints handle the content creation workflow and temporary session management.

Endpoints tested:
- POST /api/content/refined-material
- POST /api/content/mcq
- GET  /api/content/sessions
- POST /api/content/topics
- GET  /api/content/topics/{id}
- POST /api/content/topics/{id}/components
"""

import pytest
import json
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from contextlib import contextmanager

# Import system under test
import sys
import os
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


class TestContentCreationAPI:
    """Test class for Content Creation API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

        # Sample data for testing
        self.sample_refined_material_request = {
            "topic": "Python Functions",
            "source_material": "Functions in Python are defined using the def keyword...",
            "domain": "Programming",
            "level": "intermediate",
            "model": "gpt-4o"
        }

        self.sample_topic_request = {
            "title": "Python Functions",
            "source_material": "Functions in Python are defined using the def keyword...",
            "source_domain": "Programming",
            "source_level": "intermediate"
        }

        self.sample_component_request = {
            "component_type": "mcq",
            "learning_objective": "Define Python functions",
            "topic_context": {
                "topic": "Python Functions",
                "key_facts": ["Use def keyword"],
                "common_misconceptions": [],
                "assessment_angles": ["Syntax"]
            }
        }

    @patch('src.api.content_creation_routes.create_llm_client')
    def test_create_refined_material_success(self, mock_create_client):
        """Test successful creation of refined material - with proper LLM mocking."""
        # Create a mock LLM client
        mock_llm_client = Mock()

        # Mock refined material response
        mock_refined_response = Mock()
        mock_refined_response.content = json.dumps({
            "topics": [
                {
                    "topic": "Python Function Basics",
                    "learning_objectives": ["Define functions", "Use parameters"],
                    "key_facts": ["Use def keyword", "Functions can return values"],
                    "common_misconceptions": [],
                    "assessment_angles": ["Syntax knowledge"]
                }
            ]
        })

        mock_llm_client.generate_response = AsyncMock(return_value=mock_refined_response)
        mock_create_client.return_value = mock_llm_client

        # Make request
        response = self.client.post("/api/content/refined-material", json=self.sample_refined_material_request)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "refined_material" in data
        assert data["topic"] == "Python Functions"
        assert data["level"] == "intermediate"
        assert len(data["refined_material"]["topics"]) >= 1  # Allow multiple topics

        # Verify first topic has expected structure
        first_topic = data["refined_material"]["topics"][0]
        assert "topic" in first_topic
        assert "learning_objectives" in first_topic
        assert "key_facts" in first_topic

    @patch('src.api.content_creation_routes.create_llm_client')
    def test_create_mcq_success(self, mock_create_client):
        """Test successful MCQ creation - with proper LLM mocking."""
        # Create a mock LLM client
        mock_llm_client = Mock()

        # Mock MCQ creation response
        mock_mcq_response = Mock()
        mock_mcq_response.content = json.dumps({
            "stem": "What keyword defines a function?",
            "options": ["def", "function", "define", "func"],
            "correct_answer": "def"
        })

        # Mock MCQ evaluation response
        mock_evaluation_response = Mock()
        mock_evaluation_response.content = json.dumps({"overall": "High quality"})

        # Set up side_effect for multiple calls
        mock_llm_client.generate_response = AsyncMock(side_effect=[mock_mcq_response, mock_evaluation_response])
        mock_create_client.return_value = mock_llm_client

        # Create a session first (mock it in the in-memory store)
        session_id = str(uuid.uuid4())
        from src.api.content_creation_routes import content_sessions
        content_sessions[session_id] = {
            "session_id": session_id,
            "topic": "Python Functions",
            "mcqs": []
        }

        request_data = {
            "session_id": session_id,
            "topic": "Python Functions",
            "learning_objective": "Define Python functions",
            "key_facts": ["Use def keyword"],
            "common_misconceptions": [],
            "assessment_angles": ["Syntax"]
        }

        # Make request
        response = self.client.post("/api/content/mcq", json=request_data)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "mcq_id" in data
        assert "mcq" in data
        assert "evaluation" in data
        assert data["session_id"] == session_id

    def test_create_mcq_session_not_found(self):
        """Test MCQ creation with non-existent session."""
        request_data = {
            "session_id": "non-existent-session",
            "topic": "Python Functions",
            "learning_objective": "Define Python functions"
        }

        response = self.client.post("/api/content/mcq", json=request_data)

        assert response.status_code == 404
        assert "session not found" in response.json()["detail"].lower()

    @patch('src.api.content_creation_routes.create_llm_client')
    @patch('database_service.DatabaseService')
    @patch('data_structures.BiteSizedTopic')
    def test_create_topic_from_material_success(self, mock_topic_class, mock_db_service_class, mock_create_client):
        """Test successful topic creation from material - with proper LLM mocking."""
        # Create a mock LLM client
        mock_llm_client = Mock()

        # Mock refined material response
        mock_refined_response = Mock()
        mock_refined_response.content = json.dumps({
            "topics": [
                {
                    "topic": "Python Functions",
                    "learning_objectives": ["Define functions"],
                    "key_facts": ["Use def keyword"]
                }
            ]
        })

        mock_llm_client.generate_response = AsyncMock(return_value=mock_refined_response)
        mock_create_client.return_value = mock_llm_client

        # Mock database using helper
        mock_db_service, mock_session = create_mock_db_session()
        mock_db_service_class.return_value = mock_db_service

        # Mock topic creation
        mock_topic = Mock()
        mock_topic.id = "test-topic-123"
        mock_topic.title = "Python Functions"
        mock_topic.core_concept = "Python Functions"
        mock_topic.user_level = "intermediate"
        mock_topic.learning_objectives = ["Define functions"]
        mock_topic.key_concepts = ["Use def keyword"]
        mock_topic.key_aspects = []
        mock_topic.target_insights = []
        mock_topic.source_material = self.sample_topic_request["source_material"]
        mock_topic.source_domain = "Programming"
        mock_topic.source_level = "intermediate"
        mock_topic.refined_material = {
            "topics": [
                {
                    "topic": "Python Functions",
                    "learning_objectives": ["Define functions"],
                    "key_facts": ["Use def keyword"]
                }
            ]
        }
        mock_topic.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_topic.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_topic_class.return_value = mock_topic

        # Make request
        response = self.client.post("/api/content/topics", json=self.sample_topic_request)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Python Functions"
        assert data["user_level"] == "intermediate"
        assert "refined_material" in data

    def test_get_content_sessions_empty(self):
        """Test getting content sessions when none exist."""
        # Clear sessions
        from src.api.content_creation_routes import content_sessions
        content_sessions.clear()

        response = self.client.get("/api/content/sessions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_content_session_not_found(self):
        """Test getting a specific session that doesn't exist."""
        response = self.client.get("/api/content/sessions/non-existent-session")

        assert response.status_code == 404
        assert "session not found" in response.json()["detail"].lower()


class TestContentCreationValidation:
    """Test input validation for Content Creation API."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_refined_material_missing_required_fields(self):
        """Test refined material creation with missing required fields."""
        invalid_request = {
            "source_material": "Some text"
            # Missing topic, which is required
        }

        response = self.client.post("/api/content/refined-material", json=invalid_request)

        assert response.status_code == 422  # Validation error

    def test_mcq_creation_missing_session_id(self):
        """Test MCQ creation with missing session_id."""
        invalid_request = {
            "topic": "Python Functions",
            "learning_objective": "Define functions"
            # Missing session_id
        }

        response = self.client.post("/api/content/mcq", json=invalid_request)

        assert response.status_code == 422  # Validation error

    def test_topic_creation_missing_title(self):
        """Test topic creation with missing title."""
        invalid_request = {
            "source_material": "Some text"
            # Missing title
        }

        response = self.client.post("/api/content/topics", json=invalid_request)

        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])