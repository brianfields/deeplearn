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
from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text
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
