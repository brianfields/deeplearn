"""
Types for LLM Services module API.

This module defines the data transfer objects and types used in the
public API of the LLM Services module.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# Re-export key domain types for external use


@dataclass
class LLMResponse:
    """Response from LLM generation (simplified for external API)"""

    content: str
    tokens_used: int
    cost_estimate: float | None = None
    metadata: dict[str, Any] | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class PromptContext:
    """Context for prompt generation (simplified for external API)"""

    user_level: str = "beginner"  # Use string for simpler API
    learning_style: str = "balanced"
    time_constraint: int = 15
    previous_performance: dict[str, Any] = None
    prerequisites_met: list[str] = None
    custom_instructions: str | None = None

    def __post_init__(self):
        if self.previous_performance is None:
            self.previous_performance = {}
        if self.prerequisites_met is None:
            self.prerequisites_met = []


class LLMConfig(BaseModel):
    """Configuration for LLM services (simplified for external API)"""

    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=16384, gt=0)
    timeout: int = Field(default=180, gt=0)


class GenerationRequest(BaseModel):
    """Request for content generation"""

    prompt_name: str
    context: dict[str, Any] | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    config_overrides: dict[str, Any] | None = None


class GenerationResponse(BaseModel):
    """Response from content generation"""

    content: str
    tokens_used: int
    cost_estimate: float | None = None
    generation_time: float  # seconds
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StructuredGenerationRequest(BaseModel):
    """Request for structured content generation"""

    prompt_name: str
    response_schema: dict[str, Any]
    context: dict[str, Any] | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    config_overrides: dict[str, Any] | None = None


class StructuredGenerationResponse(BaseModel):
    """Response from structured content generation"""

    data: dict[str, Any]
    tokens_used: int
    cost_estimate: float | None = None
    generation_time: float  # seconds
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthStatus(BaseModel):
    """Health status of LLM services"""

    status: str  # "healthy" | "unhealthy" | "degraded"
    service: str = "llm_services"
    provider: str | None = None
    model: str | None = None
    error: str | None = None
    stats: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ServiceStats(BaseModel):
    """Statistics for LLM services"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_size: int = 0
    average_tokens_per_request: float = 0.0
    total_cost: float = 0.0
    uptime_seconds: float = 0.0
    last_request: datetime | None = None
