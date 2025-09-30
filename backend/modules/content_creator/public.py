"""Protocol definition and dependency injection provider."""

import logging
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from modules.content.public import ContentProvider, content_provider
from modules.infrastructure.public import infrastructure_provider
from modules.task_queue.public import register_task_handler

from .service import ContentCreatorService, CreateLessonRequest, LessonCreationResult


class ContentCreatorProvider(Protocol):
    """Protocol defining the content creator module's public async interface."""

    async def create_unit(
        self,
        *,
        topic: str,
        source_material: str | None = None,
        background: bool = False,
        target_lesson_count: int | None = None,
        learner_level: str = "beginner",
    ) -> ContentCreatorService.UnitCreationResult | ContentCreatorService.MobileUnitCreationResult:
        ...


def content_creator_provider(session: AsyncSession) -> ContentCreatorProvider:
    """Build the content creator service for the given async session."""

    content: ContentProvider = content_provider(session)
    return ContentCreatorService(content)


# -----------------------------
# Task registration (called on import)
# -----------------------------

logger = logging.getLogger(__name__)


async def _handle_unit_creation(payload: dict) -> None:
    """ARQ handler: execute unit creation end-to-end in content_creator."""

    infra = infrastructure_provider()
    infra.initialize()
    inputs = payload.get("inputs") or {}
    unit_id = str(payload.get("unit_id") or inputs.get("unit_id") or "")
    topic = str(payload.get("topic") or inputs.get("topic") or "")
    source_material = inputs.get("source_material")
    learner_level = str(payload.get("learner_level") or inputs.get("learner_level") or "beginner")
    target = (
        payload.get("target_lesson_count")
        if payload.get("target_lesson_count") is not None
        else inputs.get("target_lesson_count")
    )

    # Use a fresh DB session for the whole operation
    async with infra.get_async_session_context() as session:
        svc = content_creator_provider(session)
        await svc._execute_unit_creation_pipeline(  # type: ignore[attr-defined]
            unit_id=unit_id,
            topic=topic,
            source_material=source_material,
            target_lesson_count=target,
            learner_level=learner_level,
        )


# Register on import
try:
    register_task_handler("content_creator.unit_creation", _handle_unit_creation)
    logger.debug("Registered content_creator.unit_creation handler")
except Exception:  # pragma: no cover
    logger.exception("Failed to register content_creator.unit_creation handler")


__all__ = [
    "ContentCreatorProvider",
    "CreateLessonRequest",
    "LessonCreationResult",
    "content_creator_provider",
]
