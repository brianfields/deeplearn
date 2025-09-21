"""
Content Creator Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Protocol

from modules.content.public import ContentProvider

from .service import ContentCreatorService, CreateLessonRequest, LessonCreationResult


class ContentCreatorProvider(Protocol):
    """Protocol defining the content creator module's public interface."""

    async def create_lesson_from_source_material(self, request: CreateLessonRequest, *, use_fast_flow: bool = False) -> LessonCreationResult: ...

    # Unit creation methods
    async def create_unit_from_topic(self, request: ContentCreatorService.CreateUnitFromTopicRequest) -> ContentCreatorService.UnitCreationResult: ...
    async def create_unit_from_source_material(self, request: ContentCreatorService.CreateUnitFromSourceRequest) -> ContentCreatorService.UnitCreationResult: ...

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


__all__ = [
    "ContentCreatorProvider",
    "CreateLessonRequest",
    "LessonCreationResult",
    "content_creator_provider",
]
