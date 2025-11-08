"""Utility helpers to generate unit-level podcast transcripts and audio."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import logging
import math
import re

from modules.llm_services.public import AudioResponse

from .flows import LessonPodcastFlow, UnitPodcastFlow

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PodcastLesson:
    """Lightweight container for lesson data fed into podcast generation."""

    title: str
    podcast_transcript: str


@dataclass(slots=True)
class LessonPodcastResult:
    """Result of lesson podcast generation."""

    transcript: str
    audio_bytes: bytes
    mime_type: str
    voice: str
    duration_seconds: int | None


@dataclass(slots=True)
class UnitPodcast:
    """Result of intro podcast generation for the full unit."""

    transcript: str
    audio_bytes: bytes
    mime_type: str
    voice: str
    duration_seconds: int | None


class UnitPodcastGenerator:
    """Generates the narrated intro podcast for a learning unit."""

    def __init__(
        self,
        *,
        audio_model: str = "tts-1-hd",
        default_voice_id: str = "fable",
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
        learner_desires: str,
        unit_title: str,
        voice_label: str,
        unit_summary: str,
        lessons: Sequence[PodcastLesson],
        arq_task_id: str | None = None,
    ) -> UnitPodcast:
        """Generate both transcript text and narrated audio for the intro podcast."""

        if not lessons:
            raise ValueError("At least one lesson is required to build a podcast")

        resolved_voice = voice_label or self.default_voice_id
        # Build plain-JSON lesson inputs to avoid Pydantic instances leaking into DB JSON columns
        lesson_inputs = [{"title": lesson.title, "podcast_transcript": lesson.podcast_transcript} for lesson in lessons]
        flow_inputs = {
            "learner_desires": learner_desires,
            "unit_title": unit_title,
            "voice": resolved_voice,
            "unit_summary": unit_summary,
            "lessons": lesson_inputs,
            "audio_model": self.audio_model,
            "audio_format": self.audio_format,
        }
        if self.audio_speed is not None:
            flow_inputs["audio_speed"] = self.audio_speed

        flow_result = await self._flow.execute(flow_inputs, arq_task_id=arq_task_id)
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
                duration_seconds = math.ceil(parsed_audio.duration_seconds)

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
        return max(1, math.ceil(estimated_minutes * 60))


class LessonPodcastGenerator:
    """Generates narrated podcast audio for a single lesson."""

    def __init__(
        self,
        *,
        audio_model: str = "tts-1-hd",
        default_voice_id: str = "fable",
        audio_format: str = "mp3",
        audio_speed: float | None = None,
        podcast_flow: LessonPodcastFlow | None = None,
    ) -> None:
        self.audio_model = audio_model
        self.default_voice_id = default_voice_id
        self.audio_format = audio_format
        self.audio_speed = audio_speed
        self._flow = podcast_flow or LessonPodcastFlow()

    async def create_podcast(
        self,
        *,
        learner_desires: str,
        lesson_index: int,
        lesson_title: str,
        lesson_objective: str,
        voice_label: str,
        podcast_transcript: str | None = None,
        learning_objectives: list[dict] | None = None,
        sibling_lessons: list[dict] | None = None,
        source_material: str | None = None,
        arq_task_id: str | None = None,
    ) -> LessonPodcastResult:
        """Generate transcript and audio for the specified lesson."""

        resolved_voice = voice_label or self.default_voice_id
        flow_inputs = {
            "learner_desires": learner_desires,
            "lesson_number": lesson_index + 1,
            "lesson_title": lesson_title,
            "lesson_objective": lesson_objective,
            "voice": resolved_voice,
            "podcast_transcript": podcast_transcript or "",
            "learning_objectives": learning_objectives or [],
            "sibling_lessons": sibling_lessons or [],
            "source_material": source_material,
            "audio_model": self.audio_model,
            "audio_format": self.audio_format,
        }
        if self.audio_speed is not None:
            flow_inputs["audio_speed"] = self.audio_speed

        flow_result = await self._flow.execute(flow_inputs, arq_task_id=arq_task_id)
        transcript_text = str(flow_result.get("transcript", "")).strip()
        if not transcript_text:
            raise RuntimeError("Lesson podcast transcript generation returned empty content")

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
                duration_seconds = math.ceil(parsed_audio.duration_seconds)

        if not audio_bytes:
            raise RuntimeError("Lesson podcast audio synthesis returned no audio bytes")

        if duration_seconds is None:
            words = re.findall(r"[\w']+", transcript_text)
            if not words:
                duration_seconds = 0
            else:
                estimated_minutes = len(words) / 165
                duration_seconds = max(1, math.ceil(estimated_minutes * 60))

        return LessonPodcastResult(
            transcript=transcript_text,
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            voice=playback_voice,
            duration_seconds=duration_seconds,
        )
