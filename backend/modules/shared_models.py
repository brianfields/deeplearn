"""
Shared database models and base classes for all modules.

This module provides the SQLAlchemy Base class and common database utilities
that are used across multiple modules in the application.
"""

from sqlalchemy.ext.declarative import declarative_base

# Create the SQLAlchemy Base class
Base = declarative_base()

__all__ = ["Base"]
