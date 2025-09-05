"""
Topic Discovery Service for the Topic Catalog module.

This service orchestrates topic retrieval, filtering, and discovery operations.
"""

import logging
from typing import Any

from ..domain.entities.topic_summary import TopicSummary
from ..domain.policies.search_policy import SearchPolicy
from ..domain.repositories.catalog_repository import CatalogRepository

logger = logging.getLogger(__name__)


class TopicDiscoveryError(Exception):
    """Exception raised when topic discovery operations fail."""

    pass


class TopicDiscoveryService:
    """
    Application service for topic discovery and filtering.

    Orchestrates topic retrieval and filtering operations using domain policies
    and repository interfaces.
    """

    def __init__(self, catalog_repository: CatalogRepository):
        """
        Initialize the topic discovery service.

        Args:
            catalog_repository: Repository for catalog and topic data
        """
        self.catalog_repository = catalog_repository

    async def discover_topics(
        self,
        query: str | None = None,
        user_level: str | None = None,
        ready_only: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[TopicSummary]:
        """
        Discover topics based on search criteria.

        Args:
            query: Text search query
            user_level: Filter by user level
            ready_only: Filter by readiness status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching topic summaries

        Raises:
            TopicDiscoveryError: If discovery fails
        """
        try:
            logger.info(f"Discovering topics: query='{query}', user_level={user_level}, ready_only={ready_only}")

            # Get catalog from repository
            catalog = await self.catalog_repository.get_catalog()

            # Apply search policy
            policy = SearchPolicy()
            filtered_topics = policy.apply_filters(
                topics=catalog.topics,
                query=query,
                user_level=user_level,
                ready_only=ready_only,
            )

            # Sort by relevance
            sorted_topics = policy.sort_by_relevance(filtered_topics, query=query)

            # Apply pagination
            paginated_topics = policy.apply_pagination(sorted_topics, limit=limit, offset=offset)

            logger.info(f"Discovered {len(paginated_topics)} topics")
            return paginated_topics

        except Exception as e:
            logger.error(f"Error during topic discovery: {e}")
            raise TopicDiscoveryError(f"Failed to retrieve catalog: {e}") from e

    async def get_topic_by_id(self, topic_id: str) -> TopicSummary:
        """
        Get a specific topic by its ID.

        Args:
            topic_id: The topic identifier

        Returns:
            Topic summary

        Raises:
            TopicDiscoveryError: If topic not found or retrieval fails
        """
        try:
            logger.info(f"Getting topic by ID: {topic_id}")

            # Get catalog from repository
            catalog = await self.catalog_repository.get_catalog()

            # Find topic by ID
            for topic in catalog.topics:
                if topic.topic_id == topic_id:
                    logger.info(f"Found topic: {topic_id}")
                    return topic

            # Topic not found
            raise TopicDiscoveryError("Topic not found")

        except TopicDiscoveryError:
            raise
        except Exception as e:
            logger.error(f"Error getting topic {topic_id}: {e}")
            raise TopicDiscoveryError(f"Failed to retrieve topic: {e}") from e

    async def get_popular_topics(self, limit: int = 10) -> list[TopicSummary]:
        """
        Get popular topics for discovery.

        Args:
            limit: Maximum number of topics to return

        Returns:
            List of popular topic summaries

        Raises:
            TopicDiscoveryError: If retrieval fails
        """
        try:
            logger.info(f"Getting popular topics: limit={limit}")

            # Get catalog from repository
            catalog = await self.catalog_repository.get_catalog()

            # Filter to ready topics only
            ready_topics = [topic for topic in catalog.topics if topic.is_ready_for_learning]

            # Sort by component count (descending) as a popularity metric
            popular_topics = sorted(ready_topics, key=lambda t: t.component_count, reverse=True)

            # Apply limit
            result = popular_topics[:limit]

            logger.info(f"Retrieved {len(result)} popular topics")
            return result

        except Exception as e:
            logger.error(f"Error getting popular topics: {e}")
            raise TopicDiscoveryError(f"Failed to retrieve popular topics: {e}") from e

    async def get_catalog_statistics(self) -> dict[str, Any]:
        """
        Get catalog statistics.

        Returns:
            Dictionary containing catalog statistics

        Raises:
            TopicDiscoveryError: If statistics retrieval fails
        """
        try:
            logger.info("Getting catalog statistics")

            # Get catalog from repository
            catalog = await self.catalog_repository.get_catalog()

            # Use catalog's statistics method
            stats = catalog.get_statistics()

            logger.info("Successfully retrieved catalog statistics")
            return stats

        except Exception as e:
            logger.error(f"Error getting catalog statistics: {e}")
            raise TopicDiscoveryError(f"Failed to retrieve catalog statistics: {e}") from e

    async def refresh_catalog(self) -> dict[str, Any]:
        """
        Refresh the catalog with latest data.

        Returns:
            Dictionary containing refresh results

        Raises:
            TopicDiscoveryError: If refresh fails
        """
        try:
            logger.info("Refreshing catalog")

            # Delegate to repository
            result = await self.catalog_repository.refresh_catalog()

            logger.info("Successfully refreshed catalog")
            return result

        except Exception as e:
            logger.error(f"Error refreshing catalog: {e}")
            raise TopicDiscoveryError(f"Failed to refresh catalog: {e}") from e
