"""Gemini provider implementation."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from datetime import UTC, datetime
from typing import Any, Mapping
import uuid

try:  # pragma: no cover - optional dependency
    import httpx
    _HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover - guard when httpx is missing
    httpx = None  # type: ignore[assignment]
    _HTTPX_AVAILABLE = False

from sqlalchemy.orm import Session

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
    LLMProviderType,
    LLMResponse,
    MessageRole,
    WebSearchResponse,
)
from .base import LLMProvider

_GEMINI_BASE_URL_DEFAULT = "https://generativelanguage.googleapis.com/v1beta"

# Pricing map (USD per 1M tokens) derived from https://ai.google.dev/gemini-api/docs/pricing
_GEMINI_PRICING: Mapping[str, tuple[float, float]] = {
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.5-pro-preview": (1.25, 10.00),
    "gemini-2.5-pro-preview-tts": (1.00, 20.00),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-preview": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-flash-lite-preview": (0.10, 0.40),
    "gemini-2.5-flash-native-audio": (3.00, 12.00),
    "gemini-2.5-flash-preview-tts": (0.50, 10.00),
    "gemini-2.5-computer-use-preview": (1.25, 10.00),
}

__all__ = ["GeminiProvider"]


class GeminiProvider(LLMProvider):
    """Gemini provider supporting text, image, and audio generation."""

    def __init__(self, config: LLMConfig, db_session: Session) -> None:
        super().__init__(config, db_session)
        if not config.api_key:
            raise LLMAuthenticationError("GEMINI_API_KEY must be configured to use the Gemini provider")
        if not _HTTPX_AVAILABLE:
            raise LLMAuthenticationError("httpx is required to use the Gemini provider")

        self._base_url = (config.base_url or _GEMINI_BASE_URL_DEFAULT).rstrip("/")
        self._logger = logging.getLogger(__name__)

    # ---------------------------------------------------------------------
    # Core helpers
    # ---------------------------------------------------------------------
    async def _post(
        self,
        model: str,
        payload: dict[str, Any],
        endpoint: str = "generateContent",
    ) -> dict[str, Any]:
        """Send a POST request to the Gemini API and return JSON payload."""

        if httpx is None:  # pragma: no cover - defensive guard
            raise LLMAuthenticationError("httpx is not available in this environment")

        url = f"{self._base_url}/models/{model}:{endpoint}"
        params = {"key": self.config.api_key}
        timeout = httpx.Timeout(self.config.timeout) if isinstance(self.config.timeout, (int, float)) else self.config.timeout

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, params=params, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - http failure
            raise self._convert_http_error(exc) from exc
        except httpx.TimeoutException as exc:  # pragma: no cover - timeout
            raise LLMTimeoutError(f"Gemini request timed out: {exc}") from exc
        except httpx.RequestError as exc:  # pragma: no cover - network failure
            raise LLMError(f"Gemini request failed: {exc}") from exc

        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - unexpected payload
            raise LLMError("Gemini returned a non-JSON response") from exc

    def _convert_http_error(self, exc: "httpx.HTTPStatusError") -> Exception:
        """Map HTTP status codes to module-specific exceptions."""

        status = exc.response.status_code
        if status in {401, 403}:
            return LLMAuthenticationError("Gemini API rejected the request. Check GEMINI_API_KEY permissions.")
        if status == 429:
            return LLMRateLimitError("Gemini rate limit exceeded")
        if status in {408, 504}:
            return LLMTimeoutError("Gemini request timed out")
        if status in {400, 422}:
            return LLMValidationError(f"Gemini request validation failed: {exc.response.text}")
        return LLMError(f"Gemini request failed with status {status}: {exc.response.text}")

    def _convert_messages(
        self, messages: list[LLMMessage]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert internal messages into Gemini payload format."""

        system_parts: list[str] = []
        contents: list[dict[str, Any]] = []

        for message in messages:
            if message.role is MessageRole.SYSTEM:
                if isinstance(message.content, str):
                    system_parts.append(message.content)
                else:
                    system_parts.append(json.dumps(message.content))
                continue

            role = "user"
            if message.role is MessageRole.ASSISTANT:
                role = "model"

            parts = self._convert_content_parts(message.content)
            contents.append({"role": role, "parts": parts})

        system_instruction = "\n".join(part.strip() for part in system_parts if part)
        return (system_instruction or None, contents)

    def _convert_content_parts(self, content: Any) -> list[dict[str, Any]]:
        """Normalize message content into Gemini parts."""

        parts: list[dict[str, Any]] = []
        if isinstance(content, str):
            parts.append({"text": content})
            return parts

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    part_type = item.get("type")
                    if part_type in {"text", "input_text"}:
                        text_value = item.get("text") or item.get("content")
                        if text_value:
                            parts.append({"text": text_value})
                        continue
                    if part_type in {"image", "input_image", "image_url"}:
                        image_info = item.get("image") or item.get("image_url")
                        if isinstance(image_info, dict):
                            uri = image_info.get("url") or image_info.get("source")
                            if uri:
                                parts.append(self._convert_image_reference(uri))
                        continue
                    # Fallback for unknown types: convert to JSON text
                    parts.append({"text": json.dumps(item)})
                else:
                    parts.append({"text": str(item)})
            return parts or [{"text": ""}]

        # Fallback for unrecognised content types
        parts.append({"text": json.dumps(content) if not isinstance(content, str) else content})
        return parts

    def _convert_image_reference(self, uri: str) -> dict[str, Any]:
        """Convert an image reference into Gemini inline data or file reference."""

        if uri.startswith("data:"):
            header, _, data = uri.partition(",")
            mime_type = "image/png"
            if ";" in header:
                mime_part = header.split(";", 1)[0]
                mime_type = mime_part.replace("data:", "") or mime_type
            base64_data = data
            return {"inlineData": {"mimeType": mime_type, "data": base64_data}}

        return {"fileData": {"fileUri": uri}}

    def _split_generation_kwargs(self, kwargs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Separate generationConfig values from top-level overrides."""

        generation_config: dict[str, Any] = {}
        payload_overrides: dict[str, Any] = {}

        for key, value in kwargs.items():
            if value is None:
                continue
            if key in {"top_p", "top_k", "candidate_count", "stop_sequences", "presence_penalty", "frequency_penalty", "response_mime_type"}:
                generation_config[key] = value
            elif key == "safety_settings":
                payload_overrides["safetySettings"] = value
            else:
                payload_overrides[key] = value
        return generation_config, payload_overrides

    def _build_payload(
        self,
        messages: list[LLMMessage],
        temperature: float | None,
        max_output_tokens: int | None,
        generation_overrides: dict[str, Any] | None,
        payload_overrides: dict[str, Any] | None,
    ) -> dict[str, Any]:
        system_instruction, contents = self._convert_messages(messages)
        payload: dict[str, Any] = {"contents": contents}

        generation_config: dict[str, Any] = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_output_tokens is not None:
            generation_config["max_output_tokens"] = max_output_tokens
        if generation_overrides:
            generation_config.update(generation_overrides)
        if generation_config:
            payload["generationConfig"] = generation_config

        if system_instruction:
            payload["systemInstruction"] = {
                "role": "system",
                "parts": [{"text": system_instruction}],
            }

        if payload_overrides:
            payload.update(payload_overrides)

        return payload

    def _extract_text_response(self, response: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]] | None]:
        """Extract textual content and raw parts from Gemini response."""

        candidates = response.get("candidates") or []
        full_text_parts: list[str] = []
        response_parts: list[dict[str, Any]] | None = None

        for candidate in candidates:
            content = candidate.get("content") or {}
            parts = content.get("parts") or []
            if response_parts is None and isinstance(parts, list):
                response_parts = parts
            for part in parts:
                text_value = part.get("text") if isinstance(part, dict) else None
                if text_value:
                    full_text_parts.append(text_value)

        return "".join(full_text_parts).strip(), response_parts

    def _extract_usage(self, response: Mapping[str, Any]) -> tuple[int | None, int | None, int | None]:
        usage = response.get("usageMetadata") or {}
        input_tokens = usage.get("promptTokenCount")
        output_tokens = usage.get("candidatesTokenCount")
        total_tokens = usage.get("totalTokenCount")
        if total_tokens is None and (input_tokens is not None or output_tokens is not None):
            total_tokens = (input_tokens or 0) + (output_tokens or 0)
        return total_tokens, input_tokens, output_tokens

    def _parse_timestamp(self, value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value.astimezone(UTC)
        if isinstance(value, str):
            try:
                normalized = value.replace("Z", "+00:00")
                return datetime.fromisoformat(normalized).astimezone(UTC)
            except ValueError:
                return None
        return None

    # ------------------------------------------------------------------
    # Text and structured generation
    # ------------------------------------------------------------------
    async def generate_response(
        self,
        messages: list[LLMMessage],
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[LLMResponse, uuid.UUID]:
        start_time = datetime.now(UTC)
        model = kwargs.pop("model", None) or self.config.model
        temperature = kwargs.pop("temperature", None)
        max_output_tokens = kwargs.pop("max_output_tokens", None)
        extra_generation, payload_overrides = self._split_generation_kwargs(kwargs)

        try:
            llm_request = self._create_llm_request(
                messages=messages,
                user_id=user_id,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            if llm_request.id is None:  # pragma: no cover - defensive guard
                raise LLMError("Failed to create LLM request record")
            request_id: uuid.UUID = llm_request.id

            payload = self._build_payload(
                messages,
                temperature,
                max_output_tokens,
                extra_generation,
                payload_overrides,
            )

            response_data = await self._post(model, payload)

            content, response_parts = self._extract_text_response(response_data)
            total_tokens, input_tokens, output_tokens = self._extract_usage(response_data)
            cost_estimate = self.estimate_cost(input_tokens or 0, output_tokens or 0, model)
            created_at = self._parse_timestamp(response_data.get("createTime"))

            llm_response = LLMResponse(
                content=content,
                provider=LLMProviderType.GEMINI,
                model=model,
                tokens_used=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_estimate=cost_estimate,
                response_time_ms=int((datetime.now(UTC) - start_time).total_seconds() * 1000),
                cached=False,
                provider_response_id=response_data.get("responseId"),
                response_output=response_parts,
                response_created_at=created_at,
            )

            with contextlib.suppress(Exception):  # pragma: no cover - best effort persistence
                llm_request.request_payload = payload
                llm_request.response_raw = response_data

            self._update_llm_request_success(
                llm_request,
                llm_response,
                llm_response.response_time_ms or 0,
            )

            return llm_response, request_id

        except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
            raise
        except Exception as exc:
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            if "llm_request" in locals():
                self._update_llm_request_error(llm_request, exc, execution_time_ms)
            if isinstance(exc, (LLMError, LLMAuthenticationError, LLMRateLimitError, LLMTimeoutError, LLMValidationError)):
                raise
            raise LLMError(f"Gemini text generation failed: {exc}") from exc

    async def generate_structured_object(
        self,
        messages: list[LLMMessage],
        response_model: type[Any],
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[Any, uuid.UUID, dict[str, Any]]:
        start_time = datetime.now(UTC)
        model = kwargs.pop("model", None) or self.config.model
        temperature = kwargs.pop("temperature", None)
        max_output_tokens = kwargs.pop("max_output_tokens", None)
        extra_generation, payload_overrides = self._split_generation_kwargs(kwargs)
        extra_generation["response_mime_type"] = "application/json"

        try:
            llm_request = self._create_llm_request(
                messages=messages,
                user_id=user_id,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            if llm_request.id is None:  # pragma: no cover - defensive guard
                raise LLMError("Failed to create LLM request record")
            request_id: uuid.UUID = llm_request.id

            payload = self._build_payload(
                messages,
                temperature,
                max_output_tokens,
                extra_generation,
                payload_overrides,
            )

            response_data = await self._post(model, payload)
            content, response_parts = self._extract_text_response(response_data)
            if not content:
                raise LLMValidationError("Gemini returned an empty structured response")

            try:
                parsed_payload = json.loads(content)
                structured_obj = response_model(**parsed_payload)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise LLMValidationError(f"Failed to parse structured Gemini response: {exc}") from exc

            total_tokens, input_tokens, output_tokens = self._extract_usage(response_data)
            cost_estimate = self.estimate_cost(input_tokens or 0, output_tokens or 0, model)
            created_at = self._parse_timestamp(response_data.get("createTime"))

            llm_response = LLMResponse(
                content=content,
                provider=LLMProviderType.GEMINI,
                model=model,
                tokens_used=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_estimate=cost_estimate,
                response_time_ms=int((datetime.now(UTC) - start_time).total_seconds() * 1000),
                cached=False,
                provider_response_id=response_data.get("responseId"),
                response_output=response_parts,
                response_created_at=created_at,
            )

            with contextlib.suppress(Exception):  # pragma: no cover - best effort persistence
                llm_request.request_payload = payload
                llm_request.response_raw = response_data

            self._update_llm_request_success(
                llm_request,
                llm_response,
                llm_response.response_time_ms or 0,
            )

            usage_info = {
                "tokens_used": total_tokens or 0,
                "cost_estimate": cost_estimate,
            }
            return structured_obj, request_id, usage_info

        except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
            raise
        except Exception as exc:
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            if "llm_request" in locals():
                self._update_llm_request_error(llm_request, exc, execution_time_ms)
            if isinstance(exc, (LLMError, LLMAuthenticationError, LLMRateLimitError, LLMTimeoutError, LLMValidationError)):
                raise
            raise LLMError(f"Gemini structured generation failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Image generation
    # ------------------------------------------------------------------
    async def generate_image(
        self,
        request: ImageGenerationRequest,
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[ImageResponse, uuid.UUID]:
        start_time = datetime.now(UTC)
        model = self.config.image_model or "gemini-2.5-flash-image"
        messages = [LLMMessage(role=MessageRole.USER, content=request.prompt)]

        try:
            llm_request = self._create_llm_request(
                messages=messages,
                user_id=user_id,
                model=model,
            )
            if llm_request.id is None:  # pragma: no cover - defensive guard
                raise LLMError("Failed to create LLM request record")
            request_id: uuid.UUID = llm_request.id

            extra_generation, payload_overrides = self._split_generation_kwargs(kwargs)
            extra_generation.setdefault("response_mime_type", "image/png")
            payload = self._build_payload(messages, None, None, extra_generation, payload_overrides)

            response_data = await self._post(model, payload)
            with contextlib.suppress(Exception):  # pragma: no cover - best effort persistence
                llm_request.request_payload = payload
                llm_request.response_raw = response_data
            candidates = response_data.get("candidates") or []
            image_data = None
            for candidate in candidates:
                parts = ((candidate.get("content") or {}).get("parts") or [])
                for part in parts:
                    inline_data = part.get("inlineData") if isinstance(part, dict) else None
                    if inline_data:
                        image_data = inline_data
                        break
                if image_data:
                    break

            if not image_data:
                raise LLMError("Gemini did not return image data")

            mime_type = image_data.get("mimeType", "image/png")
            encoded_image = image_data.get("data")
            if not isinstance(encoded_image, str):
                raise LLMError("Gemini returned malformed image data")

            image_url = f"data:{mime_type};base64,{encoded_image}"
            cost_estimate = 0.039 * request.n  # Price per image from pricing docs

            image_response = ImageResponse(
                image_url=image_url,
                revised_prompt=None,
                size=request.size.value,
                cost_estimate=round(cost_estimate, 6),
            )

            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            self._update_image_request_success(
                llm_request,
                image_response,
                execution_time_ms,
                response_raw=response_data,
            )
            return image_response, request_id

        except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
            raise
        except Exception as exc:
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            if "llm_request" in locals():
                self._update_llm_request_error(llm_request, exc, execution_time_ms)
            if isinstance(exc, (LLMError, LLMAuthenticationError, LLMRateLimitError, LLMTimeoutError, LLMValidationError)):
                raise
            raise LLMError(f"Gemini image generation failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Audio generation (TTS)
    # ------------------------------------------------------------------
    async def generate_audio(
        self,
        request: AudioGenerationRequest,
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[AudioResponse, uuid.UUID]:
        start_time = datetime.now(UTC)
        model = request.model or self.config.audio_model or "gemini-2.5-flash-preview-tts"
        messages = [LLMMessage(role=MessageRole.USER, content=request.text)]

        try:
            llm_request = self._create_llm_request(
                messages=messages,
                user_id=user_id,
                model=model,
                temperature=0.0,
            )
            if llm_request.id is None:  # pragma: no cover - defensive guard
                raise LLMError("Failed to create LLM request record")
            request_id: uuid.UUID = llm_request.id

            extra_generation, payload_overrides = self._split_generation_kwargs(kwargs)
            mime_type = f"audio/{request.audio_format}"
            extra_generation.setdefault("response_mime_type", mime_type)
            if request.voice:
                extra_generation.setdefault("voice_config", {"prebuilt_voice": request.voice})
            if request.speed is not None:
                extra_generation.setdefault("speaking_rate", request.speed)
            payload_overrides.setdefault("responseModalities", ["AUDIO"])

            payload = self._build_payload(messages, None, None, extra_generation, payload_overrides)
            response_data = await self._post(model, payload)
            with contextlib.suppress(Exception):  # pragma: no cover - best effort persistence
                llm_request.request_payload = payload
                llm_request.response_raw = response_data

            candidates = response_data.get("candidates") or []
            audio_payload = None
            for candidate in candidates:
                parts = ((candidate.get("content") or {}).get("parts") or [])
                for part in parts:
                    inline_data = part.get("inlineData") if isinstance(part, dict) else None
                    if inline_data and inline_data.get("mimeType", "").startswith("audio/"):
                        audio_payload = inline_data
                        break
                if audio_payload:
                    break

            if not audio_payload:
                raise LLMError("Gemini did not return audio data")

            encoded_audio = audio_payload.get("data")
            mime_type = audio_payload.get("mimeType", mime_type)
            if not isinstance(encoded_audio, str):
                raise LLMError("Gemini returned malformed audio data")

            total_tokens, input_tokens, output_tokens = self._extract_usage(response_data)
            inferred_prompt_tokens = input_tokens if input_tokens is not None else len(request.text) // 4
            inferred_completion_tokens = output_tokens or 0
            cost_estimate = self.estimate_cost(inferred_prompt_tokens, inferred_completion_tokens, model)

            audio_response = AudioResponse(
                audio_base64=encoded_audio,
                mime_type=mime_type,
                voice=request.voice,
                model=model,
                cost_estimate=cost_estimate,
                duration_seconds=None,
            )

            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            self._update_audio_request_success(
                llm_request,
                audio_response,
                execution_time_ms,
                response_raw=response_data,
            )
            return audio_response, request_id

        except asyncio.CancelledError:  # pragma: no cover - cooperative cancellation
            raise
        except Exception as exc:
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            if "llm_request" in locals():
                self._update_llm_request_error(llm_request, exc, execution_time_ms)
            if isinstance(exc, (LLMError, LLMAuthenticationError, LLMRateLimitError, LLMTimeoutError, LLMValidationError)):
                raise
            raise LLMError(f"Gemini audio generation failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Optional interfaces
    # ------------------------------------------------------------------
    async def search_recent_news(
        self,
        search_queries: list[str],
        user_id: int | None = None,
        **_kwargs: Any,
    ) -> tuple[WebSearchResponse, uuid.UUID]:  # pragma: no cover - not implemented
        raise NotImplementedError("Gemini provider does not implement web search")

    # ------------------------------------------------------------------
    # Pricing
    # ------------------------------------------------------------------
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str | None = None,
    ) -> float:
        model_name = (model or self.config.model).lower()
        if model_name.endswith("-image"):
            # Flat fee per generated image handled elsewhere; return marginal token cost
            return 0.0

        best_match: str | None = None
        for key in _GEMINI_PRICING:
            if model_name.startswith(key) and (best_match is None or len(key) > len(best_match)):
                best_match = key

        if best_match is None:
            best_match = "gemini-2.5-flash"

        input_cost, output_cost = _GEMINI_PRICING.get(best_match, (0.30, 2.50))
        prompt_component = (prompt_tokens / 1_000_000) * input_cost
        completion_component = (completion_tokens / 1_000_000) * output_cost
        return round(prompt_component + completion_component, 6)
