"""
Type definitions for Topic Catalog module API.

This module defines the data transfer objects (DTOs) and types
used in the public API of the topic catalog module.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..domain.entities.topic_summary import TopicSummary


class TopicCatalogError(Exception):
    """Base exception for topic catalog module errors"""

    pass


# Request DTOs
class SearchTopicsRequest(BaseModel):
    """Request to search topics in the catalog."""

    query: str | None = Field(default=None, description="Text search query")
    user_level: str | None = Field(default=None, description="Filter by user level")
    min_duration: int | None = Field(default=None, ge=0, description="Minimum duration in minutes")
    max_duration: int | None = Field(default=None, ge=0, description="Maximum duration in minutes")
    ready_only: bool | None = Field(default=None, description="Filter by readiness status")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Results offset")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Python variables",
                "user_level": "beginner",
                "min_duration": 10,
                "max_duration": 30,
                "ready_only": True,
                "limit": 20,
                "offset": 0,
            }
        }


class BrowseTopicsRequest(BaseModel):
    """Request to browse topics by categories."""

    user_level: str | None = Field(default=None, description="Filter by user level")
    ready_only: bool = Field(default=True, description="Only include ready topics")

    class Config:
        json_schema_extra = {"example": {"user_level": "intermediate", "ready_only": True}}


class GetRecommendationsRequest(BaseModel):
    """Request to get topic recommendations."""

    user_level: str = Field(..., description="User's skill level")
    completed_topics: list[str] | None = Field(default=None, description="List of completed topic IDs")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum recommendations")

    class Config:
        json_schema_extra = {"example": {"user_level": "intermediate", "completed_topics": ["topic_123", "topic_456"], "limit": 5}}


class SearchSuggestionsRequest(BaseModel):
    """Request to get search suggestions."""

    query: str = Field(..., min_length=2, description="Partial search query")

    class Config:
        json_schema_extra = {"example": {"query": "Pyt"}}


# Response DTOs
class TopicSummaryResponse(BaseModel):
    """Response containing topic summary data."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    estimated_duration: int
    component_count: int
    is_ready_for_learning: bool
    created_at: str
    updated_at: str
    difficulty_level: str
    duration_display: str
    readiness_status: str
    tags: list[str]

    @classmethod
    def from_topic_summary(cls, topic: TopicSummary) -> "TopicSummaryResponse":
        """Create response from domain topic summary."""
        return cls(
            id=topic.topic_id,
            title=topic.title,
            core_concept=topic.core_concept,
            user_level=topic.user_level,
            learning_objectives=topic.learning_objectives,
            key_concepts=topic.key_concepts,
            estimated_duration=topic.estimated_duration,
            component_count=topic.component_count,
            is_ready_for_learning=topic.is_ready_for_learning,
            created_at=topic.created_at.isoformat(),
            updated_at=topic.updated_at.isoformat(),
            difficulty_level=topic.get_difficulty_level(),
            duration_display=topic.get_duration_display(),
            readiness_status=topic.get_readiness_status(),
            tags=topic.get_tags(),
        )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "topic_123",
                "title": "Python Variables",
                "core_concept": "Understanding variable declaration and usage",
                "user_level": "beginner",
                "learning_objectives": ["Declare variables", "Assign values"],
                "key_concepts": ["variable", "assignment", "data types"],
                "estimated_duration": 15,
                "component_count": 3,
                "is_ready_for_learning": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "difficulty_level": "Beginner",
                "duration_display": "15 min",
                "readiness_status": "Ready",
                "tags": ["Beginner", "15 min", "Ready", "3 components"],
            }
        }


class SearchTopicsResponse(BaseModel):
    """Response containing search results."""

    topics: list[TopicSummaryResponse]
    total_count: int
    query: str | None
    filters: dict[str, Any]
    pagination: dict[str, int]

    class Config:
        json_schema_extra = {
            "example": {
                "topics": [],  # Would contain TopicSummaryResponse objects
                "total_count": 25,
                "query": "Python variables",
                "filters": {"user_level": "beginner", "ready_only": True},
                "pagination": {"limit": 20, "offset": 0},
            }
        }


class BrowseTopicsResponse(BaseModel):
    """Response containing categorized topics."""

    categories: dict[str, list[TopicSummaryResponse]]
    total_topics: int
    filters: dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "categories": {
                    "Popular": [],  # Would contain TopicSummaryResponse objects
                    "Quick Learning (≤15 min)": [],
                    "Beginner Friendly": [],
                },
                "total_topics": 45,
                "filters": {"user_level": "beginner", "ready_only": True},
            }
        }


class GetRecommendationsResponse(BaseModel):
    """Response containing topic recommendations."""

    recommendations: list[TopicSummaryResponse]
    user_level: str
    completed_topics: list[str]
    recommendation_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "recommendations": [],  # Would contain TopicSummaryResponse objects
                "user_level": "intermediate",
                "completed_topics": ["topic_123", "topic_456"],
                "recommendation_count": 5,
            }
        }


class SearchSuggestionsResponse(BaseModel):
    """Response containing search suggestions."""

    query: str
    suggestions: list[str]

    class Config:
        json_schema_extra = {"example": {"query": "Pyt", "suggestions": ["Python", "Python Variables", "PyTorch"]}}


class CatalogStatisticsResponse(BaseModel):
    """Response containing catalog statistics."""

    total_topics: int
    topics_by_user_level: dict[str, int]
    topics_by_readiness: dict[str, int]
    average_duration: float
    duration_distribution: dict[str, int]

    class Config:
        json_schema_extra = {
            "example": {
                "total_topics": 150,
                "topics_by_user_level": {"beginner": 60, "intermediate": 70, "advanced": 20},
                "topics_by_readiness": {"ready": 120, "not_ready": 30},
                "average_duration": 22.5,
                "duration_distribution": {"0-15": 45, "16-30": 80, "31-60": 20, "60+": 5},
            }
        }


# Alias for backward compatibility
TopicCatalogStatsResponse = CatalogStatisticsResponse


# Health check and status types
class ModuleHealthResponse(BaseModel):
    """Health check response for the topic catalog module."""

    status: str  # "healthy", "degraded", "unhealthy"
    service: str = "topic_catalog"
    timestamp: str
    dependencies: dict[str, str]  # dependency_name -> status
    statistics: dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "topic_catalog",
                "timestamp": "2024-01-01T12:00:00Z",
                "dependencies": {"database": "healthy", "content_creation": "healthy"},
                "statistics": {"total_topics": 150, "cache_hit_rate": 0.92},
            }
        }


# Filter and sorting types
class TopicFilters(BaseModel):
    """Filters for topic queries."""

    user_level: str | None = None
    min_duration: int | None = None
    max_duration: int | None = None
    ready_only: bool | None = None
    has_components: bool | None = None

    class Config:
        json_schema_extra = {"example": {"user_level": "intermediate", "min_duration": 10, "max_duration": 45, "ready_only": True}}


class TopicSortOptions(BaseModel):
    """Sorting options for topic queries."""

    sort_by: str = Field(default="relevance", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")

    class Config:
        json_schema_extra = {"example": {"sort_by": "created_at", "sort_order": "desc"}}


# Pagination types
class PaginationRequest(BaseModel):
    """Pagination parameters."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    class Config:
        json_schema_extra = {"example": {"limit": 20, "offset": 0}}


class PaginationResponse(BaseModel):
    """Pagination metadata in responses."""

    limit: int
    offset: int
    total_count: int
    has_more: bool

    class Config:
        json_schema_extra = {"example": {"limit": 20, "offset": 0, "total_count": 150, "has_more": True}}
