"""
Content Creator Module - HTTP Routes

HTTP API for AI-powered content creation.
Only includes routes actually used by the Content Creation Studio.
"""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modules.content.public import content_provider
from modules.infrastructure.public import infrastructure_provider

from .service import ContentCreatorService, CreateTopicRequest, TopicCreationResult

router = APIRouter(prefix="/api/v1/content-creator")


def get_session() -> Generator[Session, None, None]:
    """Request-scoped database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as s:
        yield s


def get_content_creator_service(s: Session = Depends(get_session)) -> ContentCreatorService:
    """Build ContentCreatorService for this request."""
    content_service = content_provider(s)
    return ContentCreatorService(content_service)


@router.post("/topics", response_model=TopicCreationResult)
async def create_topic(request: CreateTopicRequest, creator: ContentCreatorService = Depends(get_content_creator_service)) -> TopicCreationResult:
    """
    Create topic with AI-generated content from source material.

    Used by the Content Creation Studio to create complete topics
    with didactic snippets, glossaries, and MCQs.
    """
    try:
        return await creator.create_topic_from_source_material(request)
    except Exception as e:
        raise HTTPException(500, f"Failed to create topic: {e!s}") from e


# Note: Additional component creation endpoints will be added only when
# the Content Creation Studio frontend actually needs them
