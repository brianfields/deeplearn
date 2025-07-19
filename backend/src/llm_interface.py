"""
LLM Interface Module for Proactive Learning App

This module provides a clean abstraction layer for interacting with Large Language Models.
It's designed to be easily swappable between different LLM providers while maintaining
consistent API interfaces for the learning application.

Key Features:
- Abstract base class for easy provider switching
- OpenAI implementation with proper error handling
- Structured response parsing
- Token usage tracking
- Retry logic with exponential backoff
- Type hints and comprehensive documentation
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import openai
import tiktoken
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


# Types and Enums
class LLMProviderType(str, Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class MessageRole(str, Enum):
    """Message roles for conversation"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """Structured message for LLM conversations"""

    role: MessageRole
    content: str
    timestamp: datetime | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class LLMResponse:
    """Structured response from LLM"""

    content: str
    provider: LLMProviderType
    model: str
    tokens_used: int
    cost_estimate: float | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] | None = None


class LLMConfig(BaseModel):
    """Configuration for LLM providers"""

    provider: LLMProviderType
    model: str
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, gt=0)
    timeout: int = Field(default=30, gt=0)
    max_retries: int = Field(default=3, ge=0)


class LLMError(Exception):
    """Base exception for LLM-related errors"""

    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded"""

    pass


class LLMAuthenticationError(LLMError):
    """Authentication failed"""

    pass


class LLMContentError(LLMError):
    """Content policy violation"""

    pass


# Abstract Base Class
class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    This class defines the interface that all LLM providers must implement.
    It ensures consistency across different providers and makes it easy to
    switch between them.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.token_encoder = None
        self._setup_token_encoder()

    @abstractmethod
    def _setup_token_encoder(self) -> None:
        """Setup token encoder for the specific provider"""
        pass

    @abstractmethod
    async def generate_response(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            messages: List of conversation messages
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse object with generated content and metadata

        Raises:
            LLMError: For various LLM-related errors
        """
        pass

    @abstractmethod
    async def generate_structured_response(self, messages: list[LLMMessage], response_schema: dict[str, Any], **kwargs) -> dict[str, Any]:
        """
        Generate a structured response (JSON) from the LLM.

        Args:
            messages: List of conversation messages
            response_schema: Expected JSON schema for response
            **kwargs: Additional provider-specific parameters

        Returns:
            Parsed JSON response

        Raises:
            LLMError: For various LLM-related errors
        """
        pass

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if self.token_encoder is None:
            # Fallback: approximate token count
            return int(len(text.split()) * 1.3)
        return len(self.token_encoder.encode(text))

    def estimate_cost(self, tokens: int) -> float:
        """
        Estimate cost for token usage.

        Args:
            tokens: Number of tokens

        Returns:
            Estimated cost in USD
        """
        # This should be implemented by each provider
        # Default implementation returns 0
        return 0.0


# OpenAI Implementation
class OpenAIProvider(LLMProvider):
    """
    OpenAI provider implementation.

    Supports both regular OpenAI API and Azure OpenAI.
    Includes proper error handling, retry logic, and token tracking.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._setup_client()

    def _setup_client(self) -> None:
        """Setup OpenAI client"""
        try:
            if self.config.provider == LLMProviderType.AZURE_OPENAI:
                self.client = AsyncOpenAI(api_key=self.config.api_key, base_url=self.config.base_url, timeout=self.config.timeout)
            else:
                self.client = AsyncOpenAI(api_key=self.config.api_key, timeout=self.config.timeout)
        except Exception as e:
            raise LLMAuthenticationError(f"Failed to setup OpenAI client: {e}") from e

    def _setup_token_encoder(self) -> None:
        """Setup tiktoken encoder for OpenAI models"""
        try:
            model_name = self.config.model
            if "gpt-4o" in model_name.lower():
                self.token_encoder = tiktoken.encoding_for_model("gpt-4o")
            elif "gpt-3.5" in model_name.lower():
                self.token_encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                self.token_encoder = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to setup token encoder: {e}")
            self.token_encoder = None

    async def generate_response(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Generate response from OpenAI API"""

        # Convert messages to OpenAI format
        openai_messages = [{"role": msg.role.value, "content": msg.content} for msg in messages]

        # Prepare request parameters
        request_params = {
            "model": self.config.model,
            "messages": openai_messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        # Add additional parameters if provided
        if "functions" in kwargs:
            request_params["functions"] = kwargs["functions"]
        if "function_call" in kwargs:
            request_params["function_call"] = kwargs["function_call"]

        # Execute request with retry logic
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self.client.chat.completions.create(**request_params)

                # Extract response data
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
                tokens_used = response.usage.total_tokens

                return LLMResponse(
                    content=content,
                    provider=self.config.provider,
                    model=self.config.model,
                    tokens_used=tokens_used,
                    cost_estimate=self.estimate_cost(tokens_used),
                    finish_reason=finish_reason,
                    metadata={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "attempt": attempt + 1,
                    },
                )

            except openai.RateLimitError as e:
                if attempt == self.config.max_retries:
                    raise LLMRateLimitError(f"Rate limit exceeded after {attempt + 1} attempts") from e
                wait_time = 2**attempt
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}")
                await asyncio.sleep(wait_time)

            except openai.AuthenticationError as e:
                raise LLMAuthenticationError(f"Authentication failed: {e}") from e

            except openai.BadRequestError as e:
                if "content_policy" in str(e).lower():
                    raise LLMContentError(f"Content policy violation: {e}") from e
                raise LLMError(f"Bad request: {e}") from e

            except Exception as e:
                if attempt == self.config.max_retries:
                    raise LLMError(f"Unexpected error after {attempt + 1} attempts: {e}") from e
                wait_time = 2**attempt
                logger.warning(f"Unexpected error, waiting {wait_time}s before retry {attempt + 1}: {e}")
                await asyncio.sleep(wait_time)

        # This should never be reached, but satisfies type checker
        raise LLMError("Failed to generate response after all retry attempts")

    async def generate_structured_response(self, messages: list[LLMMessage], response_schema: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Generate structured JSON response from OpenAI"""

        # Add schema instruction to system message
        schema_instruction = f"""
        You must respond with valid JSON that matches this exact schema:
        {json.dumps(response_schema, indent=2)}

        Do not include any text outside of the JSON response.
        """

        # Find system message or create one
        system_message = None
        user_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_message = LLMMessage(role=MessageRole.SYSTEM, content=msg.content + "\n\n" + schema_instruction)
            else:
                user_messages.append(msg)

        if system_message is None:
            system_message = LLMMessage(role=MessageRole.SYSTEM, content=schema_instruction)

        # Combine messages
        structured_messages = [system_message] + user_messages

        # Generate response
        response = await self.generate_response(
            structured_messages,
            temperature=kwargs.get("temperature", 0.3),  # Lower temperature for structured output
            **kwargs,
        )

        # Parse JSON response
        try:
            content = response.content.strip()

            # Handle markdown code blocks
            if content.startswith("```json"):
                # Extract JSON from markdown code block
                start_idx = content.find("```json") + 7
                end_idx = content.rfind("```")
                if end_idx > start_idx:
                    content = content[start_idx:end_idx].strip()
            elif content.startswith("```"):
                # Handle generic code block
                start_idx = content.find("```") + 3
                end_idx = content.rfind("```")
                if end_idx > start_idx:
                    content = content[start_idx:end_idx].strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse JSON response: {e}\nResponse: {response.content}") from e

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for OpenAI API usage"""
        # OpenAI pricing (as of 2024, subject to change)
        pricing = {
            "gpt-4o": {"prompt": 0.03, "completion": 0.06},  # per 1K tokens
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
        }

        model_key = None
        for key in pricing.keys():
            if key in self.config.model.lower():
                model_key = key
                break

        if model_key is None:
            return 0.0

        # Rough estimate assuming 70% prompt, 30% completion
        prompt_tokens = int(tokens * 0.7)
        completion_tokens = int(tokens * 0.3)

        prompt_cost = (prompt_tokens / 1000) * pricing[model_key]["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing[model_key]["completion"]

        return prompt_cost + completion_cost


# Factory function
def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """
    Factory function to create LLM provider instances.

    Args:
        config: LLM configuration

    Returns:
        LLM provider instance

    Raises:
        ValueError: If provider is not supported
    """
    if config.provider in [LLMProviderType.OPENAI, LLMProviderType.AZURE_OPENAI]:
        return OpenAIProvider(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


# Example usage and testing
async def test_llm_provider():
    """Test function for LLM provider"""
    config = LLMConfig(provider=LLMProviderType.OPENAI, model="gpt-3.5-turbo", api_key="your-api-key-here", temperature=0.7, max_tokens=500)

    provider = create_llm_provider(config)

    messages = [
        LLMMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        LLMMessage(role=MessageRole.USER, content="What is machine learning?"),
    ]

    try:
        response = await provider.generate_response(messages)
        print(f"Response: {response.content}")
        print(f"Tokens used: {response.tokens_used}")
        print(f"Cost estimate: ${response.cost_estimate:.4f}")
    except LLMError as e:
        print(f"LLM Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_llm_provider())
