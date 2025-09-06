"""
Topic Catalog Service.

Simple service for topic browsing and discovery operations.
"""

import logging

from modules.content_creation.module_api import create_content_creation_service

from ..domain.repository import TopicCatalogRepository
from ..infrastructure.content_creation_repository import ContentCreationTopicRepository
from .types import (
    BrowseTopicsRequest,
    BrowseTopicsResponse,
    TopicCatalogError,
    TopicDetailResponse,
    TopicSummaryResponse,
)

logger = logging.getLogger(__name__)


class TopicCatalogService:
    """
    Service for topic catalog operations.

    Provides simple topic browsing and discovery functionality.
    """

    def __init__(self, repository: TopicCatalogRepository):
        """Initialize the service with a repository."""
        self.repository = repository

    async def browse_topics(self, request: BrowseTopicsRequest) -> BrowseTopicsResponse:
        """
        Browse topics with optional filtering.

        Args:
            request: Browse request with optional filters

        Returns:
            Response with list of topic summaries

        Raises:
            TopicCatalogError: If browsing fails
        """
        try:
            topics = await self.repository.list_topics(user_level=request.user_level, limit=request.limit)

            topic_responses = [
                TopicSummaryResponse(
                    id=topic.id,
                    title=topic.title,
                    core_concept=topic.core_concept,
                    user_level=topic.user_level,
                    learning_objectives=topic.learning_objectives,
                    key_concepts=topic.key_concepts,
                    created_at=topic.created_at,
                    component_count=topic.component_count,
                )
                for topic in topics
            ]

            return BrowseTopicsResponse(topics=topic_responses, total_count=len(topic_responses))

        except Exception as e:
            logger.error(f"Failed to browse topics: {e}")
            raise TopicCatalogError(f"Failed to browse topics: {e}") from e

    async def get_topic_by_id(self, topic_id: str) -> TopicDetailResponse:
        """
        Get detailed topic information by ID.

        Args:
            topic_id: The topic ID to retrieve

        Returns:
            Detailed topic information

        Raises:
            TopicCatalogError: If topic not found or retrieval fails
        """
        try:
            topic = await self.repository.get_topic_by_id(topic_id)

            if not topic:
                raise TopicCatalogError(f"Topic not found: {topic_id}")

            return TopicDetailResponse(
                id=topic.id,
                title=topic.title,
                core_concept=topic.core_concept,
                user_level=topic.user_level,
                learning_objectives=topic.learning_objectives,
                key_concepts=topic.key_concepts,
                key_aspects=topic.key_aspects,
                target_insights=topic.target_insights,
                source_material=topic.source_material,
                refined_material=topic.refined_material,
                created_at=topic.created_at,
                updated_at=topic.updated_at,
                components=topic.components,
                component_count=topic.component_count,
                is_ready_for_learning=topic.is_ready_for_learning(),
            )

        except TopicCatalogError:
            raise
        except Exception as e:
            logger.error(f"Failed to get topic {topic_id}: {e}")
            raise TopicCatalogError(f"Failed to get topic: {e}") from e


def create_topic_catalog_service() -> TopicCatalogService:
    """
    Factory function to create a topic catalog service.

    Returns:
        Configured topic catalog service
    """
    # Create content creation service
    content_creation_service = create_content_creation_service()

    # Create repository
    repository = ContentCreationTopicRepository(content_creation_service)

    # Create and return service
    return TopicCatalogService(repository)
