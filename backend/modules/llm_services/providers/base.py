"""Abstract base classes and common functionality for LLM providers."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, TypeVar
import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import LLMConfig
from ..types import (
    ImageGenerationRequest,
    ImageResponse,
    LLMMessage,
    LLMResponse,
    WebSearchResponse,
)

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
        **kwargs: Any,
    ) -> "LLMRequestModel":
        """
        Create a database record for an LLM request.

        Args:
            messages: List of messages in the conversation
            user_id: Optional user identifier
            model: Model name (defaults to config.model)
            temperature: Temperature setting (defaults to config.temperature)
            max_output_tokens: Maximum output tokens (optional)
            **kwargs: Additional parameters

        Returns:
            LLMRequestModel database record
        """
        from ..models import LLMRequestModel

        # Use provided values or fall back to config
        request_model = model or self.config.model
        request_temperature = temperature if temperature is not None else self.config.temperature
        request_max_output_tokens = max_output_tokens if max_output_tokens is not None else self.config.max_output_tokens

        # Convert messages to JSON-serializable format
        messages_json = [msg.to_dict() for msg in messages]

        # Build additional params
        additional_params = {
            "temperature": request_temperature,
            **({"max_output_tokens": request_max_output_tokens} if request_max_output_tokens is not None else {}),
            **kwargs,
        }

        llm_request = LLMRequestModel(
            user_id=user_id,
            provider=self.config.provider.value,
            model=request_model,
            temperature=request_temperature,
            max_output_tokens=request_max_output_tokens,
            messages=messages_json,
            additional_params=additional_params,
            status="pending",
            created_at=datetime.now(UTC),
        )

        self.db_session.add(llm_request)
        self.db_session.flush()  # Get the ID

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
        try:
            self.db_session.rollback()
        except Exception:
            pass
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
        response_raw: dict | None = None,
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
        **kwargs: Any,
    ) -> tuple[LLMResponse, uuid.UUID]:
        """
        Generate a response from the LLM.

        Args:
            messages: List of conversation messages
            user_id: Optional user identifier for tracking
            **kwargs: Additional parameters (temperature, max_output_tokens, etc.)

        Returns:
            Tuple of (LLMResponse, LLMRequest ID)

        Raises:
            LLMError: If the request fails
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_structured_object(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        user_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> tuple[T, uuid.UUID]:
        """
        Generate a structured response using instructor and Pydantic models.

        Args:
            messages: List of conversation messages
            response_model: Pydantic model class for structured output
            user_id: Optional user identifier for tracking
            **kwargs: Additional parameters

        Returns:
            Tuple of (structured response object, LLMRequest ID)

        Raises:
            LLMError: If the request fails
            LLMValidationError: If response doesn't match the model
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_image(
        self,
        request: ImageGenerationRequest,
        user_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> tuple[ImageResponse, uuid.UUID]:
        """
        Generate an image from a text prompt.

        Args:
            request: Image generation request parameters
            user_id: Optional user identifier for tracking
            **kwargs: Additional parameters

        Returns:
            Tuple of (ImageResponse, LLMRequest ID)

        Raises:
            LLMError: If the request fails
        """
        raise NotImplementedError

    @abstractmethod
    async def search_recent_news(
        self,
        search_queries: list[str],
        user_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> tuple[WebSearchResponse, uuid.UUID]:
        """
        Search for recent news using web search capabilities.

        Args:
            search_queries: List of search queries
            user_id: Optional user identifier for tracking
            **kwargs: Additional parameters

        Returns:
            Tuple of (WebSearchResponse, LLMRequest ID)

        Raises:
            LLMError: If the search fails
        """
        raise NotImplementedError

    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str | None = None,
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
