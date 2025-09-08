"""
Infrastructure Public API - Protocol and DI provider.

This module provides the narrow contract for the Infrastructure module
and returns the service instance directly for dependency injection.
"""

from typing import Protocol

from .service import (
    APIConfig,
    AppConfig,
    DatabaseConfig,
    DatabaseSession,
    EnvironmentStatus,
    InfrastructureService,
    LoggingConfig,
)


class InfrastructureProvider(Protocol):
    """Protocol defining the public interface for infrastructure operations."""

    def initialize(self, env_file: str | None = None) -> None:
        """Initialize the infrastructure service."""
        ...

    def get_database_session(self) -> DatabaseSession:
        """Get a database session for data operations."""
        ...

    def close_database_session(self, database_session: DatabaseSession) -> None:
        """Close a database session."""
        ...

    def get_session_context(self):
        """Get a database session context manager."""
        ...

    def get_config(self) -> AppConfig:
        """Get application configuration."""
        ...

    def validate_environment(self) -> EnvironmentStatus:
        """Validate infrastructure environment."""
        ...

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        ...

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        ...

    def shutdown(self) -> None:
        """Shutdown infrastructure service and cleanup resources."""
        ...


def infrastructure_provider() -> InfrastructureProvider:
    """
    Dependency injection provider for infrastructure services.

    Returns:
        Infrastructure service instance that implements the protocol
    """
    # Return the concrete service; it already returns DTOs
    return InfrastructureService()


# Export the DTOs and provider for external use
__all__ = [
    "APIConfig",
    "AppConfig",
    "DatabaseConfig",
    "DatabaseSession",
    "EnvironmentStatus",
    "InfrastructureProvider",
    "LoggingConfig",
    "infrastructure_provider",
]
