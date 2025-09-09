"""
Topic Catalog Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Protocol

from fastapi import Depends

from modules.content.public import ContentProvider, content_provider

from .service import (
    BrowseTopicsResponse,
    CatalogStatistics,
    RefreshCatalogResponse,
    SearchTopicsResponse,
    TopicCatalogService,
    TopicDetail,
    TopicSummary,
)


class TopicCatalogProvider(Protocol):
    """Protocol defining the topic catalog module's public interface."""

    def browse_topics(self, user_level: str | None = None, limit: int = 100) -> BrowseTopicsResponse: ...
    def get_topic_details(self, topic_id: str) -> TopicDetail | None: ...
    def search_topics(
        self,
        query: str | None = None,
        user_level: str | None = None,
        min_duration: int | None = None,
        max_duration: int | None = None,
        ready_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> SearchTopicsResponse: ...
    def get_popular_topics(self, limit: int = 10) -> list[TopicSummary]: ...
    def get_catalog_statistics(self) -> CatalogStatistics: ...
    def refresh_catalog(self) -> RefreshCatalogResponse: ...


def topic_catalog_provider(content: ContentProvider = Depends(content_provider)) -> TopicCatalogProvider:
    """
    Dependency injection provider for topic catalog services.

    Returns the concrete TopicCatalogService which implements the TopicCatalogProvider protocol.
    """
    return TopicCatalogService(content)


__all__ = [
    "BrowseTopicsResponse",
    "CatalogStatistics",
    "RefreshCatalogResponse",
    "SearchTopicsResponse",
    "TopicCatalogProvider",
    "TopicDetail",
    "TopicSummary",
    "topic_catalog_provider",
]
