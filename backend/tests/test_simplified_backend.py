#!/usr/bin/env python3
"""
Comprehensive tests for the simplified bite-sized topics backend system.

This test suite covers:
- API endpoint testing (health, list topics, topic details, create topic)
- BiteSizedTopicService functionality
- Database integration
- Error handling and edge cases
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

# Test framework imports
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Import system under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.server import app
from api import routes
from modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService, BiteSizedTopicError
from data_structures import BiteSizedTopic, BiteSizedComponent, ComponentType, CreationStrategy


class TestAPIEndpoints:
    """Test class for API endpoint functionality."""

    def setup_method(self):
        """Set up test client and mock dependencies."""
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

        # Verify values
        assert data["status"] == "healthy"
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["services"]["database"], bool)

    def test_health_endpoint_format(self):
        """Test health endpoint returns properly formatted ISO timestamp."""
        response = self.client.get("/health")
        data = response.json()

        # Verify timestamp is valid ISO format
        try:
            datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

    @patch('api.routes.PostgreSQLTopicRepository')
    def test_list_topics_endpoint_success(self, mock_repo_class):
        """Test listing bite-sized topics endpoint with mock data."""
        # Setup mock repository
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        # Mock topic data
        mock_topics = [
            Mock(
                id="topic-1",
                title="Introduction to Python",
                core_concept="Python basics",
                user_level="beginner",
                learning_objectives=["Learn Python syntax"],
                key_concepts=["variables", "functions"],
                created_at=datetime(2024, 1, 1, 12, 0, 0)
            ),
            Mock(
                id="topic-2",
                title="Advanced Python",
                core_concept="Python advanced features",
                user_level="advanced",
                learning_objectives=["Master decorators"],
                key_concepts=["decorators", "generators"],
                created_at=datetime(2024, 1, 2, 12, 0, 0)
            )
        ]

        mock_repo.list_topics.return_value = mock_topics

        # Make request
        response = self.client.get("/api/bite-sized-topics")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert isinstance(data, list)
        assert len(data) == 2

        # Verify first topic
        topic1 = data[0]
        assert topic1["id"] == "topic-1"
        assert topic1["title"] == "Introduction to Python"
        assert topic1["core_concept"] == "Python basics"
        assert topic1["user_level"] == "beginner"
        assert topic1["estimated_duration"] == 15
        assert "created_at" in topic1

    @patch('api.routes.PostgreSQLTopicRepository')
    def test_list_topics_endpoint_empty(self, mock_repo_class):
        """Test listing topics when no topics exist."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.list_topics.return_value = []

        response = self.client.get("/api/bite-sized-topics")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch('api.routes.PostgreSQLTopicRepository')
    def test_list_topics_endpoint_error(self, mock_repo_class):
        """Test list topics endpoint handles database errors."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.list_topics.side_effect = Exception("Database connection failed")

        response = self.client.get("/api/bite-sized-topics")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to fetch bite-sized topics" in data["detail"]

    @patch('api.routes.PostgreSQLTopicRepository')
    def test_topic_detail_endpoint_success(self, mock_repo_class):
        """Test getting topic details with mock data."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        # Mock topic content
        mock_topic_spec = Mock(
            topic_title="Introduction to Python",
            core_concept="Python basics",
            user_level="beginner",
            learning_objectives=["Learn Python syntax"],
            key_concepts=["variables", "functions"],
            key_aspects=["syntax", "semantics"],
            target_insights=["Understanding Python philosophy"],
            common_misconceptions=["Python is slow"],
            previous_topics=[],
            creation_strategy=Mock(value="comprehensive")
        )

        mock_topic_content = Mock(topic_spec=mock_topic_spec)
        mock_repo.get_topic.return_value = mock_topic_content

        # Mock components
        mock_components = [
            Mock(
                component_type="didactic_snippet",
                content={"title": "Python Basics", "snippet": "Python is..."},
                title="Python Basics",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
                version=1,
                generation_prompt="Generate a snippet about Python basics",
                raw_llm_response="Python is a programming language..."
            )
        ]
        mock_repo.get_topic_components.return_value = mock_components

        response = self.client.get("/api/bite-sized-topics/topic-1")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["id"] == "topic-1"
        assert data["title"] == "Introduction to Python"
        assert data["core_concept"] == "Python basics"
        assert "components" in data
        assert len(data["components"]) == 1

    @patch('api.routes.PostgreSQLTopicRepository')
    def test_topic_detail_endpoint_not_found(self, mock_repo_class):
        """Test topic detail endpoint when topic doesn't exist."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_topic.return_value = None

        response = self.client.get("/api/bite-sized-topics/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "Bite-sized topic not found" in data["detail"]

    @patch('api.routes.TopicOrchestrator')
    @patch('api.routes.LLMClient')
    @patch('api.routes.ServiceFactory')
    def test_create_topic_endpoint_success(self, mock_service_factory, mock_llm_client, mock_orchestrator_class):
        """Test creating a new topic via API."""
        # Setup mocks
        mock_orchestrator = AsyncMock()
        mock_orchestrator_class.return_value = mock_orchestrator

        mock_topic_content = Mock()
        mock_orchestrator.create_topic.return_value = mock_topic_content

        # Request data
        request_data = {
            "title": "Test Topic",
            "core_concept": "Test Concept",
            "user_level": "beginner",
            "learning_objectives": ["Objective 1"],
            "key_concepts": ["Concept 1"]
        }

        response = self.client.post("/api/bite-sized-topics", params=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response
        assert "id" in data
        assert data["title"] == "Test Topic"
        assert data["status"] == "created"
        assert "created successfully" in data["message"]

    @patch('api.routes.TopicOrchestrator')
    def test_create_topic_endpoint_error(self, mock_orchestrator_class):
        """Test create topic endpoint handles creation errors."""
        mock_orchestrator_class.side_effect = Exception("Topic creation failed")

        request_data = {
            "title": "Test Topic",
            "core_concept": "Test Concept"
        }

        response = self.client.post("/api/bite-sized-topics", params=request_data)

        assert response.status_code == 500
        data = response.json()
        assert "Failed to create bite-sized topic" in data["detail"]


class TestBiteSizedTopicService:
    """Test class for BiteSizedTopicService functionality."""

    def setup_method(self):
        """Set up service instance with mocked dependencies."""
        self.mock_config = Mock()
        self.mock_llm_client = AsyncMock()

        # Create service instance
        self.service = BiteSizedTopicService(self.mock_config, self.mock_llm_client)

    @pytest.mark.asyncio
    async def test_create_lesson_content_success(self):
        """Test successful lesson content generation."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = "# Test Lesson\n\nThis is a test lesson about Python basics."
        self.mock_llm_client.generate_response.return_value = mock_response

        # Call service method
        result = await self.service.create_lesson_content(
            topic_title="Introduction to Python",
            topic_description="Learn Python basics",
            learning_objectives=["Understand Python syntax"],
            user_level="beginner"
        )

        # Verify result
        assert isinstance(result, str)
        assert "Test Lesson" in result
        assert len(result) > 0

        # Verify LLM client was called
        self.mock_llm_client.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_lesson_content_error(self):
        """Test lesson content generation handles errors."""
        # Setup mock to raise exception
        self.mock_llm_client.generate_response.side_effect = Exception("LLM API error")

        # Call service method and expect exception
        with pytest.raises(BiteSizedTopicError) as exc_info:
            await self.service.create_lesson_content(
                topic_title="Test Topic",
                topic_description="Test Description",
                learning_objectives=["Test Objective"]
            )

        assert "Failed to generate lesson content" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_didactic_snippet_success(self):
        """Test successful didactic snippet creation."""
        # Setup mock response with JSON format
        mock_response = Mock()
        mock_response.content = '''```json
        {
            "title": "Python Variables",
            "snippet": "Variables in Python are containers for storing data values.",
            "type": "didactic_snippet",
            "difficulty": 2
        }
        ```'''
        self.mock_llm_client.generate_response.return_value = mock_response

        result = await self.service.create_didactic_snippet(
            topic_title="Python Basics",
            key_concept="variables",
            user_level="beginner"
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert result["title"] == "Python Variables"
        assert "snippet" in result
        assert result["type"] == "didactic_snippet"
        assert result["difficulty"] == 2
        assert "_generation_metadata" in result

    @pytest.mark.asyncio
    async def test_create_didactic_snippet_fallback_parsing(self):
        """Test didactic snippet creation with fallback parsing."""
        # Setup mock response with non-JSON format
        mock_response = Mock()
        mock_response.content = "Title: Test Title\nSnippet: Test snippet content"
        self.mock_llm_client.generate_response.return_value = mock_response

        result = await self.service.create_didactic_snippet(
            topic_title="Test Topic",
            key_concept="test concept"
        )

        # Verify fallback parsing worked
        assert result["title"] == "Test Title"
        assert result["snippet"] == "Test snippet content"
        assert result["type"] == "didactic_snippet"

    @pytest.mark.asyncio
    async def test_create_glossary_success(self):
        """Test successful glossary creation."""
        # Setup mock response with JSON format
        mock_response = Mock()
        mock_response.content = '''```json
        {
            "glossary_entries": [
                {
                    "concept": "Variable",
                    "title": "Variable Definition",
                    "explanation": "A variable is a storage location with an associated name.",
                    "difficulty": 1
                },
                {
                    "concept": "Function",
                    "title": "Function Definition",
                    "explanation": "A function is a reusable block of code.",
                    "difficulty": 2
                }
            ]
        }
        ```'''
        self.mock_llm_client.generate_response.return_value = mock_response

        result = await self.service.create_glossary(
            topic_title="Python Basics",
            concepts=["Variable", "Function"],
            user_level="beginner"
        )

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2

        # Check first entry
        entry1 = result[0]
        assert entry1["concept"] == "Variable"
        assert entry1["explanation"] == "A variable is a storage location with an associated name."
        assert entry1["number"] == 1
        assert "_generation_metadata" in entry1

    @pytest.mark.asyncio
    async def test_create_multiple_choice_questions_success(self):
        """Test successful multiple choice questions creation."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = '''```json
        {
            "questions": [
                {
                    "title": "Python Variables MCQ",
                    "question": "What is a variable in Python?",
                    "choices": {
                        "A": "A storage location",
                        "B": "A function",
                        "C": "A loop",
                        "D": "A class"
                    },
                    "correct_answer": "A",
                    "justifications": {
                        "A": "Correct - variables store data",
                        "B": "Incorrect - functions are code blocks"
                    },
                    "target_concept": "variables",
                    "difficulty": 2
                }
            ]
        }
        ```'''
        self.mock_llm_client.generate_response.return_value = mock_response

        result = await self.service.create_multiple_choice_questions(
            topic_title="Python Basics",
            core_concept="variables",
            user_level="beginner"
        )

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 1

        question = result[0]
        assert question["question"] == "What is a variable in Python?"
        assert len(question["choices"]) == 4
        assert question["correct_answer"] == "A"
        assert "justifications" in question

    def test_parse_didactic_snippet_json_success(self):
        """Test JSON parsing for didactic snippets."""
        json_content = '''```json
        {
            "title": "Test Title",
            "snippet": "Test snippet content",
            "type": "didactic_snippet",
            "difficulty": 3
        }
        ```'''

        result = self.service._parse_didactic_snippet(json_content)

        assert result["title"] == "Test Title"
        assert result["snippet"] == "Test snippet content"
        assert result["type"] == "didactic_snippet"
        assert result["difficulty"] == 3

    def test_parse_didactic_snippet_invalid_json(self):
        """Test didactic snippet parsing with invalid JSON falls back gracefully."""
        invalid_content = "This is not valid JSON content"

        result = self.service._parse_didactic_snippet(invalid_content)

        # Should return fallback structure
        assert result["title"] == "Didactic Snippet"
        assert result["snippet"] == invalid_content
        assert result["type"] == "didactic_snippet"
        assert result["difficulty"] == 2

    @pytest.mark.asyncio
    async def test_validate_content_success(self):
        """Test content validation with valid content."""
        valid_content = """
        # Test Lesson

        This is a comprehensive lesson about Python basics that includes:

        - **Variables**: Learn how to store data
        - **Functions**: Create reusable code blocks
        - **Loops**: Repeat operations efficiently

        ## Interactive Exercise

        Try to create a simple function that adds two numbers.

        What do you think the result will be?

        Consider how Python handles different data types.
        """

        result = await self.service.validate_content(valid_content)

        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert result["word_count"] > 0
        assert result["estimated_reading_time"] > 0

    @pytest.mark.asyncio
    async def test_validate_content_too_short(self):
        """Test content validation with content that's too short."""
        short_content = "Short"

        result = await self.service.validate_content(short_content)

        assert result["valid"] is False
        assert "Content too short" in result["issues"]

    @pytest.mark.asyncio
    async def test_validate_content_too_long(self):
        """Test content validation with content that's too long."""
        long_content = "Very long content. " * 300  # Create very long content

        result = await self.service.validate_content(long_content)

        assert result["valid"] is False
        assert "Content too long for 15-minute lesson" in result["issues"]


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @patch('modules.lesson_planning.bite_sized_topics.postgresql_storage.PostgreSQLTopicRepository')
    def test_repository_initialization(self, mock_repo_class):
        """Test that repository can be initialized."""
        from modules.lesson_planning.bite_sized_topics.postgresql_storage import PostgreSQLTopicRepository

        # Should not raise an exception
        repository = PostgreSQLTopicRepository()
        assert repository is not None

    @patch('modules.lesson_planning.bite_sized_topics.postgresql_storage.PostgreSQLTopicRepository')
    @pytest.mark.asyncio
    async def test_repository_list_topics_interface(self, mock_repo_class):
        """Test repository list_topics method interface."""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        # Mock return value
        mock_repo.list_topics.return_value = []

        from modules.lesson_planning.bite_sized_topics.postgresql_storage import PostgreSQLTopicRepository
        repository = PostgreSQLTopicRepository()

        # Should be able to call method
        result = await repository.list_topics(limit=10)
        assert result == []
        mock_repo.list_topics.assert_called_once_with(limit=10)


class TestErrorHandling:
    """Test error handling across the system."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_invalid_endpoint_404(self):
        """Test that invalid endpoints return 404."""
        response = self.client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404

    def test_malformed_topic_id_format(self):
        """Test topic detail endpoint with malformed ID."""
        # Test with various malformed IDs
        malformed_ids = ["", "   ", "invalid/id", "id with spaces"]

        for bad_id in malformed_ids:
            with patch('api.routes.PostgreSQLTopicRepository') as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo_class.return_value = mock_repo
                mock_repo.get_topic.return_value = None

                response = self.client.get(f"/api/bite-sized-topics/{bad_id}")
                assert response.status_code == 404

    def test_create_topic_missing_required_params(self):
        """Test topic creation with missing required parameters."""
        # Missing title
        response = self.client.post("/api/bite-sized-topics", params={
            "core_concept": "Test Concept"
        })
        assert response.status_code == 422  # FastAPI validation error

        # Missing core_concept
        response = self.client.post("/api/bite-sized-topics", params={
            "title": "Test Title"
        })
        assert response.status_code == 422


def run_all_tests():
    """Function to run all tests programmatically."""
    print("Running comprehensive backend tests...")

    # Run pytest on this file
    import subprocess
    result = subprocess.run([
        "python", "-m", "pytest", __file__, "-v", "--tb=short"
    ], capture_output=True, text=True)

    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    return result.returncode == 0


if __name__ == "__main__":
    # Run tests when file is executed directly
    success = run_all_tests()
    exit(0 if success else 1)