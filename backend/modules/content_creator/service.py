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

    @property
    def components_created(self) -> int:
        """Total number of components created."""
        return self.objectives_count + self.glossary_terms_count + self.mcqs_count


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

        # Build package metadata (use budgets from flow if available)
        flow_budgets = flow_result.get("length_budgets", {})
        if isinstance(flow_budgets, dict):
            budgets = LengthBudgets(
                stem_max_words=flow_budgets.get("stem_max_words", 35),
                vignette_max_words=flow_budgets.get("vignette_max_words", 80),
                option_max_words=flow_budgets.get("option_max_words", 12),
            )
        else:
            budgets = LengthBudgets(stem_max_words=35, vignette_max_words=80, option_max_words=12)

        meta = Meta(
            lesson_id=lesson_id,
            title=request.title,
            core_concept=request.core_concept,
            user_level=request.user_level,
            domain=request.domain,
            package_schema_version=1,
            content_version=1,
            length_budgets=budgets,
        )

        # Build objectives from flow result (preserve LO ids from flow if provided)
        objectives: list[Objective] = []
        for i, lo in enumerate(flow_result.get("learning_objectives", [])):
            if hasattr(lo, "text"):
                text = lo.text
                bloom_level = getattr(lo, "bloom_level", None)
                lo_id_val = getattr(lo, "lo_id", None) or f"lo_{i + 1}"
            elif isinstance(lo, dict):
                text = lo.get("text", str(lo))
                bloom_level = lo.get("bloom_level", None)
                lo_id_val = lo.get("lo_id") or f"lo_{i + 1}"
            else:
                text = str(lo)
                bloom_level = None
                lo_id_val = f"lo_{i + 1}"

            objectives.append(Objective(id=lo_id_val, text=text, bloom_level=bloom_level))

        # Build glossary from flow result (supports both dict with terms and raw list)
        glossary_terms = []
        glossary_blob = flow_result.get("glossary", {})
        terms_iterable = glossary_blob.get("terms", []) if isinstance(glossary_blob, dict) else glossary_blob if isinstance(glossary_blob, list) else []

        for i, term_data in enumerate(terms_iterable):
            if hasattr(term_data, "term"):
                term = term_data.term
                definition = getattr(term_data, "definition", "")
                relation_to_core = getattr(term_data, "relation_to_core", None)
                common_confusion = getattr(term_data, "common_confusion", None)
                micro_check = getattr(term_data, "micro_check", None)
            elif isinstance(term_data, dict):
                term = term_data.get("term", f"Term {i + 1}")
                definition = term_data.get("definition", "")
                relation_to_core = term_data.get("relation_to_core", None)
                common_confusion = term_data.get("common_confusion", None)
                micro_check = term_data.get("micro_check", None)
            else:
                term = f"Term {i + 1}"
                definition = str(term_data)
                relation_to_core = None
                common_confusion = None
                micro_check = None

            glossary_terms.append(
                GlossaryTerm(
                    id=f"term_{i + 1}",
                    term=term,
                    definition=definition,
                    relation_to_core=relation_to_core,
                    common_confusion=common_confusion,
                    micro_check=micro_check,
                )
            )

        # Build didactic snippet from flow result - single snippet for entire lesson
        didactic_structure: dict[str, dict[str, DidacticSnippet]] = {}

        if "didactic_snippet" in flow_result:
            didactic_data = flow_result["didactic_snippet"]
            if isinstance(didactic_data, dict):
                # Handle new mobile-friendly structure
                introduction = didactic_data.get("introduction", "")
                core_explanation = didactic_data.get("core_explanation", "")
                key_points = didactic_data.get("key_points", [])
                practical_context = didactic_data.get("practical_context", "")

                # Fallback to legacy fields if new ones aren't present
                if not core_explanation:
                    core_explanation = didactic_data.get("plain_explanation", "")
                if not key_points:
                    key_points = didactic_data.get("key_takeaways", [])

                # Combine all parts into a cohesive explanation for mobile display
                explanation_parts = []
                if introduction:
                    explanation_parts.append(introduction)
                if core_explanation:
                    explanation_parts.append(core_explanation)
                if practical_context:
                    explanation_parts.append(practical_context)

                full_explanation = "\n\n".join(explanation_parts) if explanation_parts else "No explanation provided"

                # Legacy fields for backward compatibility
                mini_vignette = didactic_data.get("mini_vignette", None)
                worked_example = didactic_data.get("worked_example", None)
                near_miss_example = didactic_data.get("near_miss_example", None)
                discriminator_hint = didactic_data.get("discriminator_hint", None)
            else:
                full_explanation = str(didactic_data)
                key_points = []
                mini_vignette = None
                worked_example = None
                near_miss_example = None
                discriminator_hint = None

            # Create single lesson-wide snippet
            lesson_snippet = DidacticSnippet(
                id="lesson_explanation",
                mini_vignette=mini_vignette,
                plain_explanation=full_explanation,
                key_takeaways=key_points if isinstance(key_points, list) else [str(key_points)],
                worked_example=worked_example,
                near_miss_example=near_miss_example,
                discriminator_hint=discriminator_hint,
            )
            # Store under "lesson" key to indicate this is lesson-wide content
            didactic_structure["lesson"] = {"explanation": lesson_snippet}

        # Legacy: per-LO didactic snippets (for backward compatibility with old data)
        elif "didactic_snippets" in flow_result:
            raw_map = flow_result.get("didactic_snippets", {}) or {}
            if isinstance(raw_map, dict):
                for lo_id, didactic_data in raw_map.items():
                    if isinstance(didactic_data, dict):
                        mini_vignette = didactic_data.get("mini_vignette", None)
                        plain_explanation = didactic_data.get("plain_explanation", didactic_data.get("explanation", ""))
                        key_takeaways = didactic_data.get("key_takeaways", [])
                        worked_example = didactic_data.get("worked_example", None)
                        near_miss_example = didactic_data.get("near_miss_example", None)
                        discriminator_hint = didactic_data.get("discriminator_hint", None)
                    else:
                        mini_vignette = None
                        plain_explanation = str(didactic_data)
                        key_takeaways = []
                        worked_example = None
                        near_miss_example = None
                        discriminator_hint = None

                    snippet = DidacticSnippet(
                        id=f"didactic_{lo_id}",
                        mini_vignette=mini_vignette,
                        plain_explanation=plain_explanation,
                        key_takeaways=key_takeaways if isinstance(key_takeaways, list) else [str(key_takeaways)],
                        worked_example=worked_example,
                        near_miss_example=near_miss_example,
                        discriminator_hint=discriminator_hint,
                    )
                    didactic_structure[lo_id] = {"main": snippet}

        # Build MCQs from flow result
        mcqs = []
        labels = ["A", "B", "C", "D"]  # Define labels once

        for i, mcq_data in enumerate(flow_result.get("mcqs", [])):
            if not objectives:
                continue  # Skip MCQs if no objectives

            # Associate with corresponding objective if counts match; else fallback to first objective
            lo_id = objectives[min(i, len(objectives) - 1)].id if len(flow_result.get("mcqs", [])) == len(objectives) else objectives[0].id

            if isinstance(mcq_data, dict):
                stem = mcq_data.get("stem", mcq_data.get("question", f"Question {i + 1}"))
                options_data = mcq_data.get("options", [])
                # Prefer new shape: answer_key: {label, option_id?, rationale_right?}
                answer_key_blob = mcq_data.get("answer_key")
                rationale_right = None
                if isinstance(answer_key_blob, dict) and "label" in answer_key_blob:
                    correct_answer = str(answer_key_blob.get("label", "A"))
                    rationale_right = answer_key_blob.get("rationale_right", None)
                else:
                    correct_answer_raw = mcq_data.get("correct_answer", "A")
                    correct_answer = labels[correct_answer_raw] if isinstance(correct_answer_raw, int) and 0 <= correct_answer_raw < len(labels) else str(correct_answer_raw)
                    rationale_right = mcq_data.get("rationale_right", None)
                cognitive_level = mcq_data.get("cognitive_level", None)
                estimated_difficulty = mcq_data.get("estimated_difficulty", None)
                misconceptions_used = mcq_data.get("misconceptions_used", [])
            else:
                stem = str(mcq_data)
                options_data = []
                correct_answer = "A"
                rationale_right = None
                cognitive_level = None
                estimated_difficulty = None
                misconceptions_used = []

            # Build options
            options = []
            for j, option_data in enumerate(options_data[:4]):  # Max 4 options
                if j >= len(labels):
                    break

                if isinstance(option_data, dict):
                    text = option_data.get("text", f"Option {labels[j]}")
                    rationale_wrong = option_data.get("rationale_wrong", None)
                else:
                    text = str(option_data)
                    rationale_wrong = None

                options.append(MCQOption(id=f"mcq_{i + 1}_option_{labels[j]}", label=labels[j], text=text, rationale_wrong=rationale_wrong))

            # Ensure we have at least 3 options
            while len(options) < 3:
                label = labels[len(options)]
                options.append(MCQOption(id=f"mcq_{i + 1}_option_{label}", label=label, text=f"Option {label}", rationale_wrong=None))

            # Build answer key
            # Try to attach option_id convenience if label matches
            option_id = None
            for opt in options:
                if opt.label == correct_answer:
                    option_id = opt.id
                    break
            answer_key = MCQAnswerKey(label=correct_answer, option_id=option_id, rationale_right=rationale_right)

            mcqs.append(
                MCQItem(
                    id=f"mcq_{i + 1}",
                    lo_id=lo_id,
                    stem=stem,
                    cognitive_level=cognitive_level,
                    estimated_difficulty=estimated_difficulty,
                    options=options,
                    answer_key=answer_key,
                    misconceptions_used=misconceptions_used if isinstance(misconceptions_used, list) else [],
                )
            )

        # Build complete lesson package
        package = LessonPackage(
            meta=meta,
            objectives=objectives,
            glossary={"terms": glossary_terms},
            didactic=didactic_structure,
            mcqs=mcqs,
            misconceptions=flow_result.get("misconceptions", []),
            confusables=flow_result.get("confusables", []),
        )

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
