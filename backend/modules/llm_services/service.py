"""Service layer for LLM operations with DTOs."""

from datetime import datetime
from typing import Any, TypeVar
import uuid

from pydantic import BaseModel, Field

from .config import create_llm_config_from_env
from .providers.factory import create_llm_provider
from .repo import LLMRequestRepo
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
    MessageRole,
)
from .types import (
    SearchResult as SearchResultInternal,
)
from .types import (
    WebSearchResponse as WebSearchResponseInternal,
)

# Type variable for structured responses
T = TypeVar("T", bound=BaseModel)

__all__ = ["ImageRequest", "ImageResponse", "LLMMessage", "LLMRequest", "LLMResponse", "LLMService", "SearchResult", "WebSearchResponse"]


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
    prompt_tokens: int | None = Field(None, description="Prompt tokens used")
    completion_tokens: int | None = Field(None, description="Completion tokens used")
    cost_estimate: float | None = Field(None, description="Estimated cost in USD")
    finish_reason: str | None = Field(None, description="Reason for completion")
    response_time_ms: int | None = Field(None, description="Response time in milliseconds")
    cached: bool = Field(False, description="Whether response was cached")

    @classmethod
    def from_llm_response(cls, response: LLMResponseInternal) -> "LLMResponse":
        """Create DTO from internal LLMResponse."""
        return cls(
            content=response.content,
            provider=response.provider.value,
            model=response.model,
            tokens_used=response.tokens_used,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            cost_estimate=response.cost_estimate,
            finish_reason=response.finish_reason,
            response_time_ms=response.response_time_ms,
            cached=response.cached,
        )


class LLMRequest(BaseModel):
    """DTO for LLM request records."""

    id: uuid.UUID = Field(..., description="Request ID")
    user_id: uuid.UUID | None = Field(None, description="User ID")
    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Model used")
    temperature: float = Field(..., description="Temperature setting")
    max_tokens: int = Field(..., description="Max tokens setting")
    messages: dict[str, Any] = Field(..., description="Request messages")
    additional_params: dict[str, Any] | None = Field(None, description="Additional parameters")
    response_content: str | None = Field(None, description="Response content")
    response_raw: dict[str, Any] | None = Field(None, description="Raw response data")
    tokens_used: int | None = Field(None, description="Tokens used")
    prompt_tokens: int | None = Field(None, description="Prompt tokens")
    completion_tokens: int | None = Field(None, description="Completion tokens")
    cost_estimate: float | None = Field(None, description="Cost estimate")
    finish_reason: str | None = Field(None, description="Finish reason")
    status: str = Field(..., description="Request status")
    execution_time_ms: int | None = Field(None, description="Execution time")
    error_message: str | None = Field(None, description="Error message if failed")
    error_type: str | None = Field(None, description="Error type")
    retry_attempt: int = Field(1, description="Retry attempt number")
    cached: bool = Field(False, description="Whether cached")
    context_data: dict[str, Any] | None = Field(None, description="Context data")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


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
        # Initialize LLM provider
        try:
            config = create_llm_config_from_env()
            self.provider = create_llm_provider(config, repo.s)
        except Exception as e:
            # Log error but don't fail initialization
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize LLM provider: {e}")
            self.provider = None

    async def generate_response(self, messages: list[LLMMessage], user_id: uuid.UUID | None = None, model: str | None = None, temperature: float | None = None, max_tokens: int | None = None, **kwargs: Any) -> tuple[LLMResponse, uuid.UUID]:
        """
        Generate a text response from the LLM.
        """
        if not self.provider:
            raise RuntimeError("LLM provider not initialized")

        # Convert DTOs to internal types
        internal_messages = [msg.to_llm_message() for msg in messages]

        # Call provider
        internal_response, request_id = await self.provider.generate_response(messages=internal_messages, user_id=user_id, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs)

        # Convert back to DTO
        response_dto = LLMResponse.from_llm_response(internal_response)
        return response_dto, request_id

    async def generate_structured_response(
        self, messages: list[LLMMessage], response_model: type[T], user_id: uuid.UUID | None = None, model: str | None = None, temperature: float | None = None, max_tokens: int | None = None, **kwargs: Any
    ) -> tuple[T, uuid.UUID]:
        """
        Generate a structured response using a Pydantic model.
        """
        if not self.provider:
            raise RuntimeError("LLM provider not initialized")

        # Convert DTOs to internal types
        internal_messages = [msg.to_llm_message() for msg in messages]

        # Call provider
        structured_obj, request_id = await self.provider.generate_structured_object(messages=internal_messages, response_model=response_model, user_id=user_id, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs)

        return structured_obj, request_id

    async def generate_image(self, prompt: str, user_id: uuid.UUID | None = None, size: str = "1024x1024", quality: str = "standard", style: str | None = None, **kwargs: Any) -> tuple[ImageResponse, uuid.UUID]:
        """
        Generate an image from a text prompt.
        """
        if not self.provider:
            raise RuntimeError("LLM provider not initialized")

        # Create image request
        from .types import ImageGenerationRequest, ImageQuality, ImageSize

        # Convert string parameters to enums
        image_size = ImageSize(size) if size in [s.value for s in ImageSize] else ImageSize.LARGE
        image_quality = ImageQuality(quality) if quality in [q.value for q in ImageQuality] else ImageQuality.STANDARD

        request = ImageGenerationRequest(prompt=prompt, size=image_size, quality=image_quality, style=style)

        # Call provider
        internal_response, request_id = await self.provider.generate_image(request=request, user_id=user_id, **kwargs)

        # Convert to DTO
        response_dto = ImageResponse.from_image_response(internal_response)
        return response_dto, request_id

    async def search_web(self, queries: list[str], user_id: uuid.UUID | None = None, max_results: int = 10, **kwargs: Any) -> tuple[WebSearchResponse, uuid.UUID]:
        """
        Search the web for recent information.
        """
        if not self.provider:
            raise RuntimeError("LLM provider not initialized")

        # Call provider (this will raise NotImplementedError for OpenAI)
        internal_response, request_id = await self.provider.search_recent_news(search_queries=queries, user_id=user_id, max_results=max_results, **kwargs)

        # Convert to DTO
        response_dto = WebSearchResponse.from_web_search_response(internal_response)
        return response_dto, request_id

    def get_request(self, request_id: uuid.UUID) -> LLMRequest | None:
        """Retrieve details of a previous LLM request."""
        request = self.repo.by_id(request_id)
        return LLMRequest.model_validate(request) if request else None

    def get_user_requests(self, user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> list[LLMRequest]:
        """Get recent requests for a specific user."""
        requests = self.repo.by_user_id(user_id, limit, offset)
        return [LLMRequest.model_validate(req) for req in requests]

    def estimate_cost(self, messages: list[LLMMessage], model: str | None = None) -> float:
        """
        Estimate the cost of a request before making it.
        """
        if not self.provider:
            return 0.0

        # Rough token estimation (this is approximate)
        # In production, you might want to use tiktoken or similar
        total_chars = sum(len(msg.content) for msg in messages)
        estimated_tokens = total_chars // 4  # Rough approximation

        return self.provider.estimate_cost(
            prompt_tokens=estimated_tokens,
            completion_tokens=estimated_tokens // 4,  # Estimate completion tokens
            model=model,
        )

    def get_request_count_by_user(self, user_id: uuid.UUID) -> int:
        """Get total request count for a user."""
        return self.repo.count_by_user(user_id)

    def get_request_count_by_status(self, status: str) -> int:
        """Get request count by status."""
        return self.repo.count_by_status(status)
