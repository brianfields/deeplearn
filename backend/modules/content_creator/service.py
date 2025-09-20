"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

import logging
import uuid

from pydantic import BaseModel

from modules.content.package_models import DidacticSnippet, GlossaryTerm, LengthBudgets, LessonPackage, Meta, Objective
from modules.content.public import ContentProvider, LessonCreate, UnitCreate

from .flows import LessonCreationFlow, UnitCreationFlow

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
        didactic_data = flow_result.get("didactic_snippet")
        if didactic_data is None:
            # Handle missing didactic snippet
            full_explanation = "No explanation provided"
            key_points = []
            mini_vignette = None
            worked_example = None
            near_miss_example = None
            discriminator_hint = None
        elif isinstance(didactic_data, dict):
            # Handle new mobile-friendly structure from DidacticSnippetOutputs
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

            mini_vignette = didactic_data.get("mini_vignette", None)
            worked_example = didactic_data.get("worked_example", None)
            near_miss_example = didactic_data.get("near_miss_example", None)
            discriminator_hint = didactic_data.get("discriminator_hint", None)
        else:
            full_explanation = str(didactic_data) if didactic_data else "No explanation provided"
            key_points = []
            mini_vignette = None
            worked_example = None
            near_miss_example = None
            discriminator_hint = None

        # Create single lesson-wide snippet
        lesson_didactic_snippet = DidacticSnippet(
            id="lesson_explanation",
            mini_vignette=mini_vignette,
            plain_explanation=full_explanation,
            key_takeaways=key_points if isinstance(key_points, list) else [str(key_points)],
            worked_example=worked_example,
            near_miss_example=near_miss_example,
            discriminator_hint=discriminator_hint,
        )

        # Build exercises from flow result
        exercises = flow_result.get("exercises", [])

        # Build complete lesson package
        package = LessonPackage(
            meta=meta,
            objectives=objectives,
            glossary={"terms": glossary_terms},
            didactic_snippet=lesson_didactic_snippet,
            exercises=exercises,
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

        logger.info(f"🎉 Lesson creation completed! Package contains {len(objectives)} objectives, {len(glossary_terms)} terms, {len(exercises)} exercises")
        return LessonCreationResult(lesson_id=lesson_id, title=request.title, package_version=1, objectives_count=len(objectives), glossary_terms_count=len(glossary_terms), mcqs_count=len(exercises))

    # ======================
    # Unit creation (NEW)
    # ======================
    class CreateUnitFromTopicRequest(BaseModel):
        topic: str
        target_lesson_count: int | None = None
        user_level: str = "beginner"
        domain: str | None = None

    class CreateUnitFromSourceRequest(BaseModel):
        source_material: str
        target_lesson_count: int | None = None
        user_level: str = "beginner"
        domain: str | None = None

    class UnitCreationResult(BaseModel):
        unit_id: str
        title: str
        lesson_titles: list[str]
        lesson_count: int
        target_lesson_count: int | None = None
        generated_from_topic: bool = False
        # When generating a complete unit (including lessons), these are returned
        lesson_ids: list[str] | None = None

    async def create_unit_from_topic(self, request: "ContentCreatorService.CreateUnitFromTopicRequest") -> "ContentCreatorService.UnitCreationResult":
        """Create a learning unit end-to-end from just a topic using UnitCreationFlow."""
        logger.info(f"🏗️ Creating unit from topic: {request.topic}")

        flow = UnitCreationFlow()
        flow_result = await flow.execute(
            {
                "topic": request.topic,
                "source_material": None,
                "target_lesson_count": request.target_lesson_count,
                "user_level": request.user_level,
                "domain": request.domain,
            }
        )

        # Persist unit
        unit_title = str(flow_result.get("unit_title") or request.topic)
        data = UnitCreate(
            title=unit_title,
            description=flow_result.get("summary"),
            difficulty=request.user_level,
            lesson_order=[],
            learning_objectives=flow_result.get("learning_objectives"),
            target_lesson_count=flow_result.get("target_lesson_count"),
            source_material=flow_result.get("source_material"),
            generated_from_topic=True,
        )
        created = self.content.create_unit(data)

        return self.UnitCreationResult(
            unit_id=created.id,
            title=created.title,
            lesson_titles=list(flow_result.get("lesson_titles", [])),
            lesson_count=int(flow_result.get("lesson_count", 0)),
            target_lesson_count=flow_result.get("target_lesson_count"),
            generated_from_topic=True,
        )

    async def create_unit_from_source_material(self, request: "ContentCreatorService.CreateUnitFromSourceRequest") -> "ContentCreatorService.UnitCreationResult":
        """Create a learning unit from provided source material using UnitCreationFlow."""
        logger.info("🏗️ Creating unit from provided source material")

        flow = UnitCreationFlow()
        flow_result = await flow.execute(
            {
                "topic": None,
                "source_material": request.source_material,
                "target_lesson_count": request.target_lesson_count,
                "user_level": request.user_level,
                "domain": request.domain,
            }
        )

        # Persist unit
        unit_title = str(flow_result.get("unit_title") or "Learning Unit")
        data = UnitCreate(
            title=unit_title,
            description=flow_result.get("summary"),
            difficulty=request.user_level,
            lesson_order=[],
            learning_objectives=flow_result.get("learning_objectives"),
            target_lesson_count=flow_result.get("target_lesson_count"),
            source_material=flow_result.get("source_material"),
            generated_from_topic=False,
        )
        created = self.content.create_unit(data)

        return self.UnitCreationResult(
            unit_id=created.id,
            title=created.title,
            lesson_titles=list(flow_result.get("lesson_titles", [])),
            lesson_count=int(flow_result.get("lesson_count", 0)),
            target_lesson_count=flow_result.get("target_lesson_count"),
            generated_from_topic=False,
        )

    # ======================
    # Complete unit creation (unit + lessons)
    # ======================
    async def create_complete_unit_from_topic(
        self,
        request: "ContentCreatorService.CreateUnitFromTopicRequest",
    ) -> "ContentCreatorService.UnitCreationResult":
        """Create a unit and generate all lessons from topic-only input.

        This orchestrates UnitCreationFlow to obtain lesson chunks, persists the
        unit, generates a full lesson for each chunk via LessonCreationFlow, and
        assigns the created lessons to the unit preserving order.
        """
        logger.info(f"🏗️ Creating complete unit from topic: {request.topic}")

        # Run unit flow to get plan and chunks
        flow = UnitCreationFlow()
        flow_result = await flow.execute(
            {
                "topic": request.topic,
                "source_material": None,
                "target_lesson_count": request.target_lesson_count,
                "user_level": request.user_level,
                "domain": request.domain,
            }
        )

        unit_title = str(flow_result.get("unit_title") or request.topic)

        # Persist unit first
        unit_data = UnitCreate(
            title=unit_title,
            description=flow_result.get("summary"),
            difficulty=request.user_level,
            lesson_order=[],
            learning_objectives=flow_result.get("learning_objectives"),
            target_lesson_count=flow_result.get("target_lesson_count"),
            source_material=flow_result.get("source_material"),
            generated_from_topic=True,
        )
        created_unit = self.content.create_unit(unit_data)

        # Generate lessons per chunk and collect IDs
        chunks = list(flow_result.get("chunks", []) or [])
        lesson_titles: list[str] = list(flow_result.get("lesson_titles", []) or [])
        lesson_ids: list[str] = []
        previous_titles: list[str] = []

        for index, chunk in enumerate(chunks):
            # Determine title/core concept
            chunk_title: str | None = None
            chunk_text: str = ""
            if isinstance(chunk, dict):
                chunk_title = chunk.get("title")
                chunk_text = str(chunk.get("chunk_text", ""))
            # Fallbacks
            title = chunk_title or (lesson_titles[index] if index < len(lesson_titles) else f"Lesson {index + 1}")
            core_concept = title

            # Add lightweight prior context to encourage cross-lesson references
            prior_context = "Previously in this unit: " + ", ".join(previous_titles) + ".\n\n" if previous_titles else ""
            lesson_source_material = f"{prior_context}{chunk_text}" if chunk_text else prior_context

            # Create lesson from chunk
            lesson_req = CreateLessonRequest(
                title=title,
                core_concept=core_concept,
                source_material=lesson_source_material,
                user_level=request.user_level,
                domain=request.domain or "General",
            )
            lesson_result = await self.create_lesson_from_source_material(lesson_req)
            lesson_ids.append(lesson_result.lesson_id)
            previous_titles.append(title)

        # Associate lessons with unit and set ordering
        if lesson_ids:
            self.content.assign_lessons_to_unit(created_unit.id, lesson_ids)

        return self.UnitCreationResult(
            unit_id=created_unit.id,
            title=created_unit.title,
            lesson_titles=lesson_titles or previous_titles,
            lesson_count=len(lesson_ids) or int(flow_result.get("lesson_count", 0)),
            target_lesson_count=flow_result.get("target_lesson_count"),
            generated_from_topic=True,
            lesson_ids=lesson_ids,
        )

    async def create_complete_unit_from_source_material(
        self,
        request: "ContentCreatorService.CreateUnitFromSourceRequest",
    ) -> "ContentCreatorService.UnitCreationResult":
        """Create a unit and generate all lessons from provided source material."""
        logger.info("🏗️ Creating complete unit from provided source material")

        # Run unit flow to get plan and chunks
        flow = UnitCreationFlow()
        flow_result = await flow.execute(
            {
                "topic": None,
                "source_material": request.source_material,
                "target_lesson_count": request.target_lesson_count,
                "user_level": request.user_level,
                "domain": request.domain,
            }
        )

        unit_title = str(flow_result.get("unit_title") or "Learning Unit")

        # Persist unit first
        unit_data = UnitCreate(
            title=unit_title,
            description=flow_result.get("summary"),
            difficulty=request.user_level,
            lesson_order=[],
            learning_objectives=flow_result.get("learning_objectives"),
            target_lesson_count=flow_result.get("target_lesson_count"),
            source_material=flow_result.get("source_material"),
            generated_from_topic=False,
        )
        created_unit = self.content.create_unit(unit_data)

        # Generate lessons per chunk and collect IDs
        chunks = list(flow_result.get("chunks", []) or [])
        lesson_titles: list[str] = list(flow_result.get("lesson_titles", []) or [])
        lesson_ids: list[str] = []
        previous_titles: list[str] = []

        for index, chunk in enumerate(chunks):
            # Determine title/core concept
            chunk_title: str | None = None
            chunk_text: str = ""
            if isinstance(chunk, dict):
                chunk_title = chunk.get("title")
                chunk_text = str(chunk.get("chunk_text", ""))
            # Fallbacks
            title = chunk_title or (lesson_titles[index] if index < len(lesson_titles) else f"Lesson {index + 1}")
            core_concept = title

            # Add lightweight prior context
            prior_context = "Previously in this unit: " + ", ".join(previous_titles) + ".\n\n" if previous_titles else ""
            lesson_source_material = f"{prior_context}{chunk_text}" if chunk_text else prior_context

            # Create lesson from chunk
            lesson_req = CreateLessonRequest(
                title=title,
                core_concept=core_concept,
                source_material=lesson_source_material,
                user_level=request.user_level,
                domain=request.domain or "General",
            )
            lesson_result = await self.create_lesson_from_source_material(lesson_req)
            lesson_ids.append(lesson_result.lesson_id)
            previous_titles.append(title)

        # Associate lessons with unit and set ordering
        if lesson_ids:
            self.content.assign_lessons_to_unit(created_unit.id, lesson_ids)

        return self.UnitCreationResult(
            unit_id=created_unit.id,
            title=created_unit.title,
            lesson_titles=lesson_titles or previous_titles,
            lesson_count=len(lesson_ids) or int(flow_result.get("lesson_count", 0)),
            target_lesson_count=flow_result.get("target_lesson_count"),
            generated_from_topic=False,
            lesson_ids=lesson_ids,
        )
