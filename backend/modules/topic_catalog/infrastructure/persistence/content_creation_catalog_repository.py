"""
Content Creation integration for Topic Catalog Repository.

This module provides the concrete implementation of the catalog repository
that integrates with the content creation module to provide topic summaries.
"""

from datetime import UTC, datetime
import logging
from typing import Any

from modules.content_creation.module_api import ContentCreationService

from ...domain.entities.catalog import Catalog
from ...domain.entities.topic_summary import TopicSummary
from ...domain.repositories.catalog_repository import CatalogRepository

logger = logging.getLogger(__name__)


class ContentCreationCatalogRepository(CatalogRepository):
    """
    Catalog repository implementation that integrates with content creation module.

    This repository provides topic catalog functionality by consuming
    topics from the content creation module and converting them to
    topic summaries optimized for browsing and discovery.
    """

    def __init__(self, content_creation_service: ContentCreationService):
        """
        Initialize repository with content creation service.

        Args:
            content_creation_service: Service for accessing topic data
        """
        self.content_creation_service = content_creation_service

    async def get_catalog(self) -> Catalog:
        """Get the catalog with all available topics."""
        try:
            logger.info("Building catalog from content creation service")

            # Get all topics from content creation
            topic_responses = await self.content_creation_service.list_topics()

            # Convert to topic summaries
            topic_summaries = [self._convert_topic_response_to_summary(topic_response) for topic_response in topic_responses]

            # Create catalog
            catalog = Catalog(topics=topic_summaries, last_updated=datetime.now(UTC), total_count=len(topic_summaries))

            logger.info(f"Built catalog with {len(topic_summaries)} topics")
            return catalog

        except Exception as e:
            logger.error(f"Failed to build catalog: {e}")
            raise

    async def refresh_catalog(self) -> dict[str, Any]:
        """Refresh the catalog with latest data."""
        try:
            logger.info("Refreshing catalog")

            # Delegate to content creation service
            result = await self.content_creation_service.refresh_topic_cache()

            logger.info("Successfully refreshed catalog")
            return result

        except Exception as e:
            logger.error(f"Failed to refresh catalog: {e}")
            raise

    def _convert_topic_response_to_summary(self, topic_response) -> TopicSummary:
        """Convert a TopicSummaryResponse to a TopicSummary."""
        return TopicSummary(
            topic_id=topic_response.id,
            title=topic_response.title,
            core_concept=topic_response.core_concept,
            user_level=topic_response.user_level,
            learning_objectives=topic_response.learning_objectives,
            key_concepts=topic_response.key_concepts,
            estimated_duration=topic_response.estimated_duration,
            component_count=topic_response.component_count,
            is_ready_for_learning=topic_response.is_ready_for_learning,
            created_at=topic_response.created_at,
            updated_at=topic_response.updated_at,
        )
