"""
Learning Session Module - Database Models

Minimal SQLAlchemy models to support existing frontend learning session functionality.
This is a migration, not new feature development.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column  # type: ignore[attr-defined]

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
    id: Mapped[str] = mapped_column(String, primary_key=True)
    lesson_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Optional association to a unit for unit-level progress tracking
    unit_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)  # Optional for anonymous sessions
    status: Mapped[str] = mapped_column(String, nullable=False, default=SessionStatus.ACTIVE.value, index=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Progress tracking across exercises only (didactic/glossary excluded)
    current_exercise_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_exercises: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Total number of exercises
    exercises_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Number of exercises completed
    exercises_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Number of exercises answered correctly
    progress_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Session data (flexible JSON field) - now stores exercise-specific answers
    session_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<LearningSession(id={self.id}, lesson_id={self.lesson_id}, status={self.status})>"


class UnitSessionModel(Base):
    """Persistent unit-level session tracking for a user's progress in a unit.

    Moved from modules.content.models to modules.learning_session.models as part of
    model architecture correction. Table name remains the same for migration stability.
    """

    __tablename__ = "unit_sessions"

    # Identifiers and relations
    id: Mapped[str] = mapped_column(String, primary_key=True)
    unit_id: Mapped[str] = mapped_column(String, ForeignKey("units.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Status and timestamps
    status: Mapped[str] = mapped_column(String, nullable=False, default=SessionStatus.ACTIVE.value, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Progress summary
    progress_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_lesson_id: Mapped[str | None] = mapped_column(String, nullable=True)
    completed_lesson_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
