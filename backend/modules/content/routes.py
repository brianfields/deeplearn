"""HTTP routes exposing content module functionality."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from modules.infrastructure.public import infrastructure_provider

from .public import content_provider
from .service import ContentService

router = APIRouter(prefix="/api/v1/content", tags=["Content"])


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async SQLAlchemy session."""

    infra = infrastructure_provider()
    infra.initialize()
    async with infra.get_async_session_context() as session:
        yield session


async def get_content_service(session: AsyncSession = Depends(get_async_session)) -> ContentService:
    """Build the content service from the provider."""

    return cast(ContentService, content_provider(session))


class UnitShareUpdate(BaseModel):
    """Request payload for toggling unit sharing state."""

    is_global: bool
    acting_user_id: int | None = Field(default=None, ge=1)


@router.get("/units", response_model=list[ContentService.UnitRead])
async def list_units(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to return"),
    offset: int = Query(0, ge=0, description="Pagination offset for unit listing"),
    service: ContentService = Depends(get_content_service),
) -> list[ContentService.UnitRead]:
    """Return all units ordered by most recent update."""

    return await service.list_units(limit=limit, offset=offset)


@router.get("/units/sync", response_model=ContentService.UnitSyncResponse)
async def sync_units(
    since: str | None = Query(
        None,
        description="ISO-8601 timestamp indicating the last successful sync",
    ),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to inspect"),
    include_deleted: bool = Query(False, description="Whether to include deletion tombstones"),
    service: ContentService = Depends(get_content_service),
) -> ContentService.UnitSyncResponse:
    """Return units and lessons that have changed since the provided cursor."""

    parsed_since: datetime | None = None
    if since:
        try:
            parsed_since = datetime.fromisoformat(since)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid since timestamp") from exc

        if parsed_since.tzinfo is None:
            parsed_since = parsed_since.replace(tzinfo=timezone.utc)

    return await service.get_units_since(
        since=parsed_since,
        limit=limit,
        include_deleted=include_deleted,
    )


@router.get("/units/personal", response_model=list[ContentService.UnitRead])
async def list_personal_units(
    user_id: int = Query(..., ge=1, description="Identifier for the unit owner"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to return"),
    offset: int = Query(0, ge=0, description="Pagination offset for unit listing"),
    service: ContentService = Depends(get_content_service),
) -> list[ContentService.UnitRead]:
    """Return units owned by the provided user."""

    return await service.list_units_for_user(user_id=user_id, limit=limit, offset=offset)


@router.get("/units/global", response_model=list[ContentService.UnitRead])
async def list_global_units(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to return"),
    offset: int = Query(0, ge=0, description="Pagination offset for unit listing"),
    service: ContentService = Depends(get_content_service),
) -> list[ContentService.UnitRead]:
    """Return units that have been shared globally."""

    return await service.list_global_units(limit=limit, offset=offset)


@router.get("/units/{unit_id}", response_model=ContentService.UnitDetailRead)
async def get_unit_detail(
    unit_id: str,
    service: ContentService = Depends(get_content_service),
) -> ContentService.UnitDetailRead:
    """Retrieve a fully hydrated unit with ordered lesson summaries."""

    unit = await service.get_unit_detail(unit_id, include_art_presigned_url=True)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    return unit


@router.get("/units/{unit_id}/podcast/audio", response_model=None)
async def stream_unit_podcast_audio(
    unit_id: str,
    service: ContentService = Depends(get_content_service),
) -> RedirectResponse:
    """Stream the generated podcast audio for a unit."""

    audio = await service.get_unit_podcast_audio(unit_id)
    if not audio or not audio.presigned_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Podcast audio not found")

    return RedirectResponse(audio.presigned_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.post("/units", response_model=ContentService.UnitRead, status_code=status.HTTP_201_CREATED)
async def create_unit(
    payload: ContentService.UnitCreate,
    service: ContentService = Depends(get_content_service),
) -> ContentService.UnitRead:
    """Create a new unit with optional ownership and sharing metadata."""

    return await service.create_unit(payload)


@router.patch("/units/{unit_id}/sharing", response_model=ContentService.UnitRead)
async def update_unit_sharing(
    unit_id: str,
    payload: UnitShareUpdate,
    service: ContentService = Depends(get_content_service),
) -> ContentService.UnitRead:
    """Toggle a unit's global sharing state, enforcing ownership when provided."""

    try:
        return await service.set_unit_sharing(
            unit_id,
            is_global=payload.is_global,
            acting_user_id=payload.acting_user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
