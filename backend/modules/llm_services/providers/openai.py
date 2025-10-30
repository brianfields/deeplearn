"""OpenAI provider implementation."""

import asyncio
import base64
import contextlib
from datetime import UTC, datetime
import importlib
import json
import logging
import math
import re
from typing import Any, TypeVar, cast
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
    APIConnectionError = Exception
    APIError = Exception
    APITimeoutError = Exception
    RateLimitError = Exception
    AuthenticationError = Exception
    PermissionDeniedError = Exception
    AsyncAzureOpenAI = None
    AsyncOpenAI = None

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
    AudioGenerationRequest,
    AudioResponse,
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

        self._cache: LLMCache | None = None

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
                assert AsyncAzureOpenAI is not None
                self.client = cast(Any, AsyncAzureOpenAI)(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                )
            else:
                assert AsyncOpenAI is not None
                self.client = cast(Any, AsyncOpenAI)(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                )
        except Exception as e:
            raise LLMAuthenticationError(f"Failed to setup OpenAI client: {e}") from e

    @staticmethod
    def _normalize_voice(voice: str) -> str:
        """Normalize friendly voice labels to OpenAI-supported voice values.

        Falls back to a default if the provided voice is not recognized.
        """
        supported = {
            "alloy",
            "echo",
            "fable",
            "onyx",
            "nova",
            "shimmer",
            "coral",
            "verse",
            "ballad",
            "ash",
            "sage",
            "marin",
            "cedar",
        }
        aliases = {
            "plain": "fable",
            "neutral": "fable",
            "default": "fable",
        }

        v = (voice or "").strip()
        v_lower = v.lower()
        if v_lower in supported:
            return v_lower
        if v_lower in aliases:
            return aliases[v_lower]

        logger.warning("Unsupported voice '%s'. Falling back to 'alloy'", voice)
        return "alloy"

    def _to_jsonable(self, obj: Any) -> Any:
        """Convert SDK/Pydantic objects to JSON-serializable structures recursively."""
        # Primitive types
        if obj is None or isinstance(obj, str | int | float | bool):
            return obj
        # Pydantic v2 models
        if hasattr(obj, "model_dump") and callable(obj.model_dump):
            try:
                return self._to_jsonable(obj.model_dump())
            except Exception:
                return str(obj)
        # Pydantic v1 models
        if hasattr(obj, "dict") and callable(obj.dict):
            try:
                return self._to_jsonable(obj.dict())
            except Exception:
                return str(obj)
        # Mapping
        if isinstance(obj, dict):
            return {self._to_jsonable(k): self._to_jsonable(v) for k, v in obj.items()}
        # Sequence
        if isinstance(obj, list | tuple):
            return [self._to_jsonable(v) for v in obj]
        # Fallback
        return str(obj)

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

    def _parse_gpt5_response(self, response: Any) -> tuple[str, dict[str, Any] | list[dict[str, Any]] | None, dict[str, Any] | None]:
        """Parse GPT-5 Responses API and extract content, output array, and usage."""
        # Use output_text if available (convenience property in SDK)
        if hasattr(response, "output_text"):
            content = response.output_text
        else:
            # Parse output array manually
            content = ""
            for output_item in getattr(response, "output", []) or []:
                if hasattr(output_item, "content"):
                    for content_item in output_item.content:
                        if hasattr(content_item, "text"):
                            content += content_item.text

        # Extract usage if available
        usage = getattr(response, "usage", None)
        output = getattr(response, "output", None)

        return content, output, usage

    async def _handle_cached_response(
        self,
        messages: list[LLMMessage],
        llm_request: Any,
        start_time: datetime,
        **kwargs: Any,
    ) -> LLMResponse | None:
        """Check cache for existing response."""
        cache = getattr(self, "_cache", None)
        if self.config.cache_enabled and cache is not None:
            cached_response = await cache.get(messages, **kwargs)
            if cached_response:
                self._update_llm_request_success(
                    llm_request,
                    cached_response,
                    int((datetime.now(UTC) - start_time).total_seconds() * 1000),
                )
                return cast(LLMResponse | None, cached_response)
        return None

    def _prepare_gpt5_request_params(
        self,
        messages: list[LLMMessage],
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Prepare request parameters for GPT-5 API call."""
        input_messages = self._convert_messages_to_gpt5_input(messages)

        request_params = {
            "model": model,
            "input": input_messages,
        }

        # Add GPT-5 specific parameters
        if "instructions" in kwargs:
            request_params["instructions"] = kwargs["instructions"]
            logger.debug(f"Instructions: {kwargs['instructions'][:100]}...")

        # Reasoning configuration
        if "reasoning" in kwargs:
            request_params["reasoning"] = kwargs["reasoning"]
            logger.debug(f"Reasoning: {kwargs['reasoning']}")

        # Text configuration (verbosity)
        if "text" in kwargs:
            request_params["text"] = kwargs["text"]
            logger.debug(f"Text config: {kwargs['text']}")
        elif "verbosity" in kwargs:
            # Support direct verbosity parameter for convenience
            request_params["text"] = {"verbosity": kwargs["verbosity"]}  # type: ignore[assignment]
            logger.debug(f"Verbosity: {kwargs['verbosity']}")

        # Chain of thought persistence
        if "previous_response_id" in kwargs:
            request_params["previous_response_id"] = kwargs["previous_response_id"]
            logger.debug(f"Using previous response ID: {kwargs['previous_response_id']}")

        # Add optional parameters that work with GPT-5
        for param in ["temperature", "top_p", "frequency_penalty", "presence_penalty", "stop", "max_output_tokens"]:
            if param in kwargs:
                request_params[param] = kwargs[param]

        logger.debug(f"GPT-5 request params: {list(request_params.keys())}")
        return request_params

    async def generate_response(
        self,
        messages: list[LLMMessage],
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[LLMResponse, uuid.UUID]:
        """
        Generate a response from OpenAI.

        Args:
            messages: List of conversation messages
            user_id: Optional user identifier for tracking
            **kwargs: Additional parameters (temperature, max_output_tokens, etc.)

        Returns:
            Tuple of (LLMResponse, LLMRequest ID)

        Raises:
            LLMError: If the request fails
        """
        start_time = datetime.now(UTC)

        try:
            # Create database record
            llm_request = self._create_llm_request(messages=messages, user_id=user_id, **kwargs)
            if llm_request.id is None:
                raise LLMError("Failed to create LLM request record")
            request_id: uuid.UUID = llm_request.id

            # Check cache first (if enabled)
            cached_response = await self._handle_cached_response(messages, llm_request, start_time, **kwargs)
            if cached_response:
                return cached_response, request_id

            # Validate model and prepare GPT-5 request
            model = kwargs.get("model", self.config.model) or self.config.model
            self._validate_gpt5_model(model)

            logger.info(f"🤖 Starting GPT-5 request - Model: {model}, Messages: {len(messages)}")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Messages: %s",
                    [
                        {
                            "role": msg.role.value,
                            "content": (
                                msg.content[:100] + "..."
                                if isinstance(msg.content, str) and len(msg.content) > 100
                                else (msg.content if isinstance(msg.content, str) else "[non-text content]")
                            ),
                        }
                        for msg in messages
                    ],
                )

            # Prepare request parameters (avoid passing duplicate 'model')
            kwargs_clean = kwargs.copy()
            if "model" in kwargs_clean:
                kwargs_clean.pop("model")
            request_params = self._prepare_gpt5_request_params(messages, model, **kwargs_clean)

            # Store request payload in DB record for traceability
            with contextlib.suppress(Exception):
                # Save a simplified payload
                input_messages = self._convert_messages_to_gpt5_input(messages)
                llm_request.request_payload = {"model": model, "input": input_messages}

            # Make API call with retry logic
            logger.info("⏳ Making GPT-5 API call...")
            responses_client = getattr(self.client, "responses", None)
            create_method = getattr(responses_client, "create", None)
            if not callable(create_method):
                raise LLMError("OpenAI Responses API is not available in this environment")
            response = await self._make_api_call_with_retry(lambda: create_method(**request_params))
            logger.info("✅ GPT-5 API call completed")

            # Parse GPT-5 response
            content, output, usage = self._parse_gpt5_response(response)

            # Extract usage information
            tokens_used = getattr(usage, "total_tokens", None) if usage else None
            input_tokens = getattr(usage, "input_tokens", None) if usage else None
            output_tokens = getattr(usage, "output_tokens", None) if usage else None

            # Calculate cost estimate
            # Estimate cost using input/output tokens if available
            cost_estimate = self.estimate_cost(input_tokens or 0, output_tokens or 0, model)

            # Create response object
            # Convert provider created timestamp to datetime if available
            created_raw = getattr(response, "created", None)
            created_dt = None
            if isinstance(created_raw, int | float):
                created_dt = datetime.fromtimestamp(created_raw, tz=UTC)
            elif isinstance(created_raw, datetime):
                created_dt = created_raw

            llm_response = LLMResponse(
                content=content,
                provider=self.config.provider,
                model=model,
                tokens_used=tokens_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_estimate=cost_estimate,
                response_time_ms=int((datetime.now(UTC) - start_time).total_seconds() * 1000),
                cached=False,
                provider_response_id=getattr(response, "id", None),
                system_fingerprint=getattr(response, "system_fingerprint", None),
                response_output=self._to_jsonable(output) if output is not None else None,
                response_created_at=created_dt,
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

    def _fix_schema_for_structured_outputs(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Fix JSON schema to be compatible with OpenAI structured outputs."""

        def fix_object_schema(obj: dict[str, Any]) -> dict[str, Any]:
            """Recursively fix object schemas to include additionalProperties: false."""
            if isinstance(obj, dict):
                # Fix current object
                if obj.get("type") == "object":
                    obj["additionalProperties"] = False

                # Recursively fix nested objects
                for key, value in obj.items():
                    if isinstance(value, dict):
                        obj[key] = fix_object_schema(value)
                    elif isinstance(value, list):
                        obj[key] = [fix_object_schema(item) if isinstance(item, dict) else item for item in value]

            return obj

        fixed_schema = fix_object_schema(schema.copy())

        # Also ensure the root object has additionalProperties: false
        if fixed_schema.get("type") == "object":
            fixed_schema["additionalProperties"] = False

        return fixed_schema

    def _prepare_structured_request_params(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        model: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Prepare request parameters for structured outputs."""
        schema = response_model.model_json_schema()
        # Fix schema for OpenAI structured outputs compatibility
        schema = self._fix_schema_for_structured_outputs(schema)
        input_messages = self._convert_messages_to_gpt5_input(messages)

        request_params = {"model": model, "input": input_messages, "text": {"format": {"type": "json_schema", "name": response_model.__name__.lower(), "schema": schema, "strict": True}}}

        # Add GPT-5 specific parameters for structured outputs
        if "reasoning" in kwargs:
            request_params["reasoning"] = kwargs["reasoning"]

        if "text" in kwargs:
            # Merge with existing text.format configuration
            if "text" not in request_params:
                request_params["text"] = {}
            request_params["text"].update(kwargs["text"])  # type: ignore[attr-defined]
        elif "verbosity" in kwargs:
            # Support direct verbosity parameter
            if "text" not in request_params:
                request_params["text"] = {}
            request_params["text"]["verbosity"] = kwargs["verbosity"]  # type: ignore[index]

        if "previous_response_id" in kwargs:
            request_params["previous_response_id"] = kwargs["previous_response_id"]

        # Add optional parameters
        for param in ["top_p", "frequency_penalty", "presence_penalty", "stop", "max_output_tokens"]:
            if param in kwargs:
                request_params[param] = kwargs[param]

        return request_params

    def _validate_structured_response(self, response: Any) -> None:
        """Validate structured response for errors and refusals."""
        if not hasattr(response, "status"):
            return

        if response.status == "incomplete" and hasattr(response, "incomplete_details"):
            reason = getattr(response.incomplete_details, "reason", "unknown")
            if reason == "max_output_tokens":
                raise LLMValidationError("Response was incomplete due to max_output_tokens limit")
            if reason == "content_filter":
                raise LLMValidationError("Response was filtered due to content policy")
            raise LLMValidationError(f"Response incomplete: {reason}")

        # Check for refusals in the output
        if hasattr(response, "output") and response.output:
            for output_item in response.output:
                if hasattr(output_item, "content") and output_item.content:
                    for content_item in output_item.content:
                        if hasattr(content_item, "type") and content_item.type == "refusal":
                            refusal_message = getattr(content_item, "refusal", "Model refused to respond")
                            raise LLMValidationError(f"Model refused request: {refusal_message}")

    async def generate_structured_object(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[T, uuid.UUID, dict[str, Any]]:
        """
        Generate a structured response using OpenAI's Structured Outputs feature.

        Uses the text.format parameter with json_schema for reliable schema adherence.
        """
        start_time = datetime.now(UTC)

        try:
            # Validate model
            model = kwargs.get("model", self.config.model) or self.config.model
            self._validate_gpt5_model(model)

            # Create database record
            llm_request = self._create_llm_request(messages=messages, user_id=user_id, **kwargs)
            if llm_request.id is None:
                raise LLMError("Failed to create LLM request record")
            request_id: uuid.UUID = llm_request.id

            # Check cache first (if enabled)
            cached_response = await self._handle_cached_response(messages, llm_request, start_time, **kwargs)
            if cached_response:
                # Parse cached response into structured object
                try:
                    json_data = json.loads(cached_response.content)
                    structured_obj = response_model(**json_data)
                    usage_info = {"tokens_used": cached_response.tokens_used or 0, "cost_estimate": cached_response.cost_estimate or 0.0}
                    return structured_obj, request_id, usage_info
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Cached response not valid JSON, proceeding with new request: {e}")

            # Use OpenAI's native structured outputs
            # Remove model from kwargs to avoid duplicate parameter
            kwargs_clean = kwargs.copy()
            kwargs_clean.pop("model", None)  # Remove model if present
            request_params = self._prepare_structured_request_params(messages, response_model, model, **kwargs_clean)
            logger.info("🤖 Starting structured GPT-5 request using native Structured Outputs")

            # Try using responses.parse if available (newer SDK versions)
            responses_client = getattr(self.client, "responses", None)
            parse_method = getattr(responses_client, "parse", None)
            if callable(parse_method):
                # Use the native SDK parsing method
                # For responses.parse(), we use text_format instead of text.format
                parse_params = request_params.copy()
                parse_params.pop("text", None)  # Remove text.format for responses.parse()
                response = await cast(Any, parse_method)(**parse_params, text_format=response_model)

                # Extract the parsed object directly
                if hasattr(response, "output_parsed") and response.output_parsed is not None:
                    structured_obj = response.output_parsed

                    # Create our LLMResponse for consistency
                    usage = getattr(response, "usage", None)
                    tokens_used = getattr(usage, "total_tokens", None) if usage else None
                    input_tokens = getattr(usage, "input_tokens", None) if usage else None
                    output_tokens = getattr(usage, "output_tokens", None) if usage else None
                    cost_estimate = self.estimate_cost(input_tokens or 0, output_tokens or 0, model)

                    llm_response = LLMResponse(
                        content=json.dumps(structured_obj.model_dump() if hasattr(structured_obj, "model_dump") else structured_obj),
                        provider=self.config.provider,
                        model=model,
                        tokens_used=tokens_used,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost_estimate=cost_estimate,
                        response_time_ms=int((datetime.now(UTC) - start_time).total_seconds() * 1000),
                        cached=False,
                        provider_response_id=getattr(response, "id", None),
                        system_fingerprint=getattr(response, "system_fingerprint", None),
                    )

                    # Update database and cache
                    self._update_llm_request_success(llm_request, llm_response, llm_response.response_time_ms or 0)

                    cache = getattr(self, "_cache", None)
                    if self.config.cache_enabled and cache is not None:
                        await cache.set(messages, llm_response, **kwargs)

                    logger.info(f"🎉 Structured response completed using native parsing - Tokens: {tokens_used or 0}")
                    usage_info = {"tokens_used": tokens_used or 0, "cost_estimate": cost_estimate}
                    return structured_obj, request_id, usage_info

            # Fallback to manual API call with structured outputs
            response = await self._make_api_call_with_retry(lambda: self.client.responses.create(**request_params))

            # Handle potential refusals and errors
            self._validate_structured_response(response)

            # Parse response using existing logic
            content, output, usage = self._parse_gpt5_response(response)

            # Parse JSON response
            content_to_parse = content.strip()
            logger.debug(f"Raw LLM response content for parsing: '{content_to_parse[:200]}...'")
            if not content_to_parse:
                raise LLMValidationError("LLM returned empty response for structured output")

            json_data = json.loads(content_to_parse)
            structured_obj = response_model(**json_data)

            # Create LLMResponse for tracking
            tokens_used = getattr(usage, "total_tokens", None) if usage else None
            input_tokens = getattr(usage, "input_tokens", None) if usage else None
            output_tokens = getattr(usage, "output_tokens", None) if usage else None
            cost_estimate = self.estimate_cost(input_tokens or 0, output_tokens or 0, model)

            llm_response = LLMResponse(
                content=content_to_parse,
                provider=self.config.provider,
                model=model,
                tokens_used=tokens_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_estimate=cost_estimate,
                response_time_ms=int((datetime.now(UTC) - start_time).total_seconds() * 1000),
                cached=False,
                provider_response_id=getattr(response, "id", None),
                system_fingerprint=getattr(response, "system_fingerprint", None),
                response_output=self._to_jsonable(output) if output is not None else None,
                response_created_at=getattr(response, "created", None),
            )

            # Update database record
            self._update_llm_request_success(llm_request, llm_response, llm_response.response_time_ms or 0)

            # Cache response
            cache = getattr(self, "_cache", None)
            if self.config.cache_enabled and cache is not None:
                await cache.set(messages, llm_response, **kwargs)

            logger.info(f"🎉 Structured object parsed successfully: {type(structured_obj).__name__}")
            usage_info = {"tokens_used": tokens_used or 0, "cost_estimate": cost_estimate}
            return structured_obj, request_id, usage_info

        except (json.JSONDecodeError, ValueError) as e:
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            if "llm_request" in locals():
                self._update_llm_request_error(llm_request, e, execution_time_ms)
            logger.error(f"Failed to parse structured response. Content: '{content[:200] if 'content' in locals() else 'N/A'}...'")
            raise LLMValidationError(f"Failed to parse structured response: {e}") from e

        except Exception as e:
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            # Update database record with error
            if "llm_request" in locals():
                self._update_llm_request_error(llm_request, e, execution_time_ms)

            if isinstance(e, LLMValidationError):
                raise
            raise LLMError(f"Failed to generate structured object: {e}") from e

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        user_id: int | None = None,
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
            response = await self._make_api_call_with_retry(lambda: self.client.images.generate(**request_params))

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

    async def generate_audio(
        self,
        request: AudioGenerationRequest,
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[AudioResponse, uuid.UUID]:
        """Synthesize narrated audio using the OpenAI Text-to-Speech API."""

        start_time = datetime.now(UTC)

        try:
            messages = [LLMMessage(role=MessageRole.USER, content=request.text)]
            llm_request = self._create_llm_request(
                messages=messages,
                user_id=user_id,
                model=request.model,
                temperature=0.0,
            )

            if llm_request.id is None:
                raise LLMError("Failed to create LLM request record")
            request_id: uuid.UUID = llm_request.id

            speech_client = getattr(getattr(self.client, "audio", None), "speech", None)
            if speech_client is None:
                raise LLMError("OpenAI audio synthesis API is not available in this environment")

            normalized_voice = self._normalize_voice(request.voice)

            # Use new TTS model default if caller passes gpt-4o-mini-tts
            resolved_model = request.model
            if resolved_model == "gpt-4o-mini-tts":
                resolved_model = "tts-1-hd"

            request_kwargs = {
                "model": resolved_model,
                "voice": normalized_voice,
                "input": request.text,
                # OpenAI SDK expects 'response_format' for TTS output format
                "response_format": request.audio_format,
            }
            request_kwargs.update({k: v for k, v in kwargs.items() if v is not None})
            if request.speed is not None:
                request_kwargs["speed"] = str(request.speed)

            audio_bytes: bytes
            create_method = getattr(speech_client, "create", None)
            if not callable(create_method):
                raise LLMError("OpenAI audio synthesis API does not expose a create() method")

            response = await cast(Any, create_method)(**request_kwargs)

            audio_payload = getattr(response, "content", None)
            if isinstance(audio_payload, bytes | bytearray):
                audio_bytes = bytes(audio_payload)
            else:
                audio_payload = getattr(response, "audio", audio_payload)
                if isinstance(audio_payload, bytes | bytearray):
                    audio_bytes = bytes(audio_payload)
                elif isinstance(audio_payload, str):
                    audio_bytes = base64.b64decode(audio_payload)
                else:
                    raise LLMError("Unsupported audio response format from OpenAI")

            audio_base64 = base64.b64encode(audio_bytes).decode("ascii")
            mime_type = "audio/mpeg" if request.audio_format == "mp3" else f"audio/{request.audio_format}"
            duration_seconds = self._estimate_audio_duration_seconds(request.text)

            audio_response = AudioResponse(
                audio_base64=audio_base64,
                mime_type=mime_type,
                voice=request.voice,
                model=request.model,
                cost_estimate=None,
                duration_seconds=duration_seconds,
            )

            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            with contextlib.suppress(Exception):
                llm_request.request_payload = request_kwargs
                llm_request.additional_params = {
                    "audio_format": request.audio_format,
                    "speed": request.speed,
                }

            self._update_audio_request_success(
                llm_request,
                audio_response,
                execution_time_ms,
                {"mime_type": mime_type, "voice": request.voice},
            )

            logger.info(
                "Generated audio narration - Model: %s Voice: %s Duration: %ss",
                request.model,
                request.voice,
                duration_seconds,
            )
            return audio_response, request_id

        except Exception as e:
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            if "llm_request" in locals():
                self._update_llm_request_error(llm_request, e, execution_time_ms)

            raise self._convert_exception(e) from e

    async def search_recent_news(
        self,
        search_queries: list[str],
        user_id: int | None = None,
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
        """Estimate cost from hardcoded GPT-5 family pricing (as of Sep 2025).

        Rates are USD per 1M tokens:
        - gpt-5: input $1.25, output $10.00
        - gpt-5-mini: input $0.25, output $2.00
        - gpt-5-nano: input $0.05, output $0.40
        """
        model_name = (model or self.config.model).lower()

        pricing_map: dict[str, tuple[float, float]] = {
            "gpt-5": (1.25, 10.00),
            "gpt-5-mini": (0.25, 2.00),
            "gpt-5-nano": (0.05, 0.40),
        }

        # Longest-prefix match
        best_key = None
        for key in pricing_map:
            if model_name.startswith(key) and (best_key is None or len(key) > len(best_key)):
                best_key = key

        if best_key is None:
            # Conservative fallback if unknown model: use gpt-5-mini
            best_key = "gpt-5-mini"

        input_rate, output_rate = pricing_map[best_key]
        input_cost = (prompt_tokens / 1000000.0) * input_rate
        output_cost = (completion_tokens / 1000000.0) * output_rate
        return input_cost + output_cost

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

    def _estimate_audio_duration_seconds(self, transcript: str) -> int:
        """Estimate narration duration based on transcript length."""

        words = re.findall(r"[\w']+", transcript)
        if not words:
            return 0

        estimated_minutes = len(words) / 165  # Approximate spoken words per minute
        return max(1, math.ceil(estimated_minutes * 60))

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
        return cast(float, min(delay, max_delay))

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
