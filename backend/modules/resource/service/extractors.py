"""Text extraction helpers for supported resource types."""

from __future__ import annotations

from collections.abc import Iterable
from io import BytesIO
from urllib.parse import parse_qs, urlparse
import re
from zipfile import BadZipFile, ZipFile

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)


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


def extract_text_from_docx(content: bytes) -> str:
    """Extract text content from a DOCX document."""

    try:
        with ZipFile(BytesIO(content)) as archive:
            try:
                document_xml = archive.read("word/document.xml")
            except KeyError as exc:
                raise ExtractionError("DOCX file is missing document.xml") from exc
    except BadZipFile as exc:  # pragma: no cover - corrupted files
        raise ExtractionError("Invalid DOCX file") from exc

    try:
        root = ET.fromstring(document_xml)
    except (ET.ParseError, DefusedXmlException) as exc:  # pragma: no cover - malformed XML
        raise ExtractionError("Failed to parse DOCX XML content") from exc

    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{namespace}p"):
        texts = [node.text or "" for node in paragraph.iter(f"{namespace}t")]
        paragraph_text = "".join(texts)
        if paragraph_text.strip():
            paragraphs.append(paragraph_text.strip())

    if not paragraphs:
        raise ExtractionError("No text content found in the document")

    return "\n".join(paragraphs)


def extract_text_from_pptx(content: bytes) -> str:
    """Extract text content from a PPTX presentation."""

    slide_pattern = re.compile(r"ppt/slides/slide(\d+)\.xml")
    slides: list[str] = []

    try:
        with ZipFile(BytesIO(content)) as archive:
            slide_entries = [
                (int(match.group(1)), name)
                for name in archive.namelist()
                if (match := slide_pattern.fullmatch(name))
            ]

            if not slide_entries:
                raise ExtractionError("No slides found in the presentation")

            sorted_entries = sorted(slide_entries, key=lambda item: item[0])

            for _index, name in sorted_entries:
                try:
                    slide_xml = archive.read(name)
                except KeyError as exc:  # pragma: no cover - inconsistent archive
                    raise ExtractionError(f"Missing slide content: {name}") from exc

                try:
                    root = ET.fromstring(slide_xml)
                except (ET.ParseError, DefusedXmlException) as exc:  # pragma: no cover - malformed XML
                    raise ExtractionError(f"Failed to parse slide XML: {name}") from exc

                namespace = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
                texts = [node.text or "" for node in root.iter(f"{namespace}t")]
                slide_text = "\n".join(part for part in texts if part)
                if slide_text.strip():
                    slides.append(slide_text.strip())

    except BadZipFile as exc:  # pragma: no cover - corrupted files
        raise ExtractionError("Invalid PPTX file") from exc

    if not slides:
        raise ExtractionError("No text content found in the presentation")

    return "\n\n".join(slides)


def extract_youtube_transcript(url: str) -> str:
    """Fetch the transcript text for a YouTube video."""

    video_id = _parse_youtube_video_id(url)
    if video_id is None:
        raise ExtractionError("Could not determine YouTube video ID from URL")

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except TranscriptsDisabled as exc:
        raise ExtractionError("Transcripts are disabled for this YouTube video") from exc
    except NoTranscriptFound as exc:
        raise ExtractionError("No transcript available for this YouTube video") from exc
    except VideoUnavailable as exc:
        raise ExtractionError("YouTube video is unavailable") from exc
    except Exception as exc:  # pragma: no cover - network/library edge cases
        raise ExtractionError("Failed to fetch YouTube transcript") from exc

    lines: list[str] = []
    for entry in transcript:
        text = (entry.get("text") or "").strip()
        if text:
            lines.append(text.replace("\n", " ").strip())

    if not lines:
        raise ExtractionError("Transcript for this YouTube video was empty")

    return "\n".join(lines)


def _parse_youtube_video_id(url: str) -> str | None:
    """Extract the canonical video ID from common YouTube URL formats."""

    parsed = urlparse(url)
    host = parsed.netloc.lower()

    path_segments = [segment for segment in parsed.path.split("/") if segment]

    if host in {"youtu.be", "www.youtu.be"}:
        return path_segments[0] if path_segments else None

    if host.endswith("youtube.com"):
        if parsed.path == "/watch":
            query = parse_qs(parsed.query)
            video_values = query.get("v")
            if video_values:
                return video_values[0]
        if path_segments:
            if path_segments[0] in {"embed", "shorts", "v", "live"} and len(path_segments) >= 2:
                return path_segments[1]
            if len(path_segments) == 1 and 10 <= len(path_segments[0]) <= 20:
                return path_segments[0]

    return None


def scrape_web_page(url: str) -> str:
    """Extract text content from a web page using BeautifulSoup."""
    from bs4 import BeautifulSoup
    import requests

    try:
        # Set a reasonable timeout and user agent
        headers = {"User-Agent": "Mozilla/5.0 (compatible; LearningApp/1.0; +http://example.com/bot)"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script, style, and other non-content elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Extract text from the page
        text = soup.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = "\n".join(lines)

        if not cleaned_text:
            raise ExtractionError("No text content found on the page")

        return cleaned_text

    except requests.exceptions.Timeout as exc:
        raise ExtractionError("Request timed out while fetching the page") from exc
    except requests.exceptions.RequestException as exc:
        raise ExtractionError(f"Failed to fetch page: {exc!s}") from exc
    except Exception as exc:
        raise ExtractionError(f"Failed to parse page content: {exc!s}") from exc
