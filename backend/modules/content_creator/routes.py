"""
Content Creator Module - HTTP Routes

HTTP API for AI-powered content creation.
Only includes routes actually used by the Content Creation Studio.
"""

from fastapi import APIRouter, Depends, HTTPException

from .public import ContentCreatorProvider, content_creator_provider
from .service import CreateTopicRequest, TopicCreationResult

router = APIRouter(prefix="/api/content-creator", tags=["content-creator"])


@router.post("/topics", response_model=TopicCreationResult)
async def create_topic(request: CreateTopicRequest, creator: ContentCreatorProvider = Depends(content_creator_provider)) -> TopicCreationResult:
    """
    Create topic with AI-generated content from source material.

    Used by the Content Creation Studio to create complete topics
    with didactic snippets, glossaries, and MCQs.
    """
    try:
        return await creator.create_topic_from_source_material(request)
    except Exception as e:
        raise HTTPException(500, f"Failed to create topic: {e!s}")


# Note: Additional component creation endpoints will be added only when
# the Content Creation Studio frontend actually needs them
