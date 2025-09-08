"""
Topic Catalog Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Protocol

from fastapi import Depends

from modules.content.public import ContentProvider, content_provider

from .service import BrowseTopicsResponse, TopicCatalogService, TopicDetail


class TopicCatalogProvider(Protocol):
    """Protocol defining the topic catalog module's public interface."""

    def browse_topics(self, user_level: str | None = None, limit: int = 100) -> BrowseTopicsResponse: ...
    def get_topic_details(self, topic_id: str) -> TopicDetail | None: ...


def topic_catalog_provider(content: ContentProvider = Depends(content_provider)) -> TopicCatalogProvider:
    """
    Dependency injection provider for topic catalog services.

    Returns the concrete TopicCatalogService which implements the TopicCatalogProvider protocol.
    """
    return TopicCatalogService(content)


__all__ = ["BrowseTopicsResponse", "TopicCatalogProvider", "TopicDetail", "topic_catalog_provider"]
