"""Public interface for the object_store module."""

from __future__ import annotations

import os
from typing import Protocol
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .repo import AudioRepo, ImageRepo
from .s3_provider import S3Provider, create_s3_config_from_env
from .service import AudioCreate, AudioRead, FileUploadResult, ImageCreate, ImageRead, ObjectStoreService


class ObjectStoreProvider(Protocol):
    """Protocol exposing the object store service contract."""

    async def upload_image(
        self,
        data: ImageCreate,
        *,
        generate_presigned_url: bool = False,
        presigned_ttl_seconds: int = 3600,
    ) -> FileUploadResult:
        """Upload an image and store metadata."""

    async def upload_audio(
        self,
        data: AudioCreate,
        *,
        generate_presigned_url: bool = False,
        presigned_ttl_seconds: int = 3600,
    ) -> FileUploadResult:
        """Upload an audio file and store metadata."""

    async def get_image(
        self,
        image_id: uuid.UUID,
        *,
        requesting_user_id: int | None,
        include_presigned_url: bool = False,
        presigned_ttl_seconds: int = 3600,
    ) -> ImageRead:
        """Retrieve a single image by id."""

    async def get_audio(
        self,
        audio_id: uuid.UUID,
        *,
        requesting_user_id: int | None,
        include_presigned_url: bool = False,
        presigned_ttl_seconds: int = 3600,
    ) -> AudioRead:
        """Retrieve a single audio file by id."""

    async def list_images(
        self,
        user_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
        include_presigned_url: bool = False,
        presigned_ttl_seconds: int = 3600,
        include_system: bool = False,
    ) -> tuple[list[ImageRead], int]:
        """List images for a given user with pagination."""

    async def list_audio(
        self,
        user_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
        include_presigned_url: bool = False,
        presigned_ttl_seconds: int = 3600,
        include_system: bool = False,
    ) -> tuple[list[AudioRead], int]:
        """List audio files for a given user with pagination."""

    async def delete_image(self, image_id: uuid.UUID, *, requesting_user_id: int | None) -> None:
        """Delete an image by id."""

    async def delete_audio(self, audio_id: uuid.UUID, *, requesting_user_id: int | None) -> None:
        """Delete an audio file by id."""

    async def generate_presigned_url(self, s3_key: str, *, expires_in: int = 3600) -> str:
        """Generate a presigned URL for a stored file."""


def object_store_provider(
    session: AsyncSession,
    *,
    bucket_name: str | None = None,
) -> ObjectStoreProvider:
    """Factory for the object store service used by other modules."""

    config = create_s3_config_from_env()
    resolved_bucket = bucket_name or os.getenv("OBJECT_STORE_BUCKET", "digital-innie")
    s3 = S3Provider(config, resolved_bucket)
    return ObjectStoreService(ImageRepo(session), AudioRepo(session), s3)


__all__ = [
    "AudioCreate",
    "AudioRead",
    "FileUploadResult",
    "ImageCreate",
    "ImageRead",
    "ObjectStoreProvider",
    "object_store_provider",
]
