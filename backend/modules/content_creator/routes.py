"""
Content Creator Module - Mobile API Routes

FastAPI routes for mobile unit creation functionality.
Provides endpoints for creating units from mobile app.
"""

from collections.abc import Generator
import logging
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from modules.content.public import content_provider
from modules.content.service import ContentService, UnitStatus
from modules.infrastructure.public import infrastructure_provider

from .service import ContentCreatorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/content-creator", tags=["content-creator"])


def get_session() -> Generator[Session, None, None]:
    """Request-scoped database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as s:
        yield s


def get_content_creator_service(s: Session = Depends(get_session)) -> ContentCreatorService:
    """Build ContentCreatorService for this request."""
    content = cast(ContentService, content_provider(s))
    object_store = getattr(content, "_object_store", None)
    return ContentCreatorService(content, object_store=object_store)


# DTOs for mobile unit creation
class MobileUnitCreateRequest(BaseModel):
    """Request to create a unit from mobile app."""

    topic: str
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    target_lesson_count: int | None = None


class MobileUnitCreateResponse(BaseModel):
    """Response from mobile unit creation."""

    unit_id: str
    status: str  # Will be "in_progress" initially
    title: str


@router.post("/units", response_model=MobileUnitCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_unit_from_mobile(request: MobileUnitCreateRequest, service: ContentCreatorService = Depends(get_content_creator_service)) -> MobileUnitCreateResponse:
    """
    Create a unit from mobile app with topic and difficulty.

    Unit creation happens in the background and returns immediately with in_progress status.
    The client should poll the units endpoint to check for completion.
    """
    try:
        logger.info(f"🔥 Mobile unit creation request: topic='{request.topic}', difficulty='{request.difficulty}'")

        result = await service.create_unit(topic=request.topic, learner_level=request.difficulty, target_lesson_count=request.target_lesson_count, background=True)

        logger.info(f"✅ Mobile unit creation started: unit_id={result.unit_id}")

        return MobileUnitCreateResponse(unit_id=result.unit_id, status=UnitStatus.IN_PROGRESS.value, title=result.title)

    except ValueError as e:
        logger.error(f"❌ Invalid request for mobile unit creation: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    except Exception as e:
        logger.error(f"❌ Unexpected error in mobile unit creation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create unit") from e


@router.post("/units/{unit_id}/retry", response_model=MobileUnitCreateResponse)
async def retry_unit_creation(unit_id: str, service: ContentCreatorService = Depends(get_content_creator_service)) -> MobileUnitCreateResponse:
    """
    Retry failed unit creation.

    This will reset the unit to in_progress status and restart the background creation process.
    """
    try:
        logger.info(f"🔄 Retrying unit creation: unit_id={unit_id}")

        result = await service.retry_unit_creation(unit_id)

        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

        logger.info(f"✅ Unit retry started: unit_id={unit_id}")

        return MobileUnitCreateResponse(unit_id=result.unit_id, status=result.status, title=result.title)

    except ValueError as e:
        logger.error(f"❌ Invalid unit retry request: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    except Exception as e:
        logger.error(f"❌ Unexpected error in unit retry: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retry unit creation") from e


@router.delete("/units/{unit_id}")
def dismiss_unit(unit_id: str, service: ContentCreatorService = Depends(get_content_creator_service)) -> dict[str, str]:
    """
    Dismiss (delete) a failed unit.

    This will permanently remove the unit from the database.
    """
    try:
        logger.info(f"🗑️ Dismissing unit: unit_id={unit_id}")

        success = service.dismiss_unit(unit_id)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

        logger.info(f"✅ Unit dismissed: unit_id={unit_id}")

        return {"message": "Unit dismissed successfully"}

    except Exception as e:
        logger.error(f"❌ Unexpected error in unit dismissal: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to dismiss unit") from e
