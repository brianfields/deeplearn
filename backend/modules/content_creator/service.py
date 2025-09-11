"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

import logging
import uuid

from pydantic import BaseModel

from modules.content.public import ContentProvider, LessonComponentCreate, LessonCreate

from .flows import LessonCreationFlow

logger = logging.getLogger(__name__)


# DTOs
class CreateLessonRequest(BaseModel):
    """Request to create a lesson from source material."""

    title: str
    core_concept: str
    source_material: str
    user_level: str = "intermediate"
    domain: str = "General"


# CreateComponentRequest removed - generate_component method is unused


class LessonCreationResult(BaseModel):
    """Result of lesson creation with component count."""

    lesson_id: str
    title: str
    components_created: int


class ContentCreatorService:
    """Service for AI-powered content creation."""

    def __init__(self, content: ContentProvider) -> None:
        """Initialize with content storage only - flows handle LLM interactions."""
        self.content = content

    def _truncate_title(self, title: str, max_length: int = 255) -> str:
        """
        Truncate title to fit database constraint.

        Args:
            title: The title to truncate
            max_length: Maximum allowed length (default: 255 for database constraint)

        Returns:
            Truncated title with "..." if needed
        """
        if len(title) <= max_length:
            return title

        # Reserve 3 characters for "..."
        truncated = title[: max_length - 3] + "..."
        return truncated

    async def create_lesson_from_source_material(self, request: CreateLessonRequest) -> LessonCreationResult:
        """
        Create a complete lesson with AI-generated content from source material.

        This method:
        1. Uses LLM to extract structured content from source material
        2. Creates the lesson in the content module
        3. Generates and saves components (didactic snippet, glossary, MCQs)
        4. Returns summary of what was created
        """
        lesson_id = str(uuid.uuid4())
        logger.info(f"🎯 Creating lesson: {request.title} (ID: {lesson_id})")

        # Use flow engine for content extraction
        logger.info("🔄 Starting LessonCreationFlow...")
        flow = LessonCreationFlow()
        flow_result = await flow.execute({"title": request.title, "core_concept": request.core_concept, "source_material": request.source_material, "user_level": request.user_level, "domain": request.domain})
        logger.info("✅ LessonCreationFlow completed successfully")

        # Debug: Log the structure of flow result
        logger.debug(f"Flow result keys: {list(flow_result.keys())}")
        if "learning_objectives" in flow_result:
            logger.debug(f"Learning objectives type: {type(flow_result['learning_objectives'])}")
            if flow_result["learning_objectives"]:
                logger.debug(f"First LO type: {type(flow_result['learning_objectives'][0])}")

        # Transform rich structured data to simple DTO format
        # Handle both Pydantic objects and dictionaries
        learning_objectives_simple = []
        for lo in flow_result["learning_objectives"]:
            if hasattr(lo, "text"):
                learning_objectives_simple.append(lo.text)
            elif isinstance(lo, dict) and "text" in lo:
                learning_objectives_simple.append(lo["text"])
            else:
                learning_objectives_simple.append(str(lo))

        key_concepts_simple = []
        for kc in flow_result["key_concepts"]:
            if hasattr(kc, "term"):
                key_concepts_simple.append(kc.term)
            elif isinstance(kc, dict) and "term" in kc:
                key_concepts_simple.append(kc["term"])
            else:
                key_concepts_simple.append(str(kc))

        # Convert refined material to string format
        refined_material_obj = flow_result.get("refined_material", {})
        if hasattr(refined_material_obj, "outline_bullets"):
            refined_material_str = "\n".join(refined_material_obj.outline_bullets)
            if hasattr(refined_material_obj, "evidence_anchors") and refined_material_obj.evidence_anchors:
                refined_material_str += "\n\nEvidence Anchors:\n" + "\n".join(refined_material_obj.evidence_anchors)
        else:
            refined_material_str = str(refined_material_obj) if refined_material_obj else ""

        # Save lesson to content module
        lesson_data = LessonCreate(
            id=lesson_id,
            title=request.title,
            core_concept=request.core_concept,
            user_level=request.user_level,
            learning_objectives=learning_objectives_simple,
            key_concepts=key_concepts_simple,
            source_material=request.source_material,
            source_domain=request.domain,
            source_level=request.user_level,
            refined_material=refined_material_str,
        )

        logger.info("💾 Saving lesson to database...")
        self.content.save_lesson(lesson_data)

        # Generate and save components
        components_created = 0
        logger.info("🧩 Creating components...")

        # Create didactic snippet
        if "didactic_snippet" in flow_result:
            logger.debug("Creating didactic snippet component")
            didactic_title = self._truncate_title(f"Overview: {request.title}")
            component_data = LessonComponentCreate(id=str(uuid.uuid4()), lesson_id=lesson_id, component_type="didactic_snippet", title=didactic_title, content=flow_result["didactic_snippet"])
            self.content.save_lesson_component(component_data)
            components_created += 1

        # Create glossary
        if "glossary" in flow_result:
            logger.debug("Creating glossary component")
            glossary_title = self._truncate_title(f"Glossary: {request.title}")
            component_data = LessonComponentCreate(id=str(uuid.uuid4()), lesson_id=lesson_id, component_type="glossary", title=glossary_title, content=flow_result["glossary"])
            self.content.save_lesson_component(component_data)
            components_created += 1

        # Create MCQs
        mcqs = flow_result.get("mcqs", [])
        logger.debug(f"Creating {len(mcqs)} MCQ components")
        for i, mcq in enumerate(mcqs):
            question_text = mcq.get("question", "MCQ")
            mcq_title = self._truncate_title(f"Question {i + 1}: {question_text}")
            component_data = LessonComponentCreate(id=str(uuid.uuid4()), lesson_id=lesson_id, component_type="mcq", title=mcq_title, content=mcq)
            self.content.save_lesson_component(component_data)
            components_created += 1

        logger.info(f"🎉 Lesson creation completed! Created {components_created} components")
        return LessonCreationResult(lesson_id=lesson_id, title=request.title, components_created=components_created)
