"""
Domain entities for LLM providers.

This module contains the business logic and domain rules for LLM providers,
separate from infrastructure implementation details.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


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
    """Domain representation of an LLM message"""

    role: MessageRole
    content: str
    timestamp: datetime | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class LLMResponse:
    """Domain representation of an LLM response"""

    content: str
    provider: LLMProviderType
    model: str
    tokens_used: int
    cost_estimate: float | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def is_complete(self) -> bool:
        """Check if the response is complete (not truncated)"""
        return self.finish_reason != "length"

    def calculate_cost_per_token(self) -> float:
        """Calculate cost per token if cost estimate is available"""
        if self.cost_estimate and self.tokens_used > 0:
            return self.cost_estimate / self.tokens_used
        return 0.0


class LLMConfig(BaseModel):
    """Configuration for LLM providers"""

    provider: LLMProviderType
    model: str = "gpt-4o"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=16384, gt=0)
    timeout: int = Field(default=180, gt=0)
    max_retries: int = Field(default=3, ge=0)

    def is_valid_for_provider(self) -> bool:
        """Validate configuration for the specified provider"""
        if self.provider in [LLMProviderType.OPENAI, LLMProviderType.AZURE_OPENAI]:
            return self.api_key is not None
        return True

    def get_estimated_cost_per_token(self) -> float:
        """Get estimated cost per token for this configuration"""
        # OpenAI pricing (approximate, should be updated regularly)
        pricing = {
            "gpt-4o": 0.00003,  # $0.03 per 1K tokens average
            "gpt-3.5-turbo": 0.000002,  # $0.002 per 1K tokens average
        }

        for model_key, cost in pricing.items():
            if model_key in self.model.lower():
                return cost
        return 0.0


class LLMProvider(ABC):
    """
    Abstract domain entity for LLM providers.

    This defines the business interface for LLM operations without
    implementation details.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate the provider configuration"""
        if not self.config.is_valid_for_provider():
            raise ValueError(f"Invalid configuration for provider {self.config.provider}")

    @abstractmethod
    async def generate_response(
        self,
        messages: list[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a text response from the LLM"""
        pass

    @abstractmethod
    async def generate_structured_response(
        self,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a structured JSON response from the LLM"""
        pass

    @abstractmethod
    async def generate_structured_object(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        **kwargs: Any,
    ) -> T:
        """Generate a structured response using Pydantic models"""
        pass

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Simple approximation: ~1.3 tokens per word
        return int(len(text.split()) * 1.3)

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for token usage"""
        cost_per_token = self.config.get_estimated_cost_per_token()
        return tokens * cost_per_token


# Domain exceptions
class LLMDomainError(Exception):
    """Base exception for LLM domain errors"""

    pass


class InvalidPromptError(LLMDomainError):
    """Raised when a prompt violates business rules"""

    pass


class TokenLimitExceededError(LLMDomainError):
    """Raised when token limit is exceeded"""

    pass


class UnsupportedProviderError(LLMDomainError):
    """Raised when an unsupported provider is requested"""

    pass


# Domain policies
class LLMUsagePolicy:
    """Business rules for LLM usage"""

    MAX_TOKENS_PER_REQUEST = 32000
    MAX_MESSAGES_PER_CONVERSATION = 50
    MIN_TEMPERATURE = 0.0
    MAX_TEMPERATURE = 2.0

    @classmethod
    def validate_messages(cls, messages: list[LLMMessage]) -> None:
        """Validate messages according to business rules"""
        if len(messages) > cls.MAX_MESSAGES_PER_CONVERSATION:
            raise InvalidPromptError(f"Too many messages: {len(messages)} > {cls.MAX_MESSAGES_PER_CONVERSATION}")

        if not messages:
            raise InvalidPromptError("At least one message is required")

        # Check for empty messages
        for i, message in enumerate(messages):
            if not message.content.strip():
                raise InvalidPromptError(f"Message {i} is empty")

    @classmethod
    def validate_config(cls, config: LLMConfig) -> None:
        """Validate LLM configuration according to business rules"""
        if config.max_tokens > cls.MAX_TOKENS_PER_REQUEST:
            raise InvalidPromptError(f"Max tokens {config.max_tokens} exceeds limit {cls.MAX_TOKENS_PER_REQUEST}")

        if not (cls.MIN_TEMPERATURE <= config.temperature <= cls.MAX_TEMPERATURE):
            raise InvalidPromptError(f"Temperature {config.temperature} outside valid range [{cls.MIN_TEMPERATURE}, {cls.MAX_TEMPERATURE}]")

    @classmethod
    def should_cache_response(cls, messages: list[LLMMessage], response: LLMResponse) -> bool:
        """Determine if a response should be cached based on business rules"""
        # Don't cache very short responses (likely errors)
        if len(response.content) < 10:
            return False

        # Don't cache incomplete responses
        if not response.is_complete():
            return False

        # Don't cache responses with high temperature (more random)
        if len(messages) > 0 and hasattr(messages[0], "metadata"):
            temperature = messages[0].metadata.get("temperature", 0.7) if messages[0].metadata else 0.7
            if temperature > 1.0:
                return False

        return True
