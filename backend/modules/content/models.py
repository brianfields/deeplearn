# /backend/modules/content/models.py
"""
Content Module - Database Models

SQLAlchemy ORM models for educational content storage.
Uses single lessons table with JSON package field.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from modules.shared_models import Base, PostgresUUID
from modules.user.models import UserModel  # noqa: F401  # Ensure users table registered for FK


class LessonModel(Base):
    """SQLAlchemy model for educational lessons with embedded package content."""

    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    learner_level: Mapped[str] = mapped_column(String(50), nullable=False)

    source_material: Mapped[str | None] = mapped_column(Text)

    package: Mapped[dict] = mapped_column(JSON, nullable=False)  # Defined in @package_models.py
    package_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Reference to the flow run that generated this lesson
    flow_run_id: Mapped[str | None] = mapped_column(PostgresUUID(), ForeignKey("flow_runs.id"), nullable=True, index=True)

    # Association to unit (every lesson belongs to a unit)
    unit_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("units.id"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class UnitModel(Base):
    """SQLAlchemy model representing a learning unit that groups ordered lessons.

    Moved from modules.units.models to consolidate content-related models.
    """

    __tablename__ = "units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    learner_level: Mapped[str] = mapped_column(String(50), nullable=False, default="beginner")

    # Ordered list of lesson IDs belonging to this unit
    lesson_order: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Ownership and sharing metadata
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    is_global: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # New fields for unit-level generation and metadata
    # JSON structure: list of unit-level learning objectives or structured objects
    learning_objectives: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Target number of lessons for the unit (e.g., 5, 10, 20)
    target_lesson_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Full source material used to generate the unit (if any)
    source_material: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Whether this unit was generated from topic-only input
    generated_from_topic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Track which content creation flow was used: "standard" | "fast"
    flow_type: Mapped[str] = mapped_column(String(20), nullable=False, default="standard")

    # Status tracking fields for mobile unit creation
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    creation_progress: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Podcast fields - transcript + generated audio asset
    podcast_transcript = Column(Text, nullable=True)
    podcast_voice = Column(String(100), nullable=True)
    podcast_audio_object_id = Column(PostgresUUID(), nullable=True)
    podcast_generated_at = Column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Add constraint for status enum
    __table_args__ = (CheckConstraint("status IN ('draft', 'in_progress', 'completed', 'failed')", name="check_unit_status"),)

    def __repr__(self) -> str:  # pragma: no cover - repr convenience only
        return f"<UnitModel(id={self.id}, title='{self.title}', learner_level='{self.learner_level}')>"


"""
UnitSessionModel moved to modules.learning_session.models
"""
