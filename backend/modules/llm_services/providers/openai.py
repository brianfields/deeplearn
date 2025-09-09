"""OpenAI provider implementation."""

import asyncio
from datetime import UTC, datetime
import importlib
import json
import logging
from typing import Any, TypeVar
import uuid

# Dynamically import OpenAI to avoid hard dependency during static analysis
try:  # pragma: no cover - dynamic import guard
    _openai = importlib.import_module("openai")
    APIConnectionError = _openai.APIConnectionError
    APIError = _openai.APIError
    APITimeoutError = _openai.APITimeoutError
    RateLimitError = _openai.RateLimitError
    AuthenticationError = _openai.AuthenticationError
    PermissionDeniedError = _openai.PermissionDeniedError
    AsyncAzureOpenAI = _openai.AsyncAzureOpenAI
    AsyncOpenAI = _openai.AsyncOpenAI
    _OPENAI_AVAILABLE = True
except Exception:
    _OPENAI_AVAILABLE = False
    APIConnectionError = Exception  # type: ignore[assignment]
    APIError = Exception  # type: ignore[assignment]
    APITimeoutError = Exception  # type: ignore[assignment]
    RateLimitError = Exception  # type: ignore[assignment]
    AuthenticationError = Exception  # type: ignore[assignment]
    PermissionDeniedError = Exception  # type: ignore[assignment]
    AsyncAzureOpenAI = None  # type: ignore[assignment]
    AsyncOpenAI = None  # type: ignore[assignment]

from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..cache import LLMCache
from ..config import LLMConfig
from ..exceptions import (
    LLMAuthenticationError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from ..types import (
    ImageGenerationRequest,
    ImageResponse,
    LLMMessage,
    LLMResponse,
    MessageRole,
    WebSearchResponse,
)
from .base import LLMProvider

logger = logging.getLogger(__name__)

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)

__all__ = ["OpenAIProvider"]


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPT-5 provider implementation supporting text and image generation.

    Focuses exclusively on GPT-5 using the Responses API with automatic retry logic,
    error handling, and token tracking. Supports both regular OpenAI API and Azure OpenAI.
    """

    def __init__(self, config: LLMConfig, db_session: Session) -> None:
        """Initialize the OpenAI provider with configuration and database session."""
        super().__init__(config, db_session)

        # Initialize cache if enabled
        try:
            self._cache = LLMCache(
                cache_dir=self.config.cache_dir,
                enabled=self.config.cache_enabled,
            )
        except Exception:
            # Cache should never block provider initialization
            self._cache = None

        self._setup_client()
        # Client typing
        self.client: Any

    def _setup_client(self) -> None:
        """Setup OpenAI client based on configuration."""
        try:
            if not _OPENAI_AVAILABLE or (AsyncOpenAI is None and AsyncAzureOpenAI is None):
                raise LLMAuthenticationError("OpenAI SDK is not installed. Please install 'openai' package to use this provider.")
            if self.config.provider.value == "azure_openai":
                self.client = AsyncAzureOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                )  # type: ignore[misc]
            else:
                self.client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                )  # type: ignore[misc]
        except Exception as e:
            raise LLMAuthenticationError(f"Failed to setup OpenAI client: {e}") from e

    def _validate_gpt5_model(self, model: str) -> None:
        """Validate that the model is GPT-5 since we only support GPT-5."""
        if not model.startswith("gpt-5"):
            raise LLMValidationError(f"Only GPT-5 models are supported. Got: {model}")

    def _convert_messages_to_gpt5_input(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        """Convert LLMMessage list to GPT-5 input format."""
        input_messages = []
        for msg in messages:
            input_msg = {
                "role": msg.role.value,
                "content": msg.content,
            }
            if msg.name:
                input_msg["name"] = msg.name
            input_messages.append(input_msg)
        return input_messages

    def _parse_gpt5_response(self, response: Any) -> tuple[str, str | None, dict[str, Any] | None]:
        """Parse GPT-5 response format and extract content, finish_reason, and usage."""
        # Use output_text if available (convenience property in SDK)
        if hasattr(response, "output_text"):
            content = response.output_text
        else:
            # Parse output array manually
            content = ""
            for output_item in response.output:
                if hasattr(output_item, "content"):
                    for content_item in output_item.content:
                        if hasattr(content_item, "text"):
                            content += content_item.text

        # Extract finish reason and usage if available
        finish_reason = None
        usage = None

        # GPT-5 response structure may have different usage tracking
        if hasattr(response, "usage"):
            usage = response.usage

        return content, finish_reason, usage

    async def generate_response(
        self,
        messages: list[LLMMessage],
        user_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> tuple[LLMResponse, uuid.UUID]:
        """
        Generate a response from OpenAI.

        Args:
            messages: List of conversation messages
            user_id: Optional user identifier for tracking
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Tuple of (LLMResponse, LLMRequest ID)

        Raises:
            LLMError: If the request fails
        """
        start_time = datetime.now(UTC)

        try:
            # Create database record
            llm_request = self._create_llm_request(messages=messages, user_id=user_id, **kwargs)
            # Ensure we have a valid request ID
            if llm_request.id is None:
                raise LLMError("Failed to create LLM request record")
            request_id: uuid.UUID = llm_request.id

            # Check cache first (if enabled)
            cache = getattr(self, "_cache", None)
            if self.config.cache_enabled and cache is not None:
                cached_response = await cache.get(messages, **kwargs)
                if cached_response:
                    self._update_llm_request_success(
                        llm_request,
                        cached_response,
                        int((datetime.now(UTC) - start_time).total_seconds() * 1000),
                    )
                    return cached_response, request_id

            # Validate model and prepare GPT-5 request
            model = kwargs.get("model", self.config.model) or self.config.model
            self._validate_gpt5_model(model)

            logger.info(f"🤖 Starting GPT-5 request - Model: {model}, Messages: {len(messages)}")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Messages: {[{'role': m.role.value, 'content': m.content[:100] + '...' if len(m.content) > 100 else m.content} for m in messages]}")

            # Convert messages to GPT-5 format
            input_messages = self._convert_messages_to_gpt5_input(messages)

            request_params = {
                "model": model,
                "input": input_messages,
            }

            # Add GPT-5 specific parameters
            if "instructions" in kwargs:
                request_params["instructions"] = kwargs["instructions"]
                logger.debug(f"Instructions: {kwargs['instructions'][:100]}...")
            if "reasoning" in kwargs:
                request_params["reasoning"] = kwargs["reasoning"]
                logger.debug(f"Reasoning: {kwargs['reasoning']}")

            # Add optional parameters that work with GPT-5
            for param in ["top_p", "frequency_penalty", "presence_penalty", "stop"]:
                if param in kwargs:
                    request_params[param] = kwargs[param]

            logger.debug(f"GPT-5 request params: {list(request_params.keys())}")

            # Make API call with retry logic
            logger.info("⏳ Making GPT-5 API call...")
            response = await self._make_api_call_with_retry(
                lambda: self.client.responses.create(**request_params)  # type: ignore[attr-defined]
            )
            logger.info("✅ GPT-5 API call completed")

            # Parse GPT-5 response
            content, finish_reason, usage = self._parse_gpt5_response(response)

            # Extract usage information
            if usage:
                tokens_used = getattr(usage, "total_tokens", None)
                prompt_tokens = getattr(usage, "prompt_tokens", None)
                completion_tokens = getattr(usage, "completion_tokens", None)
            else:
                tokens_used = prompt_tokens = completion_tokens = None

            # Calculate cost estimate
            cost_estimate = self.estimate_cost(prompt_tokens or 0, completion_tokens or 0, model)

            # Create response object
            llm_response = LLMResponse(
                content=content,
                provider=self.config.provider,
                model=model,
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_estimate=cost_estimate,
                finish_reason=finish_reason,
                response_time_ms=int((datetime.now(UTC) - start_time).total_seconds() * 1000),
                cached=False,
            )

            # Cache response (if enabled)
            cache = getattr(self, "_cache", None)
            if self.config.cache_enabled and cache is not None:
                await cache.set(messages, llm_response, **kwargs)

            # Update database record
            self._update_llm_request_success(
                llm_request,
                llm_response,
                llm_response.response_time_ms or 0,
            )

            logger.info(f"🎉 LLM response completed - Tokens: {tokens_used or 0}, Cost: ${cost_estimate:.4f}, Time: {llm_response.response_time_ms}ms")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Response content: '{content[:200]}{'...' if len(content) > 200 else ''}'")
            if not content:
                logger.warning("⚠️ LLM returned empty content!")
            return llm_response, request_id

        except Exception as e:
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            # Update database record with error
            if "llm_request" in locals():
                self._update_llm_request_error(llm_request, e, execution_time_ms)

            # Convert to appropriate LLM exception
            raise self._convert_exception(e) from e

    async def generate_structured_object(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        user_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> tuple[T, uuid.UUID]:
        """
        Generate a structured response using GPT-5 with JSON schema instructions.

        Uses GPT-5's instructions parameter to enforce JSON schema compliance.
        """
        try:
            # Validate GPT-5 model
            model = kwargs.get("model", self.config.model) or self.config.model
            self._validate_gpt5_model(model)

            # Create JSON schema instruction for GPT-5
            schema = response_model.model_json_schema()
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            # Create a clearer instruction with examples
            prop_descriptions = []
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get("type", "string")
                prop_desc = prop_info.get("description", f"{prop_name} field")
                prop_descriptions.append(f"- {prop_name} ({prop_type}): {prop_desc}")

            schema_instruction = f"""
You must respond with a valid JSON object containing these fields:
{chr(10).join(prop_descriptions)}

Required fields: {", ".join(required)}

Respond ONLY with the JSON object - no explanations, no markdown formatting, no additional text.

Example format:
{{
  "field1": "value1",
  "field2": "value2"
}}
"""

            # For GPT-5, use instructions parameter
            kwargs_copy = kwargs.copy()
            kwargs_copy["instructions"] = schema_instruction
            response, llm_request_id = await self.generate_response(messages=messages, user_id=user_id, **kwargs_copy)

            # Parse JSON response
            try:
                content_to_parse = response.content.strip()
                logger.debug(f"Raw LLM response content for parsing: '{content_to_parse}'")
                if not content_to_parse:
                    raise LLMValidationError("LLM returned empty response for structured output")

                json_data = json.loads(content_to_parse)
                structured_obj = response_model(**json_data)
                return structured_obj, llm_request_id

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse structured response. Content: '{response.content[:200]}...'")
                raise LLMValidationError(f"Failed to parse structured response: {e}") from e

        except Exception as e:
            if isinstance(e, LLMValidationError):
                raise
            raise LLMError(f"Failed to generate structured object: {e}") from e

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        user_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> tuple[ImageResponse, uuid.UUID]:
        """Generate an image from a text prompt."""
        start_time = datetime.now(UTC)

        try:
            # Create database record
            messages = [LLMMessage(role=MessageRole.USER, content=request.prompt)]
            llm_request = self._create_llm_request(
                messages=messages,
                user_id=user_id,
                model=self.config.image_model,
                **kwargs,
            )
            # Ensure we have a valid request ID
            if llm_request.id is None:
                raise LLMError("Failed to create LLM request record")
            request_id: uuid.UUID = llm_request.id

            # Prepare request parameters
            request_params = {
                "model": self.config.image_model,
                "prompt": request.prompt,
                "size": request.size.value,
                "quality": request.quality.value,
                "n": request.n,
            }

            if request.style:
                request_params["style"] = request.style

            # Make API call with retry logic
            response = await self._make_api_call_with_retry(
                lambda: self.client.images.generate(**request_params)  # type: ignore[attr-defined]
            )

            # Extract response data
            image_data = response.data[0]
            image_url = image_data.url
            revised_prompt = getattr(image_data, "revised_prompt", None)

            # Create response object
            image_response = ImageResponse(
                image_url=image_url,
                revised_prompt=revised_prompt,
                size=request.size.value,
                cost_estimate=self._estimate_image_cost(request.size, request.quality),
            )

            # Update database record
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            self._update_image_request_success(
                llm_request,
                image_response,
                execution_time_ms,
                response.model_dump() if hasattr(response, "model_dump") else None,
            )

            logger.info(f"Generated image: {image_url}")
            return image_response, request_id

        except Exception as e:
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            # Update database record with error
            if "llm_request" in locals():
                self._update_llm_request_error(llm_request, e, execution_time_ms)

            raise self._convert_exception(e) from e

    async def search_recent_news(
        self,
        search_queries: list[str],
        user_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> tuple[WebSearchResponse, uuid.UUID]:
        """
        Search for recent news.

        Note: This is a placeholder implementation. OpenAI doesn't provide
        native web search, so this would need to be integrated with a
        separate search provider like Bing Web Search or similar.
        """
        raise NotImplementedError("Web search not implemented for OpenAI provider. Consider integrating with Bing Web Search or another provider.")

    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str | None = None,
    ) -> float:
        """Estimate cost for GPT-5 API usage."""
        model_name = model or self.config.model

        # GPT-5 pricing (estimated - adjust based on actual pricing when available)
        if "gpt-5" in model_name:
            # Placeholder pricing for GPT-5 - update when official pricing is released
            prompt_cost = (prompt_tokens / 1000) * 0.05  # Estimated
            completion_cost = (completion_tokens / 1000) * 0.10  # Estimated
        else:
            # Fallback for any non-GPT-5 models (should not happen with validation)
            prompt_cost = (prompt_tokens / 1000) * 0.05
            completion_cost = (completion_tokens / 1000) * 0.10

        return prompt_cost + completion_cost

    def _estimate_image_cost(self, size: Any, quality: Any) -> float:
        """Estimate cost for DALL-E image generation."""
        # DALL-E 3 pricing (as of 2024)
        if quality.value == "hd":
            if size.value in ["1024x1024", "1024x1792", "1792x1024"]:
                return 0.080  # HD price
            else:
                return 0.120  # HD + large size
        elif size.value == "1024x1024":
            return 0.040  # Standard
        else:
            return 0.080  # Standard + large size

    async def _make_api_call_with_retry(self, api_call_func: Any) -> Any:
        """Make API call with retry logic for rate limits and transient errors."""
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return await api_call_func()
            except Exception as e:
                last_exception = e

                # Check if we should retry
                if attempt < self.config.max_retries and self._should_retry(e):
                    wait_time = self._calculate_backoff(attempt)
                    logger.warning(f"API call failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue

                # Don't retry or max retries reached
                break

        # All retries failed
        if last_exception is not None:
            # Convert to LLMError subtype for consistency
            raise self._convert_exception(last_exception)
        raise LLMError("Unknown error during OpenAI API call")

    def _should_retry(self, exception: Any) -> bool:
        """Determine if an exception should trigger a retry."""

        # Always retry on these errors
        if isinstance(exception, APIConnectionError | APITimeoutError):
            return True

        # Retry on rate limits
        if isinstance(exception, RateLimitError):
            return True

        # Retry on server errors (5xx)
        if isinstance(exception, APIError):
            status_code = getattr(exception, "status_code", None)
            return status_code is not None and 500 <= status_code < 600

        return False

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff time."""
        base_delay = 1.0
        max_delay = 60.0
        delay = base_delay * (2**attempt)
        return min(delay, max_delay)

    def _convert_exception(self, exception: Any) -> LLMError:
        """Convert OpenAI exceptions to LLM exceptions."""
        # Use imported symbols or fallbacks
        if isinstance(exception, AuthenticationError | PermissionDeniedError):
            return LLMAuthenticationError(str(exception))

        if isinstance(exception, RateLimitError):
            retry_after = getattr(exception, "retry_after", None)
            return LLMRateLimitError(str(exception), retry_after=retry_after)

        if isinstance(exception, APIError):
            status_code = getattr(exception, "status_code", None)
            if status_code == 408 or isinstance(exception, APITimeoutError):
                return LLMTimeoutError(str(exception))

        return LLMError(str(exception))
