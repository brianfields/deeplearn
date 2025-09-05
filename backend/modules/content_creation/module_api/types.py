"""
Type definitions for Content Creation module API.

This module defines the data transfer objects (DTOs) and types
used in the public API of the content creation module.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..domain.entities.component import Component
from ..domain.entities.topic import Topic


class ContentCreationError(Exception):
    """Base exception for content creation module errors"""

    pass


# Request DTOs
class CreateTopicRequest(BaseModel):
    """Request to create a new topic from source material."""

    title: str = Field(..., min_length=1, max_length=200, description="Topic title")
    core_concept: str = Field(..., min_length=1, max_length=500, description="Core concept being taught")
    source_material: str = Field(..., min_length=100, description="Source material text")
    user_level: str = Field(default="intermediate", description="Target user level")
    domain: str | None = Field(default=None, description="Subject domain")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Introduction to Python Variables",
                "core_concept": "Understanding how to declare and use variables in Python",
                "source_material": "Variables in Python are used to store data values. A variable is created the moment you first assign a value to it...",
                "user_level": "beginner",
                "domain": "Programming",
            }
        }


class CreateComponentRequest(BaseModel):
    """Request to create a new component for a topic."""

    component_type: str = Field(..., description="Type of component (mcq, didactic_snippet, etc.)")
    learning_objective: str = Field(..., min_length=1, description="Learning objective this component addresses")

    class Config:
        json_schema_extra = {"example": {"component_type": "mcq", "learning_objective": "Understand how to declare variables in Python"}}


class UpdateTopicRequest(BaseModel):
    """Request to update topic metadata."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    core_concept: str | None = Field(default=None, min_length=1, max_length=500)
    user_level: str | None = Field(default=None)
    learning_objectives: list[str] | None = Field(default=None)
    key_concepts: list[str] | None = Field(default=None)


class UpdateComponentRequest(BaseModel):
    """Request to update component content."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: dict[str, Any] | None = Field(default=None)
    learning_objective: str | None = Field(default=None)


# Response DTOs
class ComponentResponse(BaseModel):
    """Response containing component data."""

    id: str
    topic_id: str
    component_type: str
    title: str
    content: dict[str, Any]
    learning_objective: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_component(cls, component: Component) -> "ComponentResponse":
        """Create response from domain component."""
        return cls(
            id=component.id,
            topic_id=component.topic_id,
            component_type=component.component_type,
            title=component.title,
            content=component.content,
            learning_objective=component.learning_objective,
            created_at=component.created_at.isoformat(),
            updated_at=component.updated_at.isoformat(),
        )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "comp_123",
                "topic_id": "topic_456",
                "component_type": "mcq",
                "title": "MCQ: Variable Declaration",
                "content": {
                    "question": "How do you declare a variable in Python?",
                    "choices": {"A": "var x = 5", "B": "x = 5", "C": "int x = 5", "D": "declare x = 5"},
                    "correct_answer": "B",
                    "explanation": "In Python, you simply assign a value to create a variable.",
                },
                "learning_objective": "Understand variable declaration syntax",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }


class TopicResponse(BaseModel):
    """Response containing topic data."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    key_aspects: list[str]
    target_insights: list[str]
    common_misconceptions: list[str]
    previous_topics: list[str]
    source_material: str | None
    source_domain: str | None
    refined_material: dict[str, Any]
    created_at: str
    updated_at: str
    version: int
    components: list[ComponentResponse]
    completion_percentage: float
    is_ready_for_learning: bool
    readiness_status: str
    quality_score: float

    @classmethod
    def from_topic(cls, topic: Topic) -> "TopicResponse":
        """Create response from domain topic."""
        from ..domain.policies.topic_validation_policy import TopicValidationPolicy

        components = [ComponentResponse.from_component(c) for c in topic.get_components()]
        readiness_status = TopicValidationPolicy.get_topic_readiness_status(topic)
        quality_score = TopicValidationPolicy.calculate_topic_quality_score(topic)

        return cls(
            id=topic.id,
            title=topic.title,
            core_concept=topic.core_concept,
            user_level=topic.user_level,
            learning_objectives=topic.learning_objectives,
            key_concepts=topic.key_concepts,
            key_aspects=topic.key_aspects,
            target_insights=topic.target_insights,
            common_misconceptions=topic.common_misconceptions,
            previous_topics=topic.previous_topics,
            source_material=topic.source_material,
            source_domain=topic.source_domain,
            refined_material=topic.refined_material,
            created_at=topic.created_at.isoformat(),
            updated_at=topic.updated_at.isoformat(),
            version=topic.version,
            components=components,
            completion_percentage=topic.calculate_completion_percentage(),
            is_ready_for_learning=topic.is_ready_for_learning(),
            readiness_status=readiness_status,
            quality_score=quality_score,
        )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "topic_123",
                "title": "Python Variables",
                "core_concept": "Understanding variable declaration and usage",
                "user_level": "beginner",
                "learning_objectives": ["Declare variables", "Assign values", "Use variables in expressions"],
                "key_concepts": ["variable", "assignment", "data types"],
                "key_aspects": ["syntax", "naming rules", "scope"],
                "target_insights": ["Variables store data", "Assignment creates variables"],
                "common_misconceptions": ["Variables must be declared before use"],
                "previous_topics": [],
                "source_material": "Variables in Python...",
                "source_domain": "Programming",
                "refined_material": {"topics": []},
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "version": 1,
                "components": [],
                "completion_percentage": 0.0,
                "is_ready_for_learning": False,
                "readiness_status": "needs_components",
                "quality_score": 0.3,
            }
        }


class TopicSummaryResponse(BaseModel):
    """Lightweight topic response for listings."""

    id: str
    title: str
    core_concept: str
    user_level: str
    component_count: int
    completion_percentage: float
    is_ready_for_learning: bool
    readiness_status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_topic(cls, topic: Topic) -> "TopicSummaryResponse":
        """Create summary response from domain topic."""
        from ..domain.policies.topic_validation_policy import TopicValidationPolicy

        readiness_status = TopicValidationPolicy.get_topic_readiness_status(topic)

        return cls(
            id=topic.id,
            title=topic.title,
            core_concept=topic.core_concept,
            user_level=topic.user_level,
            component_count=len(topic.get_components()),
            completion_percentage=topic.calculate_completion_percentage(),
            is_ready_for_learning=topic.is_ready_for_learning(),
            readiness_status=readiness_status,
            created_at=topic.created_at.isoformat(),
            updated_at=topic.updated_at.isoformat(),
        )

    @classmethod
    def from_topic_response(cls, topic_response: "TopicResponse") -> "TopicSummaryResponse":
        """Create summary response from topic response."""
        return cls(
            id=topic_response.id,
            title=topic_response.title,
            core_concept=topic_response.core_concept,
            user_level=topic_response.user_level,
            component_count=len(topic_response.components),
            completion_percentage=topic_response.completion_percentage,
            is_ready_for_learning=topic_response.is_ready_for_learning,
            readiness_status=topic_response.readiness_status,
            created_at=topic_response.created_at,
            updated_at=topic_response.updated_at,
        )


class ContentCreationStatsResponse(BaseModel):
    """Response containing content creation statistics."""

    total_topics: int
    topics_by_user_level: dict[str, int]
    topics_by_readiness_status: dict[str, int]
    total_components: int
    components_by_type: dict[str, int]
    average_completion_percentage: float
    average_quality_score: float
    topics_ready_for_learning: int


class SearchTopicsRequest(BaseModel):
    """Request to search topics."""

    query: str | None = Field(default=None, description="Text query to search")
    user_level: str | None = Field(default=None, description="Filter by user level")
    has_components: bool | None = Field(default=None, description="Filter by component availability")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Results offset")


class GenerateAllComponentsRequest(BaseModel):
    """Request to generate all components for a topic."""

    component_types: list[str] | None = Field(default=None, description="Specific component types to generate (default: all supported types)")
    max_concurrent: int = Field(default=5, ge=1, le=10, description="Maximum concurrent generations")


# Health check and status types
class ModuleHealthResponse(BaseModel):
    """Health check response for the content creation module."""

    status: str  # "healthy", "degraded", "unhealthy"
    service: str = "content_creation"
    timestamp: str
    dependencies: dict[str, str]  # dependency_name -> status
    statistics: dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "content_creation",
                "timestamp": "2024-01-01T12:00:00Z",
                "dependencies": {"llm_services": "healthy", "database": "healthy"},
                "statistics": {"total_topics": 42, "total_components": 156, "cache_hit_rate": 0.85},
            }
        }
