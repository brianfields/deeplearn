"""Utility helpers to generate unit-level podcast transcripts and audio."""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from typing import Sequence

from modules.llm_services.public import AudioResponse

from .flows import UnitPodcastFlow
from .steps import PodcastLessonInput

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
        audio_format: str = "mp3",
        audio_speed: float | None = None,
        podcast_flow: UnitPodcastFlow | None = None,
    ) -> None:
        self.audio_model = audio_model
        self.default_voice_id = default_voice_id
        self.audio_format = audio_format
        self.audio_speed = audio_speed
        self._flow = podcast_flow or UnitPodcastFlow()

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

        resolved_voice = voice_label or self.default_voice_id
        lesson_inputs = [PodcastLessonInput(title=lesson.title, mini_lesson=lesson.mini_lesson) for lesson in lessons]
        flow_inputs = {
            "unit_title": unit_title,
            "voice": resolved_voice,
            "unit_summary": unit_summary,
            "lessons": lesson_inputs,
            "audio_model": self.audio_model,
            "audio_format": self.audio_format,
        }
        if self.audio_speed is not None:
            flow_inputs["audio_speed"] = self.audio_speed

        flow_result = await self._flow.execute(flow_inputs)
        transcript_text = str(flow_result.get("transcript", "")).strip()
        if not transcript_text:
            raise RuntimeError("Podcast transcript generation returned empty content")

        audio_payload = flow_result.get("audio") or {}
        audio_bytes = b""
        mime_type = "audio/mpeg" if self.audio_format == "mp3" else f"audio/{self.audio_format}"
        playback_voice = resolved_voice
        duration_seconds: int | None = None

        if audio_payload:
            parsed_audio = AudioResponse.model_validate(audio_payload)
            audio_bytes = parsed_audio.audio_bytes()
            if parsed_audio.mime_type:
                mime_type = parsed_audio.mime_type
            if parsed_audio.voice:
                playback_voice = parsed_audio.voice
            if parsed_audio.duration_seconds is not None:
                duration_seconds = int(math.ceil(parsed_audio.duration_seconds))

        if duration_seconds is None:
            duration_seconds = self._estimate_duration_seconds(transcript_text)

        return UnitPodcast(
            transcript=transcript_text,
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            voice=playback_voice,
            duration_seconds=duration_seconds,
        )

    def _estimate_duration_seconds(self, transcript: str) -> int:
        words = re.findall(r"[\w']+", transcript)
        if not words:
            return 0

        estimated_minutes = len(words) / 165  # ~165 spoken words per minute
        return max(1, int(math.ceil(estimated_minutes * 60)))
