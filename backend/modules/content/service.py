"""
Content Module - Service Layer

Business logic layer that returns DTOs (Pydantic models).
Handles content operations and data transformation.
"""

from datetime import datetime

from pydantic import BaseModel

from .models import ComponentModel, TopicModel
from .repo import ContentRepo


# DTOs (Data Transfer Objects)
class ComponentRead(BaseModel):
    """DTO for reading component data."""

    id: str
    topic_id: str
    component_type: str
    title: str
    content: dict
    learning_objective: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopicRead(BaseModel):
    """DTO for reading topic data."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict | None = None
    created_at: datetime
    updated_at: datetime
    components: list[ComponentRead] = []

    class Config:
        from_attributes = True


class TopicCreate(BaseModel):
    """DTO for creating new topics."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict | None = None


class ComponentCreate(BaseModel):
    """DTO for creating new components."""

    id: str
    topic_id: str
    component_type: str
    title: str
    content: dict
    learning_objective: str | None = None


class ContentService:
    """Service for content operations."""

    def __init__(self, repo: ContentRepo):
        """Initialize service with repository."""
        self.repo = repo

    # Topic operations
    def get_topic(self, topic_id: str) -> TopicRead | None:
        """Get topic with components by ID."""
        topic = self.repo.get_topic_by_id(topic_id)
        if not topic:
            return None

        # Load components
        components = self.repo.get_components_by_topic_id(topic_id)

        # Convert to DTO
        topic_dict = {
            "id": topic.id,
            "title": topic.title,
            "core_concept": topic.core_concept,
            "user_level": topic.user_level,
            "learning_objectives": topic.learning_objectives,
            "key_concepts": topic.key_concepts,
            "source_material": topic.source_material,
            "source_domain": topic.source_domain,
            "source_level": topic.source_level,
            "refined_material": topic.refined_material,
            "created_at": topic.created_at,
            "updated_at": topic.updated_at,
            "components": [ComponentRead.model_validate(c) for c in components],
        }

        return TopicRead.model_validate(topic_dict)

    def get_all_topics(self, limit: int = 100, offset: int = 0) -> list[TopicRead]:
        """Get all topics with components."""
        topics = self.repo.get_all_topics(limit, offset)
        result = []

        for topic in topics:
            components = self.repo.get_components_by_topic_id(topic.id)
            topic_dict = {
                "id": topic.id,
                "title": topic.title,
                "core_concept": topic.core_concept,
                "user_level": topic.user_level,
                "learning_objectives": topic.learning_objectives,
                "key_concepts": topic.key_concepts,
                "source_material": topic.source_material,
                "source_domain": topic.source_domain,
                "source_level": topic.source_level,
                "refined_material": topic.refined_material,
                "created_at": topic.created_at,
                "updated_at": topic.updated_at,
                "components": [ComponentRead.model_validate(c) for c in components],
            }
            result.append(TopicRead.model_validate(topic_dict))

        return result

    def search_topics(self, query: str | None = None, user_level: str | None = None, limit: int = 100, offset: int = 0) -> list[TopicRead]:
        """Search topics with optional filters."""
        topics = self.repo.search_topics(query, user_level, limit, offset)
        result = []

        for topic in topics:
            components = self.repo.get_components_by_topic_id(topic.id)
            topic_dict = {
                "id": topic.id,
                "title": topic.title,
                "core_concept": topic.core_concept,
                "user_level": topic.user_level,
                "learning_objectives": topic.learning_objectives,
                "key_concepts": topic.key_concepts,
                "source_material": topic.source_material,
                "source_domain": topic.source_domain,
                "source_level": topic.source_level,
                "refined_material": topic.refined_material,
                "created_at": topic.created_at,
                "updated_at": topic.updated_at,
                "components": [ComponentRead.model_validate(c) for c in components],
            }
            result.append(TopicRead.model_validate(topic_dict))

        return result

    def save_topic(self, topic_data: TopicCreate) -> TopicRead:
        """Create new topic."""
        topic_model = TopicModel(
            id=topic_data.id,
            title=topic_data.title,
            core_concept=topic_data.core_concept,
            user_level=topic_data.user_level,
            learning_objectives=topic_data.learning_objectives,
            key_concepts=topic_data.key_concepts,
            source_material=topic_data.source_material,
            source_domain=topic_data.source_domain,
            source_level=topic_data.source_level,
            refined_material=topic_data.refined_material or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        saved_topic = self.repo.save_topic(topic_model)

        # Return as DTO with empty components list
        topic_dict = {
            "id": saved_topic.id,
            "title": saved_topic.title,
            "core_concept": saved_topic.core_concept,
            "user_level": saved_topic.user_level,
            "learning_objectives": saved_topic.learning_objectives,
            "key_concepts": saved_topic.key_concepts,
            "source_material": saved_topic.source_material,
            "source_domain": saved_topic.source_domain,
            "source_level": saved_topic.source_level,
            "refined_material": saved_topic.refined_material,
            "created_at": saved_topic.created_at,
            "updated_at": saved_topic.updated_at,
            "components": [],
        }

        return TopicRead.model_validate(topic_dict)

    def delete_topic(self, topic_id: str) -> bool:
        """Delete topic by ID."""
        return self.repo.delete_topic(topic_id)

    def topic_exists(self, topic_id: str) -> bool:
        """Check if topic exists."""
        return self.repo.topic_exists(topic_id)

    # Component operations
    def get_component(self, component_id: str) -> ComponentRead | None:
        """Get component by ID."""
        component = self.repo.get_component_by_id(component_id)
        return ComponentRead.model_validate(component) if component else None

    def get_components_by_topic(self, topic_id: str) -> list[ComponentRead]:
        """Get all components for a topic."""
        components = self.repo.get_components_by_topic_id(topic_id)
        return [ComponentRead.model_validate(c) for c in components]

    def save_component(self, component_data: ComponentCreate) -> ComponentRead:
        """Create new component."""
        component_model = ComponentModel(
            id=component_data.id,
            topic_id=component_data.topic_id,
            component_type=component_data.component_type,
            title=component_data.title,
            content=component_data.content,
            learning_objective=component_data.learning_objective,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        saved_component = self.repo.save_component(component_model)
        return ComponentRead.model_validate(saved_component)

    def delete_component(self, component_id: str) -> bool:
        """Delete component by ID."""
        return self.repo.delete_component(component_id)
