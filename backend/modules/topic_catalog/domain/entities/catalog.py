"""
Catalog domain entity for topic discovery and browsing.

This module contains the core business logic for topic catalog management.
"""

from datetime import UTC, datetime
from typing import Any

from .topic_summary import TopicSummary


class CatalogError(Exception):
    """Base exception for catalog-related errors"""

    pass


class InvalidCatalogError(CatalogError):
    """Raised when catalog validation fails"""

    pass


class Catalog:
    """
    Domain entity representing a catalog of topics for discovery and browsing.

    Contains business logic for topic organization, filtering, search, and discovery.
    """

    def __init__(
        self,
        topics: list[TopicSummary],
        last_updated: datetime,
        total_count: int,
    ):
        """
        Initialize a Catalog entity.

        Args:
            topics: List of topic summaries in the catalog
            last_updated: When the catalog was last updated
            total_count: Total number of topics available
        """
        self.topics = topics
        self.last_updated = last_updated
        self.total_count = total_count

        # Validate on creation
        self.validate()

    def validate(self) -> None:
        """
        Validate catalog business rules.

        Raises:
            InvalidCatalogError: If validation fails
        """
        if self.total_count < 0:
            raise InvalidCatalogError("Total count must be non-negative")

        if len(self.topics) > self.total_count:
            raise InvalidCatalogError("Topics list cannot be larger than total count")

    def filter_by_user_level(self, user_level: str) -> list[TopicSummary]:
        """
        Filter topics by user level.

        Args:
            user_level: User level to filter by

        Returns:
            List of topics for the specified user level
        """
        return [topic for topic in self.topics if topic.user_level == user_level]

    def filter_by_readiness(self, ready_only: bool = True) -> list[TopicSummary]:
        """
        Filter topics by readiness for learning.

        Args:
            ready_only: If True, return only ready topics; if False, return all topics

        Returns:
            List of topics matching the readiness criteria
        """
        if ready_only:
            return [topic for topic in self.topics if topic.is_ready_for_learning]
        else:
            return self.topics.copy()

    def search_topics(self, query: str) -> list[TopicSummary]:
        """
        Search topics by query string.

        Args:
            query: Search query

        Returns:
            List of matching topics
        """
        if not query or not query.strip():
            return self.topics.copy()

        return [topic for topic in self.topics if topic.matches_query(query)]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get catalog statistics.

        Returns:
            Dictionary containing catalog statistics
        """
        total_topics = len(self.topics)
        if total_topics == 0:
            return {
                "total_topics": 0,
                "topics_by_user_level": {},
                "topics_by_readiness": {"ready": 0, "not_ready": 0},
                "average_duration": 0.0,
                "duration_distribution": {},
            }

        # User level distribution
        user_level_counts = {}
        for topic in self.topics:
            level = topic.user_level
            user_level_counts[level] = user_level_counts.get(level, 0) + 1

        # Readiness distribution
        ready_count = sum(1 for t in self.topics if t.is_ready_for_learning)
        not_ready_count = total_topics - ready_count

        # Duration statistics
        durations = [t.estimated_duration for t in self.topics]
        avg_duration = sum(durations) / len(durations)

        # Duration distribution (buckets)
        duration_buckets = {"0-15": 0, "16-30": 0, "31-60": 0, "60+": 0}
        for duration in durations:
            if duration <= 15:
                duration_buckets["0-15"] += 1
            elif duration <= 30:
                duration_buckets["16-30"] += 1
            elif duration <= 60:
                duration_buckets["31-60"] += 1
            else:
                duration_buckets["60+"] += 1

        return {
            "total_topics": total_topics,
            "topics_by_user_level": user_level_counts,
            "topics_by_readiness": {"ready": ready_count, "not_ready": not_ready_count},
            "average_duration": round(avg_duration, 1),
            "duration_distribution": duration_buckets,
        }

    def is_stale(self, max_age_hours: int = 24) -> bool:
        """
        Check if the catalog is stale and needs refreshing.

        Args:
            max_age_hours: Maximum age in hours before catalog is considered stale

        Returns:
            True if catalog is stale
        """
        now = datetime.now(UTC)
        age_hours = (now - self.last_updated).total_seconds() / 3600
        return age_hours > max_age_hours
