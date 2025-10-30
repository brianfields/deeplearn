"""Business logic for managing learner-provided resources."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import uuid

from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from modules.llm_services.public import LLMServicesProvider, llm_services_provider
from modules.object_store.public import (
    DocumentCreate,
    ImageCreate,
    ObjectStoreProvider,
    object_store_provider,
)

from ..models import ResourceModel
from ..repo import ResourceRepo
from .dtos import (
    FileResourceCreate,
    PhotoResourceCreate,
    ResourceRead,
    ResourceSummary,
    UrlResourceCreate,
)
from .extractors import (
    ExtractionError,
    extract_text_from_photo,
    extract_text_from_docx,
    extract_text_from_markdown,
    extract_text_from_pdf,
    extract_text_from_pptx,
    extract_text_from_txt,
    extract_youtube_transcript,
    scrape_web_page,
)

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
MAX_EXTRACTED_TEXT_BYTES = 100 * 1024
PREVIEW_CHAR_LIMIT = 200
ALLOWED_IMAGE_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/jpg",
        "image/heic",
        "image/heif",
    }
)
ALLOWED_FILE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".txt",
        ".md",
        ".markdown",
        ".pdf",
        ".docx",
        ".pptx",
    }
)


class ResourceError(Exception):
    """Base exception for resource operations."""


class ResourceValidationError(ResourceError):
    """Raised when a request fails validation."""


class ResourceExtractionError(ResourceError):
    """Raised when extraction fails for a resource."""


@dataclass(slots=True)
class ResourceService:
    """Coordinates storage, extraction, and persistence of learner resources."""

    repo: ResourceRepo
    object_store: ObjectStoreProvider
    llm_services: LLMServicesProvider

    async def upload_file_resource(self, data: FileResourceCreate) -> ResourceRead:
        """Upload a file, extract text, and persist the resource."""

        normalized_name = data.filename.strip()
        if not normalized_name:
            raise ResourceValidationError("Filename is required")

        extension = Path(normalized_name).suffix.lower()
        if extension not in ALLOWED_FILE_EXTENSIONS:
            raise ResourceValidationError(f"Unsupported file type: {extension}")

        file_size = data.file_size or len(data.content)
        self._validate_file_size(file_size)

        extracted_text, extraction_metadata = await self._extract_file_text(
            extension,
            data.content,
            filename=normalized_name,
        )

        truncated_text, truncate_meta = self._truncate_extracted_text(extracted_text)
        extraction_metadata.update(truncate_meta)
        document_result = await self.object_store.upload_document(
            DocumentCreate(
                user_id=data.user_id,
                filename=normalized_name,
                content_type=data.content_type,
                content=data.content,
            ),
            generate_presigned_url=False,
        )

        resource = await self.repo.create(
            user_id=data.user_id,
            resource_type="file_upload",
            filename=normalized_name,
            source_url=None,
            extracted_text=truncated_text,
            extraction_metadata=extraction_metadata,
            file_size=file_size,
            object_store_document_id=document_result.document.id,
            object_store_image_id=None,
        )
        return ResourceRead.model_validate(resource)

    async def create_url_resource(self, data: UrlResourceCreate) -> ResourceRead:
        """Create a resource from a URL by fetching or delegating extraction."""

        parsed = urlparse(str(data.url))
        if parsed.scheme not in {"http", "https"}:
            raise ResourceValidationError("Only HTTP and HTTPS URLs are supported")

        try:
            extractor_result = self._extract_text_for_url(parsed.geturl())
        except NotImplementedError as exc:
            raise ResourceExtractionError(str(exc)) from exc

        truncated_text, truncate_meta = self._truncate_extracted_text(extractor_result.text)
        metadata = extractor_result.metadata
        metadata.update(truncate_meta)

        resource = await self.repo.create(
            user_id=data.user_id,
            resource_type="url",
            filename=None,
            source_url=parsed.geturl(),
            extracted_text=truncated_text,
            extraction_metadata=metadata,
            file_size=None,
            object_store_document_id=None,
            object_store_image_id=None,
        )
        return ResourceRead.model_validate(resource)

    async def upload_photo_resource(self, data: PhotoResourceCreate) -> ResourceRead:
        """Upload a learner photo, extract context, and persist the resource."""

        normalized_name = data.filename.strip() or "photo.jpg"
        content_type = data.content_type.lower()
        if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise ResourceValidationError(
                f"Unsupported image type: {data.content_type}"
            )

        file_size = data.file_size or len(data.content)
        self._validate_file_size(file_size)

        try:
            upload_result = await self.object_store.upload_image(
                ImageCreate(
                    user_id=data.user_id,
                    filename=normalized_name,
                    content_type=content_type,
                    content=data.content,
                ),
                generate_presigned_url=True,
                presigned_ttl_seconds=900,
            )
        except Exception as exc:  # pragma: no cover - defensive storage handling
            logger.exception("Failed to upload photo to object store")
            raise ResourceExtractionError("Failed to store photo") from exc

        if upload_result.presigned_url is None:
            raise ResourceExtractionError("Failed to generate image URL for analysis")

        try:
            extracted_text, extraction_metadata = await extract_text_from_photo(
                upload_result.presigned_url,
                self.llm_services,
            )
        except ExtractionError as exc:
            raise ResourceExtractionError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - unexpected errors
            logger.exception("Unexpected error during photo analysis")
            raise ResourceExtractionError("Failed to analyse the photo") from exc

        extraction_metadata.update(
            {
                "filename": normalized_name,
                "file_size": file_size,
                "image_id": str(upload_result.file.id),
            }
        )

        truncated_text, truncate_meta = self._truncate_extracted_text(extracted_text)
        extraction_metadata.update(truncate_meta)

        resource = await self.repo.create(
            user_id=data.user_id,
            resource_type="photo",
            filename=normalized_name,
            source_url=None,
            extracted_text=truncated_text,
            extraction_metadata=extraction_metadata,
            file_size=file_size,
            object_store_document_id=None,
            object_store_image_id=upload_result.file.id,
        )
        return ResourceRead.model_validate(resource)

    async def get_resource(self, resource_id: uuid.UUID) -> ResourceRead | None:
        """Retrieve a single resource."""

        record = await self.repo.get_by_id(resource_id)
        if record is None:
            return None
        return ResourceRead.model_validate(record)

    async def list_user_resources(self, user_id: int) -> list[ResourceSummary]:
        """List resources for a learner ordered by recency."""

        records = await self.repo.list_by_user(user_id)
        return [self._build_summary(record) for record in records]

    async def get_resources_for_unit(self, unit_id: str) -> list[ResourceSummary]:
        """Return resources linked to a specific unit."""

        records = await self.repo.get_by_unit(unit_id)
        return [self._build_summary(record) for record in records]

    async def attach_resources_to_unit(self, *, unit_id: str, resource_ids: list[uuid.UUID]) -> None:
        """Link resources to a unit for later retrieval."""

        await self.repo.link_resources_to_unit(unit_id=unit_id, resource_ids=resource_ids)

    def _extract_text_for_url(self, url: str) -> _ExtractionResult:
        hostname = urlparse(url).hostname or ""
        lowered_host = hostname.lower()
        metadata: dict[str, Any] = {"source": "url"}

        try:
            if "youtube.com" in lowered_host or "youtu.be" in lowered_host:
                text = extract_youtube_transcript(url)
                metadata["content_type"] = "youtube"
            elif any(url.lower().endswith(ext) for ext in (".pdf", ".docx", ".pptx")):
                raise NotImplementedError("Direct document links coming soon. Please download and upload the file.")
            else:
                text = scrape_web_page(url)
                metadata["content_type"] = "web_page"
        except NotImplementedError:
            raise
        except Exception as exc:  # pragma: no cover - defensive network handling
            raise ResourceExtractionError("Failed to fetch URL content") from exc
        return _ExtractionResult(text=text, metadata=metadata)

    async def _extract_file_text(self, extension: str, content: bytes, *, filename: str) -> tuple[str, dict[str, Any]]:
        metadata: dict[str, Any] = {
            "source": "file_upload",
            "filename": filename,
        }
        try:
            if extension in {".txt"}:
                text = extract_text_from_txt(content)
                metadata["content_type"] = "text/plain"
            elif extension in {".md", ".markdown"}:
                text = extract_text_from_markdown(content)
                metadata["content_type"] = "text/markdown"
            elif extension == ".pdf":
                reader = PdfReader(BytesIO(content))
                total_pages = len(reader.pages)
                selected_pages = self._prompt_for_page_selection(total_pages)
                metadata["pages_extracted"] = [page + 1 for page in selected_pages]
                metadata["total_pages"] = total_pages
                text = extract_text_from_pdf(content, pages=selected_pages)
                if total_pages > len(selected_pages):
                    metadata["page_selection_mode"] = "auto_first_5"
            elif extension == ".docx":
                text = extract_text_from_docx(content)
            elif extension == ".pptx":
                text = extract_text_from_pptx(content)
            else:  # pragma: no cover - should not be reachable due to earlier validation
                raise ResourceValidationError(f"Unsupported file extension: {extension}")
        except ExtractionError as exc:
            raise ResourceExtractionError(str(exc)) from exc
        except NotImplementedError as exc:
            raise ResourceExtractionError(str(exc)) from exc
        return text, metadata

    def _truncate_extracted_text(self, text: str) -> tuple[str, dict[str, Any]]:
        encoded = text.encode("utf-8")
        if len(encoded) <= MAX_EXTRACTED_TEXT_BYTES:
            return text, {"truncated": False, "original_size": len(encoded)}
        truncated_bytes = encoded[:MAX_EXTRACTED_TEXT_BYTES]
        truncated_text = truncated_bytes.decode("utf-8", errors="ignore")
        return truncated_text, {
            "truncated": True,
            "original_size": len(encoded),
            "truncated_size": len(truncated_bytes),
        }

    @staticmethod
    def _prompt_for_page_selection(total_pages: int) -> list[int]:
        if total_pages <= 5:
            return list(range(total_pages))
        logger.info("PDF exceeds 5 pages; automatically selecting first 5 pages")
        return list(range(min(5, total_pages)))

    @staticmethod
    def _validate_file_size(file_size: int) -> None:
        if file_size > MAX_FILE_SIZE_BYTES:
            raise ResourceValidationError("File exceeds maximum size of 100MB")

    def _build_summary(self, record: ResourceModel) -> ResourceSummary:
        preview = record.extracted_text[:PREVIEW_CHAR_LIMIT]
        return ResourceSummary(
            id=record.id,
            resource_type=record.resource_type,
            filename=record.filename,
            source_url=record.source_url,
            file_size=record.file_size,
            created_at=record.created_at,
            preview_text=preview,
        )


@dataclass(slots=True)
class _ExtractionResult:
    text: str
    metadata: dict[str, Any]


async def resource_service_factory(session: AsyncSession) -> ResourceService:
    """Factory used by routes to construct the resource service."""

    return ResourceService(
        repo=ResourceRepo(session),
        object_store=object_store_provider(session),
        llm_services=llm_services_provider(),
    )


__all__ = [
    "ResourceError",
    "ResourceExtractionError",
    "ResourceService",
    "ResourceValidationError",
    "resource_service_factory",
]
