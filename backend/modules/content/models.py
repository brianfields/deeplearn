# /backend/modules/content/models.py
"""
Content Module - Database Models

SQLAlchemy ORM models for educational content storage.
Uses single lessons table with JSON package field.
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text

from modules.shared_models import Base, PostgresUUID
from modules.user.models import UserModel  # noqa: F401  # Ensure users table registered for FK


class LessonModel(Base):
    """SQLAlchemy model for educational lessons with embedded package content."""

    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    learner_level = Column(String(50), nullable=False)

    source_material = Column(Text)

    package = Column(JSON, nullable=False)  # Defined in @package_models.py
    package_version = Column(Integer, nullable=False, default=1)

    # Reference to the flow run that generated this lesson
    flow_run_id = Column(PostgresUUID(), ForeignKey("flow_runs.id"), nullable=True, index=True)

    # Association to unit (every lesson belongs to a unit)
    unit_id = Column(String(36), ForeignKey("units.id"), nullable=True, index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class UnitModel(Base):
    """SQLAlchemy model representing a learning unit that groups ordered lessons.

    Moved from modules.units.models to consolidate content-related models.
    """

    __tablename__ = "units"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    learner_level = Column(String(50), nullable=False, default="beginner")

    # Ordered list of lesson IDs belonging to this unit
    lesson_order = Column(JSON, nullable=False, default=list)

    # Ownership and sharing metadata
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    is_global = Column(Boolean, nullable=False, default=False)

    # New fields for unit-level generation and metadata
    # JSON structure: list of unit-level learning objectives or structured objects
    learning_objectives = Column(JSON, nullable=True)
    # Target number of lessons for the unit (e.g., 5, 10, 20)
    target_lesson_count = Column(Integer, nullable=True)
    # Full source material used to generate the unit (if any)
    source_material = Column(Text, nullable=True)
    # Whether this unit was generated from topic-only input
    generated_from_topic = Column(Boolean, nullable=False, default=False)

    # Track which content creation flow was used: "standard" | "fast"
    flow_type = Column(String(20), nullable=False, default="standard")

    # Status tracking fields for mobile unit creation
    status = Column(String(20), nullable=False, default="completed")
    creation_progress = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Podcast fields - transcript + generated audio asset
    podcast_transcript = Column(Text, nullable=True)
    podcast_voice = Column(String(100), nullable=True)
    podcast_audio_object_id = Column(PostgresUUID(), nullable=True)
    podcast_generated_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Add constraint for status enum
    __table_args__ = (CheckConstraint("status IN ('draft', 'in_progress', 'completed', 'failed')", name="check_unit_status"),)

    def __repr__(self) -> str:  # pragma: no cover - repr convenience only
        return f"<UnitModel(id={self.id}, title='{self.title}', learner_level='{self.learner_level}')>"


"""
UnitSessionModel moved to modules.learning_session.models
"""
