"""
Topic Catalog Module API.

This module provides the public interface for the topic catalog module.
All external modules should only import from this module_api package.
"""

# Main service
# Domain entities (for type hints and advanced usage)
from ..domain.entities.catalog import Catalog
from ..domain.entities.topic_summary import InvalidTopicSummaryError, TopicSummary

# Domain policies (for external validation)
from ..domain.policies.search_policy import SearchPolicy

# Repository interface (for dependency injection)
from ..domain.repositories.catalog_repository import (
    CatalogNotFoundError,
    CatalogRepository,
    CatalogRepositoryError,
)
from .topic_catalog_service import TopicCatalogService, create_topic_catalog_service

# Types and DTOs
from .types import (
    # Request types
    BrowseTopicsRequest,
    # Response types
    BrowseTopicsResponse,
    # Exception types
    CatalogStatisticsResponse,
    GetRecommendationsRequest,
    GetRecommendationsResponse,
    ModuleHealthResponse,
    PaginationRequest,
    PaginationResponse,
    SearchSuggestionsRequest,
    SearchSuggestionsResponse,
    SearchTopicsRequest,
    SearchTopicsResponse,
    TopicCatalogError,
    TopicCatalogStatsResponse,
    TopicFilters,
    TopicSortOptions,
    TopicSummaryResponse,
)

__all__ = [
    # Main service
    "TopicCatalogService",
    "create_topic_catalog_service",
    # Request types
    "SearchTopicsRequest",
    "BrowseTopicsRequest",
    "GetRecommendationsRequest",
    "SearchSuggestionsRequest",
    "TopicFilters",
    "TopicSortOptions",
    "PaginationRequest",
    # Response types
    "TopicSummaryResponse",
    "SearchTopicsResponse",
    "BrowseTopicsResponse",
    "GetRecommendationsResponse",
    "SearchSuggestionsResponse",
    "TopicCatalogStatsResponse",
    "ModuleHealthResponse",
    "PaginationResponse",
    # Exception types
    "CatalogStatisticsResponse",
    "TopicCatalogError",
    "InvalidTopicSummaryError",
    "CatalogRepositoryError",
    "CatalogNotFoundError",
    # Domain entities (for type hints)
    "TopicSummary",
    "Catalog",
    # Repository interface
    "CatalogRepository",
    # Domain policies
    "SearchPolicy",
]
