"""
Content Creation Module API.

This module provides the public interface for the content creation module.
All external modules should only import from this module_api package.
"""

# Main service
from ..domain.entities.component import Component, InvalidComponentError

# Domain entities (for type hints and advanced usage)
from ..domain.entities.topic import InvalidTopicError, Topic

# Validation policies (for external validation)
from ..domain.policies.topic_validation_policy import TopicValidationPolicy

# Repository interface (for dependency injection)
from ..domain.repositories.topic_repository import (
    TopicNotFoundError,
    TopicRepository,
    TopicRepositoryError,
)
from .content_creation_service import ContentCreationService, create_content_creation_service

# Types and DTOs
from .types import (
    ComponentResponse,
    # Exception types
    ContentCreationError,
    ContentCreationStatsResponse,
    CreateComponentRequest,
    # Request types
    CreateTopicRequest,
    GenerateAllComponentsRequest,
    ModuleHealthResponse,
    SearchTopicsRequest,
    # Response types
    TopicResponse,
    TopicSummaryResponse,
    UpdateComponentRequest,
    UpdateTopicRequest,
)

__all__ = [
    # Main service
    "ContentCreationService",
    "create_content_creation_service",
    # Request types
    "CreateTopicRequest",
    "CreateComponentRequest",
    "UpdateTopicRequest",
    "UpdateComponentRequest",
    "SearchTopicsRequest",
    "GenerateAllComponentsRequest",
    # Response types
    "TopicResponse",
    "ComponentResponse",
    "TopicSummaryResponse",
    "ContentCreationStatsResponse",
    "ModuleHealthResponse",
    # Exception types
    "ContentCreationError",
    "InvalidTopicError",
    "InvalidComponentError",
    "TopicRepositoryError",
    "TopicNotFoundError",
    # Domain entities (for type hints)
    "Topic",
    "Component",
    # Repository interface
    "TopicRepository",
    # Validation policies
    "TopicValidationPolicy",
]
