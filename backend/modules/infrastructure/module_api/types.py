"""
Types for the Infrastructure module API.

This module defines the public types that other modules can import
and use when interacting with the Infrastructure module.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..domain.entities.configuration import APIConfig, DatabaseConfig, LoggingConfig


@dataclass
class DatabaseSession:
    """
    Database session wrapper for external modules.

    Provides a clean interface for database sessions without exposing
    SQLAlchemy implementation details.
    """

    session: Session
    connection_id: str


@dataclass
class AppConfig:
    """
    Application configuration for external modules.

    Aggregates configuration from various sources into a single
    interface for other modules to consume.
    """

    database_url: str
    api_config: APIConfig
    feature_flags: dict[str, bool]
    logging_config: LoggingConfig


@dataclass
class EnvironmentStatus:
    """
    Environment validation status.

    Provides information about the health and validity of the
    infrastructure environment.
    """

    is_valid: bool
    errors: list[str]


# Re-export configuration types for convenience
__all__ = ["APIConfig", "AppConfig", "DatabaseConfig", "DatabaseSession", "EnvironmentStatus", "LoggingConfig"]
