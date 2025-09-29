"""
S3 provider implementation for general file storage and retrieval.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
import logging
import os
from pathlib import Path
from typing import Any
import uuid

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

# Configure logging
logger = logging.getLogger(__name__)

__all__ = ["FileMetadata", "S3Config", "S3Error", "S3Provider", "create_s3_config_from_env"]


class S3Error(Exception):
    """Base exception for S3 operations."""

    pass


class S3AuthenticationError(S3Error):
    """Authentication error with S3."""

    pass


class S3FileNotFoundError(S3Error):
    """File not found in S3."""

    pass


@dataclass
class S3Config:
    """S3 configuration."""

    region: str = "us-east-1"
    access_key_id: str | None = None
    secret_access_key: str | None = None
    endpoint_url: str | None = None  # For localstack/minio


def create_s3_config_from_env() -> S3Config:
    """
    Create S3 configuration from environment variables.

    Returns:
        S3Config: Configured S3 instance

    Raises:
        ValueError: If configuration is invalid
    """
    # Read environment variables
    region = os.getenv("S3_REGION", "us-east-1")
    access_key_id = os.getenv("S3_ACCESS_KEY_ID")
    secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY")
    endpoint_url = os.getenv("S3_ENDPOINT_URL")  # For localstack/minio

    # Note: AWS SDK will fall back to IAM roles, instance profiles, etc.
    # if access keys are not provided, so we don't require them here

    return S3Config(
        region=region,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        endpoint_url=endpoint_url,
    )


@dataclass
class FileMetadata:
    """File metadata returned from S3 operations."""

    file_id: str
    s3_key: str
    filename: str
    content_type: str
    file_size: int
    created_at: datetime


class S3Provider:
    """
    S3 provider for general file storage and retrieval.

    Handles file uploads, downloads, deletions, and URL generation
    with proper error handling and async support.
    """

    def __init__(self, config: S3Config, bucket_name: str) -> None:
        """
        Initialize S3 provider.

        Args:
            config: S3 configuration
            bucket_name: S3 bucket name to use for operations
        """
        self.config = config
        self.bucket_name = bucket_name
        self._client = None

    def _get_client(self) -> Any:
        """Get S3 client, creating if needed."""
        if self._client is None:
            session = boto3.Session(aws_access_key_id=self.config.access_key_id, aws_secret_access_key=self.config.secret_access_key, region_name=self.config.region)
            self._client = session.client("s3", endpoint_url=self.config.endpoint_url)
        return self._client

    def _generate_file_key(self, user_id: str, filename: str, category: str = "files") -> str:
        """
        Generate a unique S3 key for the file.

        Args:
            user_id: User ID
            filename: Original filename
            category: File category (e.g., "images", "documents")

        Returns:
            Unique S3 key
        """
        file_id = str(uuid.uuid4())
        file_extension = Path(filename).suffix.lower()
        return f"users/{user_id}/{category}/{file_id}{file_extension}"

    async def upload_file(self, user_id: str, file: UploadFile, category: str = "files", allowed_types: list[str] | None = None, max_size_mb: int = 10) -> FileMetadata:
        """
        Upload a file to S3.

        Args:
            user_id: User ID
            file: File to upload
            category: File category for organization
            allowed_types: Allowed MIME types (None = allow all)
            max_size_mb: Maximum file size in MB

        Returns:
            File metadata

        Raises:
            S3Error: If upload fails
        """
        try:
            # Validate file type
            if allowed_types and file.content_type not in allowed_types:
                raise S3Error(f"File type {file.content_type} not allowed")

            # Read file content
            content = await file.read()
            file_size = len(content)

            # Validate file size
            max_size_bytes = max_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                raise S3Error(f"File size {file_size} exceeds limit of {max_size_bytes} bytes")

            # Generate S3 key
            s3_key = self._generate_file_key(user_id, file.filename or "unnamed", category)

            # Upload to S3
            client = self._get_client()
            await asyncio.get_event_loop().run_in_executor(None, lambda: client.put_object(Bucket=self.bucket_name, Key=s3_key, Body=content, ContentType=file.content_type or "application/octet-stream"))

            logger.info(f"Successfully uploaded file {s3_key} for user {user_id}")

            return FileMetadata(file_id=Path(s3_key).stem, s3_key=s3_key, filename=file.filename or "unnamed", content_type=file.content_type or "application/octet-stream", file_size=file_size, created_at=datetime.utcnow())

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoCredentialsError":
                raise S3AuthenticationError("Invalid AWS credentials") from e
            raise S3Error(f"S3 upload failed: {error_code}") from e
        except Exception as e:
            logger.error(f"Failed to upload file for user {user_id}: {e!s}")
            raise S3Error(f"Upload failed: {e!s}") from e

    async def get_presigned_url(self, s3_key: str, expires_in: int = 3600, method: str = "get_object") -> str:
        """
        Generate a presigned URL for file access.

        Args:
            s3_key: S3 key of the file
            expires_in: URL expiration time in seconds
            method: S3 method (get_object, put_object, etc.)

        Returns:
            Presigned URL

        Raises:
            S3Error: If URL generation fails
        """
        try:
            client = self._get_client()
            url = await asyncio.get_event_loop().run_in_executor(None, lambda: client.generate_presigned_url(method, Params={"Bucket": self.bucket_name, "Key": s3_key}, ExpiresIn=expires_in))

            logger.info(f"Generated presigned URL for {s3_key}")
            return url

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            raise S3Error(f"Failed to generate presigned URL: {error_code}") from e
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e!s}")
            raise S3Error(f"URL generation failed: {e!s}") from e

    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_key: S3 key of the file to delete

        Returns:
            True if deleted successfully, False if file didn't exist

        Raises:
            S3Error: If deletion fails
        """
        try:
            client = self._get_client()
            await asyncio.get_event_loop().run_in_executor(None, lambda: client.delete_object(Bucket=self.bucket_name, Key=s3_key))

            logger.info(f"Successfully deleted file {s3_key}")
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                logger.warning(f"File {s3_key} not found for deletion")
                return False
            raise S3Error(f"S3 deletion failed: {error_code}") from e
        except Exception as e:
            logger.error(f"Failed to delete file {s3_key}: {e!s}")
            raise S3Error(f"Deletion failed: {e!s}") from e

    async def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.

        Args:
            s3_key: S3 key to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            client = self._get_client()
            await asyncio.get_event_loop().run_in_executor(None, lambda: client.head_object(Bucket=self.bucket_name, Key=s3_key))
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ["NoSuchKey", "404"]:
                return False
            raise S3Error(f"Failed to check file existence: {error_code}") from e
        except Exception as e:
            logger.error(f"Failed to check existence of {s3_key}: {e!s}")
            raise S3Error(f"Existence check failed: {e!s}") from e

    async def get_file_metadata(self, s3_key: str) -> dict:
        """
        Get file metadata from S3.

        Args:
            s3_key: S3 key of the file

        Returns:
            File metadata dictionary

        Raises:
            S3FileNotFoundError: If file doesn't exist
            S3Error: If metadata retrieval fails
        """
        try:
            client = self._get_client()
            response = await asyncio.get_event_loop().run_in_executor(None, lambda: client.head_object(Bucket=self.bucket_name, Key=s3_key))

            return {"content_type": response.get("ContentType"), "content_length": response.get("ContentLength"), "last_modified": response.get("LastModified"), "etag": response.get("ETag")}

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ["NoSuchKey", "404"]:
                raise S3FileNotFoundError(f"File {s3_key} not found") from e
            raise S3Error(f"Failed to get file metadata: {error_code}") from e
        except Exception as e:
            logger.error(f"Failed to get metadata for {s3_key}: {e!s}")
            raise S3Error(f"Metadata retrieval failed: {e!s}") from e
