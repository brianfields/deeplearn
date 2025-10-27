"""HTTP routes exposing content module functionality."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any, cast

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


class MyUnitMutationRequest(BaseModel):
    """Request payload for adding or removing a unit from My Units."""

    user_id: int = Field(..., ge=1)
    unit_id: str = Field(..., min_length=1)


class MyUnitMutationResponse(BaseModel):
    """Response payload describing the unit membership state."""

    unit: ContentService.UnitRead
    is_in_my_units: bool


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
    user_id: int = Query(..., ge=1, description="User ID for filtering accessible units"),
    since: str | None = Query(
        None,
        description="ISO-8601 timestamp indicating the last successful sync",
    ),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to inspect"),
    include_deleted: bool = Query(False, description="Whether to include deletion tombstones"),
    payload: str = Query(
        "full",
        description="Payload detail level: 'full' returns lessons/audio/image metadata, 'minimal' returns unit metadata + image",
    ),
    service: ContentService = Depends(get_content_service),
) -> ContentService.UnitSyncResponse:
    """Return units and lessons that have changed since the provided cursor, filtered by user access."""

    parsed_since: datetime | None = None
    if since:
        try:
            parsed_since = datetime.fromisoformat(since)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid since timestamp") from exc

        # Convert to timezone-aware UTC if naive
        if parsed_since.tzinfo is None:
            parsed_since = parsed_since.replace(tzinfo=UTC)

        # Convert to naive datetime for database comparison (PostgreSQL TIMESTAMP WITHOUT TIME ZONE)
        parsed_since = parsed_since.replace(tzinfo=None)

    if payload not in {"full", "minimal"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload value; expected 'full' or 'minimal'",
        )

    return await service.get_units_since(
        since=parsed_since,
        limit=limit,
        include_deleted=include_deleted,
        payload=cast(ContentService.UnitSyncPayload, payload),
        user_id=user_id,
    )


@router.get("/units/personal", response_model=list[ContentService.UnitRead])
async def list_personal_units(
    user_id: int = Query(..., ge=1, description="Identifier for the unit owner"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to return"),
    offset: int = Query(0, ge=0, description="Pagination offset for unit listing"),
    service: ContentService = Depends(get_content_service),
) -> list[ContentService.UnitRead]:
    """Return units owned by the user and catalog units they added to My Units."""

    return await service.list_units_for_user_including_my_units(user_id=user_id, limit=limit, offset=offset)


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


@router.post("/units/my-units/add", response_model=MyUnitMutationResponse)
async def add_unit_to_my_units(
    payload: MyUnitMutationRequest,
    service: ContentService = Depends(get_content_service),
) -> MyUnitMutationResponse:
    """Add a catalog unit to the requesting user's My Units collection."""

    try:
        unit = await service.add_unit_to_my_units(payload.user_id, payload.unit_id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return MyUnitMutationResponse(unit=unit, is_in_my_units=True)


@router.post("/units/my-units/remove", response_model=MyUnitMutationResponse)
async def remove_unit_from_my_units(
    payload: MyUnitMutationRequest,
    service: ContentService = Depends(get_content_service),
) -> MyUnitMutationResponse:
    """Remove a catalog unit from the requesting user's My Units collection."""

    try:
        unit = await service.remove_unit_from_my_units(payload.user_id, payload.unit_id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return MyUnitMutationResponse(unit=unit, is_in_my_units=False)


@router.get("/units/{unit_id}/flow-runs")
async def get_unit_flow_runs(
    unit_id: str,
    service: ContentService = Depends(get_content_service),
) -> list[dict[str, Any]]:
    """Admin Observability: return flow runs associated with a unit."""

    runs = await service.get_unit_flow_runs(unit_id)
    return [
        {
            "id": flow_run.id,
            "flow_name": flow_run.flow_name,
            "status": flow_run.status,
            "execution_mode": flow_run.execution_mode,
            "arq_task_id": flow_run.arq_task_id,
            "user_id": flow_run.user_id,
            "created_at": flow_run.created_at.isoformat(),
            "started_at": flow_run.started_at.isoformat() if flow_run.started_at else None,
            "completed_at": flow_run.completed_at.isoformat() if flow_run.completed_at else None,
            "execution_time_ms": flow_run.execution_time_ms,
            "total_tokens": flow_run.total_tokens,
            "total_cost": flow_run.total_cost,
            "step_count": flow_run.step_count,
            "error_message": flow_run.error_message,
        }
        for flow_run in runs
    ]


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
