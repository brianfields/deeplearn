"""
Topic Catalog Module API.

This module provides the public interface for topic browsing and discovery.
"""

from .service import TopicCatalogService, create_topic_catalog_service
from .types import (
    BrowseTopicsRequest,
    BrowseTopicsResponse,
    TopicCatalogError,
    TopicDetailResponse,
    TopicSummaryResponse,
)

__all__ = [
    "BrowseTopicsRequest",
    "BrowseTopicsResponse",
    "TopicCatalogError",
    "TopicCatalogService",
    "TopicDetailResponse",
    "TopicSummaryResponse",
    "create_topic_catalog_service",
]
