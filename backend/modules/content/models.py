# /backend/modules/content/models.py
"""
Content Module - Database Models

SQLAlchemy ORM models for educational content storage.
Uses single lessons table with JSON package field.
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from modules.shared_models import Base, PostgresUUID


class LessonModel(Base):
    """SQLAlchemy model for educational lessons with embedded package content."""

    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    core_concept = Column(String(500), nullable=False)
    user_level = Column(String(50), nullable=False)

    source_material = Column(Text)
    source_domain = Column(String(100))
    source_level = Column(String(50))
    refined_material = Column(JSON)

    package = Column(JSON, nullable=False)  # Defined in @package_models.py
    package_version = Column(Integer, nullable=False, default=1)

    # Reference to the flow run that generated this lesson
    flow_run_id = Column(PostgresUUID(), ForeignKey("flow_runs.id"), nullable=True, index=True)

    # Association to unit (optional during transition; enforce later)
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
    difficulty = Column(String(50), nullable=False, default="beginner")

    # Ordered list of lesson IDs belonging to this unit
    lesson_order = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:  # pragma: no cover - repr convenience only
        return f"<UnitModel(id={self.id}, title='{self.title}', difficulty='{self.difficulty}')>"


"""
UnitSessionModel moved to modules.learning_session.models
"""
