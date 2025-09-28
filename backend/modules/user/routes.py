"""FastAPI routes for the user module."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from modules.infrastructure.public import infrastructure_provider

from .repo import UserRepo
from .service import AuthenticationResult, UserLogin, UserRead, UserRegister, UserService, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


def get_session() -> Generator[Session, None, None]:
    """Provide a request-scoped database session."""

    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as session:
        yield session


def get_user_service(session: Session = Depends(get_session)) -> UserService:
    """Construct a UserService for request handling."""

    return UserService(UserRepo(session))


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister, service: UserService = Depends(get_user_service)) -> UserRead:
    """Register a new user account."""

    try:
        return service.register(payload)
    except ValueError as exc:  # Duplicate email or validation issue
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=AuthenticationResult)
def login_user(payload: UserLogin, service: UserService = Depends(get_user_service)) -> AuthenticationResult:
    """Authenticate user credentials."""

    try:
        return service.authenticate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/profile", response_model=UserRead)
def get_profile(
    user_id: int = Query(..., ge=1, description="User identifier for profile lookup"),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Return profile details for a specific user."""

    profile = service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return profile


@router.put("/profile", response_model=UserRead)
def update_profile(
    payload: UserUpdate,
    user_id: int = Query(..., ge=1, description="User identifier whose profile is being updated"),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Update the authenticated user's profile details."""

    try:
        return service.update_profile(user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
