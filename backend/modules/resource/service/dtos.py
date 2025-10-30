"""DTOs for the resource module."""

from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, Field, HttpUrl


class ResourceRead(BaseModel):
    """DTO returning complete resource details."""

    id: uuid.UUID
    user_id: int
    resource_type: str = Field(description="Type of resource (e.g., 'file_upload', 'url', 'generated_source').")
    filename: str | None
    source_url: str | None
    extracted_text: str
    extraction_metadata: dict[str, Any]
    file_size: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ResourceSummary(BaseModel):
    """Compact representation for listing resources."""

    id: uuid.UUID
    resource_type: str
    filename: str | None
    source_url: str | None
    file_size: int | None
    created_at: datetime
    preview_text: str

    model_config = {
        "from_attributes": True,
    }


class FileResourceCreate(BaseModel):
    """Payload for file-based resource uploads."""

    user_id: int
    filename: str
    content_type: str
    content: bytes = Field(repr=False)
    file_size: int | None = None


class UrlResourceCreate(BaseModel):
    """Payload for URL-based resources."""

    user_id: int
    url: HttpUrl


__all__ = [
    "FileResourceCreate",
    "ResourceRead",
    "ResourceSummary",
    "UrlResourceCreate",
]
