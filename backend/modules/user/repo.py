"""User module data access layer."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import UserModel


class UserRepo:
    """Repository encapsulating user database operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def by_id(self, user_id: int) -> UserModel | None:
        """Return a user by database identifier."""

        return self.session.get(UserModel, user_id)

    def by_email(self, email: str) -> UserModel | None:
        """Return a user by email address."""

        stmt = select(UserModel).where(UserModel.email == email)
        return self.session.execute(stmt).scalar_one_or_none()

    def create(
        self,
        *,
        email: str,
        password_hash: str,
        name: str,
        role: str = "learner",
        is_active: bool = True,
    ) -> UserModel:
        """Persist a new user and return the ORM instance."""

        user = UserModel(
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
            is_active=is_active,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def save(self, user: UserModel) -> UserModel:
        """Persist changes to an existing user."""

        self.session.add(user)
        self.session.flush()
        return user

    def list_all(self) -> list[UserModel]:
        """Return all users. Primarily for admin tooling."""

        stmt = select(UserModel).order_by(UserModel.id.asc())
        return list(self.session.execute(stmt).scalars().all())
