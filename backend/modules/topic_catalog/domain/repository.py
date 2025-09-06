"""
Topic Catalog Repository Interface.

Simple repository interface for topic data access.
"""

from abc import ABC, abstractmethod

from .entities import TopicDetail, TopicSummary


class TopicCatalogRepository(ABC):
    """Abstract repository for topic catalog operations."""

    @abstractmethod
    async def list_topics(self, user_level: str | None = None, limit: int = 100) -> list[TopicSummary]:
        """
        List topics for browsing.

        Args:
            user_level: Optional filter by user level
            limit: Maximum number of topics to return

        Returns:
            List of topic summaries
        """
        pass

    @abstractmethod
    async def get_topic_by_id(self, topic_id: str) -> TopicDetail | None:
        """
        Get detailed topic information by ID.

        Args:
            topic_id: The topic ID to retrieve

        Returns:
            Topic details or None if not found
        """
        pass
