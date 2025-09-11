"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

import logging
import uuid

from pydantic import BaseModel

from modules.content.package_models import DidacticSnippet, GlossaryTerm, LengthBudgets, LessonPackage, MCQAnswerKey, MCQItem, MCQOption, Meta, Objective
from modules.content.public import ContentProvider, LessonCreate

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
    """Result of lesson creation with package details."""

    lesson_id: str
    title: str
    package_version: int
    objectives_count: int
    glossary_terms_count: int
    mcqs_count: int


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
        2. Builds a complete LessonPackage with all content
        3. Saves the lesson with embedded package to the content module
        4. Returns summary of what was created
        """
        lesson_id = str(uuid.uuid4())
        logger.info(f"🎯 Creating lesson: {request.title} (ID: {lesson_id})")

        # Use flow engine for content extraction
        logger.info("🔄 Starting LessonCreationFlow...")
        flow = LessonCreationFlow()
        flow_result = await flow.execute({"title": request.title, "core_concept": request.core_concept, "source_material": request.source_material, "user_level": request.user_level, "domain": request.domain})
        logger.info("✅ LessonCreationFlow completed successfully")

        # Build package metadata
        meta = Meta(lesson_id=lesson_id, title=request.title, core_concept=request.core_concept, user_level=request.user_level, domain=request.domain, package_schema_version=1, content_version=1, length_budgets=LengthBudgets())

        # Build objectives from flow result
        objectives = []
        for i, lo in enumerate(flow_result.get("learning_objectives", [])):
            if hasattr(lo, "text"):
                text = lo.text
                bloom_level = getattr(lo, "bloom_level", None)
            elif isinstance(lo, dict):
                text = lo.get("text", str(lo))
                bloom_level = lo.get("bloom_level", None)
            else:
                text = str(lo)
                bloom_level = None

            objectives.append(Objective(id=f"lo_{i + 1}", text=text, bloom_level=bloom_level))

        # Build glossary from flow result
        glossary_terms = []
        for i, term_data in enumerate(flow_result.get("glossary", [])):
            if hasattr(term_data, "term"):
                term = term_data.term
                definition = getattr(term_data, "definition", "")
                relation_to_core = getattr(term_data, "relation_to_core", None)
            elif isinstance(term_data, dict):
                term = term_data.get("term", f"Term {i + 1}")
                definition = term_data.get("definition", "")
                relation_to_core = term_data.get("relation_to_core", None)
            else:
                term = f"Term {i + 1}"
                definition = str(term_data)
                relation_to_core = None

            glossary_terms.append(GlossaryTerm(id=f"term_{i + 1}", term=term, definition=definition, relation_to_core=relation_to_core))

        # Build didactic snippets from flow result
        didactic_snippets = {}
        if "didactic_snippet" in flow_result and objectives:
            # For now, associate didactic snippet with first objective
            first_lo_id = objectives[0].id
            didactic_data = flow_result["didactic_snippet"]

            if isinstance(didactic_data, dict):
                plain_explanation = didactic_data.get("explanation", "")
                key_takeaways = didactic_data.get("key_takeaways", [])
                worked_example = didactic_data.get("worked_example", None)
            else:
                plain_explanation = str(didactic_data)
                key_takeaways = []
                worked_example = None

            didactic_snippets[first_lo_id] = DidacticSnippet(id=f"didactic_{first_lo_id}", plain_explanation=plain_explanation, key_takeaways=key_takeaways if isinstance(key_takeaways, list) else [str(key_takeaways)], worked_example=worked_example)

        # Build MCQs from flow result
        mcqs = []
        labels = ["A", "B", "C", "D"]  # Define labels once

        for i, mcq_data in enumerate(flow_result.get("mcqs", [])):
            if not objectives:
                continue  # Skip MCQs if no objectives

            # Associate with first objective for now
            lo_id = objectives[0].id

            if isinstance(mcq_data, dict):
                stem = mcq_data.get("question", mcq_data.get("stem", f"Question {i + 1}"))
                options_data = mcq_data.get("options", [])
                correct_answer_raw = mcq_data.get("correct_answer", "A")
                # Handle both index (0,1,2,3) and label ("A","B","C","D") formats
                if isinstance(correct_answer_raw, int):
                    correct_answer = labels[correct_answer_raw] if correct_answer_raw < len(labels) else "A"
                else:
                    correct_answer = str(correct_answer_raw)
            else:
                stem = str(mcq_data)
                options_data = []
                correct_answer = "A"

            # Build options
            options = []
            for j, option_data in enumerate(options_data[:4]):  # Max 4 options
                if j >= len(labels):
                    break

                if isinstance(option_data, dict):
                    text = option_data.get("text", f"Option {labels[j]}")
                else:
                    text = str(option_data)

                options.append(MCQOption(id=f"mcq_{i + 1}_option_{labels[j]}", label=labels[j], text=text))

            # Ensure we have at least 3 options
            while len(options) < 3:
                label = labels[len(options)]
                options.append(MCQOption(id=f"mcq_{i + 1}_option_{label}", label=label, text=f"Option {label}"))

            # Build answer key
            answer_key = MCQAnswerKey(label=correct_answer)

            mcqs.append(MCQItem(id=f"mcq_{i + 1}", lo_id=lo_id, stem=stem, options=options, answer_key=answer_key))

        # Build complete lesson package
        package = LessonPackage(meta=meta, objectives=objectives, glossary={"terms": glossary_terms}, didactic={"by_lo": didactic_snippets}, mcqs=mcqs, misconceptions=[], confusables=[])

        # Convert refined material to dict format
        refined_material_obj = flow_result.get("refined_material", {})
        if hasattr(refined_material_obj, "outline_bullets"):
            refined_material_dict = {"outline_bullets": refined_material_obj.outline_bullets, "evidence_anchors": getattr(refined_material_obj, "evidence_anchors", [])}
        else:
            refined_material_dict = refined_material_obj if isinstance(refined_material_obj, dict) else {}

        # Create lesson with package
        lesson_data = LessonCreate(
            id=lesson_id,
            title=request.title,
            core_concept=request.core_concept,
            user_level=request.user_level,
            source_material=request.source_material,
            source_domain=request.domain,
            source_level=request.user_level,
            refined_material=refined_material_dict,
            package=package,
            package_version=1,
        )

        logger.info("💾 Saving lesson with package to database...")
        self.content.save_lesson(lesson_data)

        logger.info(f"🎉 Lesson creation completed! Package contains {len(objectives)} objectives, {len(glossary_terms)} terms, {len(mcqs)} MCQs")
        return LessonCreationResult(lesson_id=lesson_id, title=request.title, package_version=1, objectives_count=len(objectives), glossary_terms_count=len(glossary_terms), mcqs_count=len(mcqs))
