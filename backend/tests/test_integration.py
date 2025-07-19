#!/usr/bin/env python3
"""
Integration Tests for Two-Layer Architecture

Tests end-to-end workflows for the new clean architecture:
1. Content Creation Workflow: Source material → Refined material → Topic creation → Component generation
2. Learning Consumption Workflow: Topic discovery → Topic access → Component consumption

These tests verify that the services work together correctly and that the APIs
provide the expected functionality for complete user workflows.
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


class TestContentCreationWorkflow:
    """Test complete content creation workflow."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

        self.sample_source_material = """
        Python functions are reusable blocks of code that perform specific tasks.
        They are defined using the 'def' keyword, followed by the function name
        and parentheses containing any parameters.

        Functions can accept parameters, which allow you to pass information to them.
        They can also return values using the 'return' statement.
        """

    @patch('src.api.content_creation_routes.create_llm_client')
    @patch('database_service.DatabaseService')
    @patch('data_structures.BiteSizedTopic')
    def test_complete_content_creation_workflow(self, mock_topic_class, mock_db_service_class, mock_create_client):
        """Test complete workflow from source material to topic creation - with proper LLM mocking."""

        # Step 1: Mock LLM client for refined material extraction
        mock_llm_client = Mock()

        # Mock refined material response
        mock_refined_response = Mock()
        mock_refined_response.content = json.dumps({
            "topics": [
                {
                    "topic": "Python Function Basics",
                    "learning_objectives": [
                        "Define a Python function using proper syntax",
                        "Explain the purpose of function parameters"
                    ],
                    "key_facts": [
                        "Functions are defined with the 'def' keyword",
                        "Parameters allow input to functions"
                    ],
                    "common_misconceptions": [
                        {
                            "misconception": "Functions can only return one value",
                            "correct_concept": "Functions can return multiple values"
                        }
                    ],
                    "assessment_angles": [
                        "Function definition syntax",
                        "Parameter usage"
                    ]
                }
            ]
        })

        mock_llm_client.generate_response = AsyncMock(return_value=mock_refined_response)
        mock_create_client.return_value = mock_llm_client

        # Step 2: Mock database and topic creation
        mock_db_service, mock_session = create_mock_db_session()
        mock_db_service_class.return_value = mock_db_service

        mock_topic = Mock()
        mock_topic.id = "test-topic-123"
        mock_topic.title = "Python Functions"
        mock_topic.core_concept = "Python Function Basics"
        mock_topic.user_level = "beginner"
        mock_topic.learning_objectives = ["Define a Python function using proper syntax", "Explain the purpose of function parameters"]
        mock_topic.key_concepts = ["Functions are defined with the 'def' keyword", "Parameters allow input to functions"]
        mock_topic.key_aspects = []
        mock_topic.target_insights = []
        mock_topic.source_material = self.sample_source_material
        mock_topic.source_domain = "Programming"
        mock_topic.source_level = "beginner"
        mock_topic.refined_material = {
            "topics": [
                {
                    "topic": "Python Function Basics",
                    "learning_objectives": [
                        "Define a Python function using proper syntax",
                        "Explain the purpose of function parameters"
                    ],
                    "key_facts": [
                        "Functions are defined with the 'def' keyword",
                        "Parameters allow input to functions"
                    ],
                    "common_misconceptions": [
                        {
                            "misconception": "Functions can only return one value",
                            "correct_concept": "Functions can return multiple values"
                        }
                    ],
                    "assessment_angles": [
                        "Function definition syntax",
                        "Parameter usage"
                    ]
                }
            ]
        }
        mock_topic.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_topic.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_topic_class.return_value = mock_topic

        # Step 3: Execute the complete workflow

        # Create topic from source material
        topic_request = {
            "title": "Python Functions",
            "source_material": self.sample_source_material,
            "source_domain": "Programming",
            "source_level": "beginner"
        }

        response = self.client.post("/api/content/topics", json=topic_request)

        # Verify successful topic creation
        assert response.status_code == 200
        topic_data = response.json()
        assert topic_data["title"] == "Python Functions"
        assert topic_data["user_level"] == "beginner"
        assert "refined_material" in topic_data
        assert len(topic_data["refined_material"]["topics"]) == 1
        assert len(topic_data["refined_material"]["topics"][0]["learning_objectives"]) == 2

        # Verify the refined material was properly extracted
        refined_topic = topic_data["refined_material"]["topics"][0]
        assert refined_topic["topic"] == "Python Function Basics"
        assert "Define a Python function using proper syntax" in refined_topic["learning_objectives"]
        assert "Functions are defined with the 'def' keyword" in refined_topic["key_facts"]

    @patch('src.api.content_creation_routes.create_llm_client')
    def test_refined_material_extraction_workflow(self, mock_create_client):
        """Test topic creation with refined material extraction as standalone workflow."""

        # Create a mock LLM client
        mock_llm_client = Mock()

        # Mock refined material response
        mock_refined_response = Mock()
        mock_refined_response.content = json.dumps({
            "topics": [
                {
                    "topic": "Python Variables",
                    "learning_objectives": ["Declare variables", "Assign values"],
                    "key_facts": ["Variables store data", "No type declaration needed"],
                    "common_misconceptions": [],
                    "assessment_angles": ["Variable declaration", "Data types"]
                }
            ]
        })

        mock_llm_client.generate_response = AsyncMock(return_value=mock_refined_response)
        mock_create_client.return_value = mock_llm_client

        # Make request to new topic creation endpoint
        request_data = {
            "title": "Python Variables",
            "source_material": "Variables in Python are containers for storing data values...",
            "source_domain": "Programming",
            "source_level": "beginner"
        }

        response = self.client.post("/api/content/topics", json=request_data)

        # Verify response with deterministic mock data
        assert response.status_code == 200
        data = response.json()

        # Verify topic creation
        assert "id" in data
        assert data["title"] == "Python Variables"
        assert data["user_level"] == "beginner"
        assert data["source_domain"] == "Programming"

        # Verify refined material extraction
        assert "refined_material" in data
        assert "learning_objectives" in data
        assert len(data["learning_objectives"]) >= 1

    @patch('src.api.content_creation_routes.create_llm_client')
    def test_mcq_creation_workflow(self, mock_create_client):
        """Test MCQ creation workflow using new topic-based API."""

        # Create a mock LLM client instance
        mock_llm_client = Mock()

        # Mock LLM responses for topic creation
        mock_refined_response = Mock()
        mock_refined_response.content = json.dumps({
            "topics": [
                {
                    "topic": "Function Definition",
                    "learning_objectives": ["Define functions in Python"],
                    "key_facts": ["Use def keyword", "Functions can have parameters"],
                    "common_misconceptions": [],
                    "assessment_angles": ["Syntax knowledge"]
                }
            ]
        })

        # Mock LLM responses for MCQ creation
        mock_mcq_response = Mock()
        mock_mcq_response.content = json.dumps({
            "stem": "Which keyword is used to define a function in Python?",
            "options": ["def", "function", "define", "func"],
            "correct_answer": "def",
            "rationale": "The 'def' keyword is used to define functions in Python."
        })

        mock_evaluation_response = Mock()
        mock_evaluation_response.content = json.dumps({
            "alignment": "Directly tests function definition knowledge",
            "stem_quality": "Clear and unambiguous",
            "options_quality": "Good distractors with one correct answer",
            "overall": "High quality MCQ"
        })

        # Set up the mock client to return different responses for different calls
        # First call for topic creation, then MCQ creation and evaluation
        mock_llm_client.generate_response = AsyncMock(side_effect=[
            mock_refined_response, mock_mcq_response, mock_evaluation_response
        ])

        # Make the factory function return our mock client
        mock_create_client.return_value = mock_llm_client

        # Step 1: Create topic with refined material
        topic_request = {
            "title": "Python Functions",
            "source_material": "Functions in Python are defined using the def keyword...",
            "source_domain": "Programming",
            "source_level": "beginner"
        }

        topic_response = self.client.post("/api/content/topics", json=topic_request)
        assert topic_response.status_code == 200
        topic_data = topic_response.json()
        topic_id = topic_data["id"]

        # Step 2: Create MCQ component for the topic
        mcq_request = {
            "component_type": "mcq",
            "learning_objective": "Define functions in Python"
        }

        mcq_response = self.client.post(f"/api/content/topics/{topic_id}/components", json=mcq_request)

        # Verify MCQ creation
        assert mcq_response.status_code == 200
        mcq_data = mcq_response.json()

        assert mcq_data["component_type"] == "mcq"
        assert mcq_data["topic_id"] == topic_id
        assert "content" in mcq_data
        assert "mcq" in mcq_data["content"]
        assert "evaluation" in mcq_data["content"]

        # Verify MCQ structure
        mcq_content = mcq_data["content"]["mcq"]
        assert "stem" in mcq_content
        assert "options" in mcq_content
        assert "correct_answer" in mcq_content
        assert len(mcq_content["options"]) == 4


class TestLearningConsumptionWorkflow:
    """Test complete learning consumption workflow."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_health_check_workflow(self):
        """Test health check as part of learning workflow."""
        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data["services"]

    @patch('database_service.DatabaseService')
    @patch('data_structures.BiteSizedTopic')
    @patch('data_structures.BiteSizedComponent')
    def test_complete_learning_discovery_workflow(self, mock_component_class, mock_topic_class, mock_db_service_class):
        """Test complete learning discovery and consumption workflow."""

        # Mock database setup
        mock_db_service, mock_session = create_mock_db_session()
        mock_db_service_class.return_value = mock_db_service

        # Mock topic data for discovery
        mock_topic1 = Mock()
        mock_topic1.id = "topic-123"
        mock_topic1.title = "Python Functions"
        mock_topic1.core_concept = "Function definitions"
        mock_topic1.user_level = "beginner"
        mock_topic1.learning_objectives = ["Define functions", "Use parameters"]
        mock_topic1.key_concepts = ["def keyword", "parameters"]
        mock_topic1.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        mock_topic2 = Mock()
        mock_topic2.id = "topic-456"
        mock_topic2.title = "Python Variables"
        mock_topic2.core_concept = "Variable assignment"
        mock_topic2.user_level = "beginner"
        mock_topic2.learning_objectives = ["Declare variables"]
        mock_topic2.key_concepts = ["variable assignment"]
        mock_topic2.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        # Step 1: Topic Discovery
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = [mock_topic1, mock_topic2]
        mock_session.query.return_value = mock_query

        # Mock component counts
        mock_session.query.return_value.filter.return_value.count.return_value = 2

        response = self.client.get("/api/learning/topics")

        assert response.status_code == 200
        topics = response.json()
        assert len(topics) == 2
        assert topics[0]["title"] == "Python Functions"
        assert topics[0]["component_count"] == 2
        assert topics[1]["title"] == "Python Variables"

        # Step 2: Topic Detail Access
        # Update mocks for detail retrieval
        mock_topic1.key_aspects = ["syntax"]
        mock_topic1.target_insights = ["understanding"]
        mock_topic1.updated_at.isoformat.return_value = "2024-01-01T00:00:00"

        mock_component = Mock()
        mock_component.component_type = "mcq"
        mock_component.content = {
            "stem": "What keyword defines a function?",
            "options": ["def", "function", "define", "func"],
            "correct_answer": "def"
        }
        mock_component.title = "Function Definition MCQ"
        mock_component.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_component.updated_at.isoformat.return_value = "2024-01-01T00:00:00"

        # Mock different behaviors for topic vs component queries
        def mock_query_side_effect(*args):
            query_mock = Mock()
            if args[0] == mock_topic_class:
                query_mock.filter.return_value.first.return_value = mock_topic1
            else:  # BiteSizedComponent
                query_mock.filter.return_value.all.return_value = [mock_component]
            return query_mock

        mock_session.query.side_effect = mock_query_side_effect

        response = self.client.get("/api/learning/topics/topic-123")

        assert response.status_code == 200
        topic_detail = response.json()
        assert topic_detail["id"] == "topic-123"
        assert topic_detail["title"] == "Python Functions"
        assert len(topic_detail["components"]) == 1
        assert topic_detail["components"][0]["component_type"] == "mcq"

        # Step 3: Component Access
        response = self.client.get("/api/learning/topics/topic-123/components")

        assert response.status_code == 200
        components = response.json()
        assert len(components) == 1
        assert components[0]["component_type"] == "mcq"
        assert "What keyword defines a function?" in components[0]["content"]["stem"]


class TestCrossLayerIntegration:
    """Test integration between content creation and learning layers."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @patch('src.api.content_creation_routes.create_llm_client')
    @patch('database_service.DatabaseService')
    @patch('data_structures.BiteSizedTopic')
    @patch('data_structures.BiteSizedComponent')
    def test_content_creation_to_learning_workflow(self, mock_component_class, mock_topic_class,
                                                   mock_db_service_class, mock_create_client):
        """Test creating content and then consuming it through learning API - with proper LLM mocking."""

        # Step 1: Mock LLM client for content creation
        mock_llm_client = Mock()

        # Mock refined material response
        mock_refined_response = Mock()
        mock_refined_response.content = json.dumps({
            "topics": [
                {
                    "topic": "Python Loops",
                    "learning_objectives": ["Use for loops", "Use while loops"],
                    "key_facts": ["for loops iterate over sequences", "while loops continue until condition is false"]
                }
            ]
        })

        mock_llm_client.generate_response = AsyncMock(return_value=mock_refined_response)
        mock_create_client.return_value = mock_llm_client

        # Mock database for content creation
        mock_db_service, mock_session = create_mock_db_session()
        mock_db_service_class.return_value = mock_db_service

        mock_topic = Mock()
        mock_topic.id = "loops-topic-789"
        mock_topic.title = "Python Loops"
        mock_topic.core_concept = "Python Loops"
        mock_topic.user_level = "intermediate"
        mock_topic.learning_objectives = ["Use for loops", "Use while loops"]
        mock_topic.key_concepts = ["for loops iterate over sequences"]
        mock_topic.key_aspects = []
        mock_topic.target_insights = []
        mock_topic.source_material = "Loops allow you to repeat code..."
        mock_topic.source_domain = "Programming"
        mock_topic.source_level = "intermediate"
        mock_topic.refined_material = {
            "topics": [
                {
                    "topic": "Python Loops",
                    "learning_objectives": ["Use for loops", "Use while loops"],
                    "key_facts": ["for loops iterate over sequences", "while loops continue until condition is false"]
                }
            ]
        }
        mock_topic.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_topic.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_topic_class.return_value = mock_topic

        # Create topic via Content Creation API
        topic_request = {
            "title": "Python Loops",
            "source_material": "Loops allow you to repeat code multiple times...",
            "source_domain": "Programming",
            "source_level": "intermediate"
        }

        create_response = self.client.post("/api/content/topics", json=topic_request)
        assert create_response.status_code == 200
        created_topic = create_response.json()

        # Step 2: Access the created content via Learning API
        # Mock the learning API database access
        def mock_learning_query_side_effect(*args):
            query_mock = Mock()
            if args[0] == mock_topic_class:
                query_mock.filter.return_value.first.return_value = mock_topic
            else:  # BiteSizedComponent
                query_mock.filter.return_value.all.return_value = []  # No components yet
            return query_mock

        mock_session.query.side_effect = mock_learning_query_side_effect

        # Access via Learning API
        learning_response = self.client.get("/api/learning/topics/loops-topic-789")
        assert learning_response.status_code == 200
        learning_topic = learning_response.json()

        # Verify the content is accessible through both APIs
        assert created_topic["title"] == learning_topic["title"]
        assert created_topic["user_level"] == learning_topic["user_level"]
        assert len(created_topic["refined_material"]["topics"]) == 1
        assert len(learning_topic["learning_objectives"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])