"""
Data structures for the Bite-Sized Topics Learning App

Simplified data model focused on bite-sized learning content.
"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Essential Enums
class ProgressStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"          # 70-89%
    MASTERY = "mastery"          # 90%+

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

# Bite-sized content models
class BiteSizedTopic(Base):
    __tablename__ = "bite_sized_topics"

    id = Column(String, primary_key=True)  # UUID string
    title = Column(String, nullable=False)
    core_concept = Column(String, nullable=False)
    user_level = Column(String, nullable=False)

    # Content structure
    learning_objectives = Column(JSON)  # List of strings
    key_concepts = Column(JSON)  # List of strings
    key_aspects = Column(JSON)  # List of strings
    target_insights = Column(JSON)  # List of strings
    common_misconceptions = Column(JSON)  # List of strings
    previous_topics = Column(JSON)  # List of strings

    # Creation metadata
    creation_strategy = Column(String, nullable=False)  # CreationStrategy enum value
    creation_metadata = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relationships
    components = relationship("BiteSizedComponent", back_populates="topic", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_bite_sized_topics_core_concept', 'core_concept'),
        Index('idx_bite_sized_topics_user_level', 'user_level'),
        Index('idx_bite_sized_topics_creation_strategy', 'creation_strategy'),
    )


class BiteSizedComponent(Base):
    """A component of a bite-sized topic (e.g., didactic snippet, glossary entry, question)"""

    __tablename__ = "bite_sized_components"

    id = Column(String, primary_key=True)  # UUID string
    topic_id = Column(String, ForeignKey("bite_sized_topics.id"), nullable=False)
    component_type = Column(String, nullable=False)  # didactic_snippet, glossary, etc.
    title = Column(String, nullable=False)  # 1-8 word title to identify the component
    content = Column(JSON, nullable=False)  # All component data consolidated into single JSON field

    # Generation metadata
    generation_prompt = Column(Text, nullable=True)  # The prompt used to generate this component
    raw_llm_response = Column(Text, nullable=True)  # The full unedited response from the LLM
    evaluation = Column(JSON, nullable=True)  # Quality evaluation results for the component

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

    # Relationships
    topic = relationship("BiteSizedTopic", back_populates="components")

    # Indexes
    __table_args__ = (
        Index('idx_bite_sized_components_topic_id', 'topic_id'),
        Index('idx_bite_sized_components_type', 'component_type'),
        Index('idx_bite_sized_components_topic_type', 'topic_id', 'component_type'),
    )


# Simple data structures for API responses
@dataclass
class QuizQuestion:
    """Quiz question data structure with index-based correct answer"""
    id: str
    type: QuizType
    question: str
    options: List[str]
    correct_answer_index: int  # 0-based index into options
    explanation: Optional[str] = None
    
    def __post_init__(self):
        """Validate that correct_answer_index is within bounds"""
        if not (0 <= self.correct_answer_index < len(self.options)):
            raise ValueError(f"correct_answer_index {self.correct_answer_index} out of range for {len(self.options)} options")
    
    @property
    def correct_answer(self) -> str:
        """Get the correct answer text for backward compatibility"""
        return self.options[self.correct_answer_index]
    
    @classmethod
    def from_legacy_format(cls, id: str, type: QuizType, question: str, correct_answer: str, options: List[str], explanation: Optional[str] = None) -> 'QuizQuestion':
        """Create QuizQuestion from legacy string-based correct answer format"""
        try:
            correct_answer_index = options.index(correct_answer)
        except ValueError:
            raise ValueError(f"correct_answer '{correct_answer}' not found in options: {options}")
        
        return cls(
            id=id,
            type=type,
            question=question,
            options=options,
            correct_answer_index=correct_answer_index,
            explanation=explanation
        )