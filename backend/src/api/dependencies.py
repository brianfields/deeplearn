"""
FastAPI Dependencies

This module provides dependency functions for FastAPI routes.
Dependencies are injected into route handlers and provide access to services
without creating circular imports.
"""

from typing import Annotated

from fastapi import Depends, HTTPException

from src.database_service import DatabaseService, get_database_service


def get_db_service() -> DatabaseService:
    """
    Dependency function to get the database service.

    This is used with FastAPI's dependency injection system.
    Routes can depend on this function to get access to the database service.

    Returns:
        DatabaseService: The global database service instance

    Raises:
        HTTPException: If database service is not available
    """
    db_service = get_database_service()
    if db_service is None:
        raise HTTPException(status_code=503, detail="Database service not available")
    return db_service


# Type alias for dependency injection
DatabaseDep = Annotated[DatabaseService, Depends(get_db_service)]
