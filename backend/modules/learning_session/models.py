"""
Learning Session Module - Database Models

Minimal SQLAlchemy models to support existing frontend learning session functionality.
This is a migration, not new feature development.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String

from modules.shared_models import Base


class SessionStatus(str, Enum):
    """Session status enumeration - matches frontend expectations"""

    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class LearningSessionModel(Base):
    """
    Learning session database model.

    Matches the ApiLearningSession interface expected by the frontend.
    """

    __tablename__ = "learning_sessions"

    # Core fields matching frontend ApiLearningSession
    id = Column(String, primary_key=True)
    topic_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)  # Optional for anonymous sessions
    status = Column(String, nullable=False, default=SessionStatus.ACTIVE.value, index=True)

    # Timestamps
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Progress tracking
    current_component_index = Column(Integer, nullable=False, default=0)
    total_components = Column(Integer, nullable=False, default=0)
    progress_percentage = Column(Float, nullable=False, default=0.0)

    # Session data (flexible JSON field)
    session_data = Column(JSON, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<LearningSession(id={self.id}, topic_id={self.topic_id}, status={self.status})>"
