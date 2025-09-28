"""User module service layer."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import UserModel
from .repo import UserRepo


class UserRead(BaseModel):
    """DTO returned to callers when reading user information."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserRegister(BaseModel):
    """Payload for registering a new user."""

    email: str
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)


class UserLogin(BaseModel):
    """Payload for authenticating a user."""

    email: str
    password: str


class UserUpdate(BaseModel):
    """Payload for updating mutable profile details."""

    name: str | None = None
    password: str | None = Field(default=None, min_length=8)


class AuthenticationResult(BaseModel):
    """DTO describing authentication success."""

    user: UserRead


class UserService:
    """Business logic for user registration and authentication."""

    _HASH_ITERATIONS = 390_000
    _HASH_ALGORITHM = "pbkdf2_sha256"
    _EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, repo: UserRepo) -> None:
        self.repo = repo

    # ------------------------------------------------------------------
    # Registration & Authentication
    # ------------------------------------------------------------------
    def register(self, payload: UserRegister) -> UserRead:
        """Register a new user with hashed password storage."""

        existing = self.repo.by_email(payload.email)
        if existing:
            raise ValueError("Email already registered")

        self._validate_email(payload.email)
        password_hash = self._hash_password(payload.password)
        created = self.repo.create(
            email=payload.email,
            password_hash=password_hash,
            name=payload.name,
        )
        return UserRead.model_validate(created)

    def authenticate(self, payload: UserLogin) -> AuthenticationResult:
        """Authenticate user credentials and return authenticated user."""

        self._validate_email(payload.email)
        user = self.repo.by_email(payload.email)
        if not user:
            raise ValueError("Invalid email or password")

        if not self._verify_password(payload.password, user.password_hash):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        return AuthenticationResult(user=UserRead.model_validate(user))

    # ------------------------------------------------------------------
    # Profile operations
    # ------------------------------------------------------------------
    def get_profile(self, user_id: int) -> UserRead | None:
        """Return the public profile for a user."""

        user = self.repo.by_id(user_id)
        if not user:
            return None
        return UserRead.model_validate(user)

    def update_profile(self, user_id: int, payload: UserUpdate) -> UserRead:
        """Update mutable profile fields for a user."""

        user = self.repo.by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if payload.name is not None:
            user.name = payload.name

        if payload.password is not None:
            user.password_hash = self._hash_password(payload.password)

        user.updated_at = datetime.now(UTC)
        saved = self.repo.save(user)
        return UserRead.model_validate(saved)

    def list_users(self, search: str | None = None) -> list[UserRead]:
        """Return users filtered by optional case-insensitive search."""

        users = self.repo.list_all()
        if search:
            needle = search.lower()
            users = [
                u
                for u in users
                if needle in u.email.lower() or needle in u.name.lower()
            ]
        return [UserRead.model_validate(u) for u in users]

    def update_user_admin(
        self,
        user_id: int,
        *,
        name: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> UserRead:
        """Administrative update with role and activation controls."""

        user = self.repo.by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if name is not None:
            user.name = name
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active

        user.updated_at = datetime.now(UTC)
        saved = self.repo.save(user)
        return UserRead.model_validate(saved)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _hash_password(self, password: str) -> str:
        """Return a salted PBKDF2 hash for the provided password."""

        salt = secrets.token_bytes(16)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self._HASH_ITERATIONS,
        )
        return f"{self._HASH_ALGORITHM}${self._HASH_ITERATIONS}${salt.hex()}${dk.hex()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify the provided password against stored hash."""

        try:
            algorithm, iterations_str, salt_hex, hash_hex = password_hash.split("$")
        except ValueError:
            return False

        if algorithm != self._HASH_ALGORITHM:
            return False

        try:
            iterations = int(iterations_str)
            salt = bytes.fromhex(salt_hex)
            stored_hash = bytes.fromhex(hash_hex)
        except ValueError:
            return False

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(new_hash, stored_hash)

    def _validate_email(self, email: str) -> None:
        """Ensure email roughly matches username@domain.tld format."""

        if not self._EMAIL_PATTERN.match(email):
            raise ValueError("Invalid email format")


__all__ = [
    "AuthenticationResult",
    "UserLogin",
    "UserRead",
    "UserRegister",
    "UserService",
    "UserUpdate",
]
