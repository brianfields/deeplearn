"""SQLAlchemy models for learner-provided resources."""

from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from modules.shared_models import Base, PostgresUUID


class ResourceModel(Base):
    """Persistent record describing a learner-provided resource."""

    __tablename__ = "resources"
    __table_args__ = (
        Index("ix_resources_user_id", "user_id"),
        Index("ix_resources_created_at", "created_at"),
        Index("ix_resources_object_store_image_id", "object_store_image_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    object_store_document_id: Mapped[uuid.UUID | None] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    object_store_image_id: Mapped[uuid.UUID | None] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("images.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
