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


class SearchTopicsResponse(BaseModel):
    """Response for topic search."""

    topics: list[TopicSummary]
    total: int
    query: str | None = None


class CatalogStatistics(BaseModel):
    """Catalog statistics DTO."""

    total_topics: int
    topics_by_user_level: dict[str, int]
    topics_by_readiness: dict[str, int]
    average_duration: float
    duration_distribution: dict[str, int]


class RefreshCatalogResponse(BaseModel):
    """Response for catalog refresh."""

    refreshed_topics: int
    total_topics: int
    timestamp: str


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

    def search_topics(
        self,
        query: str | None = None,
        user_level: str | None = None,
        min_duration: int | None = None,
        max_duration: int | None = None,
        ready_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> SearchTopicsResponse:
        """
        Search topics with query and filters.

        Args:
            query: Search query string
            user_level: Filter by user level
            min_duration: Minimum duration filter (not implemented yet)
            max_duration: Maximum duration filter (not implemented yet)
            ready_only: Only return ready topics
            limit: Maximum number of topics to return
            offset: Pagination offset

        Returns:
            Response with matching topic summaries
        """
        # Get topics from content module (using existing search)
        topics = self.content.search_topics(user_level=user_level, limit=limit + offset)

        # Convert to summary DTOs
        summaries = [
            TopicSummary(
                id=topic.id,
                title=topic.title,
                core_concept=topic.core_concept,
                user_level=topic.user_level,
                learning_objectives=topic.learning_objectives,
                key_concepts=topic.key_concepts,
                component_count=len(topic.components),
            )
            for topic in topics
        ]

        # Apply client-side filtering
        if query:
            query_lower = query.lower()
            summaries = [
                topic
                for topic in summaries
                if (query_lower in topic.title.lower() or query_lower in topic.core_concept.lower() or any(query_lower in obj.lower() for obj in topic.learning_objectives) or any(query_lower in concept.lower() for concept in topic.key_concepts))
            ]

        if ready_only:
            summaries = [topic for topic in summaries if topic.component_count > 0]

        # Apply pagination
        total = len(summaries)
        summaries = summaries[offset : offset + limit]

        return SearchTopicsResponse(topics=summaries, total=total, query=query)

    def get_popular_topics(self, limit: int = 10) -> list[TopicSummary]:
        """
        Get popular topics (for now, just return first N topics).

        Args:
            limit: Maximum number of topics to return

        Returns:
            List of popular topic summaries
        """
        # For now, just return the first N topics
        # In a real implementation, this would be based on usage metrics
        topics = self.content.search_topics(limit=limit)

        return [
            TopicSummary(
                id=topic.id,
                title=topic.title,
                core_concept=topic.core_concept,
                user_level=topic.user_level,
                learning_objectives=topic.learning_objectives,
                key_concepts=topic.key_concepts,
                component_count=len(topic.components),
            )
            for topic in topics
        ]

    def get_catalog_statistics(self) -> CatalogStatistics:
        """
        Get catalog statistics.

        Returns:
            Statistics about the topic catalog
        """
        # Get all topics for statistics
        all_topics = self.content.search_topics(limit=1000)  # Large limit to get all

        # Calculate statistics
        total_topics = len(all_topics)

        # Group by user level
        topics_by_user_level = {}
        for topic in all_topics:
            level = topic.user_level
            topics_by_user_level[level] = topics_by_user_level.get(level, 0) + 1

        # Group by readiness
        topics_by_readiness = {"ready": 0, "in_progress": 0, "draft": 0}
        total_duration = 0
        duration_distribution = {"0-15": 0, "15-30": 0, "30-60": 0, "60+": 0}

        for topic in all_topics:
            component_count = len(topic.components)

            # Readiness
            if component_count > 0:
                topics_by_readiness["ready"] += 1
            else:
                topics_by_readiness["draft"] += 1

            # Duration (estimate: 3 min per component, min 5 min)
            duration = max(5, component_count * 3)
            total_duration += duration

            # Duration distribution
            if duration <= 15:
                duration_distribution["0-15"] += 1
            elif duration <= 30:
                duration_distribution["15-30"] += 1
            elif duration <= 60:
                duration_distribution["30-60"] += 1
            else:
                duration_distribution["60+"] += 1

        average_duration = total_duration / total_topics if total_topics > 0 else 0

        return CatalogStatistics(
            total_topics=total_topics,
            topics_by_user_level=topics_by_user_level,
            topics_by_readiness=topics_by_readiness,
            average_duration=average_duration,
            duration_distribution=duration_distribution,
        )

    def refresh_catalog(self) -> RefreshCatalogResponse:
        """
        Refresh the catalog (placeholder implementation).

        Returns:
            Refresh response with statistics
        """
        from datetime import datetime

        # In a real implementation, this would refresh data from external sources
        # For now, just return current statistics
        all_topics = self.content.search_topics(limit=1000)

        return RefreshCatalogResponse(
            refreshed_topics=len(all_topics),
            total_topics=len(all_topics),
            timestamp=datetime.now().isoformat(),
        )
