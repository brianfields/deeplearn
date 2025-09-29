"""Unit tests for the object store service."""

from __future__ import annotations

import base64
from collections.abc import Iterable
from datetime import datetime
from io import BytesIO
from typing import Any
import uuid
import wave

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, sessionmaker

from modules.object_store.repo import AudioRepo, ImageRepo
from modules.object_store.s3_provider import FileMetadata, S3Error
from modules.object_store.service import (
    AudioCreate,
    AudioRead,
    AuthorizationError,
    FileUploadResult,
    FileValidationError,
    ImageCreate,
    ImageRead,
    ObjectStoreService,
    StorageProviderError,
)
from modules.shared_models import Base


class _AsyncSessionStub(AsyncSession):
    """Minimal async wrapper around a synchronous Session for testing."""

    def __init__(self, sync_session: Session) -> None:  # type: ignore[override]
        self._sync = sync_session

    async def get(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        return self._sync.get(*args, **kwargs)

    async def execute(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        return self._sync.execute(*args, **kwargs)

    def add(self, instance: Any, _warn: bool = True) -> None:  # type: ignore[override]
        self._sync.add(instance)

    def add_all(self, instances: Iterable[Any]) -> None:  # type: ignore[override]
        self._sync.add_all(instances)

    async def flush(self) -> None:  # type: ignore[override]
        self._sync.flush()

    async def refresh(self, instance: Any) -> None:  # type: ignore[override]
        self._sync.refresh(instance)

    async def delete(self, instance: Any) -> None:  # type: ignore[override]
        self._sync.delete(instance)


class _FakeS3Provider:
    """In-memory fake provider for unit tests."""

    def __init__(self) -> None:
        self.bucket_name = "test-bucket"
        self._files: dict[str, bytes] = {}
        self.raise_on_upload = False

    async def upload_content(
        self,
        *,
        user_identifier: str,
        filename: str,
        content: bytes,
        content_type: str,
        category: str = "files",
        allowed_types: list[str] | None = None,
        max_size_bytes: int | None = None,
    ) -> FileMetadata:  # type: ignore[override]
        if self.raise_on_upload:
            raise S3Error("forced failure")
        if allowed_types and content_type not in allowed_types:
            raise S3Error("invalid type")
        if max_size_bytes is not None and len(content) > max_size_bytes:
            raise S3Error("too large")
        key = f"users/{user_identifier}/{category}/{uuid.uuid4()}-{filename}"
        self._files[key] = content
        return FileMetadata(
            file_id="test",
            s3_key=key,
            bucket_name=self.bucket_name,
            filename=filename,
            content_type=content_type,
            file_size=len(content),
            created_at=datetime.utcnow(),
        )

    async def get_presigned_url(self, s3_key: str, expires_in: int = 3600, _method: str = "get_object") -> str:
        if s3_key not in self._files:
            raise S3Error("missing")
        return f"https://example.com/{s3_key}?expires={expires_in}"

    async def delete_file(self, s3_key: str) -> bool:
        self._files.pop(s3_key, None)
        return True


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sync_session = sessionmaker(bind=engine)()
    try:
        yield _AsyncSessionStub(sync_session)
    finally:
        sync_session.close()
        engine.dispose()


@pytest_asyncio.fixture
async def service(session: AsyncSession) -> ObjectStoreService:
    fake_s3 = _FakeS3Provider()
    return ObjectStoreService(ImageRepo(session), AudioRepo(session), fake_s3)


def _make_png() -> bytes:
    # 1x1 red pixel PNG encoded in base64
    encoded = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AArEB5nSxd3sAAAAASUVORK5CYII="
    return base64.b64decode(encoded)


def _make_wav(duration_seconds: float = 0.1, sample_rate: int = 44100) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        frames = int(duration_seconds * sample_rate)
        wav_file.writeframes(b"\x00\x00" * frames)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_upload_image_persists_metadata(service: ObjectStoreService, session: AsyncSession) -> None:
    create = ImageCreate(
        user_id=1,
        filename="example.png",
        content_type="image/png",
        content=_make_png(),
        alt_text="alt",
        description="desc",
    )
    result = await service.upload_image(create, generate_presigned_url=True)
    assert isinstance(result, FileUploadResult)
    assert result.presigned_url is not None
    dto = result.file
    assert isinstance(dto, ImageRead)
    assert dto.width == 1
    assert dto.height == 1

    record = await ImageRepo(session).by_id(dto.id)
    assert record is not None
    assert record.alt_text == "alt"


@pytest.mark.asyncio
async def test_upload_audio_extracts_duration(service: ObjectStoreService, session: AsyncSession) -> None:
    create = AudioCreate(
        user_id=None,
        filename="sound.wav",
        content_type="audio/wav",
        content=_make_wav(),
        transcript="hello",
    )
    result = await service.upload_audio(create)
    dto = result.file
    assert isinstance(dto, AudioRead)
    assert dto.user_id is None
    assert dto.duration_seconds is not None
    assert dto.sample_rate_hz == 44100

    record = await AudioRepo(session).by_id(dto.id)
    assert record is not None
    assert record.transcript == "hello"


@pytest.mark.asyncio
async def test_get_image_enforces_authorization(service: ObjectStoreService) -> None:
    upload = await service.upload_image(ImageCreate(user_id=1, filename="example.png", content_type="image/png", content=_make_png()))

    with pytest.raises(AuthorizationError):
        await service.get_image(upload.file.id, requesting_user_id=2)

    authorized = await service.get_image(upload.file.id, requesting_user_id=1)
    assert isinstance(authorized, ImageRead)


@pytest.mark.asyncio
async def test_upload_image_rejects_invalid_type(service: ObjectStoreService) -> None:
    with pytest.raises(FileValidationError):
        await service.upload_image(ImageCreate(user_id=2, filename="bad.txt", content_type="text/plain", content=b"123"))


@pytest.mark.asyncio
async def test_list_images_includes_totals(service: ObjectStoreService) -> None:
    await service.upload_image(ImageCreate(user_id=5, filename="a.png", content_type="image/png", content=_make_png()))
    await service.upload_image(ImageCreate(user_id=None, filename="system.png", content_type="image/png", content=_make_png()))

    items, total = await service.list_images(5, include_system=True, include_presigned_url=True)
    assert total == 2
    assert len(items) == 2
    assert all(item.presigned_url is not None for item in items)


@pytest.mark.asyncio
async def test_delete_audio_removes_record(service: ObjectStoreService, session: AsyncSession) -> None:
    upload = await service.upload_audio(AudioCreate(user_id=9, filename="sound.wav", content_type="audio/wav", content=_make_wav()))
    audio_id = upload.file.id
    await service.delete_audio(audio_id, requesting_user_id=9)

    deleted = await AudioRepo(session).by_id(audio_id)
    assert deleted is None


@pytest.mark.asyncio
async def test_upload_audio_wraps_s3_errors(session: AsyncSession) -> None:
    failing_provider = _FakeS3Provider()
    failing_provider.raise_on_upload = True
    failing_service = ObjectStoreService(ImageRepo(session), AudioRepo(session), failing_provider)
    with pytest.raises(StorageProviderError):
        await failing_service.upload_audio(AudioCreate(user_id=1, filename="sound.wav", content_type="audio/wav", content=_make_wav()))


@pytest.mark.asyncio
async def test_file_size_validation(service: ObjectStoreService, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("modules.object_store.service.MAX_FILE_SIZE_BYTES", 10)
    with pytest.raises(FileValidationError):
        await service.upload_image(ImageCreate(user_id=1, filename="big.png", content_type="image/png", content=b"12345678901"))
