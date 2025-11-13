"""Claude provider implementations for Anthropic and AWS Bedrock."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import importlib
import json
import logging
from typing import Any
import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import LLMConfig
from ..exceptions import (
    LLMAuthenticationError,
    LLMError,
    LLMRateLimitError,
    LLMValidationError,
)
from ..types import (
    AudioGenerationRequest,
    AudioResponse,
    AudioTranscriptionRequest,
    AudioTranscriptionResult,
    ImageGenerationRequest,
    ImageResponse,
    LLMMessage,
    LLMProviderType,
    LLMResponse,
    MessageRole,
    WebSearchResponse,
)
from .base import LLMProvider

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    _anthropic = importlib.import_module("anthropic")
    AsyncAnthropic = getattr(_anthropic, "AsyncAnthropic", None)
    AnthropIcAuthenticationError = getattr(_anthropic, "AuthenticationError", Exception)
    AnthropIcRateLimitError = getattr(_anthropic, "RateLimitError", Exception)
    AnthropIcAPIError = getattr(_anthropic, "APIError", Exception)
    _ANTHROPIC_AVAILABLE = AsyncAnthropic is not None
except Exception:  # pragma: no cover - guard when SDK missing
    AsyncAnthropic = None
    AnthropIcAuthenticationError = Exception
    AnthropIcRateLimitError = Exception
    AnthropIcAPIError = Exception
    _ANTHROPIC_AVAILABLE = False

try:  # pragma: no cover - optional dependency
    _boto3 = importlib.import_module("boto3")
    _botocore_exceptions = importlib.import_module("botocore.exceptions")
    _botocore_config = importlib.import_module("botocore.config")
    Boto3ClientError = getattr(_botocore_exceptions, "ClientError", Exception)
    Boto3BotoCoreError = getattr(_botocore_exceptions, "BotoCoreError", Exception)
    BotocoreConfig = getattr(_botocore_config, "Config", None)
    _BOTO3_AVAILABLE = True
except Exception:  # pragma: no cover
    _boto3 = None
    _botocore_config = None
    Boto3ClientError = Exception
    Boto3BotoCoreError = Exception
    BotocoreConfig = None
    _BOTO3_AVAILABLE = False


@dataclass(frozen=True)
class ClaudeModelConfig:
    """Configuration metadata for Claude models."""

    name: str
    anthropic_id: str
    bedrock_id: str
    context_window: int
    max_output_tokens: int
    input_cost_per_mtoken: float
    output_cost_per_mtoken: float


@dataclass
class ClaudeRequestResult:
    """Normalized result returned from provider implementations."""

    text: str
    input_tokens: int
    output_tokens: int
    model_id: str
    provider_response_id: str | None
    stop_reason: str | None
    raw_response: Any


_CLAUDE_MODEL_CONFIGS: dict[str, ClaudeModelConfig] = {
    "claude-haiku-4-5": ClaudeModelConfig(
        name="claude-haiku-4-5",
        anthropic_id="claude-haiku-4-5-20250219",
        bedrock_id="us.anthropic.claude-haiku-4-5-v1:0",
        context_window=200000,
        max_output_tokens=4096,
        input_cost_per_mtoken=1.0,
        output_cost_per_mtoken=5.0,
    ),
    "claude-sonnet-4-5": ClaudeModelConfig(
        name="claude-sonnet-4-5",
        anthropic_id="claude-sonnet-4-5-20250514",
        bedrock_id="us.anthropic.claude-sonnet-4-5-v1:0",
        context_window=200000,
        max_output_tokens=8192,
        input_cost_per_mtoken=3.0,
        output_cost_per_mtoken=15.0,
    ),
    "claude-opus-4-1": ClaudeModelConfig(
        name="claude-opus-4-1",
        anthropic_id="claude-opus-4-1-20250115",
        bedrock_id="us.anthropic.claude-opus-4-1-v1:0",
        context_window=200000,
        max_output_tokens=8192,
        input_cost_per_mtoken=15.0,
        output_cost_per_mtoken=75.0,
    ),
}


__all__ = [
    "AnthropicProvider",
    "BedrockProvider",
    "ClaudeModelConfig",
    "ClaudeRequestResult",
    "convert_to_claude_messages",
    "estimate_claude_cost",
    "get_claude_model_config",
    "parse_claude_response",
]


def get_claude_model_config(model: str) -> ClaudeModelConfig:
    """Return configuration metadata for a Claude model."""

    key = model.strip().lower()
    if key not in _CLAUDE_MODEL_CONFIGS:
        raise LLMValidationError(f"Unsupported Claude model: {model}")
    return _CLAUDE_MODEL_CONFIGS[key]


def estimate_claude_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate Claude request cost based on token usage."""

    config = get_claude_model_config(model)
    input_cost = (input_tokens / 1_000_000) * config.input_cost_per_mtoken
    output_cost = (output_tokens / 1_000_000) * config.output_cost_per_mtoken
    return round(input_cost + output_cost, 6)


def _ensure_iterable(value: Any) -> Iterable[Any]:
    if value is None:
        return []
    if isinstance(value, Iterable) and not isinstance(value, str | bytes | dict):
        return value
    return [value]


def parse_claude_response(response_content: Any) -> str:
    """Extract the textual response from Claude response payloads."""

    if response_content is None:
        return ""
    if isinstance(response_content, str):
        return response_content
    if isinstance(response_content, dict):
        if "text" in response_content:
            return str(response_content["text"])
        if "output" in response_content:
            return parse_claude_response(response_content["output"])
        if "message" in response_content:
            return parse_claude_response(response_content["message"])
        if "content" in response_content:
            return "".join(parse_claude_response(part) for part in _ensure_iterable(response_content["content"]))
        return "".join(parse_claude_response(value) for value in response_content.values())
    if isinstance(response_content, Sequence):
        return "".join(parse_claude_response(item) for item in response_content)
    if hasattr(response_content, "text"):
        return parse_claude_response({"text": response_content.text})
    return str(response_content)


def convert_to_claude_messages(messages: list[LLMMessage]) -> tuple[str | None, list[dict[str, Any]]]:
    """Convert internal LLM messages into Claude request payloads."""

    system_messages: list[str] = []
    claude_messages: list[dict[str, Any]] = []

    for message in messages:
        if message.role is MessageRole.SYSTEM:
            system_messages.append(message.content)
            continue

        role = "assistant" if message.role is MessageRole.ASSISTANT else "user"
        content_blocks: list[dict[str, Any]] = []
        if message.content:
            content_blocks.append({"type": "text", "text": message.content})
        if message.tool_calls:
            content_blocks.append({"type": "tool_result", "tool_calls": message.tool_calls})
        claude_messages.append({"role": role, "content": content_blocks})

    system_prompt = "\n\n".join(system_messages) if system_messages else None
    return system_prompt, claude_messages


def _to_serializable(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, str | int | float | bool):
        return obj
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_serializable(item) for item in obj]
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:  # pragma: no cover - defensive
            return str(obj)
    if hasattr(obj, "dict"):
        try:
            return obj.dict()
        except Exception:  # pragma: no cover - defensive
            return str(obj)
    return str(obj)


class ClaudeProviderBase(LLMProvider):
    """Shared helpers for Claude providers."""

    provider_type: LLMProviderType

    def __init__(self, config: LLMConfig, db_session: Session) -> None:
        super().__init__(config, db_session)
        self.provider_type = config.provider

    async def _execute_request(
        self,
        *,
        model_config: ClaudeModelConfig,
        messages: list[dict[str, Any]],
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> ClaudeRequestResult:
        raise NotImplementedError

    async def _generate(
        self,
        messages: list[LLMMessage],
        user_id: int | None,
        is_structured: bool = False,
        response_model: type[BaseModel] | None = None,
        **kwargs: Any,
    ) -> tuple[Any, uuid.UUID, dict[str, Any]]:
        model_name = (kwargs.get("model") or self.config.model).strip()
        config = get_claude_model_config(model_name)
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_output_tokens") or self.config.max_output_tokens or config.max_output_tokens

        system_prompt, payload_messages = convert_to_claude_messages(messages)
        if is_structured and response_model is not None:
            schema = response_model.model_json_schema() if hasattr(response_model, "model_json_schema") else response_model.schema()
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": schema,
                },
            }
            extra_system = "You must respond with a strict JSON object that matches the provided schema. Do not include any additional commentary or markdown."
            system_prompt = f"{system_prompt}\n\n{extra_system}" if system_prompt else extra_system
        else:
            response_format = None

        llm_request = self._create_llm_request(
            messages=messages,
            user_id=user_id,
            model=model_name,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if llm_request.id is None:  # pragma: no cover - defensive
            raise LLMError("Failed to create LLM request record")
        request_id: uuid.UUID = llm_request.id

        start_time = datetime.now(UTC)

        try:
            result = await self._execute_request(
                model_config=config,
                messages=payload_messages,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format,
            )
        except Exception as exc:
            elapsed = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            self._update_llm_request_error(llm_request, exc, elapsed)
            raise

        response_time = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        cost_estimate = estimate_claude_cost(config.name, result.input_tokens, result.output_tokens)

        llm_response = LLMResponse(
            content=result.text,
            provider=self.provider_type,
            model=model_name,
            tokens_used=result.input_tokens + result.output_tokens,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_estimate=cost_estimate,
            response_time_ms=response_time,
            cached=False,
            provider_response_id=result.provider_response_id,
            response_created_at=datetime.now(UTC),
            finish_reason=result.stop_reason,
            response_output=result.raw_response if is_structured else None,
        )

        self._update_llm_request_success(llm_request, llm_response, response_time)

        usage_info = {
            "tokens_used": llm_response.tokens_used or 0,
            "cost_estimate": cost_estimate,
        }

        if is_structured and response_model is not None:
            try:
                # Strip markdown code blocks if present
                text_to_parse = result.text.strip()
                if text_to_parse.startswith("```json"):
                    text_to_parse = text_to_parse[7:]  # Remove ```json
                elif text_to_parse.startswith("```"):
                    text_to_parse = text_to_parse[3:]  # Remove ```
                if text_to_parse.endswith("```"):
                    text_to_parse = text_to_parse[:-3]  # Remove trailing ```
                text_to_parse = text_to_parse.strip()

                logger.info(f"Parsing structured response (length: {len(text_to_parse)}, first 200 chars): {text_to_parse[:200]}")
                parsed_payload = json.loads(text_to_parse)
                structured_obj = response_model(**parsed_payload)
            except json.JSONDecodeError as exc:
                logger.error(f"Failed to parse JSON. Raw text: {result.text[:500]}")
                raise LLMValidationError(f"Claude response was not valid JSON: {exc}") from exc
            except Exception as exc:
                logger.error(f"Failed to create structured object. Parsed payload keys: {list(parsed_payload.keys()) if 'parsed_payload' in locals() else 'N/A'}")
                raise LLMValidationError(f"Failed to parse Claude response: {exc}") from exc
            return structured_obj, request_id, usage_info

        return llm_response, request_id, usage_info

    async def generate_response(
        self,
        messages: list[LLMMessage],
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[LLMResponse, uuid.UUID]:
        response, request_id, _ = await self._generate(messages, user_id, **kwargs)
        assert isinstance(response, LLMResponse)
        return response, request_id

    async def generate_structured_object(
        self,
        messages: list[LLMMessage],
        response_model: type[BaseModel],
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[BaseModel, uuid.UUID, dict[str, Any]]:
        structured_obj, request_id, usage = await self._generate(
            messages,
            user_id,
            is_structured=True,
            response_model=response_model,
            **kwargs,
        )
        assert isinstance(structured_obj, BaseModel)
        return structured_obj, request_id, usage

    async def generate_image(
        self,
        request: ImageGenerationRequest,
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[ImageResponse, uuid.UUID]:  # pragma: no cover - not supported
        raise NotImplementedError("Claude providers do not support image generation")

    async def generate_audio(
        self,
        request: AudioGenerationRequest,
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[AudioResponse, uuid.UUID]:  # pragma: no cover - not supported
        raise NotImplementedError("Claude providers do not support audio generation")

    async def transcribe_audio(
        self,
        request: AudioTranscriptionRequest,
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[AudioTranscriptionResult, uuid.UUID]:  # pragma: no cover - not supported
        raise NotImplementedError("Claude providers do not support audio transcription")

    async def search_recent_news(
        self,
        search_queries: list[str],
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[WebSearchResponse, uuid.UUID]:  # pragma: no cover - not supported
        raise NotImplementedError("Claude providers do not support web search")

    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str | None = None,
    ) -> float:
        target_model = model or self.config.model
        return estimate_claude_cost(target_model, prompt_tokens, completion_tokens)


class AnthropicProvider(ClaudeProviderBase):
    """Claude provider using Anthropic's native API."""

    def __init__(self, config: LLMConfig, db_session: Session) -> None:
        super().__init__(config, db_session)
        self.provider_type = LLMProviderType.ANTHROPIC
        self._client: Any | None = None
        # Check SDK availability at initialization time
        if not _ANTHROPIC_AVAILABLE or AsyncAnthropic is None:
            raise LLMAuthenticationError("Anthropic SDK is not installed. Please install 'anthropic'.")
        logger.info("AnthropicProvider initialized")

    def _ensure_client(self) -> Any:
        if not _ANTHROPIC_AVAILABLE or AsyncAnthropic is None:
            raise LLMAuthenticationError("Anthropic SDK is not installed. Please install 'anthropic'.")
        if self._client is None:
            api_key = self.config.anthropic_api_key or self.config.api_key
            if not api_key:
                raise LLMAuthenticationError("Anthropic API key is not configured")
            try:
                self._client = AsyncAnthropic(api_key=api_key, timeout=self.config.timeout, max_retries=self.config.max_retries)
            except Exception as exc:  # pragma: no cover - network failure
                raise LLMAuthenticationError(f"Failed to initialize Anthropic client: {exc}") from exc
        return self._client

    async def _execute_request(
        self,
        *,
        model_config: ClaudeModelConfig,
        messages: list[dict[str, Any]],
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> ClaudeRequestResult:
        client = self._ensure_client()

        request_params: dict[str, Any] = {
            "model": model_config.anthropic_id,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }
        if system_prompt:
            request_params["system"] = system_prompt
        if response_format is not None:
            request_params["response_format"] = response_format

        try:
            response = await client.messages.create(**request_params)
        except AnthropIcAuthenticationError as exc:
            raise LLMAuthenticationError(str(exc)) from exc
        except AnthropIcRateLimitError as exc:
            raise LLMRateLimitError(str(exc)) from exc
        except AnthropIcAPIError as exc:
            raise LLMError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise LLMError(f"Anthropic request failed: {exc}") from exc

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None) or 0
        output_tokens = getattr(usage, "output_tokens", None) or 0
        stop_reason = getattr(response, "stop_reason", None)
        content = parse_claude_response(getattr(response, "content", None))

        return ClaudeRequestResult(
            text=content,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            model_id=model_config.anthropic_id,
            provider_response_id=getattr(response, "id", None),
            stop_reason=stop_reason,
            raw_response=_to_serializable(response),
        )


class BedrockProvider(ClaudeProviderBase):
    """Claude provider implementation using AWS Bedrock."""

    def __init__(self, config: LLMConfig, db_session: Session) -> None:
        super().__init__(config, db_session)
        self.provider_type = LLMProviderType.BEDROCK
        self._client: Any | None = None
        logger.info(f"BedrockProvider initialized (region: {config.aws_region}, model_id: {config.bedrock_model_id})")

    def _ensure_client(self) -> Any:
        if not _BOTO3_AVAILABLE or _boto3 is None:
            raise LLMAuthenticationError("boto3 is required for AWS Bedrock access")
        if self._client is None:
            client_kwargs: dict[str, Any] = {
                "region_name": self.config.aws_region or "us-west-2",
            }

            # Configure adaptive retry mode for better throttling handling
            if BotocoreConfig is not None:
                retry_config = BotocoreConfig(
                    retries={
                        "max_attempts": 10,  # More retry attempts for throttling
                        "mode": "adaptive",  # Adaptive mode learns from throttling patterns
                    }
                )
                client_kwargs["config"] = retry_config
                logger.info("Bedrock client configured with adaptive retry mode (max 10 attempts)")

            if self.config.aws_access_key_id and self.config.aws_secret_access_key:
                client_kwargs["aws_access_key_id"] = self.config.aws_access_key_id
                client_kwargs["aws_secret_access_key"] = self.config.aws_secret_access_key
            if self.config.aws_session_token:
                client_kwargs["aws_session_token"] = self.config.aws_session_token
            try:
                self._client = _boto3.client("bedrock-runtime", **client_kwargs)
            except Exception as exc:  # pragma: no cover - network failure
                raise LLMAuthenticationError(f"Failed to initialize Bedrock client: {exc}") from exc
        return self._client

    async def _execute_request(
        self,
        *,
        model_config: ClaudeModelConfig,
        messages: list[dict[str, Any]],
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
        response_format: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> ClaudeRequestResult:
        client = self._ensure_client()
        model_id = self.config.bedrock_model_id or model_config.bedrock_id

        logger.info(f"Invoking Bedrock model: '{model_id}' (region: {self.config.aws_region})")
        logger.debug(f"Model config name: '{model_config.name}', bedrock_id: '{model_config.bedrock_id}'")
        if self.config.bedrock_model_id:
            logger.debug(f"Using explicit bedrock_model_id from config: '{self.config.bedrock_model_id}'")

        payload: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt
        # Note: Bedrock doesn't support response_format parameter

        async def _invoke() -> dict[str, Any]:
            try:
                response = await asyncio.to_thread(
                    client.invoke_model,
                    modelId=model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(payload).encode("utf-8"),
                )
            except (Boto3ClientError, Boto3BotoCoreError) as exc:
                error_code = getattr(exc, "response", {}).get("Error", {}).get("Code", "bedrock_error")
                error_message = getattr(exc, "response", {}).get("Error", {}).get("Message", str(exc))

                if error_code == "ValidationException":
                    logger.error(
                        f"Bedrock model validation error for '{model_id}' in region '{self.config.aws_region}': {error_message}\n"
                        f"This usually means:\n"
                        f"  1. The model isn't available in this region\n"
                        f"  2. You haven't requested model access in AWS Bedrock console\n"
                        f"  3. The model ID is incorrect\n"
                        f"To fix: Visit AWS Bedrock console → Model access → Request access for Claude models"
                    )
                    raise LLMValidationError(f"Invalid Bedrock model '{model_id}': {error_message}") from exc

                if error_code in {"ThrottlingException", "TooManyRequestsException"}:
                    raise LLMRateLimitError(str(exc)) from exc
                raise LLMError(f"{error_code}: {error_message}") from exc
            except Exception as exc:  # pragma: no cover - defensive
                raise LLMError(f"Bedrock invocation failed: {exc}") from exc

            body = response.get("body")
            raw = body.read() if hasattr(body, "read") else body
            try:
                return json.loads(raw)
            except Exception as exc:  # pragma: no cover - defensive
                raise LLMError(f"Invalid Bedrock response body: {exc}") from exc

        result_payload = await _invoke()
        logger.debug(f"Bedrock response keys: {list(result_payload.keys())}")

        # Log full payload
        try:
            full_payload_str = json.dumps(result_payload, indent=2, default=str)
            logger.info(f"Bedrock FULL response payload:\n{full_payload_str}")
        except Exception as e:
            logger.error(f"Could not serialize payload: {e}")

        usage = result_payload.get("usage", {})
        input_tokens = int(usage.get("input_tokens") or usage.get("inputTokens") or 0)
        output_tokens = int(usage.get("output_tokens") or usage.get("outputTokens") or 0)
        stop_reason = result_payload.get("stop_reason") or result_payload.get("stopReason")
        text = parse_claude_response(result_payload.get("output") or result_payload.get("content"))
        logger.info(f"Extracted text from Bedrock (first 500 chars): {text[:500] if text else '(empty)'}")

        provider_response_id = result_payload.get("id") or result_payload.get("response_id")
        if provider_response_id is None:
            metadata = result_payload.get("ResponseMetadata") or {}
            provider_response_id = metadata.get("RequestId")

        return ClaudeRequestResult(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_id=model_id,
            provider_response_id=provider_response_id,
            stop_reason=stop_reason,
            raw_response=result_payload,
        )
