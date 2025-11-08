"""Protocol definition and dependency injection provider."""

import logging
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from modules.content.public import ContentProvider, UnitRead, content_provider
from modules.infrastructure.public import infrastructure_provider
from modules.task_queue.public import register_task_handler

from .service import ContentCreatorService


class ContentCreatorProvider(Protocol):
    """Protocol defining the content creator module's public async interface (coach-driven only)."""

    async def create_unit(
        self,
        *,
        learner_desires: str,
        learning_objectives: list,
        unit_title: str | None = None,
        target_lesson_count: int | None = None,
        conversation_id: str | None = None,
        source_material: str | None = None,
        background: bool = False,
        user_id: int | None = None,
    ) -> ContentCreatorService.UnitCreationResult | ContentCreatorService.MobileUnitCreationResult: ...
    async def create_unit_art(self, unit_id: str) -> UnitRead: ...


def content_creator_provider(session: AsyncSession) -> ContentCreatorProvider:
    """Build the content creator service for the given async session."""

    content: ContentProvider = content_provider(session)
    return ContentCreatorService(content)


# -----------------------------
# Task registration (called on import)
# -----------------------------

logger = logging.getLogger(__name__)


async def _handle_unit_creation(payload: dict) -> None:
    """ARQ handler: execute coach-driven unit creation end-to-end."""

    infra = infrastructure_provider()
    infra.initialize()
    inputs = payload.get("inputs") or {}
    unit_id = str(payload.get("unit_id") or inputs.get("unit_id") or "")
    arq_task_id = str(payload.get("task_id") or inputs.get("task_id") or "") or None

    # Coach-driven mode only (required fields)
    learner_desires = inputs.get("learner_desires")
    learning_objectives = inputs.get("learning_objectives")
    source_material = inputs.get("source_material")
    target_lesson_count = inputs.get("target_lesson_count")

    if not learner_desires or not learning_objectives:
        raise ValueError(f"Coach-driven unit creation requires learner_desires and learning_objectives. Got: learner_desires={learner_desires}, learning_objectives={learning_objectives}")

    # Use a fresh DB session for the whole operation
    try:
        async with infra.get_async_session_context() as session:
            svc = content_creator_provider(session)
            await svc._flow_handler.execute_unit_creation_pipeline(
                unit_id=unit_id,
                learner_desires=learner_desires,
                learning_objectives=learning_objectives,
                source_material=source_material,
                target_lesson_count=target_lesson_count,
                arq_task_id=arq_task_id,
            )
    except Exception as e:
        # Mark unit as failed if creation pipeline throws an exception
        logger.error("❌ Unit creation failed for unit %s: %s", unit_id, str(e), exc_info=True)
        try:
            async with infra.get_async_session_context() as session:
                content = content_provider(session)
                await content.update_unit_status(
                    unit_id=unit_id,
                    status="failed",
                    error_message=f"Unit creation failed: {e!s}",
                    creation_progress={"stage": "failed", "message": "Creation failed"},
                )
        except Exception as status_error:
            logger.error("❌ Failed to update unit status to failed: %s", str(status_error))
        # Re-raise so the task system marks the task as failed
        raise


# Register on import
try:
    register_task_handler("content_creator.unit_creation", _handle_unit_creation)
    logger.debug("Registered content_creator.unit_creation handler")
except Exception:  # pragma: no cover
    logger.exception("Failed to register content_creator.unit_creation handler")


__all__ = [
    "ContentCreatorProvider",
    "content_creator_provider",
]
