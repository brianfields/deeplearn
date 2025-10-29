"""HTTP endpoints for the resource module."""

from __future__ import annotations

from collections.abc import AsyncGenerator
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from modules.infrastructure.public import infrastructure_provider

from .service import (
    FileResourceCreate,
    ResourceExtractionError,
    ResourceRead,
    ResourceService,
    ResourceSummary,
    ResourceValidationError,
    UrlResourceCreate,
    resource_service_factory,
)

router = APIRouter(prefix="/api/v1/resources", tags=["Resources"])


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async SQLAlchemy session."""

    infra = infrastructure_provider()
    infra.initialize()
    async with infra.get_async_session_context() as session:
        yield session


async def get_resource_service(session: AsyncSession = Depends(get_async_session)) -> ResourceService:
    """Construct the resource service for the current request."""

    return await resource_service_factory(session)


class UrlResourceRequest(BaseModel):
    """Request body for URL-based resource creation."""

    user_id: int
    url: HttpUrl


@router.post("/upload", response_model=ResourceRead, status_code=status.HTTP_201_CREATED)
async def upload_resource(
    user_id: int = Form(..., ge=1),
    file: UploadFile = File(...),
    service: ResourceService = Depends(get_resource_service),
) -> ResourceRead:
    """Upload a file resource."""

    content = await file.read()
    try:
        return await service.upload_file_resource(
            FileResourceCreate(
                user_id=user_id,
                filename=file.filename or "untitled",
                content_type=file.content_type or "application/octet-stream",
                content=content,
                file_size=len(content),
            )
        )
    except ResourceValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ResourceExtractionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/from-url", response_model=ResourceRead, status_code=status.HTTP_201_CREATED)
async def create_resource_from_url(
    payload: UrlResourceRequest,
    service: ResourceService = Depends(get_resource_service),
) -> ResourceRead:
    """Create a resource from a remote URL."""

    try:
        return await service.create_url_resource(UrlResourceCreate(user_id=payload.user_id, url=payload.url))
    except ResourceValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ResourceExtractionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("", response_model=list[ResourceSummary])
async def list_resources(
    user_id: int = Query(..., ge=1),
    service: ResourceService = Depends(get_resource_service),
) -> list[ResourceSummary]:
    """List resources uploaded by a user."""

    return await service.list_user_resources(user_id)


@router.get("/{resource_id}", response_model=ResourceRead)
async def get_resource(
    resource_id: str,
    service: ResourceService = Depends(get_resource_service),
) -> ResourceRead:
    """Get a resource by identifier."""

    try:
        parsed_id = uuid.UUID(resource_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid resource id") from exc

    resource = await service.get_resource(parsed_id)
    if resource is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource
