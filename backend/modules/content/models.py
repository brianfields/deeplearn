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

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
