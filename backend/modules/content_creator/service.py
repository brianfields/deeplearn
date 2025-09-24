"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

import logging
import re
from typing import Any
import uuid

# FastAPI BackgroundTasks path was removed; keep import set minimal
from pydantic import BaseModel

from modules.content.package_models import (
    DidacticSnippet,
    GlossaryTerm,
    LengthBudgets,
    LessonPackage,
    MCQExercise,
    Meta,
    Objective,
)
from modules.content.public import ContentProvider, LessonCreate, UnitCreate, UnitStatus
from modules.task_queue.public import task_queue_provider

from .flows import LessonCreationFlow, UnitCreationFlow

logger = logging.getLogger(__name__)

MAX_PARALLEL_LESSONS = 4


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

        # Use flow engine for content extraction (fast logic is default in LessonCreationFlow)
        flow = LessonCreationFlow()
        logger.info("🔄 Starting %s...", flow.flow_name)
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

    class UnitCreationResult(BaseModel):
        unit_id: str
        title: str
        lesson_titles: list[str]
        lesson_count: int
        target_lesson_count: int | None = None
        generated_from_topic: bool = False
        # When generating a complete unit (including lessons), these are returned
        lesson_ids: list[str] | None = None

    class MobileUnitCreationResult(BaseModel):
        unit_id: str
        title: str
        status: str

    async def create_unit(
        self,
        *,
        topic: str,
        source_material: str | None = None,
        background: bool = False,
        target_lesson_count: int | None = None,
        user_level: str = "beginner",
        domain: str | None = None,
    ) -> "ContentCreatorService.UnitCreationResult | ContentCreatorService.MobileUnitCreationResult":
        """Create a learning unit (foreground or background).

        Args:
            topic: Topic used to generate or contextualize the unit.
            source_material: Optional pre-provided material. If None, it will be generated.
            background: If True, enqueue and return immediately with in_progress status.
            target_lesson_count: Optional target number of lessons.
            user_level: Difficulty level.
            domain: Optional domain context.
        """
        # Pre-create the shell unit for both paths
        provisional_title = f"Learning Unit: {topic}"
        unit = self.content.create_unit(
            UnitCreate(
                title=provisional_title,
                description=f"A learning unit about {topic}",
                difficulty=user_level,
                lesson_order=[],
                learning_objectives=None,
                target_lesson_count=target_lesson_count,
                source_material=source_material,
                generated_from_topic=(source_material is None),
                flow_type="standard",
            )
        )
        self.content.update_unit_status(
            unit_id=unit.id,
            status=UnitStatus.IN_PROGRESS.value,
            creation_progress={"stage": "starting", "message": "Initialization"},
        )

        if background:
            # Submit unified task to ARQ
            task_queue_service = task_queue_provider()
            await task_queue_service.submit_flow_task(
                flow_name="content_creator.unit_creation",
                flow_run_id=uuid.UUID(unit.id),
                inputs={
                    "unit_id": unit.id,
                    "topic": topic,
                    "source_material": source_material,
                    "target_lesson_count": target_lesson_count,
                    "user_level": user_level,
                    "domain": domain,
                },
            )
            return self.MobileUnitCreationResult(unit_id=unit.id, title=unit.title, status=UnitStatus.IN_PROGRESS.value)

        # Foreground execution
        return await self._execute_unit_creation_pipeline(
            unit_id=unit.id,
            topic=topic,
            source_material=source_material,
            target_lesson_count=target_lesson_count,
            user_level=user_level,
            domain=domain,
        )

    async def _execute_unit_creation_pipeline(
        self,
        *,
        unit_id: str,
        topic: str,
        source_material: str | None,
        target_lesson_count: int | None,
        user_level: str,
        domain: str | None,
    ) -> "ContentCreatorService.UnitCreationResult":
        """Execute the end-to-end unit creation using fast-default flows."""
        logger.info(f"🧱 Executing unit creation pipeline for unit {unit_id}")
        self.content.update_unit_status(unit_id, UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "planning", "message": "Planning unit structure..."})

        flow = UnitCreationFlow()
        unit_plan = await flow.execute(
            {
                "topic": topic,
                "source_material": source_material,
                "target_lesson_count": target_lesson_count,
                "user_level": user_level,
                "domain": domain,
            }
        )

        # Update unit metadata from plan
        final_title = str(unit_plan.get("unit_title") or f"Learning Unit: {topic}")
        self.content.update_unit_status(unit_id, UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "generating", "message": "Generating lessons..."})
        # Note: Title/metadata persistence beyond status updates is handled by assign/update ops below

        # Create lessons per chunk using the fast lesson flow (now default)
        lesson_titles: list[str] = list(unit_plan.get("lesson_titles", []) or [])
        chunks: list[dict[str, Any]] = list(unit_plan.get("chunks", []) or [])
        lesson_ids: list[str] = []

        for i, chunk in enumerate(chunks):
            lesson_title = chunk.get("title") or (lesson_titles[i] if i < len(lesson_titles) else f"Lesson {i + 1}")
            chunk_text = str(chunk.get("chunk_text") or "")

            # Execute lesson flow
            lesson_result = await LessonCreationFlow().execute(
                {
                    "title": lesson_title,
                    "core_concept": lesson_title,
                    "source_material": chunk_text,
                    "user_level": user_level,
                    "domain": (domain or "General"),
                }
            )

            # Build LessonPackage from fast result
            # Create Meta
            db_lesson_id = str(uuid.uuid4())
            meta = Meta(lesson_id=db_lesson_id, title=lesson_title, core_concept=lesson_result.get("core_concept", lesson_title), user_level=user_level, domain=(domain or "General"))

            # Objectives
            objectives: list[Objective] = []
            for lo_data in lesson_result.get("learning_objectives", []):
                if isinstance(lo_data, dict):
                    objectives.append(Objective(id=lo_data.get("id", f"lo_{len(objectives) + 1}"), text=lo_data.get("text", "")))
            if not objectives:
                objectives.append(Objective(id="lo_1", text=lesson_result.get("core_concept", lesson_title)))

            # Map normalized LO ids for MCQ mapping
            def _normalize_lo_id(value: str) -> str:
                v = value.strip()
                m = re.match(r"^lo[_-]?(\d+)$", v, flags=re.IGNORECASE)
                if m:
                    return f"lo_{m.group(1)}".lower()
                return v.lower()

            objective_id_map: dict[str, str] = {obj.id.lower(): obj.id for obj in objectives}
            for obj in objectives:
                m2 = re.match(r"^lo[_-]?(\d+)$", obj.id, flags=re.IGNORECASE)
                if m2:
                    objective_id_map[f"lo_{m2.group(1)}".lower()] = obj.id

            # Glossary
            glossary_terms: list[GlossaryTerm] = []
            for term_data in lesson_result.get("glossary", {}).get("terms", []):
                glossary_terms.append(GlossaryTerm(id=term_data.get("id", f"term_{len(glossary_terms) + 1}"), term=term_data.get("term", ""), definition=term_data.get("definition", "")))
            glossary = {"terms": glossary_terms}

            # Didactic snippet
            didactic_data = lesson_result.get("didactic_snippet", {})
            plain_explanation = didactic_data.get("plain_explanation") or ""
            key_takeaways = didactic_data.get("key_takeaways") or []
            didactic_snippet = DidacticSnippet(id=didactic_data.get("id", "lesson_explanation"), plain_explanation=plain_explanation, key_takeaways=key_takeaways)

            # Exercises
            exercises: list[MCQExercise] = []
            for ex_data in lesson_result.get("exercises", []):
                raw_lo: str | None = ex_data.get("lo_id")
                mapped_lo: str = objectives[0].id if objectives else "lo_1"
                if isinstance(raw_lo, str) and raw_lo.strip():
                    norm = _normalize_lo_id(raw_lo)
                    mapped_lo = objective_id_map.get(norm, mapped_lo)

                exercises.append(
                    MCQExercise(
                        id=ex_data.get("id", f"ex_{len(exercises) + 1}"),
                        exercise_type=ex_data.get("exercise_type", "mcq"),
                        lo_id=mapped_lo,
                        cognitive_level=ex_data.get("cognitive_level", "remember"),
                        estimated_difficulty=ex_data.get("estimated_difficulty", "easy"),
                        misconceptions_used=ex_data.get("misconceptions_used", []),
                        stem=ex_data.get("stem", ""),
                        options=ex_data.get("options", []),
                        answer_key=ex_data.get("answer_key", {}),
                    )
                )

            lesson_package = LessonPackage(
                meta=meta,
                objectives=objectives,
                glossary=glossary,
                didactic_snippet=didactic_snippet,
                exercises=exercises,
                misconceptions=lesson_result.get("misconceptions", []),
                confusables=lesson_result.get("confusables", []),
            )

            created_lesson = self.content.save_lesson(
                LessonCreate(
                    id=db_lesson_id,
                    title=lesson_title,
                    core_concept=lesson_result.get("core_concept", lesson_title),
                    user_level=user_level,
                    package=lesson_package,
                )
            )
            lesson_ids.append(created_lesson.id)

        # Associate lessons and complete
        if lesson_ids:
            self.content.assign_lessons_to_unit(unit_id, lesson_ids)

        self.content.update_unit_status(unit_id, UnitStatus.COMPLETED.value, creation_progress={"stage": "completed", "message": "Unit creation completed"})

        return self.UnitCreationResult(
            unit_id=unit_id,
            title=final_title,
            lesson_titles=lesson_titles or [c.get("title", "") for c in chunks],
            lesson_count=len(lesson_ids),
            target_lesson_count=unit_plan.get("target_lesson_count"),
            generated_from_topic=(source_material is None),
            lesson_ids=lesson_ids,
        )

    async def retry_unit_creation(self, unit_id: str) -> "ContentCreatorService.MobileUnitCreationResult | None":
        """
        Retry failed unit creation.

        This will reset the unit to in_progress status and restart the background creation process
        using the original parameters.
        """
        # Get the existing unit
        unit = self.content.get_unit(unit_id)
        if not unit:
            return None

        # Only allow retry for failed units
        if unit.status != UnitStatus.FAILED.value:
            raise ValueError(f"Unit {unit_id} is not in failed state (current: {unit.status})")

        # Ensure we have the necessary data for retry
        if not unit.generated_from_topic:
            raise ValueError(f"Unit {unit_id} was not generated from a topic and cannot be retried")

        # Reset the unit status to in_progress
        self.content.update_unit_status(unit_id=unit_id, status=UnitStatus.IN_PROGRESS.value, error_message=None, creation_progress={"stage": "retrying", "message": "Retrying unit creation..."})

        # Extract original parameters - we need to infer the topic from the unit description or title
        # Since we stored the description as "A learning unit about {topic}", we can extract it
        topic = unit.title  # Use title as topic for retry
        difficulty = unit.difficulty
        target_lesson_count = unit.target_lesson_count

        # Start background processing again via ARQ submission
        task_queue_service = task_queue_provider()
        await task_queue_service.submit_flow_task(
            flow_name="content_creator.unit_creation",
            flow_run_id=uuid.UUID(unit_id),
            inputs={
                "unit_id": unit_id,
                "topic": topic,
                "source_material": unit.source_material,
                "target_lesson_count": target_lesson_count,
                "user_level": difficulty,
                "domain": None,
            },
        )

        logger.info(f"✅ Unit retry initiated: unit_id={unit_id}")

        return self.MobileUnitCreationResult(unit_id=unit_id, title=unit.title, status=UnitStatus.IN_PROGRESS.value)

    def dismiss_unit(self, unit_id: str) -> bool:
        """
        Dismiss (delete) a unit.

        This will permanently remove the unit from the database.
        Returns True if successful, False if unit not found.
        """
        # Check if unit exists
        unit = self.content.get_unit(unit_id)
        if not unit:
            return False

        # Delete the unit
        # Note: We need to add a delete method to content service
        # For now we'll update the status to indicate dismissal
        try:
            # Try to delete via repo if available
            success = self.content.delete_unit(unit_id)
            logger.info(f"✅ Unit dismissed: unit_id={unit_id}")
            return success
        except AttributeError:
            # Fallback: mark as dismissed in status if delete method doesn't exist yet
            logger.warning(f"Delete method not available, marking unit as dismissed: unit_id={unit_id}")
            result = self.content.update_unit_status(unit_id=unit_id, status="dismissed", error_message=None, creation_progress={"stage": "dismissed", "message": "Unit dismissed by user"})
            return result is not None
