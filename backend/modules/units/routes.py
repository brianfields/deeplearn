"""
Units Module - API Routes

FastAPI routes for unit management (admin-focused for now).
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from modules.infrastructure.public import infrastructure_provider

from .public import SetLessonOrder, UnitCreate, UnitRead, UnitsProvider, units_provider

router = APIRouter(prefix="/api/v1/units", tags=["units"])


def get_session() -> Generator[Session, None, None]:
    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as s:
        yield s


def get_units_service(s: Session = Depends(get_session)) -> UnitsProvider:
    return units_provider(s)


@router.get("/{unit_id}", response_model=UnitRead)
def get_unit(unit_id: str, svc: UnitsProvider = Depends(get_units_service)) -> UnitRead:
    u = svc.get(unit_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    return u


@router.get("", response_model=list[UnitRead])
def list_units(svc: UnitsProvider = Depends(get_units_service)) -> list[UnitRead]:
    return svc.list()


@router.post("", response_model=UnitRead, status_code=status.HTTP_201_CREATED)
def create_unit(body: UnitCreate, svc: UnitsProvider = Depends(get_units_service)) -> UnitRead:
    return svc.create(body)


@router.put("/{unit_id}/lesson-order", response_model=UnitRead)
def update_lesson_order(unit_id: str, body: SetLessonOrder, svc: UnitsProvider = Depends(get_units_service)) -> UnitRead:
    try:
        return svc.set_lesson_order(unit_id, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found") from e
