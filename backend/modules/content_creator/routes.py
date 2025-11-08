from __future__ import annotations

from collections.abc import AsyncGenerator
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from modules.content.public import ContentProvider, UnitStatus, content_provider
from modules.infrastructure.public import infrastructure_provider
from modules.resource.public import ResourceProvider, resource_provider

from .service import ContentCreatorService
from .steps import UnitLearningObjective

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/content-creator", tags=["content-creator"])


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Request-scoped async database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()
    async with infra.get_async_session_context() as session:
        yield session


async def get_content_creator_service(session: AsyncSession = Depends(get_async_session)) -> ContentCreatorService:
    """Build ContentCreatorService for this request."""
    content: ContentProvider = content_provider(session)

    async def _resource_factory() -> ResourceProvider:
        return await resource_provider(session)

    return ContentCreatorService(content, resource_factory=_resource_factory)


# DTOs for mobile unit creation
class MobileUnitCreateRequest(BaseModel):
    """Request to create a unit from mobile app via learning coach.

    All fields are required because the coach conversation finalizes them
    before allowing unit creation.
    """

    learner_desires: str
    unit_title: str
    learning_objectives: list[UnitLearningObjective]
    target_lesson_count: int
    conversation_id: str
    owner_user_id: int | None = None


class MobileUnitCreateResponse(BaseModel):
    """Response from mobile unit creation."""

    unit_id: str
    status: str  # Will be "in_progress" initially
    title: str


@router.post("/units", response_model=MobileUnitCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_unit_from_mobile(
    request: MobileUnitCreateRequest,
    user_id: int | None = Query(None, ge=1, description="Authenticated user identifier"),
    service: ContentCreatorService = Depends(get_content_creator_service),
) -> MobileUnitCreateResponse:
    """Create a unit from learning coach conversation.

    Unit creation happens in the background and returns immediately with in_progress status.
    The client should poll the units endpoint to check for completion.
    """
    try:
        logger.info("🔥 Mobile unit creation request from coach: conversation_id='%s', title='%s'", request.conversation_id, request.unit_title)

        result = await service.create_unit(
            learner_desires=request.learner_desires,
            unit_title=request.unit_title,
            learning_objectives=request.learning_objectives,
            target_lesson_count=request.target_lesson_count,
            conversation_id=request.conversation_id,
            background=True,
            user_id=user_id or request.owner_user_id,
        )

        logger.info("✅ Mobile unit creation started: unit_id=%s", result.unit_id)

        return MobileUnitCreateResponse(unit_id=result.unit_id, status=UnitStatus.IN_PROGRESS.value, title=result.title)

    except ValueError as exc:
        logger.error("❌ Invalid request for mobile unit creation: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("❌ Unexpected error in mobile unit creation: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create unit") from exc


@router.post("/units/{unit_id}/retry", response_model=MobileUnitCreateResponse)
async def retry_unit_creation(
    unit_id: str,
    service: ContentCreatorService = Depends(get_content_creator_service),
) -> MobileUnitCreateResponse:
    """
    Retry failed unit creation.

    This will reset the unit to in_progress status and restart the background creation process.
    """
    try:
        logger.info("🔄 Retrying unit creation: unit_id=%s", unit_id)

        result = await service.retry_unit_creation(unit_id)

        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

        logger.info("✅ Unit retry started: unit_id=%s", unit_id)

        return MobileUnitCreateResponse(unit_id=result.unit_id, status=result.status, title=result.title)

    except ValueError as exc:
        logger.error("❌ Invalid unit retry request: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("❌ Unexpected error in unit retry: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retry unit creation") from exc


@router.delete("/units/{unit_id}")
async def dismiss_unit(
    unit_id: str,
    service: ContentCreatorService = Depends(get_content_creator_service),
) -> dict[str, str]:
    """
    Dismiss (delete) a failed unit.

    This will permanently remove the unit from the database.
    """
    try:
        logger.info("🗑️ Dismissing unit: unit_id=%s", unit_id)

        success = await service.dismiss_unit(unit_id)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

        logger.info("✅ Unit dismissed: unit_id=%s", unit_id)

        return {"message": "Unit dismissed successfully"}

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("❌ Unexpected error in unit dismissal: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to dismiss unit") from exc


@router.post("/units/check-timeouts")
async def check_unit_timeouts(
    timeout_seconds: int = Query(3600, ge=60, le=86400, description="Timeout threshold in seconds (default: 1 hour)"),
    service: ContentCreatorService = Depends(get_content_creator_service),
) -> dict[str, int]:
    """
    Check for stale units stuck in 'in_progress' status and mark them as failed.

    This endpoint checks all in_progress units and marks them as failed if:
    - Their associated task has failed
    - They have been in_progress for longer than the timeout threshold

    This can be called periodically by clients or by a background job.
    """
    try:
        logger.info("🔍 Checking for stale units (timeout: %s seconds)", timeout_seconds)

        timed_out_count = await service.check_and_timeout_stale_units(timeout_seconds)

        logger.info("✅ Timeout check completed: %s units marked as failed", timed_out_count)

        return {"timed_out_count": timed_out_count}

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("❌ Unexpected error checking unit timeouts: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to check unit timeouts") from exc
