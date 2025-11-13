from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
import uuid

from pydantic import BaseModel, ConfigDict

from ..package_models import LessonPackage


class UnitStatus(str, Enum):
    """Valid unit statuses for creation flow tracking."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class LessonRead(BaseModel):
    """DTO for reading lesson data with embedded package."""

    id: str
    title: str
    learner_level: str
    lesson_type: str = "standard"  # 'standard' or 'intro'
    core_concept: str | None = None  # For admin compatibility
    unit_id: str | None = None
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict[str, Any] | None = None
    package: LessonPackage
    package_version: int
    flow_run_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    schema_version: int = 1
    podcast_transcript: str | None = None
    podcast_voice: str | None = None
    podcast_duration_seconds: int | None = None
    podcast_generated_at: datetime | None = None
    podcast_audio_url: str | None = None
    has_podcast: bool = False
    podcast_transcript_segments: list["PodcastTranscriptSegment"] | None = None

    model_config = ConfigDict(from_attributes=True)


class LessonCreate(BaseModel):
    """DTO for creating new lessons with package."""

    id: str
    title: str
    learner_level: str
    lesson_type: str = "standard"  # 'standard' or 'intro'
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict[str, Any] | None = None
    package: LessonPackage
    package_version: int = 1
    flow_run_id: uuid.UUID | None = None


class PodcastTranscriptSegment(BaseModel):
    text: str
    start: float
    end: float


class UnitLearningObjective(BaseModel):
    """Structured representation of a unit-level learning objective."""

    id: str
    title: str
    description: str
    bloom_level: str | None = None
    evidence_of_mastery: str | None = None


class UnitRead(BaseModel):
    id: str
    title: str
    description: str | None = None
    learner_level: str
    lesson_order: list[str]
    user_id: int | None = None
    is_global: bool = False
    arq_task_id: str | None = None
    learning_objectives: list[UnitLearningObjective] | None = None
    target_lesson_count: int | None = None
    source_material: str | None = None
    generated_from_topic: bool = False
    flow_type: str = "standard"
    status: str = "completed"
    creation_progress: dict[str, Any] | None = None
    error_message: str | None = None
    has_podcast: bool = False
    podcast_voice: str | None = None
    podcast_duration_seconds: int | None = None
    podcast_generated_at: datetime | None = None
    podcast_transcript: str | None = None
    podcast_audio_url: str | None = None
    art_image_id: uuid.UUID | None = None
    art_image_description: str | None = None
    art_image_url: str | None = None
    created_at: datetime
    updated_at: datetime
    schema_version: int = 1

    model_config = ConfigDict(from_attributes=True)


class UnitLessonSummary(BaseModel):
    id: str
    title: str
    learner_level: str
    learning_objective_ids: list[str]
    learning_objectives: list[str]
    key_concepts: list[str]
    exercise_count: int
    has_podcast: bool = False
    podcast_voice: str | None = None
    podcast_duration_seconds: int | None = None
    podcast_generated_at: datetime | None = None
    podcast_audio_url: str | None = None


class UnitDetailRead(UnitRead):
    """Full unit detail including intro podcast and ordered lessons."""

    learning_objectives: list[UnitLearningObjective] | None = None
    lessons: list[UnitLessonSummary]
    podcast_transcript: str | None = None
    podcast_audio_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UnitSyncAsset(BaseModel):
    """Metadata describing a downloadable asset for an offline unit."""

    id: str
    unit_id: str
    type: Literal["audio", "image"]
    object_id: uuid.UUID | None = None
    remote_url: str | None = None
    presigned_url: str | None = None
    updated_at: datetime | None = None
    schema_version: int = 1


class UnitSyncEntry(BaseModel):
    """Unit payload returned from the sync endpoint."""

    unit: UnitRead
    lessons: list[LessonRead]
    assets: list[UnitSyncAsset]


class UnitSyncResponse(BaseModel):
    """Full sync response payload describing unit changes."""

    units: list[UnitSyncEntry]
    deleted_unit_ids: list[str]
    deleted_lesson_ids: list[str]
    cursor: datetime


UnitSyncPayload = Literal["full", "minimal"]


class UnitCreate(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    learner_level: str = "beginner"
    lesson_order: list[str] = []
    user_id: int | None = None
    is_global: bool = False
    learning_objectives: list[UnitLearningObjective] | None = None
    target_lesson_count: int | None = None
    source_material: str | None = None
    generated_from_topic: bool = False
    flow_type: str = "standard"


class UnitPodcastAudio(BaseModel):
    unit_id: str
    mime_type: str
    audio_bytes: bytes | None = None
    presigned_url: str | None = None


class LessonPodcastAudio(BaseModel):
    lesson_id: str
    mime_type: str
    audio_bytes: bytes | None = None
    presigned_url: str | None = None


class UnitSessionRead(BaseModel):
    id: str
    unit_id: str
    user_id: str
    status: str
    progress_percentage: float
    last_lesson_id: str | None = None
    completed_lesson_ids: list[str]
    started_at: datetime
    completed_at: datetime | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "LessonCreate",
    "LessonPodcastAudio",
    "LessonRead",
    "UnitCreate",
    "UnitDetailRead",
    "UnitLearningObjective",
    "UnitLessonSummary",
    "UnitPodcastAudio",
    "UnitRead",
    "UnitSessionRead",
    "UnitStatus",
    "UnitSyncAsset",
    "UnitSyncEntry",
    "UnitSyncPayload",
    "UnitSyncResponse",
]
