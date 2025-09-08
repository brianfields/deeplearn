"""
Content Creator Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Protocol

from fastapi import Depends

from modules.content.public import ContentProvider, content_provider
from modules.llm_services.public import LLMServicesProvider, llm_services_provider

from .service import ContentCreatorService, CreateComponentRequest, CreateTopicRequest, TopicCreationResult


class ContentCreatorProvider(Protocol):
    """Protocol defining the content creator module's public interface."""

    async def create_topic_from_source_material(self, request: CreateTopicRequest) -> TopicCreationResult: ...
    async def generate_component(self, topic_id: str, request: CreateComponentRequest) -> str: ...


def content_creator_provider(content: ContentProvider = Depends(content_provider), llm: LLMServicesProvider = Depends(llm_services_provider)) -> ContentCreatorProvider:
    """
    Dependency injection provider for content creator services.

    Returns the concrete ContentCreatorService which implements the ContentCreatorProvider protocol.
    """
    return ContentCreatorService(content, llm)


__all__ = ["ContentCreatorProvider", "CreateComponentRequest", "CreateTopicRequest", "TopicCreationResult", "content_creator_provider"]
