"""
Content Module - Database Models

SQLAlchemy ORM models for educational content storage.
Uses lessons and lesson_components tables.
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from modules.shared_models import Base


class LessonModel(Base):
    """SQLAlchemy model for educational lessons."""

    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    core_concept = Column(String(500), nullable=False)
    user_level = Column(String(50), nullable=False)
    learning_objectives = Column(JSON, nullable=False)
    key_concepts = Column(JSON, nullable=False)
    source_material = Column(Text)
    source_domain = Column(String(100))
    source_level = Column(String(50))
    refined_material = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to components
    components = relationship("LessonComponentModel", back_populates="lesson", cascade="all, delete-orphan")


class LessonComponentModel(Base):
    """SQLAlchemy model for educational lesson components."""

    __tablename__ = "lesson_components"

    id = Column(String(36), primary_key=True)
    lesson_id = Column(String(36), ForeignKey("lessons.id"), nullable=False)
    component_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(JSON, nullable=False)
    learning_objective = Column(String(500))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to lesson
    lesson = relationship("LessonModel", back_populates="components")
