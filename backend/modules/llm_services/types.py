"""Core types and data structures for LLM and image generation."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Literal

__all__ = [
    "AudioGenerationRequest",
    "AudioResponse",
    "ImageGenerationRequest",
    "ImageQuality",
    "ImageResponse",
    "ImageSize",
    "LLMMessage",
    "LLMProviderType",
    "LLMRequestMode",
    "LLMResponse",
    "MessageRole",
    "SearchResult",
    "WebSearchConfig",
    "WebSearchResponse",
]


class LLMProviderType(str, Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    BEDROCK = "bedrock"
    GEMINI = "gemini"


class LLMRequestMode(str, Enum):
    """Request modes for LLM providers"""

    CHAT = "chat"
    COMPLETION = "completion"
    STRUCTURED = "structured"
    IMAGE = "image"
    SEARCH = "search"


class MessageRole(str, Enum):
    """Message roles in LLM conversations"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


LLMMessageContent = str | list[dict[str, Any]]


@dataclass
class LLMMessage:
    """A message in an LLM conversation"""

    role: MessageRole
    content: LLMMessageContent
    name: str | None = None
    function_call: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for API calls"""
        result: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }

        if self.name:
            result["name"] = self.name
        if self.function_call:
            result["function_call"] = self.function_call
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls

        return result


@dataclass
class LLMResponse:
    """Response from an LLM provider"""

    content: str
    provider: LLMProviderType
    model: str
    tokens_used: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_estimate: float | None = None
    response_time_ms: int | None = None
    cached: bool = False
    provider_response_id: str | None = None
    system_fingerprint: str | None = None
    response_output: dict[str, Any] | list[dict[str, Any]] | None = None
    response_created_at: datetime | None = None
    finish_reason: str | None = None
    cached_input_tokens: int | None = None  # Gemini: tokens from cache (prompt caching)
    cache_creation_tokens: int | None = None  # Gemini: tokens used to create cache entry

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "content": self.content,
            "provider": self.provider.value if hasattr(self.provider, "value") else self.provider,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_estimate": self.cost_estimate,
            "response_time_ms": self.response_time_ms,
            "cached": self.cached,
            "provider_response_id": self.provider_response_id,
            "system_fingerprint": self.system_fingerprint,
            "response_output": self.response_output,
            "response_created_at": self.response_created_at.isoformat() if self.response_created_at else None,
            "finish_reason": self.finish_reason,
            "cached_input_tokens": self.cached_input_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
        }


@dataclass
class AudioGenerationRequest:
    """Request payload for audio synthesis operations."""

    text: str
    voice: str
    model: str
    audio_format: str = "mp3"
    speed: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert request to a serialisable dictionary."""
        payload: dict[str, Any] = {
            "text": self.text,
            "voice": self.voice,
            "model": self.model,
            "audio_format": self.audio_format,
        }
        if self.speed is not None:
            payload["speed"] = self.speed
        return payload


@dataclass
class AudioResponse:
    """Response payload for synthesized audio."""

    audio_base64: str
    mime_type: str
    voice: str | None = None
    model: str | None = None
    cost_estimate: float | None = None
    duration_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert response to a serialisable dictionary."""
        return {
            "audio_base64": self.audio_base64,
            "mime_type": self.mime_type,
            "voice": self.voice,
            "model": self.model,
            "cost_estimate": self.cost_estimate,
            "duration_seconds": self.duration_seconds,
        }

    @property
    def audio_bytes(self) -> bytes:
        """Decode the base64 audio payload into raw bytes."""
        return base64.b64decode(self.audio_base64)


class ImageSize(str, Enum):
    """Supported image sizes"""

    SMALL = "256x256"
    MEDIUM = "512x512"
    LARGE = "1024x1024"
    HD = "1792x1024"
    SQUARE_HD = "1024x1792"


class ImageQuality(str, Enum):
    """Image quality settings"""

    STANDARD = "standard"
    HD = "hd"


@dataclass
class ImageGenerationRequest:
    """Request for image generation"""

    prompt: str
    size: ImageSize = ImageSize.LARGE
    quality: ImageQuality = ImageQuality.STANDARD
    n: int = 1
    style: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for API calls"""
        result = {
            "prompt": self.prompt,
            "size": self.size.value,
            "quality": self.quality.value,
            "n": self.n,
        }

        if self.style:
            result["style"] = self.style

        return result


@dataclass
class ImageResponse:
    """Response from image generation"""

    image_url: str
    revised_prompt: str | None = None
    size: str | None = None
    cost_estimate: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "image_url": self.image_url,
            "revised_prompt": self.revised_prompt,
            "size": self.size,
            "cost_estimate": self.cost_estimate,
        }


@dataclass
class SearchResult:
    """Individual search result"""

    title: str
    url: str
    snippet: str
    published_date: datetime | None = None
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "source": self.source,
        }


@dataclass
class WebSearchConfig:
    """Configuration for web search"""

    enabled: bool = True
    max_results: int = 10
    context_size: Literal["low", "medium", "high"] = "medium"
    include_images: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "enabled": self.enabled,
            "max_results": self.max_results,
            "context_size": self.context_size,
            "include_images": self.include_images,
        }


@dataclass
class WebSearchResponse:
    """Response from web search"""

    query: str
    results: list[SearchResult]
    total_results: int
    search_time_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "query": self.query,
            "results": [result.to_dict() for result in self.results],
            "total_results": self.total_results,
            "search_time_ms": self.search_time_ms,
        }
