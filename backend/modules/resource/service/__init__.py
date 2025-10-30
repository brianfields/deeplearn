"""Business logic for managing learner-provided resources."""

from .dtos import (
    FileResourceCreate,
    PhotoResourceCreate,
    ResourceRead,
    ResourceSummary,
    UrlResourceCreate,
)
from .facade import (
    ResourceError,
    ResourceExtractionError,
    ResourceService,
    ResourceValidationError,
    resource_service_factory,
)

__all__ = [
    "FileResourceCreate",
    "PhotoResourceCreate",
    "ResourceError",
    "ResourceExtractionError",
    "ResourceRead",
    "ResourceService",
    "ResourceSummary",
    "ResourceValidationError",
    "UrlResourceCreate",
    "resource_service_factory",
]
