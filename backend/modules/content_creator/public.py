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

    async def create_lesson_from_source_material(self, request: CreateLessonRequest, *, use_fast_flow: bool = False) -> LessonCreationResult: ...

    # Unit creation methods
    async def create_unit_from_topic(self, request: ContentCreatorService.CreateUnitFromTopicRequest) -> ContentCreatorService.UnitCreationResult: ...
    async def create_unit_from_source_material(self, request: ContentCreatorService.CreateUnitFromSourceRequest) -> ContentCreatorService.UnitCreationResult: ...

    # Mobile unit creation
    async def create_unit_from_mobile(self, topic: str, difficulty: str = "beginner", target_lesson_count: int | None = None) -> ContentCreatorService.MobileUnitCreationResult: ...

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

    Expects payload to include: unit_id, topic, difficulty, target_lesson_count.
    """
    infra = infrastructure_provider()
    infra.initialize()
    inputs = payload.get("inputs") or {}
    unit_id = str(payload.get("unit_id") or inputs.get("unit_id") or "")
    topic = str(payload.get("topic") or inputs.get("topic") or "")
    difficulty = str(payload.get("difficulty") or inputs.get("difficulty") or "beginner")
    target = payload.get("target_lesson_count") if payload.get("target_lesson_count") is not None else inputs.get("target_lesson_count")

    from modules.content.public import content_provider  # noqa: PLC0415

    from .service import ContentCreatorService  # local import  # noqa: PLC0415

    # Use a fresh DB session for the whole operation
    with infra.get_session_context() as s:
        content = content_provider(s)
        svc = ContentCreatorService(content)
        # Reuse the background logic that persists lessons and updates statuses
        await svc._execute_background_unit_creation_logic(content, unit_id, topic, difficulty, target)


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
