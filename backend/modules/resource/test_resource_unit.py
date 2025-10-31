"""Unit tests for resource text extraction helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import uuid

from pypdf import PdfWriter
import pytest

from .service import PhotoResourceCreate, ResourceExtractionError, ResourceService, ResourceValidationError
from .service.extractors import (
    ExtractionError,
    extract_text_from_markdown,
    extract_text_from_pdf,
    extract_text_from_photo,
    extract_text_from_txt,
)
from .service.facade import MAX_EXTRACTED_TEXT_BYTES


class _StubRepo:
    def __init__(self) -> None:
        self.last_kwargs: dict[str, object] | None = None

    async def create(self, **kwargs: object) -> SimpleNamespace:  # type: ignore[override]
        self.last_kwargs = kwargs
        return SimpleNamespace(
            id=uuid.uuid4(),
            user_id=kwargs["user_id"],
            resource_type=kwargs["resource_type"],
            filename=kwargs["filename"],
            source_url=kwargs["source_url"],
            extracted_text=kwargs["extracted_text"],
            extraction_metadata=kwargs["extraction_metadata"],
            file_size=kwargs["file_size"],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


class _StubObjectStore:
    def __init__(self) -> None:
        self.last_upload: dict[str, object] | None = None
        self.last_result: SimpleNamespace | None = None

    async def upload_image(self, data, *, generate_presigned_url: bool, presigned_ttl_seconds: int):  # type: ignore[override]
        self.last_upload = {
            "data": data,
            "generate_presigned_url": generate_presigned_url,
            "presigned_ttl_seconds": presigned_ttl_seconds,
        }
        result = SimpleNamespace(
            file=SimpleNamespace(id=uuid.uuid4()),
            presigned_url="https://example.com/presigned.png",
        )
        self.last_result = result
        return result


class _StubLLMService:
    async def generate_response(self, *_args, **_kwargs):  # type: ignore[override]
        raise AssertionError("Should be patched in tests")


def test_extract_text_from_txt() -> None:
    """TXT extraction should decode UTF-8 content."""

    content = b"Learning resources are fun!"
    assert extract_text_from_txt(content) == "Learning resources are fun!"


def test_extract_text_from_markdown_preserves_content() -> None:
    """Markdown extraction should preserve structural characters."""

    content = b"# Heading\n\n- Item 1\n- Item 2"
    extracted = extract_text_from_markdown(content)
    assert "# Heading" in extracted
    assert "- Item 2" in extracted


def test_extract_text_from_pdf_handles_basic_document() -> None:
    """PDF extraction should succeed for simple documents."""

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = BytesIO()
    writer.write(buffer)
    pdf_bytes = buffer.getvalue()

    extracted = extract_text_from_pdf(pdf_bytes)
    assert isinstance(extracted, str)


@pytest.mark.asyncio
async def test_create_generated_source_resource_persists_metadata() -> None:
    """Generated source helper should persist supplemental content with metadata."""

    repo = AsyncMock()
    created_at = datetime.now(UTC)
    resource_id = uuid.uuid4()

    class _FakeResource:
        def __init__(self) -> None:
            self.id = resource_id
            self.user_id = 1
            self.resource_type = "generated_source"
            self.filename = None
            self.source_url = None
            self.extracted_text = "Combined source text"
            self.extraction_metadata = {
                "source": "generated_source",
                "unit_id": "unit-123",
                "truncated": False,
                "original_size": 18,
                "custom": "value",
            }
            self.file_size = None
            self.created_at = created_at
            self.updated_at = created_at

    repo.create.return_value = _FakeResource()

    service = ResourceService(repo=repo, object_store=MagicMock(), llm_services=MagicMock())

    result = await service.create_generated_source_resource(
        user_id=1,
        unit_id="unit-123",
        source_text="Combined source text",
        metadata={"custom": "value"},
    )

    assert result.resource_type == "generated_source"
    assert result.extraction_metadata["unit_id"] == "unit-123"
    assert result.extraction_metadata["custom"] == "value"
    repo.create.assert_awaited_once()
    kwargs = repo.create.await_args.kwargs
    assert kwargs["resource_type"] == "generated_source"
    assert kwargs["extracted_text"] == "Combined source text"
@pytest.mark.asyncio
async def test_extract_text_from_photo_parses_response() -> None:
    """Vision extraction should combine description and visible text."""

    class FakeLLM:
        async def generate_response(self, *_args, **kwargs):  # type: ignore[override]
            assert kwargs["model"] == "gpt-5-mini"
            assert kwargs["reasoning"] == {"effort": "low"}
            assert kwargs["text"] == {"verbosity": "medium"}
            assert kwargs["max_output_tokens"] == 100000
            return (
                SimpleNamespace(
                    content=json.dumps(
                        {
                            "description": "A whiteboard full of calculus",
                            "visible_text": "∫ f(x) dx = F(x) + C",
                        }
                    ),
                    model=kwargs.get("model", "gpt-5-mini"),
                ),
                uuid.uuid4(),
            )

    combined, metadata = await extract_text_from_photo(
        "https://example.com/photo.png",
        FakeLLM(),
    )

    assert "Visible text" in combined
    assert metadata["description"] == "A whiteboard full of calculus"
    assert metadata["visible_text"].startswith("∫ f(x)")
    assert metadata["vision_model"] == "gpt-5-mini"
    assert "llm_request_id" in metadata


@pytest.mark.asyncio
async def test_upload_photo_resource_persists_image(monkeypatch: pytest.MonkeyPatch) -> None:
    """Photo uploads should store image metadata and extracted context."""

    repo = _StubRepo()
    store = _StubObjectStore()
    llm = _StubLLMService()

    async def fake_extract(url: str, service: _StubLLMService) -> tuple[str, dict[str, object]]:
        assert url == "https://example.com/presigned.png"
        assert service is llm
        return "Study diagram", {"vision_model": "gpt-5-mini"}

    monkeypatch.setattr(
        "modules.resource.service.facade.extract_text_from_photo",
        fake_extract,
    )

    service = ResourceService(repo=repo, object_store=store, llm_services=llm)
    payload = PhotoResourceCreate(
        user_id=7,
        filename="notes.png",
        content_type="image/png",
        content=b"binary",
        file_size=512,
    )

    result = await service.upload_photo_resource(payload)

    assert result.resource_type == "photo"
    assert repo.last_kwargs is not None
    assert repo.last_kwargs["object_store_image_id"] == store.last_result.file.id
    assert repo.last_kwargs["extraction_metadata"]["vision_model"] == "gpt-5-mini"
    assert repo.last_kwargs["file_size"] == 512


@pytest.mark.asyncio
async def test_upload_photo_resource_validates_content_type() -> None:
    """Non-image content types should be rejected."""

    service = ResourceService(
        repo=_StubRepo(),
        object_store=_StubObjectStore(),
        llm_services=_StubLLMService(),
    )

    payload = PhotoResourceCreate(
        user_id=3,
        filename="bad.bin",
        content_type="application/octet-stream",
        content=b"bad",
        file_size=10,
    )

    with pytest.raises(ResourceValidationError):
        await service.upload_photo_resource(payload)


@pytest.mark.asyncio
async def test_upload_photo_resource_truncates_extracted_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """Long extracted text should be truncated to the service limit."""

    repo = _StubRepo()
    store = _StubObjectStore()
    llm = _StubLLMService()

    long_text = "A" * (MAX_EXTRACTED_TEXT_BYTES + 1024)
    metadata_template = {"vision_model": "gpt-5-mini"}

    async def fake_extract(url: str, service: _StubLLMService) -> tuple[str, dict[str, object]]:
        assert url == "https://example.com/presigned.png"
        return long_text, dict(metadata_template)

    monkeypatch.setattr(
        "modules.resource.service.facade.extract_text_from_photo",
        fake_extract,
    )

    service = ResourceService(repo=repo, object_store=store, llm_services=llm)
    payload = PhotoResourceCreate(
        user_id=9,
        filename="very-long.png",
        content_type="image/png",
        content=b"binary",
        file_size=MAX_EXTRACTED_TEXT_BYTES + 2048,
    )

    result = await service.upload_photo_resource(payload)

    assert len(result.extracted_text.encode("utf-8")) == MAX_EXTRACTED_TEXT_BYTES
    assert repo.last_kwargs is not None
    metadata = repo.last_kwargs["extraction_metadata"]
    assert metadata["truncated"] is True
    assert metadata["original_size"] == len(long_text.encode("utf-8"))


@pytest.mark.asyncio
async def test_upload_photo_resource_handles_vision_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vision extraction errors should surface as resource extraction errors."""

    repo = _StubRepo()
    store = _StubObjectStore()
    llm = _StubLLMService()

    async def failing_extract(url: str, service: _StubLLMService) -> tuple[str, dict[str, object]]:
        raise ExtractionError("Vision timed out")

    monkeypatch.setattr(
        "modules.resource.service.facade.extract_text_from_photo",
        failing_extract,
    )

    service = ResourceService(repo=repo, object_store=store, llm_services=llm)
    payload = PhotoResourceCreate(
        user_id=2,
        filename="fail.png",
        content_type="image/png",
        content=b"binary",
        file_size=512,
    )

    with pytest.raises(ResourceExtractionError) as exc:
        await service.upload_photo_resource(payload)

    assert "Vision timed out" in str(exc.value)


@pytest.mark.asyncio
async def test_upload_photo_resource_handles_object_store_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Object store failures should be converted to ResourceExtractionError."""

    class FailingStore(_StubObjectStore):
        async def upload_image(self, *_args, **_kwargs):  # type: ignore[override]
            raise RuntimeError("S3 offline")

    repo = _StubRepo()
    store = FailingStore()
    llm = _StubLLMService()

    async def unexpected_extract(*_args, **_kwargs):  # type: ignore[override]
        raise AssertionError("Should not run if upload fails")

    monkeypatch.setattr(
        "modules.resource.service.facade.extract_text_from_photo",
        unexpected_extract,
    )

    service = ResourceService(repo=repo, object_store=store, llm_services=llm)
    payload = PhotoResourceCreate(
        user_id=3,
        filename="fail.png",
        content_type="image/png",
        content=b"binary",
        file_size=512,
    )

    with pytest.raises(ResourceExtractionError) as exc:
        await service.upload_photo_resource(payload)

    assert "store photo" in str(exc.value)
