"""OpenRouter provider implementation."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from typing import Any, TypeVar
import uuid

try:  # pragma: no cover - optional dependency guard
    import httpx

    _HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover - dependency missing
    httpx = None  # type: ignore[assignment]
    _HTTPX_AVAILABLE = False

from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import LLMConfig
from ..exceptions import (
    LLMAuthenticationError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from ..models import LLMRequestModel
from ..types import (
    AudioGenerationRequest,
    AudioResponse,
    ImageGenerationRequest,
    ImageResponse,
    LLMMessage,
    LLMProviderType,
    LLMResponse,
    WebSearchResponse,
)
from .base import LLMProvider

_LOGGER = logging.getLogger(__name__)

_OPENROUTER_CHAT_COMPLETIONS_PATH = "/chat/completions"

T = TypeVar("T", bound=BaseModel)

__all__ = ["OpenRouterProvider"]


class OpenRouterProvider(LLMProvider):
    """LLM provider that integrates with the OpenRouter unified API for chat completions."""

    def __init__(self, config: LLMConfig, db_session: Session) -> None:
        """Initialise the provider with configuration, credentials, and DB session."""

        super().__init__(config, db_session)

        if not _HTTPX_AVAILABLE:
            raise LLMAuthenticationError("httpx is required to use the OpenRouter provider")

        api_key = config.openrouter_api_key or config.api_key
        if not api_key:
            raise LLMAuthenticationError("OPENROUTER_API_KEY must be configured to use the OpenRouter provider")

        self._api_key = api_key
        self._base_url = (config.openrouter_base_url or config.base_url or "https://openrouter.ai/api/v1").rstrip("/")
        self._timeout = httpx.Timeout(config.timeout) if isinstance(config.timeout, int | float) else config.timeout

    async def generate_response(
        self,
        messages: list[LLMMessage],
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[LLMResponse, uuid.UUID]:
        """Generate a standard chat completion using OpenRouter.

        Args:
            messages: Conversation history to send to OpenRouter.
            user_id: Optional user identifier for auditing.
            **kwargs: Additional provider specific overrides (model, temperature, etc.).

        Returns:
            Tuple containing the normalised LLM response and the database request ID.
        """

        start_time = datetime.now(UTC)
        request_kwargs = dict(kwargs)
        model = request_kwargs.get("model", self.config.model)
        request_kwargs["model"] = model

        llm_request = self._create_llm_request(messages=messages, user_id=user_id, **request_kwargs)
        if llm_request.id is None:  # pragma: no cover - defensive guard
            raise LLMError("Failed to create LLM request record")
        request_id = llm_request.id

        payload = self._build_payload(messages, model, request_kwargs)
        self._store_request_payload(llm_request, payload)

        try:
            response_data = await self._post_json(_OPENROUTER_CHAT_COMPLETIONS_PATH, payload)
            llm_response, _usage_info = self._parse_completion_response(response_data, model)
            llm_response.response_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            self._update_llm_request_success(llm_request, llm_response, llm_response.response_time_ms or 0)

            return llm_response, request_id
        except Exception as exc:  # pragma: no cover - error path
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            self._update_llm_request_error(llm_request, exc, execution_time_ms)
            if isinstance(exc, LLMError):
                raise
            raise LLMError(f"OpenRouter request failed: {exc}") from exc

    async def generate_structured_object(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[T, uuid.UUID, dict[str, Any]]:
        """Generate a structured response validated against the provided Pydantic model.

        Args:
            messages: Conversation history to send to OpenRouter.
            response_model: Pydantic model the JSON response must satisfy.
            user_id: Optional user identifier for auditing.
            **kwargs: Additional provider specific overrides (model, temperature, etc.).

        Returns:
            The parsed model instance, database request ID, and usage metadata extracted from the response.
        """

        start_time = datetime.now(UTC)
        request_kwargs = dict(kwargs)
        model = request_kwargs.get("model", self.config.model)
        request_kwargs["model"] = model

        llm_request = self._create_llm_request(messages=messages, user_id=user_id, **request_kwargs)
        if llm_request.id is None:  # pragma: no cover - defensive guard
            raise LLMError("Failed to create LLM request record")
        request_id = llm_request.id

        payload = self._build_payload(messages, model, request_kwargs, response_model=response_model)
        self._store_request_payload(llm_request, payload)

        try:
            response_data = await self._post_json(_OPENROUTER_CHAT_COMPLETIONS_PATH, payload)
            llm_response, _usage_info = self._parse_completion_response(response_data, model)

            content_to_parse = self._prepare_structured_content(llm_response.content)
            try:
                parsed_payload = json.loads(content_to_parse)
            except json.JSONDecodeError as exc:
                raise LLMValidationError(f"OpenRouter structured response is not valid JSON: {exc}") from exc

            structured_obj = self._validate_structured_payload(response_model, parsed_payload)
            llm_response.response_output = parsed_payload
            llm_response.response_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            self._update_llm_request_success(llm_request, llm_response, llm_response.response_time_ms or 0)

            usage_details = {
                key: value
                for key, value in {
                    "prompt_tokens": llm_response.input_tokens,
                    "completion_tokens": llm_response.output_tokens,
                    "total_tokens": llm_response.tokens_used,
                    "cost_estimate": llm_response.cost_estimate,
                    "cached": llm_response.cached,
                    "cached_input_tokens": llm_response.cached_input_tokens,
                    "cache_creation_tokens": llm_response.cache_creation_tokens,
                }.items()
                if value is not None
            }

            return structured_obj, request_id, usage_details
        except Exception as exc:  # pragma: no cover - error path
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            self._update_llm_request_error(llm_request, exc, execution_time_ms)
            if isinstance(exc, LLMError):
                raise
            raise LLMError(f"OpenRouter structured request failed: {exc}") from exc

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[ImageResponse, uuid.UUID]:  # pragma: no cover - unsupported in Phase 1
        """Raise a placeholder error because OpenRouter image support is future work."""
        raise NotImplementedError("OpenRouter image generation is not implemented")

    async def generate_audio(
        self,
        request: AudioGenerationRequest,
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[AudioResponse, uuid.UUID]:  # pragma: no cover - unsupported in Phase 1
        """Raise a placeholder error because OpenRouter audio support is future work."""
        raise NotImplementedError("OpenRouter audio generation is not implemented")

    async def search_recent_news(
        self,
        search_queries: list[str],
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[WebSearchResponse, uuid.UUID]:  # pragma: no cover - unsupported in Phase 1
        """Raise a placeholder error because OpenRouter news search is future work."""
        raise NotImplementedError("OpenRouter web search is not implemented")

    def _build_payload(
        self,
        messages: list[LLMMessage],
        model: str | None,
        request_kwargs: dict[str, Any],
        *,
        response_model: type[BaseModel] | None = None,
    ) -> dict[str, Any]:
        """Construct the JSON payload for the OpenRouter chat completions endpoint."""

        message_payload = [self._message_to_dict(message) for message in messages]

        temperature = request_kwargs.get("temperature", self.config.temperature)
        max_output_tokens = request_kwargs.get("max_output_tokens", self.config.max_output_tokens)

        payload: dict[str, Any] = {
            "model": self._normalize_model_name(model or self.config.model),
            "messages": message_payload,
            "temperature": temperature,
        }

        if max_output_tokens is not None:
            payload["max_tokens"] = max_output_tokens

        if response_model is not None:
            schema = response_model.model_json_schema()
            schema_prompt = f"You must respond with a JSON object that strictly conforms to this schema: {json.dumps(schema)}"
            payload["messages"] = [
                {"role": "system", "content": schema_prompt},
                *message_payload,
            ]
            payload["response_format"] = {"type": "json_object"}

        return payload

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request to OpenRouter and return the JSON response."""

        if httpx is None:  # pragma: no cover - defensive guard
            raise LLMAuthenticationError("httpx is required to use the OpenRouter provider")

        url = f"{self._base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"OpenRouter request timed out: {exc}") from exc
        except httpx.RequestError as exc:
            raise LLMError(f"OpenRouter request failed: {exc}") from exc

        if response.status_code in {401, 403}:
            message = self._extract_error_message(response)
            raise LLMAuthenticationError(
                message or "OpenRouter rejected the request. Verify OPENROUTER_API_KEY permissions.",
            )
        if response.status_code == 429:
            retry_after_header = response.headers.get("Retry-After")
            retry_after = int(retry_after_header) if retry_after_header and retry_after_header.isdigit() else None
            raise LLMRateLimitError("OpenRouter rate limit exceeded", retry_after=retry_after)
        if response.status_code == 404:
            message = self._extract_error_message(response)
            raise LLMValidationError(
                message or "Requested OpenRouter model was not found",
            )
        if response.status_code == 400:
            message = self._extract_error_message(response)
            raise LLMValidationError(message or "OpenRouter rejected the request")
        if response.status_code >= 400:
            message = self._extract_error_message(response)
            raise LLMError(message or f"OpenRouter returned error {response.status_code}")

        try:
            return response.json()
        except ValueError as exc:
            raise LLMError("OpenRouter returned a non-JSON response") from exc

    def _parse_completion_response(
        self,
        data: dict[str, Any],
        requested_model: str | None,
    ) -> tuple[LLMResponse, dict[str, Any]]:
        """Transform OpenRouter response JSON into module response objects."""

        choices = data.get("choices") or []
        content: str = ""
        finish_reason: str | None = None
        if choices:
            choice = choices[0]
            finish_reason = choice.get("finish_reason")
            message = choice.get("message") or {}
            message_content = message.get("content")
            if isinstance(message_content, str):
                content = message_content
            elif isinstance(message_content, list):
                # OpenRouter can return streaming-style segments even in sync calls; coalesce them.
                content = "".join(part.get("text", "") for part in message_content if isinstance(part, dict))

        usage = data.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        if total_tokens is None and (prompt_tokens is not None or completion_tokens is not None):
            # Some OpenRouter models omit total tokens; derive it so downstream consumers stay informed.
            total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)

        cached_flag = usage.get("cached")
        # The cache metrics differ per upstream provider; normalise the key surface area we store.
        cached_input_tokens = usage.get("cached_input_tokens") or usage.get("cache_read_input_tokens") or usage.get("cache_read_tokens")
        cache_creation_tokens = usage.get("cache_creation_input_tokens") or usage.get("cache_creation_tokens")

        cost_raw = data.get("cost")
        # Cost metadata is OpenRouter-specific and may be a string or number depending on the upstream provider.
        cost_estimate = self._parse_cost(cost_raw)

        created_ts = data.get("created")
        created_dt: datetime | None = None
        if isinstance(created_ts, int | float):
            created_dt = datetime.fromtimestamp(created_ts, tz=UTC)

        response = LLMResponse(
            content=content,
            provider=LLMProviderType.OPENROUTER,
            model=requested_model or self.config.model,
            tokens_used=total_tokens,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            cost_estimate=cost_estimate,
            response_time_ms=None,
            cached=bool(cached_flag) if cached_flag is not None else bool(cached_input_tokens),
            provider_response_id=data.get("id"),
            system_fingerprint=data.get("system_fingerprint"),
            response_output=None,
            response_created_at=created_dt,
            finish_reason=finish_reason,
            cached_input_tokens=cached_input_tokens,
            cache_creation_tokens=cache_creation_tokens,
        )

        usage_info = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_estimate": cost_estimate,
            "cached": response.cached,
            "cached_input_tokens": cached_input_tokens,
            "cache_creation_tokens": cache_creation_tokens,
        }

        return response, usage_info

    @staticmethod
    def _extract_error_message(response: httpx.Response) -> str | None:
        """Return a human readable error message from an OpenRouter HTTP response."""

        try:
            payload = response.json()
        except ValueError:
            return response.text.strip() or None

        if isinstance(payload, dict):
            error_field = payload.get("error")
            if isinstance(error_field, dict):
                message = error_field.get("message") or error_field.get("description")
                if message:
                    return str(message)
            if isinstance(error_field, str):
                return error_field
            for key in ("message", "detail", "error_message"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value

        return response.text.strip() or None

    @staticmethod
    def _parse_cost(raw_cost: Any) -> float:
        """Normalise OpenRouter cost metadata to a float, defaulting to zero."""

        if isinstance(raw_cost, int | float):
            return float(raw_cost)
        if isinstance(raw_cost, str):
            stripped = raw_cost.strip()
            if stripped:
                try:
                    return float(stripped)
                except ValueError:  # pragma: no cover - defensive parsing guard
                    return 0.0
        return 0.0

    @staticmethod
    def _normalize_model_name(model: str) -> str:
        """Strip the `openrouter/` prefix before sending to the API."""

        if model.startswith("openrouter/"):
            return model.split("/", 1)[1]
        return model

    @staticmethod
    def _message_to_dict(message: LLMMessage) -> dict[str, Any]:
        """Convert internal message representation into OpenRouter payload format."""

        if hasattr(message, "to_dict"):
            return message.to_dict()
        return {"role": message.role.value, "content": message.content}

    @staticmethod
    def _store_request_payload(llm_request: LLMRequestModel, payload: dict[str, Any]) -> None:
        """Persist a simplified request payload for traceability."""

        try:
            llm_request.request_payload = payload
        except Exception:  # pragma: no cover - best effort logging
            _LOGGER.debug("Failed to persist OpenRouter request payload", exc_info=True)

    @staticmethod
    def _prepare_structured_content(content: str) -> str:
        """Normalise structured response content by stripping code fences."""

        text = content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    @staticmethod
    def _validate_structured_payload(model: type[T], payload: dict[str, Any]) -> T:
        """Validate parsed JSON payload against the provided Pydantic model."""

        if hasattr(model, "model_validate"):
            return model.model_validate(payload)  # type: ignore[return-value]
        if hasattr(model, "parse_obj"):
            return model.parse_obj(payload)  # type: ignore[return-value]
        return model(**payload)  # type: ignore[call-arg]
