"""
Topic Catalog Module Types.

Data transfer objects and exceptions for the topic catalog module API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TopicCatalogError(Exception):
    """Base exception for topic catalog operations."""

    pass


class TopicSummaryResponse(BaseModel):
    """Response model for topic summary."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    created_at: datetime
    component_count: int


class TopicDetailResponse(BaseModel):
    """Response model for detailed topic information."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    key_aspects: list[str]
    target_insights: list[str]
    source_material: str | None
    refined_material: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    components: list[dict[str, Any]]
    component_count: int
    is_ready_for_learning: bool


class BrowseTopicsRequest(BaseModel):
    """Request model for browsing topics."""

    user_level: str | None = None
    limit: int = 100


class BrowseTopicsResponse(BaseModel):
    """Response model for browsing topics."""

    topics: list[TopicSummaryResponse]
    total_count: int
