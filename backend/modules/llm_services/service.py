"""Service layer for LLM operations with DTOs."""

import base64
import contextlib
from datetime import datetime
import logging
from typing import Any, TypeVar
import uuid

from pydantic import BaseModel, ConfigDict, Field

from .config import LLMConfig, create_llm_config_from_env
from .exceptions import LLMAuthenticationError
from .providers.base import LLMProvider, LLMProviderKwargs
from .providers.factory import create_llm_provider
from .repo import LLMRequestRepo
from .types import (
    AudioGenerationRequest,
    ImageGenerationRequest,
    ImageQuality,
    ImageSize,
    LLMProviderType,
    MessageRole,
)
from .types import (
    AudioResponse as AudioResponseInternal,
)
from .types import (
    ImageResponse as ImageResponseInternal,
)
from .types import (
    LLMMessage as LLMMessageInternal,
)
from .types import (
    LLMResponse as LLMResponseInternal,
)
from .types import (
    SearchResult as SearchResultInternal,
)
from .types import (
    WebSearchResponse as WebSearchResponseInternal,
)

# Type variable for structured responses
T = TypeVar("T", bound=BaseModel)

__all__ = [
    "AudioResponse",
    "ImageRequest",
    "ImageResponse",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "LLMService",
    "SearchResult",
    "WebSearchResponse",
]


# Explicit model-to-provider mapping
# If a model is not in this dictionary, it cannot be used.
# To add a new model, simply add it to this dictionary with its provider type.
#
# For Claude models:
#   - Always map to LLMProviderType.ANTHROPIC in this dictionary
#   - The actual provider (Anthropic vs Bedrock) is determined by CLAUDE_PROVIDER env var
#   - CLAUDE_PROVIDER='anthropic' (default) uses direct Anthropic API
#   - CLAUDE_PROVIDER='bedrock' uses AWS Bedrock
MODEL_PROVIDER_MAP: dict[str, LLMProviderType] = {
    # OpenAI GPT models
    "gpt-4o": LLMProviderType.OPENAI,
    "gpt-4o-mini": LLMProviderType.OPENAI,
    "gpt-4-turbo": LLMProviderType.OPENAI,
    "gpt-4": LLMProviderType.OPENAI,
    "gpt-3.5-turbo": LLMProviderType.OPENAI,
    # OpenAI o1 models
    "o1": LLMProviderType.OPENAI,
    "o1-mini": LLMProviderType.OPENAI,
    "o1-preview": LLMProviderType.OPENAI,
    # OpenAI GPT-5 models (when available)
    "gpt-5": LLMProviderType.OPENAI,
    "gpt-5-mini": LLMProviderType.OPENAI,
    # OpenAI TTS (Text-to-Speech) models
    "tts-1": LLMProviderType.OPENAI,
    "tts-1-hd": LLMProviderType.OPENAI,
    "gpt-4o-mini-tts": LLMProviderType.OPENAI,  # Alias for tts-1-hd
    # OpenAI DALL-E (Image Generation) models
    "dall-e-2": LLMProviderType.OPENAI,
    "dall-e-3": LLMProviderType.OPENAI,
    # Claude models (actual provider determined by CLAUDE_PROVIDER env var)
    "claude-opus-4-1": LLMProviderType.ANTHROPIC,
    "claude-sonnet-4-5": LLMProviderType.ANTHROPIC,
    "claude-haiku-4-5": LLMProviderType.ANTHROPIC,
    "claude-3-5-sonnet-20241022": LLMProviderType.ANTHROPIC,
    "claude-3-5-sonnet-20240620": LLMProviderType.ANTHROPIC,
    "claude-3-opus-20240229": LLMProviderType.ANTHROPIC,
    "claude-3-sonnet-20240229": LLMProviderType.ANTHROPIC,
    "claude-3-haiku-20240307": LLMProviderType.ANTHROPIC,
}


# DTOs for external interface
class LLMMessage(BaseModel):
    """DTO for LLM conversation messages."""

    role: str = Field(..., description="Message role (system, user, assistant, function, tool)")
    content: str = Field(..., description="Message content")
    name: str | None = Field(None, description="Optional name for the message")
    function_call: dict[str, Any] | None = Field(None, description="Function call data")
    tool_calls: list[dict[str, Any]] | None = Field(None, description="Tool calls data")

    def to_llm_message(self) -> LLMMessageInternal:
        """Convert to internal LLMMessage type."""
        return LLMMessageInternal(role=MessageRole(self.role), content=self.content, name=self.name, function_call=self.function_call, tool_calls=self.tool_calls)


class LLMResponse(BaseModel):
    """DTO for LLM responses."""

    content: str = Field(..., description="Response content")
    provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Model used")
    tokens_used: int | None = Field(None, description="Total tokens used")
    input_tokens: int | None = Field(None, description="Input tokens used")
    output_tokens: int | None = Field(None, description="Output tokens used")
    cost_estimate: float | None = Field(None, description="Estimated cost in USD")
    response_time_ms: int | None = Field(None, description="Response time in milliseconds")
    cached: bool = Field(False, description="Whether response was cached")
    provider_response_id: str | None = Field(None, description="Provider response id")
    system_fingerprint: str | None = Field(None, description="System fingerprint")
    response_output: dict[str, Any] | list[dict[str, Any]] | None = Field(None, description="Responses API output structure")
    response_created_at: datetime | None = Field(None, description="Provider response created timestamp")

    @classmethod
    def from_llm_response(cls, response: LLMResponseInternal) -> "LLMResponse":
        """Create DTO from internal LLMResponse."""
        return cls(
            content=response.content,
            provider=response.provider.value if hasattr(response.provider, "value") else response.provider,
            model=response.model,
            tokens_used=response.tokens_used,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_estimate=response.cost_estimate,
            response_time_ms=response.response_time_ms,
            cached=response.cached,
            provider_response_id=response.provider_response_id,
            system_fingerprint=response.system_fingerprint,
            response_output=response.response_output,
            response_created_at=response.response_created_at,
        )


class LLMRequest(BaseModel):
    """DTO for LLM request records."""

    id: uuid.UUID = Field(..., description="Request ID")
    user_id: int | None = Field(None, description="User ID")
    api_variant: str = Field(..., description="API variant used (e.g., responses)")
    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Model used")
    provider_response_id: str | None = Field(None, description="Provider response id")
    system_fingerprint: str | None = Field(None, description="System fingerprint")
    temperature: float = Field(..., description="Temperature setting")
    max_output_tokens: int | None = Field(None, description="Max output tokens setting")
    messages: list[dict[str, Any]] = Field(..., description="Request messages")
    additional_params: dict[str, Any] | None = Field(None, description="Additional parameters")
    request_payload: dict[str, Any] | None = Field(None, description="Final provider request payload")
    response_content: str | None = Field(None, description="Response content")
    response_raw: dict[str, Any] | None = Field(None, description="Raw response data")
    tokens_used: int | None = Field(None, description="Tokens used")
    input_tokens: int | None = Field(None, description="Input tokens")
    output_tokens: int | None = Field(None, description="Output tokens")
    cost_estimate: float | None = Field(None, description="Cost estimate")
    status: str = Field(..., description="Request status")
    execution_time_ms: int | None = Field(None, description="Execution time")
    error_message: str | None = Field(None, description="Error message if failed")
    error_type: str | None = Field(None, description="Error type")
    retry_attempt: int = Field(1, description="Retry attempt number")
    cached: bool = Field(False, description="Whether cached")
    response_created_at: datetime | None = Field(None, description="Provider response created timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class AudioResponse(BaseModel):
    """DTO for audio synthesis responses."""

    audio_base64: str = Field(..., description="Base64-encoded audio payload")
    mime_type: str = Field(..., description="MIME type of the synthesized audio")
    voice: str | None = Field(None, description="Voice used for narration")
    model: str | None = Field(None, description="Model that produced the audio")
    cost_estimate: float | None = Field(None, description="Estimated cost in USD")
    duration_seconds: float | None = Field(None, description="Estimated duration in seconds")

    def audio_bytes(self) -> bytes:
        """Decode the base64 payload into raw audio bytes."""

        return base64.b64decode(self.audio_base64)

    @classmethod
    def from_audio_response(cls, response: AudioResponseInternal) -> "AudioResponse":
        """Create DTO from internal audio response."""

        return cls(
            audio_base64=response.audio_base64,
            mime_type=response.mime_type,
            voice=response.voice,
            model=response.model,
            cost_estimate=response.cost_estimate,
            duration_seconds=response.duration_seconds,
        )


class ImageRequest(BaseModel):
    """DTO for image generation requests."""

    prompt: str = Field(..., description="Image generation prompt")
    size: str = Field("1024x1024", description="Image size")
    quality: str = Field("standard", description="Image quality")
    style: str | None = Field(None, description="Image style")


class ImageResponse(BaseModel):
    """DTO for image generation responses."""

    image_url: str = Field(..., description="Generated image URL")
    revised_prompt: str | None = Field(None, description="Revised prompt")
    size: str | None = Field(None, description="Image size")
    cost_estimate: float | None = Field(None, description="Cost estimate")

    @classmethod
    def from_image_response(cls, response: ImageResponseInternal) -> "ImageResponse":
        """Create DTO from internal ImageResponse."""
        return cls(image_url=response.image_url, revised_prompt=response.revised_prompt, size=response.size, cost_estimate=response.cost_estimate)


class SearchResult(BaseModel):
    """DTO for search results."""

    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    snippet: str = Field(..., description="Result snippet")
    published_date: datetime | None = Field(None, description="Published date")
    source: str | None = Field(None, description="Source")

    @classmethod
    def from_search_result(cls, result: SearchResultInternal) -> "SearchResult":
        """Create DTO from internal SearchResult."""
        return cls(title=result.title, url=result.url, snippet=result.snippet, published_date=result.published_date, source=result.source)


class WebSearchResponse(BaseModel):
    """DTO for web search responses."""

    query: str = Field(..., description="Search query")
    results: list[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total results count")
    search_time_ms: int | None = Field(None, description="Search time in milliseconds")

    @classmethod
    def from_web_search_response(cls, response: WebSearchResponseInternal) -> "WebSearchResponse":
        """Create DTO from internal WebSearchResponse."""
        return cls(query=response.query, results=[SearchResult.from_search_result(r) for r in response.results], total_results=response.total_results, search_time_ms=response.search_time_ms)


class LLMService:
    """Service layer for LLM operations."""

    def __init__(self, repo: LLMRequestRepo) -> None:
        self.repo = repo
        self.provider: LLMProvider | None = None
        self._provider_cache: dict[LLMProviderType, LLMProvider] = {}
        self._provider_configs: dict[LLMProviderType, LLMConfig] = {}
        self._default_provider_type: LLMProviderType | None = None
        self._logger = logging.getLogger(__name__)
        # Initialize default LLM provider
        try:
            default_config = create_llm_config_from_env()
            self._default_provider_type = default_config.provider
            self._provider_configs[default_config.provider] = default_config
            self._logger.info(f"Initializing default LLM provider: {default_config.provider.value} (model: {default_config.model})")
            provider_instance = create_llm_provider(default_config, repo.s)
            self._provider_cache[default_config.provider] = provider_instance
            self.provider = provider_instance
            self._logger.info(f"✓ Successfully initialized {default_config.provider.value} provider")
        except Exception as e:
            self._logger.warning(f"Failed to initialize LLM provider: {e}")
            self.provider = None
            self._default_provider_type = None

    def _ensure_provider(self, provider_type: LLMProviderType) -> LLMProvider:
        if provider_type in self._provider_cache:
            self._logger.debug(f"Using cached {provider_type.value} provider")
            return self._provider_cache[provider_type]

        self._logger.info(f"Initializing {provider_type.value} provider on-demand")
        config = self._provider_configs.get(provider_type)
        if config is None:
            try:
                config = create_llm_config_from_env(provider_override=provider_type)
            except Exception as exc:
                self._logger.debug(f"Failed to configure {provider_type.value}: {exc}")
                raise RuntimeError(f"Provider {provider_type.value} is not configured") from exc
            self._provider_configs[provider_type] = config

        provider = create_llm_provider(config, self.repo.s)
        self._provider_cache[provider_type] = provider
        if self.provider is None and provider_type == self._default_provider_type:
            self.provider = provider
        self._logger.info(f"✓ Successfully initialized {provider_type.value} provider")
        return provider

    def _select_provider(self, model: str | None) -> LLMProvider:
        """
        Select the appropriate provider based on the model name.

        Uses MODEL_PROVIDER_MAP to explicitly map models to providers.
        If a model is not in the map, an exception is raised.
        NO FALLBACKS: If the required provider isn't configured, fail explicitly.
        """
        if not model:
            if self._default_provider_type is None:
                raise RuntimeError("No model specified and no default provider initialized")
            self._logger.debug(f"No model specified, using default provider: {self._default_provider_type.value}")
            return self._ensure_provider(self._default_provider_type)

        # Check if model is in the explicit model map
        if model not in MODEL_PROVIDER_MAP:
            available_models = ", ".join(sorted(MODEL_PROVIDER_MAP.keys()))
            raise ValueError(f"Model '{model}' is not supported. Supported models: {available_models}")

        # Get the base provider type for this model
        base_provider_type = MODEL_PROVIDER_MAP[model]

        # For Claude models, check CLAUDE_PROVIDER setting to determine actual provider
        if base_provider_type == LLMProviderType.ANTHROPIC:
            # Check CLAUDE_PROVIDER setting
            claude_provider = None
            for config in self._provider_configs.values():
                if hasattr(config, "claude_provider") and config.claude_provider:
                    claude_provider = config.claude_provider
                    break

            # Default to anthropic if not specified
            if claude_provider is None:
                claude_provider = "anthropic"

            if claude_provider == "bedrock":
                provider_type = LLMProviderType.BEDROCK
                self._logger.debug(f"Model '{model}' will use Bedrock (CLAUDE_PROVIDER=bedrock)")
            elif claude_provider == "anthropic":
                provider_type = LLMProviderType.ANTHROPIC
                self._logger.debug(f"Model '{model}' will use Anthropic (CLAUDE_PROVIDER=anthropic)")
            else:
                raise ValueError(f"Invalid CLAUDE_PROVIDER value: '{claude_provider}'. Must be 'anthropic' or 'bedrock'")
        else:
            provider_type = base_provider_type

        # Initialize and return the provider
        try:
            provider = self._ensure_provider(provider_type)
            self._logger.info(f"Using {provider_type.value} provider for model: {model}")
            return provider
        except (RuntimeError, LLMAuthenticationError) as e:
            # Provide helpful error messages based on provider type
            if provider_type == LLMProviderType.OPENAI:
                raise RuntimeError(f"Model '{model}' requires OpenAI provider, but it's not configured. Please set OPENAI_API_KEY environment variable.") from e
            elif provider_type == LLMProviderType.ANTHROPIC:
                raise RuntimeError(f"Model '{model}' requires Anthropic provider (CLAUDE_PROVIDER=anthropic), but it's not configured. Please set ANTHROPIC_API_KEY environment variable or change CLAUDE_PROVIDER to 'bedrock'.") from e
            elif provider_type == LLMProviderType.BEDROCK:
                raise RuntimeError(f"Model '{model}' requires Bedrock provider (CLAUDE_PROVIDER=bedrock), but it's not configured. Please set AWS credentials or change CLAUDE_PROVIDER to 'anthropic'.") from e
            elif provider_type == LLMProviderType.AZURE_OPENAI:
                raise RuntimeError(f"Model '{model}' requires Azure OpenAI provider, but it's not configured. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables.") from e
            else:
                raise RuntimeError(f"Model '{model}' requires {provider_type.value} provider, but it's not configured.") from e

    def _ensure_request_user(self, request_id: uuid.UUID, user_id: int | None) -> None:
        """Persist the user association for the given LLM request when provided."""

        if user_id is None:
            return

        with contextlib.suppress(Exception):
            self.repo.assign_user(request_id, user_id)

    async def generate_response(
        self, messages: list[LLMMessage], user_id: int | None = None, model: str | None = None, temperature: float | None = None, max_output_tokens: int | None = None, **kwargs: LLMProviderKwargs
    ) -> tuple[LLMResponse, uuid.UUID]:
        """
        Generate a text response from the LLM.
        """
        provider = self._select_provider(model)

        # Convert DTOs to internal types
        internal_messages = [msg.to_llm_message() for msg in messages]

        # Call provider
        internal_response, request_id = await provider.generate_response(messages=internal_messages, user_id=user_id, model=model, temperature=temperature, max_output_tokens=max_output_tokens, **kwargs)  # type: ignore[arg-type]

        # Convert back to DTO
        response_dto = LLMResponse.from_llm_response(internal_response)
        self._ensure_request_user(request_id, user_id)
        return response_dto, request_id

    async def generate_structured_response(
        self, messages: list[LLMMessage], response_model: type[T], user_id: int | None = None, model: str | None = None, temperature: float | None = None, max_output_tokens: int | None = None, **kwargs: LLMProviderKwargs
    ) -> tuple[T, uuid.UUID, dict[str, Any]]:
        """
        Generate a structured response using a Pydantic model.

        Returns:
            Tuple of (structured_object, request_id, usage_info)
        """
        provider = self._select_provider(model)

        # Convert DTOs to internal types
        internal_messages = [msg.to_llm_message() for msg in messages]

        # Call provider
        provider_kwargs: dict[str, Any] = {}
        if model is not None:
            provider_kwargs["model"] = model
        if temperature is not None:
            provider_kwargs["temperature"] = temperature
        if max_output_tokens is not None:
            provider_kwargs["max_output_tokens"] = max_output_tokens
        structured_obj, request_id, usage_info = await provider.generate_structured_object(messages=internal_messages, response_model=response_model, user_id=user_id, **provider_kwargs, **kwargs)

        self._ensure_request_user(request_id, user_id)
        return structured_obj, request_id, usage_info

    async def generate_audio(
        self,
        text: str,
        voice: str,
        user_id: int | None = None,
        model: str | None = None,
        audio_format: str = "mp3",
        speed: float | None = None,
        **kwargs: LLMProviderKwargs,
    ) -> tuple[AudioResponse, uuid.UUID]:
        """Synthesize narrated audio from text."""

        provider = self._select_provider(model)

        resolved_model = model or getattr(provider.config, "audio_model", None) or provider.config.model

        request = AudioGenerationRequest(
            text=text,
            voice=voice,
            model=resolved_model,
            audio_format=audio_format,
            speed=speed,
        )

        internal_response, request_id = await provider.generate_audio(
            request=request,
            user_id=user_id,
            **kwargs,
        )

        response_dto = AudioResponse.from_audio_response(internal_response)
        self._ensure_request_user(request_id, user_id)
        return response_dto, request_id

    async def generate_image(self, prompt: str, user_id: int | None = None, size: str = "1024x1024", quality: str = "standard", style: str | None = None, **kwargs: LLMProviderKwargs) -> tuple[ImageResponse, uuid.UUID]:
        """
        Generate an image from a text prompt.
        """
        provider = self._select_provider(None)

        # Create image request
        # Convert string parameters to enums
        image_size = ImageSize(size) if size in [s.value for s in ImageSize] else ImageSize.LARGE
        image_quality = ImageQuality(quality) if quality in [q.value for q in ImageQuality] else ImageQuality.STANDARD

        request = ImageGenerationRequest(prompt=prompt, size=image_size, quality=image_quality, style=style)

        # Call provider
        internal_response, request_id = await provider.generate_image(request=request, user_id=user_id, **kwargs)

        # Convert to DTO
        response_dto = ImageResponse.from_image_response(internal_response)
        self._ensure_request_user(request_id, user_id)
        return response_dto, request_id

    async def search_web(self, queries: list[str], user_id: int | None = None, max_results: int = 10, **kwargs: LLMProviderKwargs) -> tuple[WebSearchResponse, uuid.UUID]:
        """
        Search the web for recent information.
        """
        provider = self._select_provider(None)

        # Call provider (this will raise NotImplementedError for OpenAI)
        internal_response, request_id = await provider.search_recent_news(search_queries=queries, user_id=user_id, max_results=max_results, **kwargs)  # type: ignore[arg-type]

        # Convert to DTO
        response_dto = WebSearchResponse.from_web_search_response(internal_response)
        self._ensure_request_user(request_id, user_id)
        return response_dto, request_id

    def get_request(self, request_id: uuid.UUID) -> LLMRequest | None:
        """Retrieve details of a previous LLM request."""
        request = self.repo.by_id(request_id)
        return LLMRequest.model_validate(request) if request else None

    def get_user_requests(self, user_id: int, limit: int = 50, offset: int = 0) -> list[LLMRequest]:
        """Get recent requests for a specific user."""
        requests = self.repo.by_user_id(user_id, limit, offset)
        return [LLMRequest.model_validate(req) for req in requests]

    def estimate_cost(self, messages: list[LLMMessage], model: str | None = None) -> float:
        """
        Estimate the cost of a request before making it.
        """
        try:
            provider = self._select_provider(model)
        except RuntimeError:
            return 0.0

        # Rough token estimation (this is approximate)
        # In production, you might want to use tiktoken or similar
        total_chars = sum(len(msg.content) for msg in messages)
        estimated_tokens = total_chars // 4  # Rough approximation

        return provider.estimate_cost(
            prompt_tokens=estimated_tokens,
            completion_tokens=estimated_tokens // 4,  # Estimate output tokens
            model=model,
        )

    def get_request_count_by_user(self, user_id: int) -> int:
        """Get total request count for a user."""
        return self.repo.count_by_user(user_id)

    def get_request_count_by_status(self, status: str) -> int:
        """Get request count by status."""
        return self.repo.count_by_status(status)

    def get_recent_requests(self, limit: int = 50, offset: int = 0) -> list[LLMRequest]:
        """Get recent LLM requests with pagination. FOR ADMIN USE ONLY."""
        requests = self.repo.get_recent(limit, offset)
        return [LLMRequest.model_validate(req) for req in requests]

    def count_all_requests(self) -> int:
        """Get total count of LLM requests. FOR ADMIN USE ONLY."""
        return self.repo.count_all()
