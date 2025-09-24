"""
Content Creator Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

import logging
from typing import Protocol

from modules.content.public import ContentProvider
from modules.infrastructure.public import infrastructure_provider
from modules.task_queue.public import register_task_handler

from .service import ContentCreatorService, CreateLessonRequest, LessonCreationResult


class ContentCreatorProvider(Protocol):
    """Protocol defining the content creator module's public interface."""

    # Unified unit creation API
    async def create_unit(
        self,
        *,
        topic: str,
        source_material: str | None = None,
        background: bool = False,
        target_lesson_count: int | None = None,
        user_level: str = "beginner",
        domain: str | None = None,
    ) -> ContentCreatorService.UnitCreationResult | ContentCreatorService.MobileUnitCreationResult: ...

    # generate_component method removed - it was unused


def content_creator_provider(content: ContentProvider) -> ContentCreatorProvider:
    """
    Dependency injection provider for content creator services.
    No longer needs LLM services - flows handle LLM interactions internally.

    Args:
        content: Content service instance (built with same session as caller).

    Returns:
        ContentCreatorService instance that implements the ContentCreatorProvider protocol.
    """
    return ContentCreatorService(content)


# -----------------------------
# Task registration (called on import)
# -----------------------------

logger = logging.getLogger(__name__)


async def _handle_unit_creation(payload: dict) -> None:
    """ARQ handler: execute unit creation end-to-end in content_creator.

    Expects payload to include: unit_id, topic, (optional) source_material, user_level, target_lesson_count, domain.
    """
    infra = infrastructure_provider()
    infra.initialize()
    inputs = payload.get("inputs") or {}
    unit_id = str(payload.get("unit_id") or inputs.get("unit_id") or "")
    topic = str(payload.get("topic") or inputs.get("topic") or "")
    source_material = inputs.get("source_material")
    user_level = str(payload.get("user_level") or inputs.get("user_level") or "beginner")
    target = payload.get("target_lesson_count") if payload.get("target_lesson_count") is not None else inputs.get("target_lesson_count")
    domain = inputs.get("domain")

    from modules.content.public import content_provider

    from .service import ContentCreatorService  # local import

    # Use a fresh DB session for the whole operation
    with infra.get_session_context() as s:
        content = content_provider(s)
        svc = ContentCreatorService(content)
        # Run the unified pipeline in the background with provided unit_id
        await svc._execute_unit_creation_pipeline(
            unit_id=unit_id,
            topic=topic,
            source_material=source_material,
            target_lesson_count=target,
            user_level=user_level,
            domain=domain,
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
    # registry side-effects are internal; no need to export handler
]
