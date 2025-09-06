"""
Unit tests for LLM Services module.

These tests use mocks and don't make external API calls.
They test the service layer orchestration and domain logic in isolation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.llm_services.domain.entities.llm_provider import (
    LLMMessage,
    LLMProviderType,
    LLMResponse,
    MessageRole,
)
from modules.llm_services.domain.entities.prompt import (
    LearningStyle,
    PromptContext,
    UserLevel,
    create_default_context,
)
from modules.llm_services.module_api import LLMService, create_llm_service


class TestLLMService:
    """Test cases for LLMService"""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client"""
        mock_client = MagicMock()
        mock_client.generate_response = AsyncMock()
        mock_client.generate_structured_response = AsyncMock()
        mock_client.generate_structured_object = AsyncMock()
        mock_client.health_check = AsyncMock()
        mock_client.get_stats = MagicMock()
        mock_client.clear_cache = MagicMock()
        return mock_client

    @pytest.fixture
    def llm_service(self, mock_llm_client):
        """Create an LLM service with mocked client"""
        with patch("modules.llm_services.module_api.llm_service.create_llm_client") as mock_create:
            mock_create.return_value = mock_llm_client
            service = LLMService(
                api_key="test-key",
                model="gpt-4o",
                provider="openai",
            )
            return service

    @pytest.mark.asyncio
    async def test_generate_content_success(self, llm_service, mock_llm_client):
        """Test successful content generation"""
        # Setup
        mock_response = LLMResponse(
            content="Generated content",
            provider=LLMProviderType.OPENAI,
            model="gpt-4o",
            tokens_used=50,
            cost_estimate=0.001,
        )
        mock_llm_client.generate_response.return_value = mock_response

        # Execute
        result = await llm_service.generate_content(prompt_name="extract_material", source_material="Test material")

        # Verify
        assert result == "Generated content"
        mock_llm_client.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_content_with_context(self, llm_service, mock_llm_client):
        """Test content generation with custom context"""
        # Setup
        mock_response = LLMResponse(
            content="Advanced content",
            provider=LLMProviderType.OPENAI,
            model="gpt-4o",
            tokens_used=75,
        )
        mock_llm_client.generate_response.return_value = mock_response

        context = PromptContext(
            user_level=UserLevel.ADVANCED,
            learning_style=LearningStyle.VISUAL,
            time_constraint=30,
        )

        # Execute
        result = await llm_service.generate_content(prompt_name="extract_material", context=context, source_material="Advanced material")

        # Verify
        assert result == "Advanced content"
        mock_llm_client.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_structured_content(self, llm_service, mock_llm_client):
        """Test structured content generation"""
        # Setup
        mock_response = {"key": "value", "items": [1, 2, 3]}
        mock_llm_client.generate_structured_response.return_value = mock_response

        schema = {"type": "object", "properties": {"key": {"type": "string"}, "items": {"type": "array"}}}

        # Execute
        result = await llm_service.generate_structured_content(prompt_name="generate_mcq", response_schema=schema, content="Test content", num_questions=3)

        # Verify
        assert result == mock_response
        mock_llm_client.generate_structured_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_custom_response(self, llm_service, mock_llm_client):
        """Test custom response generation"""
        # Setup
        mock_response = LLMResponse(
            content="Custom response",
            provider=LLMProviderType.OPENAI,
            model="gpt-4o",
            tokens_used=25,
        )
        mock_llm_client.generate_response.return_value = mock_response

        messages = [LLMMessage(role=MessageRole.USER, content="Hello")]

        # Execute
        result = await llm_service.generate_custom_response(messages)

        # Verify
        assert result.content == "Custom response"
        assert result.tokens_used == 25
        mock_llm_client.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check(self, llm_service, mock_llm_client):
        """Test health check functionality"""
        # Setup
        mock_client_health = {"status": "healthy", "provider": "openai", "model": "gpt-4o"}
        mock_llm_client.health_check.return_value = mock_client_health

        # Execute
        result = await llm_service.health_check()

        # Verify
        assert result["status"] == "healthy"
        assert result["service"] == "llm_services"
        assert result["client_health"] == mock_client_health
        mock_llm_client.health_check.assert_called_once()

    def test_get_stats(self, llm_service, mock_llm_client):
        """Test statistics retrieval"""
        # Setup
        mock_client_stats = {"total_requests": 10, "cache_hits": 3, "errors": 1}
        mock_llm_client.get_stats.return_value = mock_client_stats

        # Execute
        result = llm_service.get_stats()

        # Verify
        assert result["service"] == "llm_services"
        assert result["client_stats"] == mock_client_stats
        assert "config" in result
        mock_llm_client.get_stats.assert_called_once()

    def test_clear_caches(self, llm_service, mock_llm_client):
        """Test cache clearing"""
        # Execute
        llm_service.clear_caches()

        # Verify
        mock_llm_client.clear_cache.assert_called_once()

    def test_create_llm_service_factory(self):
        """Test the factory function"""
        with patch("modules.llm_services.module_api.llm_service.create_llm_client"):
            service = create_llm_service(api_key="test-key", model="gpt-3.5-turbo", provider="openai")

            assert isinstance(service, LLMService)
            assert service.config.model == "gpt-3.5-turbo"
            assert service.config.provider == LLMProviderType.OPENAI


class TestPromptContext:
    """Test cases for PromptContext"""

    def test_create_default_context(self):
        """Test default context creation"""
        context = create_default_context()

        assert context.user_level == UserLevel.BEGINNER
        assert context.learning_style == LearningStyle.BALANCED
        assert context.time_constraint == 15
        assert context.previous_performance == {}
        assert context.prerequisites_met == []

    def test_create_custom_context(self):
        """Test custom context creation"""
        context = create_default_context(user_level=UserLevel.ADVANCED, time_constraint=30, custom_instructions="Focus on practical examples")

        assert context.user_level == UserLevel.ADVANCED
        assert context.time_constraint == 30
        assert context.custom_instructions == "Focus on practical examples"

    def test_context_to_dict(self):
        """Test context serialization"""
        context = PromptContext(
            user_level=UserLevel.INTERMEDIATE,
            learning_style=LearningStyle.VISUAL,
            time_constraint=20,
        )

        data = context.to_dict()

        assert data["user_level"] == "intermediate"
        assert data["learning_style"] == "visual"
        assert data["time_constraint"] == 20
        assert isinstance(data["created_at"], str)

    def test_context_from_dict(self):
        """Test context deserialization"""
        data = {"user_level": "advanced", "learning_style": "auditory", "time_constraint": 25, "custom_instructions": "Test instructions"}

        context = PromptContext.from_dict(data)

        assert context.user_level == UserLevel.ADVANCED
        assert context.learning_style == LearningStyle.AUDITORY
        assert context.time_constraint == 25
        assert context.custom_instructions == "Test instructions"


if __name__ == "__main__":
    pytest.main([__file__])
