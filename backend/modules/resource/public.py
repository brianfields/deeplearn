"""Public interface for the resource module."""

from __future__ import annotations

from typing import Protocol
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .service import ResourceRead, ResourceSummary, resource_service_factory


class ResourceProvider(Protocol):
    """Protocol describing read operations exposed to other modules."""

    async def get_resource(self, resource_id: uuid.UUID) -> ResourceRead | None:
        """Fetch a single resource by identifier."""
        ...

    async def list_user_resources(self, user_id: int) -> list[ResourceSummary]:
        """List resources for a given user."""
        ...

    async def get_resources_for_unit(self, unit_id: str) -> list[ResourceSummary]:
        """List resources associated with a unit."""
        ...


async def resource_provider(session: AsyncSession) -> ResourceProvider:
    """Factory returning the concrete resource service."""

    return await resource_service_factory(session)


__all__ = [
    "ResourceProvider",
    "ResourceRead",
    "ResourceSummary",
    "resource_provider",
]
