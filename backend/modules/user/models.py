"""User module database models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from modules.shared_models import Base


class UserModel(Base):
    """SQLAlchemy model representing application users."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(512), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="learner")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<UserModel id={self.id} email={self.email!r} role={self.role!r}>"
