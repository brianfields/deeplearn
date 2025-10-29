"""Async repository for learner resources."""

from __future__ import annotations

from collections.abc import Sequence
import uuid

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.content.models import UnitResourceModel

from .models import ResourceModel


class ResourceRepo:
    """Data access helpers for the resource module."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        resource_type: str,
        filename: str | None,
        source_url: str | None,
        extracted_text: str,
        extraction_metadata: dict[str, object],
        file_size: int | None,
        object_store_document_id: uuid.UUID | None,
    ) -> ResourceModel:
        resource = ResourceModel(
            user_id=user_id,
            resource_type=resource_type,
            filename=filename,
            source_url=source_url,
            extracted_text=extracted_text,
            extraction_metadata=extraction_metadata,
            file_size=file_size,
            object_store_document_id=object_store_document_id,
        )
        self._session.add(resource)
        await self._session.flush()
        await self._session.refresh(resource)
        return resource

    async def get_by_id(self, resource_id: uuid.UUID) -> ResourceModel | None:
        return await self._session.get(ResourceModel, resource_id)

    async def list_by_user(self, user_id: int) -> list[ResourceModel]:
        stmt: Select[tuple[ResourceModel]] = select(ResourceModel).where(ResourceModel.user_id == user_id).order_by(desc(ResourceModel.created_at))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_unit(self, unit_id: str) -> list[ResourceModel]:
        stmt: Select[tuple[ResourceModel]] = select(ResourceModel).join(UnitResourceModel, UnitResourceModel.resource_id == ResourceModel.id).where(UnitResourceModel.unit_id == unit_id).order_by(desc(UnitResourceModel.added_at))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def link_resources_to_unit(self, *, unit_id: str, resource_ids: Sequence[uuid.UUID]) -> None:
        existing_stmt = select(UnitResourceModel.resource_id).where(UnitResourceModel.unit_id == unit_id)
        existing_result = await self._session.execute(existing_stmt)
        existing_ids = set(existing_result.scalars().all())
        new_links = [UnitResourceModel(unit_id=unit_id, resource_id=resource_id) for resource_id in resource_ids if resource_id not in existing_ids]
        if new_links:
            self._session.add_all(new_links)
            await self._session.flush()

    async def update_extracted_text(
        self,
        resource: ResourceModel,
        *,
        extracted_text: str,
        extraction_metadata: dict[str, object],
    ) -> ResourceModel:
        resource.extracted_text = extracted_text
        resource.extraction_metadata = extraction_metadata
        await self._session.flush()
        await self._session.refresh(resource)
        return resource
