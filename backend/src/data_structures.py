"""
Data structures for the Bite-Sized Topics Learning App

Simplified data model focused on bite-sized learning content.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, Boolean
from sqlalchemy.orm import (  # type: ignore[attr-defined]
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

if TYPE_CHECKING:
    pass


class Base(DeclarativeBase):
    pass


# Essential Enums
class ProgressStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"  # 70-89%
    MASTERY = "mastery"  # 90%+


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"


class QuizType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    SCENARIO_CRITIQUE = "scenario_critique"


class PodcastSegmentType(str, Enum):
    INTRO_HOOK = "intro_hook"
    OVERVIEW = "overview"
    MAIN_CONTENT = "main_content"
    SUMMARY = "summary"


# Bite-sized content models with modern SQLAlchemy typing
class BiteSizedTopic(Base):
    __tablename__ = "bite_sized_topics"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID string
    title: Mapped[str] = mapped_column(String, nullable=False)
    core_concept: Mapped[str] = mapped_column(String, nullable=False)
    user_level: Mapped[str] = mapped_column(String, nullable=False)

    # Content structure
    learning_objectives: Mapped[list[str] | None] = mapped_column(JSON)  # List of strings
    key_concepts: Mapped[list[str] | None] = mapped_column(JSON)  # List of strings
    key_aspects: Mapped[list[str] | None] = mapped_column(JSON)  # List of strings
    target_insights: Mapped[list[str] | None] = mapped_column(JSON)  # List of strings
    common_misconceptions: Mapped[list[str] | None] = mapped_column(JSON)  # List of strings
    previous_topics: Mapped[list[str] | None] = mapped_column(JSON)  # List of strings

    # Source material and refined content
    source_material: Mapped[str | None] = mapped_column(Text, nullable=True)  # Original input text
    source_domain: Mapped[str | None] = mapped_column(String, nullable=True)  # Domain specified during creation
    source_level: Mapped[str | None] = mapped_column(String, nullable=True)  # Level specified during creation
    refined_material: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Structured extraction from source

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    components: Mapped[list[BiteSizedComponent]] = relationship(
        "BiteSizedComponent", back_populates="topic", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_bite_sized_topics_core_concept", "core_concept"),
        Index("idx_bite_sized_topics_user_level", "user_level"),
    )


class BiteSizedComponent(Base):
    """A component of a bite-sized topic (e.g., didactic snippet, glossary entry, question)"""

    __tablename__ = "bite_sized_components"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID string
    topic_id: Mapped[str] = mapped_column(String, ForeignKey("bite_sized_topics.id"), nullable=False)
    component_type: Mapped[str] = mapped_column(String, nullable=False)  # didactic_snippet, glossary, etc.
    title: Mapped[str] = mapped_column(String, nullable=False)  # 1-8 word title to identify the component
    content: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False
    )  # All component data consolidated into single JSON field

    # Generation metadata
    generation_prompt: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # The prompt used to generate this component
    raw_llm_response: Mapped[str | None] = mapped_column(Text, nullable=True)  # The full unedited response from the LLM
    evaluation: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # Quality evaluation results for the component

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    topic: Mapped[BiteSizedTopic] = relationship("BiteSizedTopic", back_populates="components")

    # Indexes
    __table_args__ = (
        Index("idx_bite_sized_components_topic_id", "topic_id"),
        Index("idx_bite_sized_components_type", "component_type"),
        Index("idx_bite_sized_components_topic_type", "topic_id", "component_type"),
    )


# Podcast models
class PodcastEpisode(Base):
    """A podcast episode linked to a topic"""

    __tablename__ = "podcast_episodes"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID string
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    learning_outcomes: Mapped[list[str] | None] = mapped_column(JSON)  # List of strings
    total_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    full_script: Mapped[str] = mapped_column(Text, nullable=True)  # Complete script text

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    segments: Mapped[list[PodcastSegment]] = relationship(
        "PodcastSegment", back_populates="episode", cascade="all, delete-orphan"
    )
    topic_links: Mapped[list[TopicPodcastLink]] = relationship(
        "TopicPodcastLink", back_populates="podcast", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_podcast_episodes_title", "title"),
        Index("idx_podcast_episodes_duration", "total_duration_minutes"),
    )


class PodcastSegment(Base):
    """A segment of a podcast episode"""

    __tablename__ = "podcast_segments"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID string
    episode_id: Mapped[str] = mapped_column(String, ForeignKey("podcast_episodes.id"), nullable=False)
    segment_type: Mapped[str] = mapped_column(String, nullable=False)  # intro_hook, overview, main_content, summary
    title: Mapped[str] = mapped_column(String, nullable=False)
    script_content: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    episode: Mapped[PodcastEpisode] = relationship("PodcastEpisode", back_populates="segments")

    # Indexes
    __table_args__ = (
        Index("idx_podcast_segments_episode_id", "episode_id"),
        Index("idx_podcast_segments_type", "segment_type"),
        Index("idx_podcast_segments_order", "episode_id", "order_index"),
    )


class TopicPodcastLink(Base):
    """Junction table for topic-podcast relationships (ready for future one-to-many)"""

    __tablename__ = "topic_podcast_links"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID string
    topic_id: Mapped[str] = mapped_column(String, ForeignKey("bite_sized_topics.id"), nullable=False)
    podcast_id: Mapped[str] = mapped_column(String, ForeignKey("podcast_episodes.id"), nullable=False)
    is_primary_topic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))

    # Relationships
    topic: Mapped[BiteSizedTopic] = relationship("BiteSizedTopic")
    podcast: Mapped[PodcastEpisode] = relationship("PodcastEpisode", back_populates="topic_links")

    # Indexes and constraints
    __table_args__ = (
        Index("idx_topic_podcast_links_topic_id", "topic_id"),
        Index("idx_topic_podcast_links_podcast_id", "podcast_id"),
        Index("idx_topic_podcast_links_primary", "podcast_id", "is_primary_topic"),
    )


# Simple data structures for API responses
@dataclass
class QuizQuestion:
    """Quiz question data structure with index-based correct answer"""

    id: str
    type: QuizType
    question: str
    options: list[str]
    correct_answer_index: int  # 0-based index into options
    explanation: str | None = None

    def __post_init__(self) -> None:
        """Validate that correct_answer_index is within bounds"""
        if not (0 <= self.correct_answer_index < len(self.options)):
            raise ValueError(
                f"correct_answer_index {self.correct_answer_index} out of range for {len(self.options)} options"
            )

    @property
    def correct_answer(self) -> str:
        """Get the correct answer text for backward compatibility"""
        return self.options[self.correct_answer_index]

    @classmethod
    def from_legacy_format(
        cls,
        id: str,
        type: QuizType,
        question: str,
        correct_answer: str,
        options: list[str],
        explanation: str | None = None,
    ) -> QuizQuestion:
        """Create QuizQuestion from legacy string-based correct answer format"""
        try:
            correct_answer_index = options.index(correct_answer)
        except ValueError:
            raise ValueError(f"correct_answer '{correct_answer}' not found in options: {options}") from None

        return cls(
            id=id,
            type=type,
            question=question,
            options=options,
            correct_answer_index=correct_answer_index,
            explanation=explanation,
        )


# Domain Models for Service Layer (Pydantic)
# These are used by services to return data without SQLAlchemy coupling


class ComponentResult(BaseModel):
    """Base result model for component creation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    topic_id: str
    component_type: str
    title: str
    content: dict[str, Any]
    generation_prompt: str
    raw_llm_response: str
    created_at: datetime
    updated_at: datetime
    evaluation: dict[str, Any] | None = None


class RefinedMaterialResult(ComponentResult):
    """Result model for refined material extraction."""

    component_type: str = "refined_material"
    title: str = "Refined Material"


class MCQResult(ComponentResult):
    """Result model for MCQ creation."""

    component_type: str = "multiple_choice_question"


# Topic Domain Models (Pydantic) - for API responses
class TopicResult(BaseModel):
    """Domain model for topic data - returned by DatabaseService"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    key_aspects: list[str]
    target_insights: list[str]
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class ComponentData(BaseModel):
    """Domain model for component data"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    topic_id: str
    component_type: str
    title: str
    content: dict[str, Any]
    generation_prompt: str | None = None
    raw_llm_response: str | None = None
    evaluation: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


# Podcast Domain Models (Pydantic) - for API responses
class PodcastSegmentData(BaseModel):
    """Domain model for podcast segment data"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    episode_id: str
    segment_type: str
    title: str
    script_content: str
    estimated_duration_seconds: int
    order_index: int
    created_at: datetime
    updated_at: datetime


class TopicPodcastLinkData(BaseModel):
    """Domain model for topic-podcast link data"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    topic_id: str
    podcast_id: str
    is_primary_topic: bool
    created_at: datetime


class PodcastEpisodeData(BaseModel):
    """Domain model for podcast episode data - returned by DatabaseService"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    title: str
    description: str | None
    learning_outcomes: list[str]
    total_duration_minutes: int
    full_script: str | None
    segments: list[PodcastSegmentData]
    primary_topic_id: str  # For MVP: single topic relationship
    created_at: datetime
    updated_at: datetime


# Podcast Structure Models (Pydantic) - for planning and API responses
class SegmentPlan(BaseModel):
    """Plan for a single podcast segment"""

    segment_type: str  # intro_hook, overview, main_content, summary
    title: str
    purpose: str
    target_duration_seconds: int
    learning_outcomes: list[str]  # Which outcomes this segment addresses
    content_focus: str  # What content to include
    transition_in: str  # How to transition into this segment
    transition_out: str  # How to transition out of this segment


class PodcastStructure(BaseModel):
    """Complete podcast structure with segments and timing"""

    intro_hook: SegmentPlan
    overview: SegmentPlan
    main_content: SegmentPlan
    summary: SegmentPlan
    total_duration_seconds: int
    learning_outcomes: list[str]


class TimedStructure(BaseModel):
    """Podcast structure with precise timing breakdown"""

    structure: PodcastStructure
    segment_timing: dict[str, int]  # segment_type -> duration_seconds
    total_duration_seconds: int
    timing_notes: str  # Notes about timing decisions


class FlowPlan(BaseModel):
    """Plan for natural flow between segments"""

    structure: PodcastStructure
    transitions: dict[str, str]  # segment_type -> transition_text
    flow_notes: str  # Notes about flow decisions


# Podcast Script Models (Pydantic) - for script generation and API responses
class SegmentScript(BaseModel):
    """Script for a single podcast segment"""

    segment_type: str  # intro_hook, overview, main_content, summary
    title: str
    content: str  # The actual script content
    estimated_duration_seconds: int
    learning_outcomes: list[str]  # Which outcomes this segment addresses
    tone: str  # engaging, educational, conversational
    word_count: int  # For timing estimation


class ScriptMetadata(BaseModel):
    """Metadata about script generation"""

    generation_timestamp: datetime
    topic_id: str
    structure_id: str  # Reference to the structure used
    total_segments: int
    target_duration_seconds: int
    actual_duration_seconds: int
    tone_style: str  # overall tone of the podcast
    educational_level: str  # beginner, intermediate, advanced


class PodcastScript(BaseModel):
    """Complete podcast script with all segments"""

    title: str
    description: str
    segments: list[SegmentScript]
    total_duration_seconds: int
    learning_outcomes: list[str]
    metadata: ScriptMetadata
    full_script: str  # Complete script as single text


# Podcast API Models (Pydantic) - for API requests and responses
class PodcastGenerationRequest(BaseModel):
    """Request model for podcast generation"""

    topic_id: str
    generate_audio: bool = False  # For future audio generation


class PodcastGenerationResponse(BaseModel):
    """Response model for podcast generation"""

    episode_id: str
    title: str
    description: str
    total_duration_minutes: int
    learning_outcomes: list[str]
    segments: list[SegmentScript]
    full_script: str
    status: str  # "generated", "processing", "error"


class PodcastEpisodeResponse(BaseModel):
    """Response model for podcast episode data"""

    episode_id: str
    title: str
    description: str
    total_duration_minutes: int
    learning_outcomes: list[str]
    segments: list[SegmentScript]
    full_script: str
    created_at: datetime
    topic_id: str
