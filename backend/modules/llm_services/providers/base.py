"""Abstract base classes and common functionality for LLM providers."""

from abc import ABC, abstractmethod
import contextlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, TypeVar
import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import LLMConfig
from ..models import LLMRequestModel
from ..types import (
    ImageGenerationRequest,
    ImageResponse,
    LLMMessage,
    LLMResponse,
    WebSearchResponse,
)

# Type alias for LLM provider kwargs
LLMProviderKwargs = dict[str, Any]

if TYPE_CHECKING:
    from ..models import LLMRequestModel

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)

__all__ = ["LLMProvider"]


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    This class defines the interface that all LLM providers must implement
    and provides common database logging functionality.
    """

    def __init__(self, config: LLMConfig, db_session: Session) -> None:
        """Initialize the LLM provider with configuration and database session."""
        self.config = config
        self.db_session = db_session

    def _create_llm_request(
        self,
        messages: list[LLMMessage],
        user_id: uuid.UUID | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        **_kwargs: LLMProviderKwargs,
    ) -> "LLMRequestModel":
        """
        Create a database record for an LLM request.

        Args:
            messages: List of messages in the conversation
            user_id: Optional user identifier
            model: Override model (optional)
            temperature: Override temperature (optional)
            max_output_tokens: Override max tokens (optional)
            **kwargs: Additional parameters

        Returns:
            LLMRequestModel database record
        """

        # Use provided values or fall back to config
        request_model = model or self.config.model
        request_temperature = temperature if temperature is not None else self.config.temperature
        request_max_output_tokens = max_output_tokens if max_output_tokens is not None else self.config.max_output_tokens

        # Convert messages to JSON-serializable format
        messages_payload: list[dict[str, Any]] = []
        for m in messages:
            if hasattr(m, "model_dump"):
                messages_payload.append(m.model_dump())
            elif hasattr(m, "dict"):
                # Pydantic v1 compatibility
                messages_payload.append(m.dict())
            elif hasattr(m, "to_dict"):
                messages_payload.append(m.to_dict())
            else:
                # Fallback: try to build a dict from attributes
                payload: dict[str, Any] = {}
                for attr in ("role", "content", "name", "function_call", "tool_calls"):
                    if hasattr(m, attr):
                        value = getattr(m, attr)
                        # If role is an Enum, convert to value
                        if attr == "role" and hasattr(value, "value"):
                            value = value.value
                        payload[attr] = value
                messages_payload.append(payload)

        llm_request = LLMRequestModel(
            user_id=user_id,
            provider=self.config.provider.value,
            model=request_model,
            temperature=request_temperature,
            max_output_tokens=request_max_output_tokens,
            messages=messages_payload,
            created_at=datetime.now(UTC),
        )

        self.db_session.add(llm_request)
        with contextlib.suppress(Exception):
            self.db_session.flush()

        return llm_request

    def _update_llm_request_success(
        self,
        llm_request: "LLMRequestModel",
        response: LLMResponse,
        execution_time_ms: int,
    ) -> None:
        """Update LLMRequest record with successful response data."""
        llm_request.response_content = response.content
        llm_request.response_raw = response.to_dict()
        llm_request.tokens_used = response.tokens_used
        llm_request.input_tokens = response.input_tokens
        llm_request.output_tokens = response.output_tokens
        llm_request.cost_estimate = response.cost_estimate
        llm_request.execution_time_ms = execution_time_ms
        llm_request.status = "completed"
        llm_request.cached = response.cached
        llm_request.provider_response_id = response.provider_response_id
        llm_request.system_fingerprint = response.system_fingerprint
        llm_request.response_output = response.response_output
        llm_request.response_created_at = response.response_created_at

        self.db_session.commit()

    def _update_llm_request_error(
        self,
        llm_request: "LLMRequestModel",
        error: Exception,
        execution_time_ms: int,
        retry_attempt: int = 1,
    ) -> None:
        """Update LLMRequest record with error information."""
        # Ensure previous failed transaction is cleared
        with contextlib.suppress(Exception):
            self.db_session.rollback()
        llm_request.status = "failed"
        llm_request.error_message = str(error)
        llm_request.error_type = type(error).__name__
        llm_request.execution_time_ms = execution_time_ms
        llm_request.retry_attempt = retry_attempt

        self.db_session.commit()

    def _update_image_request_success(
        self,
        llm_request: "LLMRequestModel",
        response: ImageResponse,
        execution_time_ms: int,
        response_raw: dict[str, Any] | None = None,
    ) -> None:
        """Update LLMRequest record with successful image response data."""
        llm_request.response_content = response.image_url
        llm_request.response_raw = response_raw or response.to_dict()
        llm_request.cost_estimate = response.cost_estimate
        llm_request.execution_time_ms = execution_time_ms
        llm_request.status = "completed"

        self.db_session.commit()

    @abstractmethod
    async def generate_response(
        self,
        messages: list[LLMMessage],
        user_id: uuid.UUID | None = None,
        **kwargs: LLMProviderKwargs,
    ) -> tuple[LLMResponse, uuid.UUID]:
        """Generate a completion from the LLM provider."""
        raise NotImplementedError

    async def generate_structured_object(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        user_id: uuid.UUID | None = None,
        **kwargs: LLMProviderKwargs,
    ) -> tuple[T, uuid.UUID, dict[str, Any]]:
        """Default structured object generation. Provider may override."""
        raise NotImplementedError

    @abstractmethod
    async def generate_image(
        self,
        request: ImageGenerationRequest,
        user_id: uuid.UUID | None = None,
        **kwargs: LLMProviderKwargs,
    ) -> tuple[ImageResponse, uuid.UUID]:
        """Generate an image from the provider."""
        raise NotImplementedError

    @abstractmethod
    async def search_recent_news(
        self,
        search_queries: list[str],
        user_id: uuid.UUID | None = None,
        **kwargs: LLMProviderKwargs,
    ) -> tuple[WebSearchResponse, uuid.UUID]:
        """Search recent news using the provider."""
        raise NotImplementedError

    def estimate_cost(
        self,
        prompt_tokens: int,  # noqa: ARG002
        completion_tokens: int,  # noqa: ARG002
        model: str | None = None,  # noqa: ARG002
    ) -> float:
        """
        Estimate cost for a request based on token usage.

        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            model: Model name (defaults to config.model)

        Returns:
            Estimated cost in USD
        """
        # Default implementation - should be overridden by providers
        # for accurate cost estimation
        return 0.0
