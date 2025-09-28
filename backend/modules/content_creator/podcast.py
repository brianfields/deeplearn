"""Utility helpers to generate unit-level podcast transcripts and audio."""

from __future__ import annotations

import base64
import contextlib
import logging
import math
import re
from dataclasses import dataclass
from typing import Any, Sequence

try:  # pragma: no cover - optional dependency
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover - guard for environments without SDK
    AsyncOpenAI = None  # type: ignore[assignment]

from modules.llm_services.config import create_llm_config_from_env

from .steps import GenerateUnitPodcastTranscriptStep, PodcastLessonInput

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PodcastLesson:
    """Lightweight container for lesson data fed into podcast generation."""

    title: str
    mini_lesson: str


@dataclass(slots=True)
class UnitPodcast:
    """Result of unit podcast generation."""

    transcript: str
    audio_bytes: bytes
    mime_type: str
    voice: str
    duration_seconds: int | None


class UnitPodcastGenerator:
    """Generates a narrated podcast for a learning unit."""

    def __init__(
        self,
        *,
        audio_model: str = "gpt-4o-mini-tts",
        default_voice_id: str = "alloy",
        openai_client: Any | None = None,
    ) -> None:
        self.audio_model = audio_model
        self.default_voice_id = default_voice_id
        self._client: Any | None = openai_client
        self._transcript_step = GenerateUnitPodcastTranscriptStep()

    async def create_podcast(
        self,
        *,
        unit_title: str,
        voice_label: str,
        unit_summary: str,
        lessons: Sequence[PodcastLesson],
    ) -> UnitPodcast:
        """Generate both transcript text and narrated audio for a unit."""

        if not lessons:
            raise ValueError("At least one lesson is required to build a podcast")

        transcript_inputs = self._build_transcript_inputs(
            unit_title=unit_title,
            voice_label=voice_label,
            unit_summary=unit_summary,
            lessons=lessons,
        )
        transcript_result = await self._transcript_step.execute(transcript_inputs)
        transcript_text = str(transcript_result.output_content or "").strip()
        if not transcript_text:
            raise RuntimeError("Podcast transcript generation returned empty content")

        audio_bytes = await self._synthesize_audio(transcript_text)
        duration_seconds = self._estimate_duration_seconds(transcript_text)

        return UnitPodcast(
            transcript=transcript_text,
            audio_bytes=audio_bytes,
            mime_type="audio/mpeg",
            voice=voice_label,
            duration_seconds=duration_seconds,
        )

    def _build_transcript_inputs(
        self,
        *,
        unit_title: str,
        voice_label: str,
        unit_summary: str,
        lessons: Sequence[PodcastLesson],
    ) -> dict[str, Any]:
        lesson_inputs = [PodcastLessonInput(title=lesson.title, mini_lesson=lesson.mini_lesson) for lesson in lessons]

        return {
            "unit_title": unit_title,
            "voice": voice_label,
            "unit_summary": unit_summary,
            "lessons": lesson_inputs,
        }

    async def _synthesize_audio(self, transcript: str) -> bytes:
        client = await self._ensure_client()

        # Prefer streaming responses when available for efficiency
        with_streaming = getattr(getattr(client, "audio", None), "speech", None)
        streaming_method = getattr(with_streaming, "with_streaming_response", None)
        if callable(streaming_method):  # pragma: no branch - branchless guard
            response = await streaming_method.create(
                model=self.audio_model,
                voice=self.default_voice_id,
                input=transcript,
                format="mp3",
            )
            try:
                return await response.read()
            finally:
                with contextlib.suppress(Exception):
                    await response.close()

        # Fallback to standard API call
        standard_method = getattr(with_streaming, "create", None)
        if not callable(standard_method):  # pragma: no cover - defensive guard
            raise RuntimeError("OpenAI audio synthesis API is not available in this environment")

        response = await standard_method(
            model=self.audio_model,
            voice=self.default_voice_id,
            input=transcript,
            format="mp3",
        )

        # The SDK may expose different attributes depending on version
        audio_payload = getattr(response, "content", None)
        if isinstance(audio_payload, (bytes, bytearray)):
            return bytes(audio_payload)

        audio_payload = getattr(response, "audio", audio_payload)
        if isinstance(audio_payload, (bytes, bytearray)):
            return bytes(audio_payload)

        if isinstance(audio_payload, str):
            return base64.b64decode(audio_payload)

        raise RuntimeError("Unsupported audio response format from OpenAI")

    async def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client

        if AsyncOpenAI is None:
            raise RuntimeError("OpenAI SDK is required for podcast audio generation")

        config = create_llm_config_from_env()
        if getattr(config.provider, "value", "openai") != "openai":
            raise RuntimeError("Unit podcast audio generation currently supports the OpenAI provider only")

        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )
        return self._client

    def _estimate_duration_seconds(self, transcript: str) -> int:
        words = re.findall(r"[\w']+", transcript)
        if not words:
            return 0

        estimated_minutes = len(words) / 165  # ~165 spoken words per minute
        return max(1, int(math.ceil(estimated_minutes * 60)))
