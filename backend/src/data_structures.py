"""
Data structures for the Proactive Learning App
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Enums
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

class LessonType(str, Enum):
    DIDACTIC = "didactic"
    CONVERSATION = "conversation"
    QUIZ = "quiz"
    REVIEW = "review"

class CreationStrategy(str, Enum):
    SOCRATIC = "socratic"
    DIDACTIC = "didactic"
    MIXED = "mixed"
    GLOSSARY = "glossary"


class QuizType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    SCENARIO_CRITIQUE = "scenario_critique"

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # Relationships
    learning_paths = relationship("LearningPath", back_populates="user")
    topic_progress = relationship("TopicProgress", back_populates="user")
    learning_sessions = relationship("LearningSession", back_populates="user")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(String, primary_key=True)  # UUID string
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Allow null for shared paths
    topic_name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Progress tracking
    current_topic_index = Column(Integer, default=0)
    estimated_total_hours = Column(Float, default=0.0)

    # Relationships
    user = relationship("User", back_populates="learning_paths")
    topics = relationship("Topic", back_populates="learning_path", order_by="Topic.order_index")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(String, primary_key=True)  # UUID string
    learning_path_id = Column(String, ForeignKey("learning_paths.id"), nullable=False)

    # Topic details
    title = Column(String, nullable=False)
    description = Column(Text)
    order_index = Column(Integer, nullable=False)

    # Learning objectives
    learning_objectives = Column(JSON)  # List of strings
    estimated_duration = Column(Integer, default=15)  # minutes
    difficulty_level = Column(Integer, default=1)  # 1-5 scale

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Bite-sized content reference
    bite_sized_topic_id = Column(String, nullable=True)  # Reference to BiteSizedTopic

    # Relationships
    learning_path = relationship("LearningPath", back_populates="topics")
    progress = relationship("TopicProgress", back_populates="topic")
    sessions = relationship("LearningSession", back_populates="topic")


class TopicProgress(Base):
    __tablename__ = "topic_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(String, ForeignKey("topics.id"), nullable=False)

    # Progress tracking
    status = Column(String, nullable=False, default=ProgressStatus.NOT_STARTED.value)
    score = Column(Float, default=0.0)
    time_spent = Column(Integer, default=0)  # minutes
    attempts = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    last_accessed = Column(DateTime, default=datetime.utcnow)

    # Content state
    current_lesson_index = Column(Integer, default=0)
    conversation_state = Column(JSON)  # Store conversation history

    # Relationships
    user = relationship("User", back_populates="topic_progress")
    topic = relationship("Topic", back_populates="progress")


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(String, ForeignKey("topics.id"), nullable=False)
    session_type = Column(String, nullable=False)  # lesson, review, quiz

    # Session data
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_minutes = Column(Integer)
    is_paused = Column(Boolean, default=False)

    # Content and interaction
    content_data = Column(JSON)  # Lesson content, conversation history
    interaction_data = Column(JSON)  # User responses, AI prompts

    # Relationships
    user = relationship("User", back_populates="learning_sessions")
    topic = relationship("Topic", back_populates="sessions")


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
    __tablename__ = "bite_sized_components"

    id = Column(String, primary_key=True)  # UUID string
    topic_id = Column(String, ForeignKey("bite_sized_topics.id"), nullable=False)
    component_type = Column(String, nullable=False)  # didactic_snippet, glossary, etc.
    content = Column(Text, nullable=False)
    component_metadata = Column(JSON)

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


# Pydantic models for API serialization
class SimpleProgress(BaseModel):
    """Simple progress tracking for current session"""
    current_topic: str
    topics_completed: int
    total_topics: int
    last_score: float
    time_spent_minutes: int
    session_start: datetime

    @property
    def completion_percentage(self) -> float:
        if self.total_topics == 0:
            return 0.0
        return (self.topics_completed / self.total_topics) * 100


class SimpleLearningPath(BaseModel):
    """Simple learning path structure for file storage compatibility"""
    id: str
    topic_name: str
    description: str
    topics: List[Dict[str, Any]]
    current_topic_index: int
    estimated_total_hours: float
    created_at: datetime
    updated_at: datetime


@dataclass
class QuizQuestion:
    """Quiz question data structure"""
    id: str
    type: QuizType
    question: str
    correct_answer: str
    options: Optional[List[str]] = None
    explanation: Optional[str] = None


class TopicProgressResponse(BaseModel):
    """Response model for topic progress information"""
    topic_id: str
    status: str
    score: float
    time_spent: int
    attempts: int
    current_lesson_index: int