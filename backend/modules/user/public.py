"""Public interface for the user module."""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.orm import Session

from .repo import UserRepo
from .service import (
    AuthenticationResult,
    UserLogin,
    UserRead,
    UserRegister,
    UserService,
    UserUpdate,
)


class UserProvider(Protocol):
    """Protocol describing the public surface of the user module."""

    def register(self, payload: UserRegister) -> UserRead: ...

    def authenticate(self, payload: UserLogin) -> AuthenticationResult: ...

    def get_profile(self, user_id: int) -> UserRead | None: ...

    def update_profile(self, user_id: int, payload: UserUpdate) -> UserRead: ...

    def list_users(self, search: str | None = None) -> list[UserRead]: ...

    def update_user_admin(
        self,
        user_id: int,
        *,
        name: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> UserRead: ...


def user_provider(session: Session) -> UserProvider:
    """Return a configured UserService bound to a database session."""

    return UserService(UserRepo(session))


__all__ = [
    "AuthenticationResult",
    "UserLogin",
    "UserProvider",
    "UserRead",
    "UserRegister",
    "UserUpdate",
    "user_provider",
]
