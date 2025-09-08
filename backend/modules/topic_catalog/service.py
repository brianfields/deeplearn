"""
Topic Catalog Module - Service Layer

Simple topic browsing and discovery service.
Uses content module for data access.
"""

from pydantic import BaseModel

from modules.content.public import ContentProvider


# DTOs
class TopicSummary(BaseModel):
    """DTO for topic summary in browsing lists."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    component_count: int

    def matches_user_level(self, user_level: str) -> bool:
        """Check if topic matches specified user level."""
        return self.user_level == user_level


class TopicDetail(BaseModel):
    """DTO for detailed topic information."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    components: list[dict]
    created_at: str
    component_count: int

    def is_ready_for_learning(self) -> bool:
        """Check if topic has components for learning."""
        return len(self.components) > 0


class BrowseTopicsResponse(BaseModel):
    """Response for topic browsing."""

    topics: list[TopicSummary]
    total: int


class TopicCatalogService:
    """Service for topic catalog operations."""

    def __init__(self, content: ContentProvider):
        """Initialize with content provider."""
        self.content = content

    def browse_topics(self, user_level: str | None = None, limit: int = 100) -> BrowseTopicsResponse:
        """
        Browse topics with optional user level filter.

        Args:
            user_level: Optional filter by user level
            limit: Maximum number of topics to return

        Returns:
            Response with topic summaries
        """
        # Get topics from content module
        topics = self.content.search_topics(user_level=user_level, limit=limit)

        # Convert to summary DTOs
        summaries = [
            TopicSummary(id=topic.id, title=topic.title, core_concept=topic.core_concept, user_level=topic.user_level, learning_objectives=topic.learning_objectives, key_concepts=topic.key_concepts, component_count=len(topic.components))
            for topic in topics
        ]

        return BrowseTopicsResponse(topics=summaries, total=len(summaries))

    def get_topic_details(self, topic_id: str) -> TopicDetail | None:
        """
        Get detailed topic information by ID.

        Args:
            topic_id: Topic identifier

        Returns:
            Topic details or None if not found
        """
        topic = self.content.get_topic(topic_id)
        if not topic:
            return None

        return TopicDetail(
            id=topic.id,
            title=topic.title,
            core_concept=topic.core_concept,
            user_level=topic.user_level,
            learning_objectives=topic.learning_objectives,
            key_concepts=topic.key_concepts,
            components=[comp.model_dump() for comp in topic.components],
            created_at=str(topic.created_at),
            component_count=len(topic.components),
        )
