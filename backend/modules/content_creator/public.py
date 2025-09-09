"""
Content Creator Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Protocol

from modules.content.public import ContentProvider

from .service import ContentCreatorService, CreateTopicRequest, TopicCreationResult


class ContentCreatorProvider(Protocol):
    """Protocol defining the content creator module's public interface."""

    async def create_topic_from_source_material(self, request: CreateTopicRequest) -> TopicCreationResult: ...

    # generate_component method removed - it was unused


def content_creator_provider(content: ContentProvider) -> ContentCreatorProvider:
    """
    Dependency injection provider for content creator services.
    No longer needs LLM services - flows handle LLM interactions internally.

    Args:
        content: Content service instance (built with same session as caller).

    Returns:
        ContentCreatorService instance that implements the ContentCreatorProvider protocol.
    """
    return ContentCreatorService(content)


__all__ = ["ContentCreatorProvider", "CreateTopicRequest", "TopicCreationResult", "content_creator_provider"]
