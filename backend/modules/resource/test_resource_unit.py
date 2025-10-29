"""Unit tests for resource text extraction helpers."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfWriter

from .service.extractors import (
    extract_text_from_markdown,
    extract_text_from_pdf,
    extract_text_from_txt,
)


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
