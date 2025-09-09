"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

import logging
import uuid

from pydantic import BaseModel

from modules.content.public import ComponentCreate, ContentProvider, TopicCreate

from .flows import TopicCreationFlow

logger = logging.getLogger(__name__)


# DTOs
class CreateTopicRequest(BaseModel):
    """Request to create a topic from source material."""

    title: str
    core_concept: str
    source_material: str
    user_level: str = "intermediate"
    domain: str = "General"


# CreateComponentRequest removed - generate_component method is unused


class TopicCreationResult(BaseModel):
    """Result of topic creation with component count."""

    topic_id: str
    title: str
    components_created: int


class ContentCreatorService:
    """Service for AI-powered content creation."""

    def __init__(self, content: ContentProvider):
        """Initialize with content storage only - flows handle LLM interactions."""
        self.content = content

    async def create_topic_from_source_material(self, request: CreateTopicRequest) -> TopicCreationResult:
        """
        Create a complete topic with AI-generated content from source material.

        This method:
        1. Uses LLM to extract structured content from source material
        2. Creates the topic in the content module
        3. Generates and saves components (didactic snippet, glossary, MCQs)
        4. Returns summary of what was created
        """
        topic_id = str(uuid.uuid4())
        logger.info(f"🎯 Creating topic: {request.title} (ID: {topic_id})")

        # Use flow engine for content extraction
        logger.info("🔄 Starting TopicCreationFlow...")
        flow = TopicCreationFlow()
        flow_result = await flow.execute({"title": request.title, "core_concept": request.core_concept, "source_material": request.source_material, "user_level": request.user_level, "domain": request.domain})
        logger.info("✅ TopicCreationFlow completed successfully")

        # Save topic to content module
        topic_data = TopicCreate(
            id=topic_id,
            title=request.title,
            core_concept=request.core_concept,
            user_level=request.user_level,
            learning_objectives=flow_result["learning_objectives"],
            key_concepts=flow_result["key_concepts"],
            source_material=request.source_material,
            source_domain=request.domain,
            source_level=request.user_level,
            refined_material=flow_result.get("refined_material", {}),
        )

        logger.info("💾 Saving topic to database...")
        saved_topic = self.content.save_topic(topic_data)

        # Generate and save components
        components_created = 0
        logger.info("🧩 Creating components...")

        # Create didactic snippet
        if "didactic_snippet" in flow_result:
            logger.debug("Creating didactic snippet component")
            component_data = ComponentCreate(id=str(uuid.uuid4()), topic_id=topic_id, component_type="didactic_snippet", title=f"Overview: {request.title}", content=flow_result["didactic_snippet"])
            self.content.save_component(component_data)
            components_created += 1

        # Create glossary
        if "glossary" in flow_result:
            logger.debug("Creating glossary component")
            component_data = ComponentCreate(id=str(uuid.uuid4()), topic_id=topic_id, component_type="glossary", title=f"Glossary: {request.title}", content=flow_result["glossary"])
            self.content.save_component(component_data)
            components_created += 1

        # Create MCQs
        mcqs = flow_result.get("mcqs", [])
        logger.debug(f"Creating {len(mcqs)} MCQ components")
        for i, mcq in enumerate(mcqs):
            component_data = ComponentCreate(id=str(uuid.uuid4()), topic_id=topic_id, component_type="mcq", title=f"Question {i + 1}: {mcq.get('question', 'MCQ')}", content=mcq)
            self.content.save_component(component_data)
            components_created += 1

        logger.info(f"🎉 Topic creation completed! Created {components_created} components")
        return TopicCreationResult(topic_id=topic_id, title=request.title, components_created=components_created)

    # generate_component method removed - it was unused (no HTTP routes or other code calls it)

    # All LLM-related methods removed - now handled by TopicCreationFlow
