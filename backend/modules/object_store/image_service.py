"""
Image Service

This module provides image upload, storage, and retrieval capabilities
using S3 for file storage and PostgreSQL for metadata.
"""

import logging
import uuid

from fastapi import UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Image
from src.services.s3_provider import S3Provider, create_s3_config_from_env

logger = logging.getLogger(__name__)


# Pydantic Models
class ImageResponse(BaseModel):
    """Response model for image metadata and access"""

    id: str
    filename: str
    content_type: str
    file_size: int
    width: int | None = None
    height: int | None = None
    category: str
    alt_text: str | None = None
    description: str | None = None
    url: str | None = Field(default=None, description="Presigned URL for image access (if requested)")

    class Config:
        from_attributes = True


class ImageListResponse(BaseModel):
    """Response model for multiple images"""

    images: list[ImageResponse]
    total: int


class ImageService:
    """Service for managing image uploads and retrievals"""

    def __init__(self, bucket_name: str = "digital-innie") -> None:
        """
        Initialize image service.

        Args:
            bucket_name: S3 bucket name for image storage
        """
        self.bucket_name = bucket_name
        self._s3_provider: S3Provider | None = None

    def _get_s3_provider(self) -> S3Provider:
        """Get S3 provider, creating if needed."""
        if self._s3_provider is None:
            config = create_s3_config_from_env()
            self._s3_provider = S3Provider(config, self.bucket_name)
        return self._s3_provider

    async def upload_image(self, db_session: AsyncSession, user_id: uuid.UUID, file: UploadFile, width: int, height: int, category: str = "general", alt_text: str | None = None, description: str | None = None, max_size_mb: int = 10) -> ImageResponse:
        """
        Upload an image to S3 and save metadata to database.

        Args:
            db_session: Database session
            user_id: User ID uploading the image
            file: Image file to upload
            width: Image width in pixels
            height: Image height in pixels
            category: Image category (e.g., "profile", "content", "generated")
            alt_text: Alternative text for accessibility
            description: Image description
            max_size_mb: Maximum file size in MB

        Returns:
            Image metadata with upload confirmation

        Raises:
            Exception: If upload fails or validation errors occur
        """
        try:
            # Validate image type
            allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"]

            s3_provider = self._get_s3_provider()

            # Upload to S3
            file_metadata = await s3_provider.upload_file(user_id=str(user_id), file=file, category=category, allowed_types=allowed_types, max_size_mb=max_size_mb)

            # Create database record
            image = Image(
                user_id=user_id,
                s3_key=file_metadata.s3_key,
                s3_bucket=self.bucket_name,
                filename=file_metadata.filename,
                content_type=file_metadata.content_type,
                file_size=file_metadata.file_size,
                width=width,
                height=height,
                category=category,
                alt_text=alt_text,
                description=description,
            )

            db_session.add(image)
            await db_session.commit()
            await db_session.refresh(image)

            logger.info(f"Successfully uploaded image {image.id} for user {user_id}")

            return ImageResponse(
                id=str(image.id), filename=image.filename, content_type=image.content_type, file_size=image.file_size, width=image.width, height=image.height, category=image.category, alt_text=image.alt_text, description=image.description
            )

        except Exception as e:
            logger.error(f"Failed to upload image for user {user_id}: {e!s}")
            await db_session.rollback()
            raise

    async def get_image(self, db_session: AsyncSession, image_id: uuid.UUID, user_id: uuid.UUID, include_url: bool = False, url_expires_in: int = 3600) -> ImageResponse | None:
        """
        Get image metadata by ID.

        Args:
            db_session: Database session
            image_id: Image ID to retrieve
            user_id: User ID (for authorization)
            include_url: Whether to generate presigned URL
            url_expires_in: URL expiration time in seconds

        Returns:
            Image metadata or None if not found
        """
        try:
            # Query image with user authorization
            stmt = select(Image).where(Image.id == image_id, Image.user_id == user_id)
            result = await db_session.execute(stmt)
            image = result.scalar_one_or_none()

            if not image:
                return None

            # Generate presigned URL if requested
            url = None
            if include_url:
                s3_provider = self._get_s3_provider()
                url = await s3_provider.get_presigned_url(image.s3_key, expires_in=url_expires_in)

            return ImageResponse(
                id=str(image.id), filename=image.filename, content_type=image.content_type, file_size=image.file_size, width=image.width, height=image.height, category=image.category, alt_text=image.alt_text, description=image.description, url=url
            )

        except Exception as e:
            logger.error(f"Failed to get image {image_id} for user {user_id}: {e!s}")
            raise

    async def list_user_images(self, db_session: AsyncSession, user_id: uuid.UUID, category: str | None = None, include_urls: bool = False, url_expires_in: int = 3600, limit: int = 50, offset: int = 0) -> ImageListResponse:
        """
        List images for a user.

        Args:
            db_session: Database session
            user_id: User ID
            category: Optional category filter
            include_urls: Whether to generate presigned URLs
            url_expires_in: URL expiration time in seconds
            limit: Maximum number of images to return
            offset: Number of images to skip

        Returns:
            List of user's images
        """
        try:
            # Build query
            stmt = select(Image).where(Image.user_id == user_id)

            if category:
                stmt = stmt.where(Image.category == category)

            # Add pagination
            stmt = stmt.offset(offset).limit(limit)

            # Order by most recent first
            stmt = stmt.order_by(Image.created_at.desc())

            result = await db_session.execute(stmt)
            images = result.scalars().all()

            # Convert to response models
            image_responses = []
            s3_provider = self._get_s3_provider() if include_urls else None

            for image in images:
                url = None
                if include_urls and s3_provider:
                    url = await s3_provider.get_presigned_url(image.s3_key, expires_in=url_expires_in)

                image_responses.append(
                    ImageResponse(
                        id=str(image.id),
                        filename=image.filename,
                        content_type=image.content_type,
                        file_size=image.file_size,
                        width=image.width,
                        height=image.height,
                        category=image.category,
                        alt_text=image.alt_text,
                        description=image.description,
                        url=url,
                    )
                )

            # Get total count for pagination
            count_stmt = select(Image).where(Image.user_id == user_id)
            if category:
                count_stmt = count_stmt.where(Image.category == category)

            count_result = await db_session.execute(count_stmt)
            total = len(count_result.scalars().all())

            return ImageListResponse(images=image_responses, total=total)

        except Exception as e:
            logger.error(f"Failed to list images for user {user_id}: {e!s}")
            raise

    async def delete_image(self, db_session: AsyncSession, image_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Delete an image from both S3 and database.

        Args:
            db_session: Database session
            image_id: Image ID to delete
            user_id: User ID (for authorization)

        Returns:
            True if deleted successfully, False if not found
        """
        try:
            # Get image record
            stmt = select(Image).where(Image.id == image_id, Image.user_id == user_id)
            result = await db_session.execute(stmt)
            image = result.scalar_one_or_none()

            if not image:
                return False

            # Delete from S3
            s3_provider = self._get_s3_provider()
            await s3_provider.delete_file(image.s3_key)

            # Delete from database
            await db_session.delete(image)
            await db_session.commit()

            logger.info(f"Successfully deleted image {image_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete image {image_id} for user {user_id}: {e!s}")
            await db_session.rollback()
            raise
