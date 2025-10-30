"""Text extraction helpers for supported resource types."""

from __future__ import annotations

from collections.abc import Iterable
from io import BytesIO
import json
import logging
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from modules.llm_services.public import LLMMessage, LLMServicesProvider


class ExtractionError(Exception):
    """Raised when text cannot be extracted from a resource."""


logger = logging.getLogger(__name__)

VISION_ANALYSIS_PROMPT = (
    "You are assisting a learning coach by analyzing learner-provided study photos. "
    "Return a JSON object with two keys: 'description' summarizing the educationally "
    "relevant details in 2-3 sentences, and 'visible_text' containing any clearly "
    "readable text exactly as it appears (use an empty string if none)."
)


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


async def extract_text_from_photo(image_url: str, llm_service: LLMServicesProvider) -> tuple[str, dict[str, Any]]:
    """Use a vision-capable LLM to analyse a learner photo."""

    messages = [
        LLMMessage(role="system", content=VISION_ANALYSIS_PROMPT),
        LLMMessage(
            role="user",
            content=[
                {
                    "type": "text",
                    "text": ("Analyze this study photo, describe the important academic context, and transcribe any text that would help a tutor understand the material."),
                },
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        ),
    ]

    try:
        response, request_id = await llm_service.generate_response(messages, model="gpt-4o-mini")
    except Exception as exc:  # pragma: no cover - defensive against provider failures
        logger.exception("Vision extraction failed to reach LLM")
        raise ExtractionError("Failed to analyse the photo") from exc

    try:
        payload = json.loads(response.content)
    except json.JSONDecodeError as exc:
        logger.error("Vision model returned non-JSON payload: %s", response.content[:200])
        raise ExtractionError("Vision model returned an unexpected response format") from exc

    description = str(payload.get("description", "")).strip()
    visible_text = str(payload.get("visible_text", "")).strip()

    combined_text = description
    if visible_text:
        combined_text = f"{combined_text}\n\nVisible text:\n{visible_text}" if combined_text else f"Visible text:\n{visible_text}"

    if not combined_text:
        combined_text = "Photo contained no describable or legible content."

    metadata: dict[str, Any] = {
        "source": "photo",
        "vision_model": response.model,
        "llm_request_id": str(request_id),
        "description": description,
        "visible_text": visible_text,
        "raw_response": payload,
    }

    return combined_text, metadata


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
