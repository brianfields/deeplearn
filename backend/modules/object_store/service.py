"""Business logic for the object_store module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
import logging
import struct
import uuid
import wave

try:  # pragma: no cover - optional dependency
    from mutagen import File as MutagenFile  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    MutagenFile = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Image = None  # type: ignore
from pydantic import BaseModel, Field

from .repo import AudioRepo, ImageRepo
from .s3_provider import FileMetadata, S3Error, S3FileNotFoundError, S3Provider

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
IMAGE_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)
AUDIO_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/flac",
        "audio/x-flac",
        "audio/mp4",
        "audio/m4a",
    }
)


class ObjectStoreError(Exception):
    """Base exception for the object store service."""


class FileValidationError(ObjectStoreError):
    """Raised when a file fails validation checks."""


class AuthorizationError(ObjectStoreError):
    """Raised when a user attempts to access a file they do not own."""


class StoredFileNotFoundError(ObjectStoreError):
    """Raised when a requested file is not found."""


class StorageProviderError(ObjectStoreError):
    """Raised when the underlying S3 provider fails."""


class ImageRead(BaseModel):
    """DTO for image metadata."""

    id: uuid.UUID
    user_id: int | None
    s3_key: str
    s3_bucket: str
    filename: str
    content_type: str
    file_size: int
    width: int | None
    height: int | None
    alt_text: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    presigned_url: str | None = None

    model_config = {
        "from_attributes": True,
    }


class ImageCreate(BaseModel):
    """Payload for creating an image record."""

    user_id: int | None
    filename: str
    content_type: str
    content: bytes = Field(repr=False)
    alt_text: str | None = None
    description: str | None = None


class AudioRead(BaseModel):
    """DTO for audio metadata."""

    id: uuid.UUID
    user_id: int | None
    s3_key: str
    s3_bucket: str
    filename: str
    content_type: str
    file_size: int
    duration_seconds: float | None
    bitrate_kbps: int | None
    sample_rate_hz: int | None
    transcript: str | None = None
    created_at: datetime
    updated_at: datetime
    presigned_url: str | None = None

    model_config = {
        "from_attributes": True,
    }


class AudioCreate(BaseModel):
    """Payload for creating an audio record."""

    user_id: int | None
    filename: str
    content_type: str
    content: bytes = Field(repr=False)
    transcript: str | None = None


class FileUploadResult(BaseModel):
    """Return type for upload operations."""

    file: ImageRead | AudioRead
    presigned_url: str | None = None


@dataclass(slots=True)
class _ImageMetadata:
    width: int | None
    height: int | None


@dataclass(slots=True)
class _AudioMetadata:
    duration_seconds: float | None
    bitrate_kbps: int | None
    sample_rate_hz: int | None


class ObjectStoreService:
    """Service coordinating storage of images and audio in S3 with metadata in Postgres."""

    def __init__(self, image_repo: ImageRepo, audio_repo: AudioRepo, s3: S3Provider) -> None:
        self._images = image_repo
        self._audio = audio_repo
        self._s3 = s3

    async def upload_image(
        self,
        data: ImageCreate,
        *,
        generate_presigned_url: bool = False,
        presigned_ttl_seconds: int = 3600,
    ) -> FileUploadResult:
        self._validate_file(data.content, data.content_type, IMAGE_CONTENT_TYPES)
        metadata = self._extract_image_metadata(data.content)
        upload_metadata = await self._upload_to_s3(
            user_id=data.user_id,
            filename=data.filename,
            content_type=data.content_type,
            content=data.content,
            category="images",
        )
        image = await self._images.create(
            user_id=data.user_id,
            s3_key=upload_metadata.s3_key,
            s3_bucket=self._s3.bucket_name,
            filename=upload_metadata.filename,
            content_type=upload_metadata.content_type,
            file_size=upload_metadata.file_size,
            width=metadata.width,
            height=metadata.height,
            alt_text=data.alt_text,
            description=data.description,
        )
        url = await self._s3.get_presigned_url(image.s3_key, expires_in=presigned_ttl_seconds) if generate_presigned_url else None
        dto = ImageRead.model_validate(image)
        if url is not None:
            dto = dto.model_copy(update={"presigned_url": url})
        return FileUploadResult(file=dto, presigned_url=url)

    async def upload_audio(
        self,
        data: AudioCreate,
        *,
        generate_presigned_url: bool = False,
        presigned_ttl_seconds: int = 3600,
    ) -> FileUploadResult:
        self._validate_file(data.content, data.content_type, AUDIO_CONTENT_TYPES)
        metadata = self._extract_audio_metadata(data.content)
        upload_metadata = await self._upload_to_s3(
            user_id=data.user_id,
            filename=data.filename,
            content_type=data.content_type,
            content=data.content,
            category="audio",
        )
        audio = await self._audio.create(
            user_id=data.user_id,
            s3_key=upload_metadata.s3_key,
            s3_bucket=self._s3.bucket_name,
            filename=upload_metadata.filename,
            content_type=upload_metadata.content_type,
            file_size=upload_metadata.file_size,
            duration_seconds=metadata.duration_seconds,
            bitrate_kbps=metadata.bitrate_kbps,
            sample_rate_hz=metadata.sample_rate_hz,
            transcript=data.transcript,
        )
        url = await self._s3.get_presigned_url(audio.s3_key, expires_in=presigned_ttl_seconds) if generate_presigned_url else None
        dto = AudioRead.model_validate(audio)
        if url is not None:
            dto = dto.model_copy(update={"presigned_url": url})
        return FileUploadResult(file=dto, presigned_url=url)

    async def get_image(
        self,
        image_id: uuid.UUID,
        *,
        requesting_user_id: int | None,
        include_presigned_url: bool = False,
        presigned_ttl_seconds: int = 3600,
    ) -> ImageRead:
        image = await self._images.by_id(image_id)
        if not image:
            raise StoredFileNotFoundError(f"Image {image_id} not found")
        self._ensure_authorized(image.user_id, requesting_user_id)
        url = await self._s3.get_presigned_url(image.s3_key, expires_in=presigned_ttl_seconds) if include_presigned_url else None
        dto = ImageRead.model_validate(image)
        if url is not None:
            dto = dto.model_copy(update={"presigned_url": url})
        return dto

    async def get_audio(
        self,
        audio_id: uuid.UUID,
        *,
        requesting_user_id: int | None,
        include_presigned_url: bool = False,
        presigned_ttl_seconds: int = 3600,
    ) -> AudioRead:
        audio = await self._audio.by_id(audio_id)
        if not audio:
            raise StoredFileNotFoundError(f"Audio {audio_id} not found")
        self._ensure_authorized(audio.user_id, requesting_user_id)
        url = await self._s3.get_presigned_url(audio.s3_key, expires_in=presigned_ttl_seconds) if include_presigned_url else None
        dto = AudioRead.model_validate(audio)
        if url is not None:
            dto = dto.model_copy(update={"presigned_url": url})
        return dto

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
        records = await self._images.list_by_user(user_id, limit=limit, offset=offset)
        total = await self._images.count_by_user(user_id)
        if include_system:
            system_records = await self._images.list_global(limit=limit, offset=offset)
            records.extend(system_records)
            total += await self._images.count_by_user(None)
        url_map: dict[str, str | None] = {}
        if include_presigned_url:
            for record in records:
                url_map[record.s3_key] = await self._s3.get_presigned_url(record.s3_key, expires_in=presigned_ttl_seconds)
        dtos: list[ImageRead] = []
        for img in records:
            dto = ImageRead.model_validate(img)
            url = url_map.get(img.s3_key)
            if url is not None:
                dto = dto.model_copy(update={"presigned_url": url})
            dtos.append(dto)
        return dtos, total

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
        records = await self._audio.list_by_user(user_id, limit=limit, offset=offset)
        total = await self._audio.count_by_user(user_id)
        if include_system:
            system_records = await self._audio.list_global(limit=limit, offset=offset)
            records.extend(system_records)
            total += await self._audio.count_by_user(None)
        url_map: dict[str, str | None] = {}
        if include_presigned_url:
            for record in records:
                url_map[record.s3_key] = await self._s3.get_presigned_url(record.s3_key, expires_in=presigned_ttl_seconds)
        dtos: list[AudioRead] = []
        for aud in records:
            dto = AudioRead.model_validate(aud)
            url = url_map.get(aud.s3_key)
            if url is not None:
                dto = dto.model_copy(update={"presigned_url": url})
            dtos.append(dto)
        return dtos, total

    async def delete_image(self, image_id: uuid.UUID, *, requesting_user_id: int | None) -> None:
        image = await self._images.by_id(image_id)
        if not image:
            raise StoredFileNotFoundError(f"Image {image_id} not found")
        self._ensure_authorized(image.user_id, requesting_user_id)
        await self._delete_from_s3(image.s3_key)
        await self._images.delete(image)

    async def delete_audio(self, audio_id: uuid.UUID, *, requesting_user_id: int | None) -> None:
        audio = await self._audio.by_id(audio_id)
        if not audio:
            raise StoredFileNotFoundError(f"Audio {audio_id} not found")
        self._ensure_authorized(audio.user_id, requesting_user_id)
        await self._delete_from_s3(audio.s3_key)
        await self._audio.delete(audio)

    async def generate_presigned_url(self, s3_key: str, *, expires_in: int = 3600) -> str:
        try:
            return await self._s3.get_presigned_url(s3_key, expires_in=expires_in)
        except S3FileNotFoundError as exc:  # pragma: no cover - defensive, S3 returns not-found
            raise StoredFileNotFoundError(str(exc)) from exc
        except S3Error as exc:  # pragma: no cover - network edge-case
            raise StorageProviderError(str(exc)) from exc

    async def _upload_to_s3(
        self,
        *,
        user_id: int | None,
        filename: str,
        content_type: str,
        content: bytes,
        category: str,
    ) -> FileMetadata:
        try:
            return await self._s3.upload_content(
                user_identifier=self._user_identifier(user_id),
                filename=filename,
                content=content,
                content_type=content_type,
                category=category,
                max_size_bytes=MAX_FILE_SIZE_BYTES,
            )
        except S3Error as exc:  # pragma: no cover - network edge-case
            raise StorageProviderError(str(exc)) from exc

    async def _delete_from_s3(self, s3_key: str) -> None:
        try:
            await self._s3.delete_file(s3_key)
        except S3Error as exc:  # pragma: no cover - network edge-case
            raise StorageProviderError(str(exc)) from exc

    @staticmethod
    def _validate_file(content: bytes, content_type: str, allowed_types: frozenset[str]) -> None:
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise FileValidationError("File exceeds maximum size of 100MB")
        if content_type not in allowed_types:
            raise FileValidationError(f"Unsupported content type: {content_type}")

    @staticmethod
    def _ensure_authorized(owner_id: int | None, requester_id: int | None) -> None:
        if owner_id is not None and owner_id != requester_id:
            raise AuthorizationError("Requesting user does not own this file")

    @staticmethod
    def _user_identifier(user_id: int | None) -> str:
        return str(user_id) if user_id is not None else "system"

    @staticmethod
    def _extract_image_metadata(content: bytes) -> _ImageMetadata:
        if Image is not None:
            try:
                with Image.open(BytesIO(content)) as img:  # type: ignore[arg-type]
                    width, height = img.size
                    return _ImageMetadata(width=int(width), height=int(height))
            except Exception:  # pragma: no cover - fallback when metadata fails
                logger.error("Failed to extract image metadata", exc_info=True)
                pass

        if content.startswith(b"\x89PNG\r\n\x1a\n") and len(content) >= 24:
            width, height = struct.unpack(">II", content[16:24])
            return _ImageMetadata(width=int(width), height=int(height))

        if content.startswith(b"GIF") and len(content) >= 10:
            width, height = struct.unpack("<HH", content[6:10])
            return _ImageMetadata(width=int(width), height=int(height))

        return _ImageMetadata(width=None, height=None)

    @staticmethod
    def _extract_audio_metadata(content: bytes) -> _AudioMetadata:
        if MutagenFile is not None:
            try:
                audio = MutagenFile(BytesIO(content))
            except Exception:  # pragma: no cover - fallback when metadata fails
                audio = None
            if audio is not None and getattr(audio, "info", None):
                info = audio.info
                duration = float(getattr(info, "length", 0.0)) if getattr(info, "length", None) else None
                bitrate = int(getattr(info, "bitrate", 0) / 1000) if getattr(info, "bitrate", None) else None
                sample_rate = int(getattr(info, "sample_rate", 0)) if getattr(info, "sample_rate", None) else None
                return _AudioMetadata(duration_seconds=duration, bitrate_kbps=bitrate, sample_rate_hz=sample_rate)

        try:
            with wave.open(BytesIO(content)) as wav_file:
                sample_rate = wav_file.getframerate()
                frame_count = wav_file.getnframes()
                duration = frame_count / float(sample_rate) if sample_rate else None
                sample_width = wav_file.getsampwidth()
                channels = wav_file.getnchannels()
        except wave.Error:  # pragma: no cover - fallback when metadata fails
            return _AudioMetadata(duration_seconds=None, bitrate_kbps=None, sample_rate_hz=None)

        bitrate = None
        if sample_rate and sample_width:
            bitrate = int(sample_rate * sample_width * channels * 8 / 1000)
        return _AudioMetadata(duration_seconds=duration, bitrate_kbps=bitrate, sample_rate_hz=sample_rate)
