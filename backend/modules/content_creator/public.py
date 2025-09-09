"""
Content Creator Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Protocol

from fastapi import Depends

from modules.content.public import ContentProvider, content_provider

from .service import ContentCreatorService, CreateTopicRequest, TopicCreationResult


class ContentCreatorProvider(Protocol):
    """Protocol defining the content creator module's public interface."""

    async def create_topic_from_source_material(self, request: CreateTopicRequest) -> TopicCreationResult: ...

    # generate_component method removed - it was unused


def content_creator_provider(content: ContentProvider = Depends(content_provider)) -> ContentCreatorProvider:
    """
    Dependency injection provider for content creator services.
    No longer needs LLM services - flows handle LLM interactions internally.

    Returns the concrete ContentCreatorService which implements the ContentCreatorProvider protocol.
    """
    return ContentCreatorService(content)


__all__ = ["ContentCreatorProvider", "CreateTopicRequest", "TopicCreationResult", "content_creator_provider"]
