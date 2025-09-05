"""
LLM Service - Public API for LLM Services module.

This service provides the main interface for other modules to interact
with LLM functionality, including prompt generation and response handling.
"""

import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from ..domain.entities.llm_provider import (
    LLMConfig,
    LLMMessage,
    LLMProviderType,
    LLMResponse,
    LLMUsagePolicy,
)
from ..domain.entities.prompt import (
    Prompt,
    PromptContext,
    PromptMetadata,
    PromptPolicy,
    PromptType,
    create_default_context,
)
from ..infrastructure.clients.llm_client import create_llm_client

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Exception raised by LLM service operations"""

    pass


class LLMService:
    """
    Main service class for LLM operations.

    This service orchestrates between domain entities and infrastructure
    to provide a clean API for other modules.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        provider: str = "openai",
        cache_enabled: bool = True,
    ):
        self.config = LLMConfig(
            provider=LLMProviderType(provider),
            model=model,
            api_key=api_key,
        )

        # Validate configuration
        LLMUsagePolicy.validate_config(self.config)

        self.client = create_llm_client(
            api_key=api_key,
            model=model,
            provider=provider,
            cache_enabled=cache_enabled,
        )

        self.logger = logging.getLogger(__name__)
        self._prompt_cache: dict[str, Prompt] = {}

    async def generate_content(
        self,
        prompt_name: str,
        context: PromptContext | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate content using a named prompt template.

        Args:
            prompt_name: Name of the prompt template to use
            context: Prompt context (uses default if not provided)
            **kwargs: Additional variables for prompt rendering

        Returns:
            Generated content as string

        Raises:
            LLMServiceError: If generation fails
        """
        try:
            # Use default context if none provided
            if context is None:
                context = create_default_context()

            # Get or load prompt template
            prompt = await self._get_prompt_template(prompt_name)

            # Validate context for this prompt
            if not prompt.validate_context(context):
                raise LLMServiceError(f"Invalid context for prompt '{prompt_name}'")

            # Render prompt to messages
            messages = prompt.render(context, **kwargs)

            # Validate messages
            LLMUsagePolicy.validate_messages(messages)

            # Generate response
            response = await self.client.generate_response(messages)

            self.logger.info(f"Generated content for prompt '{prompt_name}': {len(response.content)} chars, {response.tokens_used} tokens")

            return response.content

        except Exception as e:
            self.logger.error(f"Failed to generate content for prompt '{prompt_name}': {e}")
            raise LLMServiceError(f"Content generation failed: {e}") from e

    async def generate_structured_content(
        self,
        prompt_name: str,
        response_schema: dict[str, Any],
        context: PromptContext | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Generate structured content using a named prompt template.

        Args:
            prompt_name: Name of the prompt template to use
            response_schema: JSON schema for expected response structure
            context: Prompt context (uses default if not provided)
            **kwargs: Additional variables for prompt rendering

        Returns:
            Generated content as structured dictionary

        Raises:
            LLMServiceError: If generation fails
        """
        try:
            # Use default context if none provided
            if context is None:
                context = create_default_context()

            # Get or load prompt template
            prompt = await self._get_prompt_template(prompt_name)

            # Validate context for this prompt
            if not prompt.validate_context(context):
                raise LLMServiceError(f"Invalid context for prompt '{prompt_name}'")

            # Render prompt to messages
            messages = prompt.render(context, **kwargs)

            # Validate messages
            LLMUsagePolicy.validate_messages(messages)

            # Generate structured response
            response = await self.client.generate_structured_response(messages, response_schema)

            self.logger.info(f"Generated structured content for prompt '{prompt_name}': {len(response)} keys")

            return response

        except Exception as e:
            self.logger.error(f"Failed to generate structured content for prompt '{prompt_name}': {e}")
            raise LLMServiceError(f"Structured content generation failed: {e}") from e

    async def generate_object(
        self,
        prompt_name: str,
        response_model: type[T],
        context: PromptContext | None = None,
        **kwargs: Any,
    ) -> T:
        """
        Generate a structured object using a named prompt template.

        Args:
            prompt_name: Name of the prompt template to use
            response_model: Pydantic model class for response structure
            context: Prompt context (uses default if not provided)
            **kwargs: Additional variables for prompt rendering

        Returns:
            Generated content as instance of response_model

        Raises:
            LLMServiceError: If generation fails
        """
        try:
            # Use default context if none provided
            if context is None:
                context = create_default_context()

            # Get or load prompt template
            prompt = await self._get_prompt_template(prompt_name)

            # Validate context for this prompt
            if not prompt.validate_context(context):
                raise LLMServiceError(f"Invalid context for prompt '{prompt_name}'")

            # Render prompt to messages
            messages = prompt.render(context, **kwargs)

            # Validate messages
            LLMUsagePolicy.validate_messages(messages)

            # Generate structured object
            response = await self.client.generate_structured_object(messages, response_model)

            self.logger.info(f"Generated object for prompt '{prompt_name}': {response_model.__name__}")

            return response

        except Exception as e:
            self.logger.error(f"Failed to generate object for prompt '{prompt_name}': {e}")
            raise LLMServiceError(f"Object generation failed: {e}") from e

    async def generate_custom_response(
        self,
        messages: list[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a response using custom messages (not from templates).

        Args:
            messages: Custom LLM messages
            **kwargs: Additional generation parameters

        Returns:
            LLM response object

        Raises:
            LLMServiceError: If generation fails
        """
        try:
            # Validate messages
            LLMUsagePolicy.validate_messages(messages)

            # Generate response
            response = await self.client.generate_response(messages, **kwargs)

            self.logger.info(f"Generated custom response: {len(response.content)} chars, {response.tokens_used} tokens")

            return response

        except Exception as e:
            self.logger.error(f"Failed to generate custom response: {e}")
            raise LLMServiceError(f"Custom response generation failed: {e}") from e

    async def _get_prompt_template(self, prompt_name: str) -> Prompt:
        """
        Get or load a prompt template by name.

        This is a placeholder implementation. In a full system, this would
        load templates from a repository or database.
        """
        # Check cache first
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]

        # For now, create a simple template
        # In a real implementation, this would load from a prompt repository
        template = self._create_default_template(prompt_name)

        # Cache the template
        if PromptPolicy.should_cache_prompt(template, create_default_context()):
            self._prompt_cache[prompt_name] = template

        return template

    def _create_default_template(self, prompt_name: str) -> Prompt:
        """Create a default template for the given name (placeholder)"""
        # This is a temporary implementation
        # In the real system, templates would be loaded from storage

        templates = {
            "extract_material": Prompt(
                template="""
                Extract and refine educational material from the following source.

                Context: {context}

                Source Material: {source_material}

                Please extract the key concepts and present them in a clear, structured format
                appropriate for the user's level and learning style.
                """,
                metadata=PromptMetadata(
                    name="extract_material",
                    description="Extract and refine educational material",
                    prompt_type=PromptType.MATERIAL_EXTRACTION,
                ),
                required_variables=["source_material"],
            ),
            "generate_mcq": Prompt(
                template="""
                Generate multiple choice questions based on the following content.

                Context: {context}

                Content: {content}

                Create {num_questions} multiple choice questions that test understanding
                of the key concepts. Each question should have 4 options with one correct answer.
                """,
                metadata=PromptMetadata(
                    name="generate_mcq",
                    description="Generate multiple choice questions",
                    prompt_type=PromptType.MCQ_GENERATION,
                ),
                required_variables=["content", "num_questions"],
            ),
        }

        if prompt_name not in templates:
            raise LLMServiceError(f"Unknown prompt template: {prompt_name}")

        return templates[prompt_name]

    async def health_check(self) -> dict[str, Any]:
        """
        Perform a health check on the LLM service.

        Returns:
            Dictionary containing health status and statistics
        """
        try:
            client_health = await self.client.health_check()

            return {
                "status": "healthy",
                "service": "llm_services",
                "client_health": client_health,
                "prompt_cache_size": len(self._prompt_cache),
                "config": {
                    "provider": self.config.provider.value,
                    "model": self.config.model,
                },
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "llm_services",
                "error": str(e),
                "prompt_cache_size": len(self._prompt_cache),
            }

    def get_stats(self) -> dict[str, Any]:
        """Get service statistics"""
        client_stats = self.client.get_stats()

        return {
            "service": "llm_services",
            "client_stats": client_stats,
            "prompt_cache_size": len(self._prompt_cache),
            "config": {
                "provider": self.config.provider.value,
                "model": self.config.model,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            },
        }

    def clear_caches(self) -> None:
        """Clear all caches"""
        self._prompt_cache.clear()
        self.client.clear_cache()
        self.logger.info("All caches cleared")


# Factory function for easy service creation
def create_llm_service(
    api_key: str,
    model: str = "gpt-4o",
    provider: str = "openai",
    cache_enabled: bool = True,
) -> LLMService:
    """
    Create an LLM service with standard configuration.

    Args:
        api_key: API key for the LLM provider
        model: Model to use
        provider: Provider name
        cache_enabled: Whether to enable caching

    Returns:
        Configured LLMService instance
    """
    return LLMService(
        api_key=api_key,
        model=model,
        provider=provider,
        cache_enabled=cache_enabled,
    )
