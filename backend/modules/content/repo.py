"""
Content Module - Repository Layer

Database access layer that returns ORM objects.
Handles all CRUD operations for topics and components.
"""

from modules.infrastructure.public import DatabaseSession

from .models import ComponentModel, TopicModel


class ContentRepo:
    """Repository for content data access operations."""

    def __init__(self, session: DatabaseSession):
        """Initialize repository with database session."""
        self.s = session

    # Topic operations
    def get_topic_by_id(self, topic_id: str) -> TopicModel | None:
        """Get topic by ID."""
        return self.s.get(TopicModel, topic_id)

    def get_all_topics(self, limit: int = 100, offset: int = 0) -> list[TopicModel]:
        """Get all topics with pagination."""
        return self.s.query(TopicModel).offset(offset).limit(limit).all()

    def search_topics(self, query: str | None = None, user_level: str | None = None, limit: int = 100, offset: int = 0) -> list[TopicModel]:
        """Search topics with optional filters."""
        q = self.s.query(TopicModel)

        if query:
            q = q.filter(TopicModel.title.contains(query))
        if user_level:
            q = q.filter(TopicModel.user_level == user_level)

        return q.offset(offset).limit(limit).all()

    def save_topic(self, topic: TopicModel) -> TopicModel:
        """Save topic to database."""
        self.s.add(topic)
        self.s.flush()
        return topic

    def delete_topic(self, topic_id: str) -> bool:
        """Delete topic by ID."""
        topic = self.get_topic_by_id(topic_id)
        if topic:
            self.s.delete(topic)
            return True
        return False

    def topic_exists(self, topic_id: str) -> bool:
        """Check if topic exists."""
        return self.s.query(TopicModel.id).filter(TopicModel.id == topic_id).first() is not None

    # Component operations
    def get_component_by_id(self, component_id: str) -> ComponentModel | None:
        """Get component by ID."""
        return self.s.get(ComponentModel, component_id)

    def get_components_by_topic_id(self, topic_id: str) -> list[ComponentModel]:
        """Get all components for a topic."""
        return self.s.query(ComponentModel).filter(ComponentModel.topic_id == topic_id).all()

    def save_component(self, component: ComponentModel) -> ComponentModel:
        """Save component to database."""
        self.s.add(component)
        self.s.flush()
        return component

    def delete_component(self, component_id: str) -> bool:
        """Delete component by ID."""
        component = self.get_component_by_id(component_id)
        if component:
            self.s.delete(component)
            return True
        return False
