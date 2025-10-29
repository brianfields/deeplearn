"""Text extraction helpers for supported resource types."""

from __future__ import annotations

from collections.abc import Iterable
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class ExtractionError(Exception):
    """Raised when text cannot be extracted from a resource."""


def extract_text_from_txt(content: bytes) -> str:
    """Decode UTF-8 plaintext safely."""

    return content.decode("utf-8", errors="replace")


def extract_text_from_markdown(content: bytes) -> str:
    """Decode Markdown files preserving formatting."""

    return content.decode("utf-8", errors="replace")


def extract_text_from_pdf(content: bytes, *, pages: Iterable[int] | None = None) -> str:
    """Extract text from a PDF using a minimal dependency."""

    try:
        reader = PdfReader(BytesIO(content))
    except PdfReadError as exc:  # pragma: no cover - corrupted files
        raise ExtractionError("Failed to read PDF content") from exc

    selected_pages = list(pages) if pages is not None else list(range(len(reader.pages)))
    text_parts: list[str] = []
    for index in selected_pages:
        if index < 0 or index >= len(reader.pages):
            continue
        try:
            page_text = reader.pages[index].extract_text() or ""
        except Exception as exc:  # pragma: no cover - library edge case
            raise ExtractionError(f"Failed to extract text from page {index + 1}") from exc
        text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(_content: bytes) -> str:
    """Placeholder for Word extraction."""

    raise NotImplementedError("Word document parsing coming soon. Please convert to PDF or copy/paste text.")


def extract_text_from_pptx(_content: bytes) -> str:
    """Placeholder for PowerPoint extraction."""

    raise NotImplementedError("PowerPoint parsing coming soon. Please convert to PDF or copy/paste text.")


def extract_youtube_transcript(_url: str) -> str:
    """Placeholder for YouTube transcript extraction."""

    raise NotImplementedError("YouTube transcript extraction coming soon. Please copy/paste the transcript.")


def scrape_web_page(_url: str) -> str:
    """Placeholder for generic web scraping."""

    raise NotImplementedError("Web page extraction coming soon. Please copy/paste the article text.")
