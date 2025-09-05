"""
Topic Catalog Service - Module API.

This module provides the public API for the topic catalog module.
It orchestrates between domain entities, application services, and external modules.
"""

import logging
from typing import Any

from ..application.topic_discovery_service import TopicDiscoveryError, TopicDiscoveryService
from ..domain.repositories.catalog_repository import CatalogRepository
from .types import (
    BrowseTopicsRequest,
    BrowseTopicsResponse,
    GetRecommendationsRequest,
    GetRecommendationsResponse,
    SearchSuggestionsRequest,
    SearchSuggestionsResponse,
    SearchTopicsRequest,
    SearchTopicsResponse,
    TopicCatalogError,
    TopicCatalogStatsResponse,
    TopicSummaryResponse,
)

logger = logging.getLogger(__name__)


class TopicCatalogService:
    """
    Main service for topic catalog operations.

    This service provides a thin orchestration layer that coordinates
    between domain entities, application services, and external dependencies.
    """

    def __init__(self, catalog_repository: CatalogRepository):
        """
        Initialize topic catalog service.

        Args:
            catalog_repository: Repository for catalog persistence
        """
        self.catalog_repository = catalog_repository

        # Initialize application services (lazy loading)
        self._topic_discovery_service: TopicDiscoveryService | None = None

    @property
    def topic_discovery_service(self) -> TopicDiscoveryService:
        """Get topic discovery service (lazy initialization)."""
        if self._topic_discovery_service is None:
            self._topic_discovery_service = TopicDiscoveryService(self.catalog_repository)
        return self._topic_discovery_service

    async def search_topics(self, request: SearchTopicsRequest) -> SearchTopicsResponse:
        """
        Search topics by criteria.

        Args:
            request: Search request

        Returns:
            Search response with matching topics

        Raises:
            TopicCatalogError: If search fails
        """
        try:
            logger.info(f"Searching topics: query='{request.query}', user_level={request.user_level}")

            # Discover topics using application service
            topics = await self.topic_discovery_service.discover_topics(
                query=request.query,
                user_level=request.user_level,
                min_duration=request.min_duration,
                max_duration=request.max_duration,
                ready_only=request.ready_only,
                limit=request.limit,
                offset=request.offset,
            )

            # Convert to response DTOs
            topic_responses = [TopicSummaryResponse.from_topic_summary(topic) for topic in topics]

            logger.info(f"Successfully found {len(topic_responses)} topics")
            return SearchTopicsResponse(
                topics=topic_responses,
                total_count=len(topic_responses),  # Note: This is the returned count, not total available
                query=request.query,
                filters={
                    "user_level": request.user_level,
                    "min_duration": request.min_duration,
                    "max_duration": request.max_duration,
                    "ready_only": request.ready_only,
                },
                pagination={"limit": request.limit, "offset": request.offset},
            )

        except TopicDiscoveryError as e:
            logger.error(f"Topic discovery error: {e}")
            raise TopicCatalogError(f"Search failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error searching topics: {e}")
            raise TopicCatalogError(f"Unexpected error: {e}") from e

    async def get_topic_by_id(self, topic_id: str) -> TopicSummaryResponse:
        """
        Get a topic by ID.

        Args:
            topic_id: Topic identifier

        Returns:
            Topic summary response

        Raises:
            TopicCatalogError: If topic not found or retrieval fails
        """
        try:
            logger.info(f"Getting topic: {topic_id}")

            topic = await self.topic_discovery_service.get_topic_by_id(topic_id)
            response = TopicSummaryResponse.from_topic_summary(topic)

            logger.info(f"Successfully retrieved topic {topic_id}")
            return response

        except TopicDiscoveryError as e:
            if "not found" in str(e).lower():
                raise TopicCatalogError(f"Topic not found: {topic_id}") from e
            logger.error(f"Topic discovery error: {e}")
            raise TopicCatalogError(f"Failed to retrieve topic: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting topic {topic_id}: {e}")
            raise TopicCatalogError(f"Unexpected error: {e}") from e

    async def browse_topics(self, request: BrowseTopicsRequest) -> BrowseTopicsResponse:
        """
        Browse topics organized by categories.

        Args:
            request: Browse request

        Returns:
            Browse response with categorized topics

        Raises:
            TopicCatalogError: If browsing fails
        """
        try:
            logger.info(f"Browsing topics: user_level={request.user_level}, ready_only={request.ready_only}")

            # Get categorized topics
            categories = await self.topic_discovery_service.browse_by_category(user_level=request.user_level, ready_only=request.ready_only)

            # Convert to response format
            category_responses = {}
            total_topics = 0

            for category_name, topics in categories.items():
                topic_responses = [TopicSummaryResponse.from_topic_summary(topic) for topic in topics]
                category_responses[category_name] = topic_responses
                total_topics += len(topic_responses)

            logger.info(f"Successfully organized {total_topics} topics into {len(category_responses)} categories")
            return BrowseTopicsResponse(
                categories=category_responses,
                total_topics=total_topics,
                filters={"user_level": request.user_level, "ready_only": request.ready_only},
            )

        except TopicDiscoveryError as e:
            logger.error(f"Topic discovery error: {e}")
            raise TopicCatalogError(f"Browse failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error browsing topics: {e}")
            raise TopicCatalogError(f"Unexpected error: {e}") from e

    async def get_recommendations(self, request: GetRecommendationsRequest) -> GetRecommendationsResponse:
        """
        Get topic recommendations for a user.

        Args:
            request: Recommendations request

        Returns:
            Recommendations response

        Raises:
            TopicCatalogError: If recommendation generation fails
        """
        try:
            logger.info(f"Getting recommendations: user_level={request.user_level}, limit={request.limit}")

            # Get recommendations using application service
            topics = await self.topic_discovery_service.get_recommended_topics(user_level=request.user_level, completed_topics=request.completed_topics, limit=request.limit)

            # Convert to response DTOs
            topic_responses = [TopicSummaryResponse.from_topic_summary(topic) for topic in topics]

            logger.info(f"Successfully generated {len(topic_responses)} recommendations")
            return GetRecommendationsResponse(
                recommendations=topic_responses,
                user_level=request.user_level,
                completed_topics=request.completed_topics or [],
                recommendation_count=len(topic_responses),
            )

        except TopicDiscoveryError as e:
            logger.error(f"Topic discovery error: {e}")
            raise TopicCatalogError(f"Recommendation failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting recommendations: {e}")
            raise TopicCatalogError(f"Unexpected error: {e}") from e

    async def get_search_suggestions(self, request: SearchSuggestionsRequest) -> SearchSuggestionsResponse:
        """
        Get search suggestions for a query.

        Args:
            request: Search suggestions request

        Returns:
            Search suggestions response

        Raises:
            TopicCatalogError: If suggestion generation fails
        """
        try:
            logger.info(f"Getting search suggestions for: '{request.query}'")

            # Get suggestions using application service
            suggestions = await self.topic_discovery_service.get_search_suggestions(request.query)

            logger.info(f"Successfully generated {len(suggestions)} suggestions")
            return SearchSuggestionsResponse(query=request.query, suggestions=suggestions)

        except TopicDiscoveryError as e:
            logger.error(f"Topic discovery error: {e}")
            raise TopicCatalogError(f"Suggestion generation failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting suggestions: {e}")
            raise TopicCatalogError(f"Unexpected error: {e}") from e

    async def get_popular_topics(self, limit: int = 10) -> list[TopicSummaryResponse]:
        """
        Get popular topics for discovery.

        Args:
            limit: Maximum number of topics to return

        Returns:
            List of popular topic responses

        Raises:
            TopicCatalogError: If retrieval fails
        """
        try:
            logger.info(f"Getting popular topics: limit={limit}")

            # Get popular topics using application service
            topics = await self.topic_discovery_service.get_popular_topics(limit=limit)

            # Convert to response DTOs
            topic_responses = [TopicSummaryResponse.from_topic_summary(topic) for topic in topics]

            logger.info(f"Successfully retrieved {len(topic_responses)} popular topics")
            return topic_responses

        except TopicDiscoveryError as e:
            logger.error(f"Topic discovery error: {e}")
            raise TopicCatalogError(f"Failed to get popular topics: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting popular topics: {e}")
            raise TopicCatalogError(f"Unexpected error: {e}") from e

    async def get_catalog_statistics(self) -> TopicCatalogStatsResponse:
        """
        Get catalog statistics.

        Returns:
            Catalog statistics response

        Raises:
            TopicCatalogError: If statistics retrieval fails
        """
        try:
            logger.info("Getting catalog statistics")

            # Get statistics using application service
            stats = await self.topic_discovery_service.get_catalog_statistics()

            response = TopicCatalogStatsResponse(
                total_topics=stats.get("total_topics", 0),
                topics_by_user_level=stats.get("topics_by_user_level", {}),
                topics_by_readiness=stats.get("topics_by_readiness", {}),
                average_duration=stats.get("average_duration", 0.0),
                duration_distribution=stats.get("duration_distribution", {}),
            )

            logger.info("Successfully retrieved catalog statistics")
            return response

        except TopicDiscoveryError as e:
            logger.error(f"Topic discovery error: {e}")
            raise TopicCatalogError(f"Failed to get statistics: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting statistics: {e}")
            raise TopicCatalogError(f"Unexpected error: {e}") from e

    async def refresh_catalog(self) -> dict[str, Any]:
        """
        Refresh the catalog with latest data.

        Returns:
            Refresh results

        Raises:
            TopicCatalogError: If refresh fails
        """
        try:
            logger.info("Refreshing catalog")

            # Refresh using application service
            result = await self.topic_discovery_service.refresh_catalog()

            logger.info(f"Successfully refreshed catalog: {result}")
            return result

        except TopicDiscoveryError as e:
            logger.error(f"Topic discovery error: {e}")
            raise TopicCatalogError(f"Failed to refresh catalog: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error refreshing catalog: {e}")
            raise TopicCatalogError(f"Unexpected error: {e}") from e


def create_topic_catalog_service(catalog_repository: CatalogRepository) -> TopicCatalogService:
    """
    Factory function to create a topic catalog service.

    Args:
        catalog_repository: Repository for catalog persistence

    Returns:
        Configured topic catalog service
    """
    return TopicCatalogService(catalog_repository=catalog_repository)
