"""
Shared database models and base classes for all modules.

This module provides the SQLAlchemy Base class and common database utilities
that are used across multiple modules in the application.
"""

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

# Create the SQLAlchemy Base class
Base = declarative_base()

# PostgreSQL UUID type for consistent usage across modules
PostgresUUID = UUID

__all__ = ["Base", "PostgresUUID"]
