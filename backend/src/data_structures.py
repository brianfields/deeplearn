"""
Data structures for the Proactive Learning App
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Enums
class ProgressStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"          # 70-89%
    MASTERY = "mastery"          # 90%+

class LearningPathStatus(str, Enum):
    CREATING = "creating"        # Syllabus being generated/refined
    ACTIVE = "active"           # Currently learning
    PAUSED = "paused"           # User paused
    COMPLETED = "completed"     # All topics mastered

class QuizType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    SCENARIO_CRITIQUE = "scenario_critique"

class SessionType(str, Enum):
    LESSON = "lesson"
    REVIEW = "review"
    QUIZ = "quiz"

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
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_name = Column(String, nullable=False)  # e.g., "Product Management"
    description = Column(Text)
    status = Column(String, default=LearningPathStatus.CREATING)
    is_active = Column(Boolean, default=True)  # For multiple paths
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="learning_paths")
    syllabus = relationship("Syllabus", back_populates="learning_path", uselist=False)
    topic_progress = relationship("TopicProgress", back_populates="learning_path")

class Syllabus(Base):
    __tablename__ = "syllabi"
    
    id = Column(Integer, primary_key=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    version = Column(Integer, default=1)
    is_locked = Column(Boolean, default=False)  # True when user confirms
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    learning_path = relationship("LearningPath", back_populates="syllabus")
    topics = relationship("Topic", back_populates="syllabus", order_by="Topic.position")

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True)
    syllabus_id = Column(Integer, ForeignKey("syllabi.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    position = Column(Integer, nullable=False)  # Order in syllabus
    estimated_duration = Column(Integer, default=15)  # minutes
    difficulty_level = Column(Integer, default=1)  # 1-5 scale
    prerequisite_topics = Column(JSON)  # List of topic IDs
    learning_objectives = Column(JSON)  # List of learning objectives
    
    # Relationships
    syllabus = relationship("Syllabus", back_populates="topics")
    progress_records = relationship("TopicProgress", back_populates="topic")
    quiz_attempts = relationship("QuizAttempt", back_populates="topic")

class TopicProgress(Base):
    __tablename__ = "topic_progress"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    
    # Progress tracking
    status = Column(String, default=ProgressStatus.NOT_STARTED)
    mastery_level = Column(Float, default=0.0)  # 0.0 to 1.0
    best_quiz_score = Column(Float, default=0.0)
    total_time_spent = Column(Integer, default=0)  # minutes
    
    # Timestamps
    first_started = Column(DateTime)
    last_studied = Column(DateTime)
    mastered_at = Column(DateTime)
    
    # Spaced repetition
    next_review_date = Column(DateTime)
    review_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="topic_progress")
    learning_path = relationship("LearningPath", back_populates="topic_progress")
    topic = relationship("Topic", back_populates="progress_records")
    quiz_attempts = relationship("QuizAttempt", back_populates="topic_progress")
    review_schedule = relationship("ReviewSchedule", back_populates="topic_progress", uselist=False)

class ReviewSchedule(Base):
    __tablename__ = "review_schedules"
    
    id = Column(Integer, primary_key=True)
    topic_progress_id = Column(Integer, ForeignKey("topic_progress.id"), nullable=False)
    
    # SM-2 Algorithm parameters
    easiness_factor = Column(Float, default=2.5)  # Initial EF
    interval = Column(Integer, default=1)  # Days until next review
    repetitions = Column(Integer, default=0)  # Number of successful reviews
    
    # Scheduling
    due_date = Column(DateTime)
    last_reviewed = Column(DateTime)
    
    # Relationships
    topic_progress = relationship("TopicProgress", back_populates="review_schedule")

class LearningSession(Base):
    __tablename__ = "learning_sessions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
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
    topic = relationship("Topic")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id = Column(Integer, primary_key=True)
    topic_progress_id = Column(Integer, ForeignKey("topic_progress.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    
    # Quiz data
    questions = Column(JSON)  # List of questions with metadata
    answers = Column(JSON)  # User responses
    score = Column(Float, nullable=False)  # 0.0 to 1.0
    max_score = Column(Float, default=1.0)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    time_spent_seconds = Column(Integer)
    
    # Relationships
    topic_progress = relationship("TopicProgress", back_populates="quiz_attempts")
    topic = relationship("Topic", back_populates="quiz_attempts")

# Pydantic Models for API
class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    last_active: datetime

class TopicCreate(BaseModel):
    title: str
    description: str
    position: int
    estimated_duration: int = 15
    difficulty_level: int = 1
    prerequisite_topics: List[int] = []
    learning_objectives: List[str] = []

class TopicResponse(BaseModel):
    id: int
    title: str
    description: str
    position: int
    estimated_duration: int
    difficulty_level: int
    prerequisite_topics: List[int]
    learning_objectives: List[str]

class TopicProgressResponse(BaseModel):
    id: int
    topic_id: int
    status: ProgressStatus
    mastery_level: float
    best_quiz_score: float
    total_time_spent: int
    last_studied: Optional[datetime]
    next_review_date: Optional[datetime]

class SyllabusCreate(BaseModel):
    learning_path_id: int
    topics: List[TopicCreate]

class SyllabusResponse(BaseModel):
    id: int
    learning_path_id: int
    version: int
    is_locked: bool
    topics: List[TopicResponse]
    created_at: datetime
    updated_at: datetime

class LearningPathCreate(BaseModel):
    topic_name: str
    description: Optional[str] = None

class LearningPathResponse(BaseModel):
    id: int
    topic_name: str
    description: Optional[str]
    status: LearningPathStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    syllabus: Optional[SyllabusResponse]
    progress_summary: Dict[str, Any]  # Computed progress statistics

class QuizQuestion(BaseModel):
    id: str
    type: QuizType
    question: str
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: str
    explanation: Optional[str] = None

class QuizAttemptCreate(BaseModel):
    topic_id: int
    questions: List[QuizQuestion]
    answers: List[str]

class QuizAttemptResponse(BaseModel):
    id: int
    topic_id: int
    score: float
    max_score: float
    questions: List[QuizQuestion]
    answers: List[str]
    started_at: datetime
    submitted_at: Optional[datetime]
    time_spent_seconds: Optional[int]

class LearningSessionCreate(BaseModel):
    topic_id: int
    session_type: SessionType

class LearningSessionResponse(BaseModel):
    id: int
    topic_id: int
    session_type: SessionType
    started_at: datetime
    completed_at: Optional[datetime]
    duration_minutes: Optional[int]
    is_paused: bool
    content_data: Dict[str, Any]
    interaction_data: Dict[str, Any]

class ReviewScheduleResponse(BaseModel):
    id: int
    topic_progress_id: int
    easiness_factor: float
    interval: int
    repetitions: int
    due_date: Optional[datetime]
    last_reviewed: Optional[datetime]

class DashboardResponse(BaseModel):
    user: UserResponse
    active_learning_path: Optional[LearningPathResponse]
    all_learning_paths: List[LearningPathResponse]
    topics_due_for_review: List[TopicProgressResponse]
    recent_activity: List[LearningSessionResponse]
    overall_progress: Dict[str, Any]

# Helper functions for SM-2 algorithm
def calculate_sm2_review(quality: int, repetitions: int, easiness_factor: float) -> tuple[int, float]:
    """
    Calculate next review interval using SM-2 algorithm
    
    Args:
        quality: Response quality (0-5, where 3+ is correct)
        repetitions: Number of consecutive correct responses
        easiness_factor: Current easiness factor
    
    Returns:
        (interval_days, new_easiness_factor)
    """
    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(interval * easiness_factor)
        repetitions += 1
    
    # Update easiness factor
    easiness_factor = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    easiness_factor = max(1.3, easiness_factor)  # Minimum EF
    
    return interval, easiness_factor

def calculate_forgetting_curve(mastery_level: float, days_since_study: int, easiness_factor: float) -> float:
    """
    Calculate current mastery level based on forgetting curve
    
    Args:
        mastery_level: Original mastery level (0.0-1.0)
        days_since_study: Days since last study
        easiness_factor: Topic easiness factor
    
    Returns:
        Current estimated mastery level
    """
    # Simplified forgetting curve: R = e^(-t/S)
    # Where S (stability) is influenced by easiness factor
    stability = easiness_factor * 2  # Days for 37% retention
    retention = mastery_level * (2.71828 ** (-days_since_study / stability))
    return max(0.0, min(1.0, retention))