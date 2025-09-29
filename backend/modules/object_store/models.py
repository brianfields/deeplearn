"""SQLAlchemy models for the object_store module."""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.shared_models import Base


class ImageModel(Base):
    """Database record representing stored images."""

    __tablename__ = "images"
    __table_args__ = (
        Index("ix_images_user_id", "user_id"),
        Index("ix_images_s3_key", "s3_key", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    s3_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    alt_text: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AudioModel(Base):
    """Database record representing stored audio files."""

    __tablename__ = "audios"
    __table_args__ = (
        Index("ix_audios_user_id", "user_id"),
        Index("ix_audios_s3_key", "s3_key", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    s3_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column()
    bitrate_kbps: Mapped[int | None] = mapped_column(Integer)
    sample_rate_hz: Mapped[int | None] = mapped_column(Integer)
    transcript: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
