"""
Integration tests for Content Creation module.

These tests verify the complete flow from service layer through to persistence.
They use real implementations (SQLAlchemy repository with test database AND real LLM service)
for true end-to-end integration testing with NO MOCKING.

Note: These tests make real API calls to OpenAI and will incur costs.
"""

import os

from modules.llm_services.module_api.llm_service import LLMService
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from modules.content_creation.infrastructure.persistence.sqlalchemy_topic_repository import SQLAlchemyTopicRepository
from modules.content_creation.module_api import (
    ContentCreationService,
    CreateComponentRequest,
    CreateTopicRequest,
    TopicResponse,
)
from modules.llm_services.module_api import create_llm_service
from src.data_structures import Base


class TestContentCreationIntegration:
    """Integration tests for content creation functionality."""

    @pytest.fixture
    def test_db_engine(self):
        """Create an in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def test_session_factory(self, test_db_engine):
        """Create a session factory for the test database."""
        return sessionmaker(bind=test_db_engine)

    @pytest.fixture
    def topic_repository(self, test_session_factory):
        """Create a SQLAlchemy topic repository for testing."""
        return SQLAlchemyTopicRepository(test_session_factory)

    @pytest.fixture
    def real_llm_service(self):
        """Create a real LLM service that makes actual API calls."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set - skipping real LLM integration tests")

        return create_llm_service(
            api_key=api_key,
            model="gpt-3.5-turbo",  # Use cheaper model for testing
            provider="openai",
            cache_enabled=True,
        )

    @pytest.fixture
    def content_service(self, topic_repository: SQLAlchemyTopicRepository, real_llm_service: LLMService) -> ContentCreationService:
        """Create content creation service with SQLAlchemy repository and real LLM service."""
        return ContentCreationService(topic_repository=topic_repository, llm_service=real_llm_service)

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.llm
    async def test_create_topic_complete_flow(self, content_service: ContentCreationService) -> None:
        """Test complete topic creation flow with real LLM API calls."""
        # Create topic request
        request = CreateTopicRequest(
            title="Python Basics",
            core_concept="Variables and data types in Python",
            user_level="beginner",
            domain="programming",
            source_material="Python is a programming language that is widely used for web development, data analysis, artificial intelligence, and more. Variables in Python are used to store data values and can hold different types of data such as strings, integers, floats, and booleans.",
        )

        # Create topic using the real method
        topic_response = await content_service.create_topic_from_source_material(request)

        # Verify topic was created
        assert isinstance(topic_response, TopicResponse)
        assert topic_response.title == "Python Basics"
        assert topic_response.core_concept == "Variables and data types in Python"
        assert topic_response.user_level == "beginner"
        assert len(topic_response.learning_objectives) >= 1  # Real LLM will determine count
        assert len(topic_response.key_concepts) >= 1  # Real LLM will determine count
        assert topic_response.source_material and "Python is a programming language" in topic_response.source_material

        # Verify topic has an ID and timestamps
        assert topic_response.id is not None
        assert topic_response.created_at is not None
        assert topic_response.updated_at is not None

    # @pytest.mark.asyncio
    # @pytest.mark.integration
    # @pytest.mark.llm
    # async def test_create_and_retrieve_topic(self, content_service):
    #     """Test creating a topic and then retrieving it."""
    #     # Create topic
    #     request = CreateTopicRequest(
    #         title="JavaScript Functions",
    #         core_concept="Function declaration and usage",
    #         user_level="intermediate",
    #         source_material="Functions in JavaScript are reusable blocks of code that can be called with different parameters. They are fundamental building blocks that help organize code and avoid repetition. Functions can return values and accept parameters to make them flexible and powerful.",
    #     )

    #     created_topic = await content_service.create_topic_from_source_material(request)

    #     # Retrieve the topic
    #     retrieved_topic = await content_service.get_topic(created_topic.id)

    #     # Verify they match
    #     assert retrieved_topic.id == created_topic.id
    #     assert retrieved_topic.title == created_topic.title
    #     assert retrieved_topic.core_concept == created_topic.core_concept
    #     assert retrieved_topic.user_level == created_topic.user_level

    # @pytest.mark.asyncio
    # async def test_create_component_for_topic(self, content_service):
    #     """Test creating a component for an existing topic."""
    #     # Skipping MCQ test for now to focus on basic topic creation
    #     pass

    # @pytest.mark.asyncio
    # @pytest.mark.integration
    # @pytest.mark.llm
    # async def test_search_topics_functionality(self, content_service):
    #     """Test topic search functionality."""
    #     # Create multiple topics
    #     topics_data = [
    #         ("Python Basics", "beginner", ["python", "variables"]),
    #         ("Python Advanced", "advanced", ["python", "decorators"]),
    #         ("JavaScript Intro", "beginner", ["javascript", "functions"]),
    #     ]

    #     created_topics = []
    #     for title, level, concepts in topics_data:
    #         request = CreateTopicRequest(
    #             title=title,
    #             core_concept=f"Learning {title.lower()}",
    #             user_level=level,
    #             domain="programming",
    #             source_material=f"This is comprehensive learning material about {title.lower()} covering all the fundamental concepts, syntax, and best practices. The content includes detailed explanations, examples, and practical applications to help learners master the subject effectively.",
    #         )
    #         topic = await content_service.create_topic_from_source_material(request)
    #         created_topics.append(topic)

    #     # Search for Python topics
    #     python_topics = await content_service.search_topics(query="Python")
    #     assert len(python_topics) == 2
    #     assert all("Python" in topic.title for topic in python_topics)

    #     # Search by user level
    #     beginner_topics = await content_service.search_topics(user_level="beginner")
    #     assert len(beginner_topics) == 2
    #     assert all(topic.user_level == "beginner" for topic in beginner_topics)

    #     # Search with no results
    #     no_results = await content_service.search_topics(query="NonexistentTopic")
    #     assert len(no_results) == 0

    # @pytest.mark.asyncio
    # @pytest.mark.integration
    # @pytest.mark.llm
    # async def test_delete_topic_functionality(self, content_service):
    #     """Test topic deletion functionality."""
    #     # Create a topic
    #     request = CreateTopicRequest(
    #         title="Temporary Topic",
    #         core_concept="This will be deleted",
    #         user_level="beginner",
    #         domain="programming",
    #         source_material="This is a temporary topic created for testing deletion functionality. It contains sample content that will be removed as part of the test to verify that the deletion process works correctly and completely.",
    #     )

    #     topic = await content_service.create_topic_from_source_material(request)
    #     topic_id = topic.id

    #     # Verify topic exists
    #     retrieved_topic = await content_service.get_topic(topic_id)
    #     assert retrieved_topic is not None

    #     # Delete the topic
    #     await content_service.delete_topic(topic_id)

    #     # Verify topic no longer exists
    #     with pytest.raises(Exception):  # Should raise an exception when topic not found
    #         await content_service.get_topic(topic_id)
