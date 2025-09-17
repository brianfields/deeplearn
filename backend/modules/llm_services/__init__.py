"""LLM Services Module.

This module provides LLM functionality following the simplified modular architecture.
It includes support for multiple LLM providers, request tracking, and structured outputs.
"""

from .exceptions import (
    LLMAuthenticationError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from .public import (
    ImageResponse,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    LLMServicesProvider,
    WebSearchResponse,
    llm_services_provider,
)

__all__ = [
    # Core DTOs
    "ImageResponse",
    "LLMAuthenticationError",
    # Exceptions
    "LLMError",
    "LLMMessage",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMRequest",
    "LLMResponse",
    # Service Interface
    "LLMServicesProvider",
    "LLMTimeoutError",
    "LLMValidationError",
    "WebSearchResponse",
    "llm_services_provider",
]
