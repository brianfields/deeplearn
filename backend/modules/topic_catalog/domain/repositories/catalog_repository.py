"""
Catalog repository interface for topic catalog domain.

This module defines the abstract interface for catalog persistence.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..entities.catalog import Catalog


class CatalogRepositoryError(Exception):
    """Base exception for catalog repository errors"""

    pass


class CatalogNotFoundError(CatalogRepositoryError):
    """Raised when a catalog is not found"""

    pass


class CatalogRepository(ABC):
    """
    Abstract repository interface for catalog persistence.

    This interface defines the contract for catalog storage and retrieval,
    allowing the domain layer to remain independent of specific storage implementations.
    """

    @abstractmethod
    async def get_catalog(self) -> Catalog:
        """
        Get the catalog with all available topics.

        Returns:
            Catalog instance with topics

        Raises:
            CatalogRepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
    async def refresh_catalog(self) -> dict[str, Any]:
        """
        Refresh the catalog with latest data.

        Returns:
            Dictionary containing refresh results

        Raises:
            CatalogRepositoryError: If refresh fails
        """
        pass
