"""Public interface for LLM services module."""

from typing import Any, Protocol, TypeVar
import uuid

from pydantic import BaseModel

from ..infrastructure.public import infrastructure_provider
from .repo import LLMRequestRepo
from .service import ImageResponse, LLMMessage, LLMRequest, LLMResponse, LLMService, WebSearchResponse

# Type variable for structured responses
T = TypeVar("T", bound=BaseModel)

__all__ = ["ImageResponse", "LLMMessage", "LLMRequest", "LLMResponse", "LLMServicesProvider", "WebSearchResponse", "llm_services_provider"]


class LLMServicesProvider(Protocol):
    """
    Protocol defining the public interface for LLM services.

    This interface provides access to LLM functionality including:
    - Text generation with conversation context
    - Structured output generation using Pydantic models
    - Image generation from text prompts
    - Web search capabilities
    - Request tracking and retrieval
    """

    async def generate_response(self, messages: list[LLMMessage], user_id: uuid.UUID | None = None, model: str | None = None, temperature: float | None = None, max_output_tokens: int | None = None, **kwargs: Any) -> tuple[LLMResponse, uuid.UUID]:
        """
        Generate a text response from the LLM.

        Args:
            messages: List of conversation messages
            user_id: Optional user identifier for tracking
            model: Override default model (e.g., "gpt-4", "gpt-3.5-turbo")
            temperature: Override default temperature (0.0-2.0)
            max_output_tokens: Override maximum output tokens
            **kwargs: Additional provider-specific parameters

        Returns:
            Tuple of (response DTO, request ID for tracking)

        Raises:
            LLMError: If the request fails
        """
        ...

    async def generate_structured_response(
        self, messages: list[LLMMessage], response_model: type[T], user_id: uuid.UUID | None = None, model: str | None = None, temperature: float | None = None, max_output_tokens: int | None = None, **kwargs: Any
    ) -> tuple[T, uuid.UUID]:
        """
        Generate a structured response using a Pydantic model.

        Args:
            messages: List of conversation messages
            response_model: Pydantic model class for structured output
            user_id: Optional user identifier for tracking
            model: Override default model
            temperature: Override default temperature
            max_output_tokens: Override maximum output tokens
            **kwargs: Additional provider-specific parameters

        Returns:
            Tuple of (structured response object, request ID)

        Raises:
            LLMError: If the request fails
            LLMValidationError: If response doesn't match the model
        """
        ...

    async def generate_image(self, prompt: str, user_id: uuid.UUID | None = None, size: str = "1024x1024", quality: str = "standard", style: str | None = None, **kwargs: Any) -> tuple[ImageResponse, uuid.UUID]:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the desired image
            user_id: Optional user identifier for tracking
            size: Image size (e.g., "1024x1024", "512x512")
            quality: Image quality ("standard" or "hd")
            style: Optional style parameter
            **kwargs: Additional provider-specific parameters

        Returns:
            Tuple of (image response DTO, request ID)

        Raises:
            LLMError: If the request fails
        """
        ...

    async def search_web(self, queries: list[str], user_id: uuid.UUID | None = None, max_results: int = 10, **kwargs: Any) -> tuple[WebSearchResponse, uuid.UUID]:
        """
        Search the web for recent information.

        Args:
            queries: List of search queries
            user_id: Optional user identifier for tracking
            max_results: Maximum number of results per query
            **kwargs: Additional search parameters

        Returns:
            Tuple of (search response DTO, request ID)

        Raises:
            LLMError: If the search fails
        """
        ...

    def get_request(self, request_id: uuid.UUID) -> LLMRequest | None:
        """
        Retrieve details of a previous LLM request.

        Args:
            request_id: UUID of the request to retrieve

        Returns:
            Request DTO if found, None otherwise
        """
        ...

    def get_user_requests(self, user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> list[LLMRequest]:
        """
        Get recent requests for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of requests to return
            offset: Number of requests to skip

        Returns:
            List of request DTOs
        """
        ...

    def estimate_cost(self, messages: list[LLMMessage], model: str | None = None) -> float:
        """
        Estimate the cost of a request before making it.

        Args:
            messages: List of conversation messages
            model: Model to use for estimation

        Returns:
            Estimated cost in USD
        """
        ...

    def get_request_count_by_user(self, user_id: uuid.UUID) -> int:
        """
        Get total request count for a user.

        Args:
            user_id: User identifier

        Returns:
            Total number of requests for the user
        """
        ...

    def get_request_count_by_status(self, status: str) -> int:
        """
        Get request count by status.

        Args:
            status: Request status to count

        Returns:
            Number of requests with the given status
        """
        ...


def llm_services_provider() -> LLMServicesProvider:
    """Dependency injection provider for LLM services."""
    # Get session from infrastructure service
    infra = infrastructure_provider()
    infra.initialize()
    db_session = infra.get_database_session()
    return LLMService(LLMRequestRepo(db_session.session))
