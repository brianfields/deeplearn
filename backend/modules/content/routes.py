"""HTTP routes exposing content module functionality."""

from __future__ import annotations

from collections.abc import Generator
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from modules.infrastructure.public import infrastructure_provider

from .public import content_provider
from .service import ContentService

router = APIRouter(prefix="/api/v1/content", tags=["Content"])


def get_session() -> Generator[Session, None, None]:
    """Yield a request-scoped SQLAlchemy session."""

    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as session:
        yield session


def get_content_service(session: Session = Depends(get_session)) -> ContentService:
    """Build the content service from the provider."""

    return cast(ContentService, content_provider(session))


class UnitShareUpdate(BaseModel):
    """Request payload for toggling unit sharing state."""

    is_global: bool
    acting_user_id: int | None = Field(default=None, ge=1)


@router.get("/units", response_model=list[ContentService.UnitRead])
def list_units(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to return"),
    offset: int = Query(0, ge=0, description="Pagination offset for unit listing"),
    service: ContentService = Depends(get_content_service),
) -> list[ContentService.UnitRead]:
    """Return all units ordered by most recent update."""

    return service.list_units(limit=limit, offset=offset)


@router.get("/units/personal", response_model=list[ContentService.UnitRead])
def list_personal_units(
    user_id: int = Query(..., ge=1, description="Identifier for the unit owner"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to return"),
    offset: int = Query(0, ge=0, description="Pagination offset for unit listing"),
    service: ContentService = Depends(get_content_service),
) -> list[ContentService.UnitRead]:
    """Return units owned by the provided user."""

    return service.list_units_for_user(user_id=user_id, limit=limit, offset=offset)


@router.get("/units/global", response_model=list[ContentService.UnitRead])
def list_global_units(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of units to return"),
    offset: int = Query(0, ge=0, description="Pagination offset for unit listing"),
    service: ContentService = Depends(get_content_service),
) -> list[ContentService.UnitRead]:
    """Return units that have been shared globally."""

    return service.list_global_units(limit=limit, offset=offset)


@router.get("/units/{unit_id}", response_model=ContentService.UnitRead)
def get_unit(
    unit_id: str,
    service: ContentService = Depends(get_content_service),
) -> ContentService.UnitRead:
    """Retrieve a single unit by identifier."""

    unit = service.get_unit(unit_id)
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    return unit


@router.post("/units", response_model=ContentService.UnitRead, status_code=status.HTTP_201_CREATED)
def create_unit(
    payload: ContentService.UnitCreate,
    service: ContentService = Depends(get_content_service),
) -> ContentService.UnitRead:
    """Create a new unit with optional ownership and sharing metadata."""

    return service.create_unit(payload)


@router.patch("/units/{unit_id}/sharing", response_model=ContentService.UnitRead)
def update_unit_sharing(
    unit_id: str,
    payload: UnitShareUpdate,
    service: ContentService = Depends(get_content_service),
) -> ContentService.UnitRead:
    """Toggle a unit's global sharing state, enforcing ownership when provided."""

    try:
        return service.set_unit_sharing(
            unit_id,
            is_global=payload.is_global,
            acting_user_id=payload.acting_user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
