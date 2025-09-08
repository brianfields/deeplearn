"""
Content Module - Database Models

SQLAlchemy ORM models for educational content storage.
Reuses existing database schema (bite_sized_topics, bite_sized_components tables).
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class TopicModel(Base):
    """SQLAlchemy model for educational topics."""

    __tablename__ = "bite_sized_topics"

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
    components = relationship("ComponentModel", back_populates="topic", cascade="all, delete-orphan")


class ComponentModel(Base):
    """SQLAlchemy model for educational content components."""

    __tablename__ = "bite_sized_components"

    id = Column(String(36), primary_key=True)
    topic_id = Column(String(36), ForeignKey("bite_sized_topics.id"), nullable=False)
    component_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(JSON, nullable=False)
    learning_objective = Column(String(500))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to topic
    topic = relationship("TopicModel", back_populates="components")
