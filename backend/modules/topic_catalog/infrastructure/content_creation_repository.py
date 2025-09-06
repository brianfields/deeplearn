"""
Content Creation Repository Implementation.

Implements topic catalog repository by delegating to the content creation module.
"""

from modules.content_creation.module_api import ContentCreationService

from ..domain.entities import TopicDetail, TopicSummary
from ..domain.repository import TopicCatalogRepository


class ContentCreationTopicRepository(TopicCatalogRepository):
    """Repository implementation that uses the content creation module."""

    def __init__(self, content_creation_service: ContentCreationService):
        """Initialize with content creation service."""
        self.content_creation_service = content_creation_service

    async def list_topics(self, user_level: str | None = None, limit: int = 100) -> list[TopicSummary]:
        """List topics by delegating to content creation service."""
        # Get all topics from content creation
        topics_response = await self.content_creation_service.get_all_topics()

        # Convert to domain entities
        topic_summaries = []
        for topic_dto in topics_response.topics:
            # Apply user level filter if specified
            if user_level and topic_dto.user_level != user_level:
                continue

            summary = TopicSummary(
                id=topic_dto.id,
                title=topic_dto.title,
                core_concept=topic_dto.core_concept,
                user_level=topic_dto.user_level,
                learning_objectives=topic_dto.learning_objectives,
                key_concepts=topic_dto.key_concepts,
                created_at=topic_dto.created_at,
                component_count=topic_dto.component_count,
            )
            topic_summaries.append(summary)

            # Apply limit
            if len(topic_summaries) >= limit:
                break

        return topic_summaries

    async def get_topic_by_id(self, topic_id: str) -> TopicDetail | None:
        """Get topic details by delegating to content creation service."""
        try:
            topic_response = await self.content_creation_service.get_topic(topic_id)

            # Convert to domain entity
            return TopicDetail(
                id=topic_response.id,
                title=topic_response.title,
                core_concept=topic_response.core_concept,
                user_level=topic_response.user_level,
                learning_objectives=topic_response.learning_objectives,
                key_concepts=topic_response.key_concepts,
                key_aspects=topic_response.key_aspects,
                target_insights=topic_response.target_insights,
                source_material=topic_response.source_material,
                refined_material=topic_response.refined_material,
                created_at=topic_response.created_at,
                updated_at=topic_response.updated_at,
                components=topic_response.components,
            )
        except Exception:
            # Topic not found or other error
            return None
