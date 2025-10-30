"""Unit tests for resource text extraction helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
import uuid

from pypdf import PdfWriter
import pytest

from .service.extractors import (
    extract_text_from_markdown,
    extract_text_from_pdf,
    extract_text_from_txt,
)
from .service.facade import ResourceService


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

    service = ResourceService(repo=repo, object_store=MagicMock())

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
