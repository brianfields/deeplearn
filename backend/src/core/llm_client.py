"""
Centralized LLM client for all learning system interactions.

This module provides a unified interface for all LLM operations across
the learning system modules.
"""

import asyncio
from datetime import UTC, datetime
import logging
from typing import Any, TypedDict, TypeVar

from pydantic import BaseModel

from src.llm_interface import (
    LLMConfig,
    LLMError,
    LLMMessage,
    LLMProviderType,
    LLMResponse,
    MessageRole,
    create_llm_provider,
)


class LLMStats(TypedDict):
    total_requests: int
    cache_hits: int
    errors: int
    last_request: datetime | None


# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


class LLMClientError(Exception):
    """Exception raised by LLM client operations"""

    pass


class LLMClient:
    """
    Centralized client for all LLM operations.

    This class provides a unified interface for generating responses,
    handling retries, caching, and error management across all modules.
    """

    def __init__(self, config: LLMConfig, cache_enabled: bool = True) -> None:
        self.config = config
        self.provider = create_llm_provider(config)
        self.cache_enabled = cache_enabled
        self.logger = logging.getLogger(__name__)
        self._response_cache: dict[str, Any] | None = {} if cache_enabled else None
        self._stats: LLMStats = {
            "total_requests": 0,
            "cache_hits": 0,
            "errors": 0,
            "last_request": None,
        }

    async def generate_response(
        self, messages: list[LLMMessage], max_retries: int = 3, use_cache: bool = True
    ) -> LLMResponse:
        """
        Generate a text response from the LLM.

        Args:
            messages: List of messages to send to the LLM
            max_retries: Maximum number of retry attempts
            use_cache: Whether to use cached responses

        Returns:
            LLMResponse object

        Raises:
            LLMClientError: If generation fails after retries
        """
        self._stats["total_requests"] += 1
        self._stats["last_request"] = datetime.now(UTC)

        # Check cache first
        if use_cache and self._response_cache:
            cache_key = self._create_cache_key(messages)
            if cache_key in self._response_cache:
                self._stats["cache_hits"] += 1
                self.logger.info(f"Cache hit for request with {len(messages)} messages")
                return self._response_cache[cache_key]

        # Generate response with retries
        for attempt in range(max_retries + 1):
            try:
                response = await self.provider.generate_response(messages)

                # Cache the response
                if use_cache and self._response_cache:
                    cache_key = self._create_cache_key(messages)
                    self._response_cache[cache_key] = response

                self.logger.info(f"Generated response with {len(response.content)} characters")
                return response

            except LLMError as e:
                self._stats["errors"] += 1
                if attempt < max_retries:
                    wait_time = 2**attempt  # Exponential backoff
                    self.logger.warning(f"LLM request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"LLM request failed after {max_retries} retries: {e}")
                    raise LLMClientError(f"Failed to generate response after {max_retries} retries: {e}") from e

        # This should never be reached due to the raise above, but satisfies type checker
        raise LLMClientError("Unexpected error in generate_response")

    async def generate_structured_response(
        self,
        messages: list[LLMMessage],
        schema: dict[str, Any],
        max_retries: int = 3,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Generate a structured response from the LLM.

        Args:
            messages: List of messages to send to the LLM
            schema: JSON schema for the expected response structure
            max_retries: Maximum number of retry attempts
            use_cache: Whether to use cached responses

        Returns:
            Parsed JSON response as dictionary

        Raises:
            LLMClientError: If generation fails after retries
        """
        self._stats["total_requests"] += 1
        self._stats["last_request"] = datetime.utcnow()

        # Check cache first
        if use_cache and self._response_cache:
            cache_key = self._create_cache_key(messages, schema)
            if cache_key in self._response_cache:
                self._stats["cache_hits"] += 1
                self.logger.info(f"Cache hit for structured request with {len(messages)} messages")
                return self._response_cache[cache_key]

        # Generate response with retries
        for attempt in range(max_retries + 1):
            try:
                response = await self.provider.generate_structured_response(messages, schema)

                # Cache the response
                if use_cache and self._response_cache:
                    cache_key = self._create_cache_key(messages, schema)
                    self._response_cache[cache_key] = response

                self.logger.info(f"Generated structured response with {len(response)} keys")
                return response

            except LLMError as e:
                self._stats["errors"] += 1
                if attempt < max_retries:
                    wait_time = 2**attempt  # Exponential backoff
                    self.logger.warning(
                        f"Structured LLM request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"Structured LLM request failed after {max_retries} retries: {e}")
                    raise LLMClientError(
                        f"Failed to generate structured response after {max_retries} retries: {e}"
                    ) from e

        # This should never be reached due to the raise above, but satisfies type checker
        raise LLMClientError("Unexpected error in generate_structured_response")

    async def generate_structured_object(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        max_retries: int = 3,
        use_cache: bool = True,
    ) -> T:
        """
        Generate a structured response using instructor and Pydantic models.

        Args:
            messages: List of messages to send to the LLM
            response_model: Pydantic model class defining the expected response structure
            max_retries: Maximum number of retry attempts
            use_cache: Whether to use cached responses

        Returns:
            Instance of the response_model with parsed data

        Raises:
            LLMClientError: If generation fails after retries
        """
        self._stats["total_requests"] += 1
        self._stats["last_request"] = datetime.utcnow()

        # Check cache first
        if use_cache and self._response_cache:
            cache_key = self._create_cache_key(messages, {"model": response_model.__name__})
            if cache_key in self._response_cache:
                self._stats["cache_hits"] += 1
                self.logger.info(f"Cache hit for structured object request with {len(messages)} messages")
                return self._response_cache[cache_key]

        # Generate response with retries
        for attempt in range(max_retries + 1):
            try:
                response = await self.provider.generate_structured_object(messages, response_model)

                # Cache the response
                if use_cache and self._response_cache:
                    cache_key = self._create_cache_key(messages, {"model": response_model.__name__})
                    self._response_cache[cache_key] = response

                self.logger.info(f"Generated structured object of type {response_model.__name__}")
                return response

            except LLMError as e:
                self._stats["errors"] += 1
                if attempt < max_retries:
                    wait_time = 2**attempt  # Exponential backoff
                    self.logger.warning(
                        f"Structured object LLM request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"Structured object LLM request failed after {max_retries} retries: {e}")
                    raise LLMClientError(
                        f"Failed to generate structured object after {max_retries} retries: {e}"
                    ) from e

        # This should never be reached due to the raise above, but satisfies type checker
        raise LLMClientError("Unexpected error in generate_structured_object")

    def _create_cache_key(self, messages: list[LLMMessage], schema: dict | None = None) -> str:
        """Create a cache key for the given messages and schema"""
        messages_str = "|".join(f"{msg.role}:{msg.content}" for msg in messages)
        if schema:
            schema_str = str(sorted(schema.items()))
            return f"{hash(messages_str + schema_str)}"
        return f"{hash(messages_str)}"

    def clear_cache(self) -> None:
        """Clear the response cache"""
        if self._response_cache:
            self._response_cache.clear()
            self.logger.info("Response cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get client statistics"""
        return {
            **self._stats,
            "cache_size": len(self._response_cache) if self._response_cache else 0,
            "cache_enabled": self.cache_enabled,
            "provider": self.config.provider.value,
            "model": self.config.model,
        }

    def get_cache_size(self) -> int:
        """Get the current cache size"""
        return len(self._response_cache) if self._response_cache else 0

    async def health_check(self) -> dict[str, Any]:
        """
        Perform a health check on the LLM client.

        Returns:
            Dictionary containing health status
        """
        try:
            # Simple test message
            test_messages = [LLMMessage(role=MessageRole.USER, content="Hello, are you working?")]

            response = await self.generate_response(test_messages, use_cache=False)

            return {
                "status": "healthy",
                "provider": self.config.provider.value,
                "model": self.config.model,
                "response_length": len(response.content),
                "stats": self.get_stats(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "provider": self.config.provider.value,
                "model": self.config.model,
                "stats": self.get_stats(),
            }


def create_llm_client(
    api_key: str,
    model: str = "gpt-4o",
    provider: str = "openai",
    cache_enabled: bool = True,
    **kwargs: Any,  # noqa: ANN401
) -> LLMClient:
    """
    Create an LLM client with common configuration.

    Args:
        api_key: API key for the LLM provider
        model: Model to use
        provider: Provider name
        cache_enabled: Whether to enable response caching
        **kwargs: Additional LLM configuration parameters

    Returns:
        Configured LLMClient instance
    """

    llm_config = LLMConfig(
        provider=LLMProviderType(provider),
        model=model,
        api_key=api_key,
        temperature=kwargs.get("temperature", 0.7),
        max_tokens=kwargs.get("max_tokens", 1500),
        **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]},
    )

    return LLMClient(llm_config, cache_enabled=cache_enabled)
