"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

import asyncio
import inspect
import logging
import re
from typing import Any, cast
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
from modules.content.public import ContentProvider, LessonCreate, UnitCreate, UnitStatus, content_provider
from modules.infrastructure.public import infrastructure_provider
from modules.task_queue.public import task_queue_provider

from .flows import FastLessonCreationFlow, FastUnitCreationFlow, LessonCreationFlow

logger = logging.getLogger(__name__)

# Global set to keep references to background tasks to prevent garbage collection
_background_tasks: set[asyncio.Task] = set()


# Fast flow parallelization control
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

    async def _call_create_lesson_with_fast_flag(self, request: "CreateLessonRequest", use_fast: bool) -> "LessonCreationResult":
        """Call create_lesson_from_source_material with compatible kwarg name.

        Some tests stub this method with a signature that expects `_use_fast_flow` instead
        of `use_fast_flow`. To remain compatible, inspect the callable and pass whichever
        parameter it supports. If neither is present, call without the flag.
        """
        func = self.create_lesson_from_source_material
        try:
            sig = inspect.signature(func)  # type: ignore[arg-type]
            params = sig.parameters
            if "use_fast_flow" in params:
                return await func(request, use_fast_flow=use_fast)  # type: ignore[misc]
            if "_use_fast_flow" in params:
                return await func(request, _use_fast_flow=use_fast)  # type: ignore[misc]
            return await func(request)  # type: ignore[misc]
        except (TypeError, ValueError):
            # Fallback: try both names
            try:
                return await func(request, use_fast_flow=use_fast)  # type: ignore[misc]
            except TypeError:
                return await func(request, _use_fast_flow=use_fast)  # type: ignore[misc]

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

    async def create_lesson_from_source_material(self, request: CreateLessonRequest, *, use_fast_flow: bool = False) -> LessonCreationResult:
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
        flow = FastLessonCreationFlow() if use_fast_flow else LessonCreationFlow()
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

    # ======================
    # Unit creation (NEW)
    # ======================
    class CreateUnitFromTopicRequest(BaseModel):
        topic: str
        target_lesson_count: int | None = None
        user_level: str = "beginner"
        domain: str | None = None
        use_fast_flow: bool = False

    class CreateUnitFromSourceRequest(BaseModel):
        source_material: str
        target_lesson_count: int | None = None
        user_level: str = "beginner"
        domain: str | None = None
        use_fast_flow: bool = False

    class UnitCreationResult(BaseModel):
        unit_id: str
        title: str
        lesson_titles: list[str]
        lesson_count: int
        target_lesson_count: int | None = None
        generated_from_topic: bool = False
        # When generating a complete unit (including lessons), these are returned
        lesson_ids: list[str] | None = None

    # ======================
    # Unit creation (NEW)
    # ======================
    async def create_unit_from_topic(self, request: "ContentCreatorService.CreateUnitFromTopicRequest") -> "ContentCreatorService.UnitCreationResult":
        """Create a learning unit from just a topic using UnitCreationFlow.

        Returns:
            UnitCreationResult with details about the created unit.
        """
        logger.info(f"🏗️ Creating unit from topic: {request.topic}")

        # Run unit flow to get plan and chunks
        flow = FastUnitCreationFlow()
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
            flow_type="fast" if request.use_fast_flow else "standard",
        )
        created_unit = self.content.create_unit(unit_data)

        # Generate lessons per chunk
        chunks = list(flow_result.get("chunks", []) or [])
        lesson_titles: list[str] = list(flow_result.get("lesson_titles", []) or [])
        lesson_ids: list[str] = []
        previous_titles: list[str] = []

        async def _create_one(index: int, chunk: dict[str, object]) -> tuple[int, str | None]:
            chunk_title: str | None = None
            chunk_text: str = ""
            if isinstance(chunk, dict):
                title_obj = chunk.get("title")
                chunk_title = title_obj if isinstance(title_obj, str) else None
                raw_text = chunk.get("chunk_text")
                chunk_text = str(raw_text) if raw_text is not None else ""
            title = chunk_title or (lesson_titles[index] if index < len(lesson_titles) else f"Lesson {index + 1}")
            core_concept = title
            # Use only titles as light prior context to avoid shared state issues
            prior_context = "Previously in this unit: " + ", ".join(previous_titles) + ".\n\n" if previous_titles else ""
            lesson_source_material = f"{prior_context}{chunk_text}" if chunk_text else prior_context
            lesson_req = CreateLessonRequest(
                title=title,
                core_concept=core_concept,
                source_material=lesson_source_material,
                user_level=request.user_level,
                domain=request.domain or "General",
            )
            try:
                res = await self._call_create_lesson_with_fast_flag(lesson_req, request.use_fast_flow)
                return (index, res.lesson_id)
            except Exception as _e:
                logger.exception("Lesson creation failed for index %s (title=%s)", index, title)
                return (index, None)

        if request.use_fast_flow and chunks:
            tasks = [_create_one(i, c if isinstance(c, dict) else {"title": None, "chunk_text": str(c)}) for i, c in enumerate(chunks)]
            results: list[tuple[int, str | None]] = []
            for i in range(0, len(tasks), MAX_PARALLEL_LESSONS):
                batch = tasks[i : i + MAX_PARALLEL_LESSONS]
                batch_results = await asyncio.gather(*batch, return_exceptions=False)
                results.extend(batch_results)
                # update previous_titles best-effort for context of later batches
                for idx, lid in batch_results:
                    if lid is not None and idx < len(lesson_titles):
                        previous_titles.append(lesson_titles[idx])
            # Collect successful lesson ids in order
            for _idx, lid in sorted(results, key=lambda t: t[0]):
                if lid is not None:
                    lesson_ids.append(lid)
        else:
            for index, chunk in enumerate(chunks):
                chunk_title: str | None = None
                chunk_text: str = ""
                if isinstance(chunk, dict):
                    chunk_title = chunk.get("title")
                    chunk_text = str(chunk.get("chunk_text", ""))
                title = chunk_title or (lesson_titles[index] if index < len(lesson_titles) else f"Lesson {index + 1}")
                core_concept = title
                prior_context = "Previously in this unit: " + ", ".join(previous_titles) + ".\n\n" if previous_titles else ""
                lesson_source_material = f"{prior_context}{chunk_text}" if chunk_text else prior_context
                lesson_req = CreateLessonRequest(
                    title=title,
                    core_concept=core_concept,
                    source_material=lesson_source_material,
                    user_level=request.user_level,
                    domain=request.domain or "General",
                )
                lesson_result = await self._call_create_lesson_with_fast_flag(lesson_req, request.use_fast_flow)
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

    async def create_unit_from_source_material(self, request: "ContentCreatorService.CreateUnitFromSourceRequest") -> "ContentCreatorService.UnitCreationResult":
        """Create a learning unit from provided source material using UnitCreationFlow.

        Returns:
            UnitCreationResult with details about the created unit.
        """
        logger.info("🏗️ Creating unit from provided source material")

        # Run unit flow to get plan and chunks
        flow = FastUnitCreationFlow()
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
            flow_type="fast" if request.use_fast_flow else "standard",
        )
        created_unit = self.content.create_unit(unit_data)

        # Generate lessons per chunk
        chunks = list(flow_result.get("chunks", []) or [])
        lesson_titles: list[str] = list(flow_result.get("lesson_titles", []) or [])
        lesson_ids: list[str] = []
        previous_titles: list[str] = []

        async def _create_one_src(index: int, chunk: dict[str, object]) -> tuple[int, str | None]:
            chunk_title: str | None = None
            chunk_text: str = ""
            if isinstance(chunk, dict):
                title_obj = chunk.get("title")
                chunk_title = title_obj if isinstance(title_obj, str) else None
                raw_text = chunk.get("chunk_text")
                chunk_text = str(raw_text) if raw_text is not None else ""
            title = chunk_title or (lesson_titles[index] if index < len(lesson_titles) else f"Lesson {index + 1}")
            core_concept = title
            prior_context = "Previously in this unit: " + ", ".join(previous_titles) + ".\n\n" if previous_titles else ""
            lesson_source_material = f"{prior_context}{chunk_text}" if chunk_text else prior_context
            lesson_req = CreateLessonRequest(
                title=title,
                core_concept=core_concept,
                source_material=lesson_source_material,
                user_level=request.user_level,
                domain=request.domain or "General",
            )
            try:
                res = await self._call_create_lesson_with_fast_flag(lesson_req, request.use_fast_flow)
                return (index, res.lesson_id)
            except Exception as _e:
                logger.exception("Lesson creation failed for index %s (title=%s)", index, title)
                return (index, None)

        if request.use_fast_flow and chunks:
            tasks = [_create_one_src(i, c if isinstance(c, dict) else {"title": None, "chunk_text": str(c)}) for i, c in enumerate(chunks)]
            results: list[tuple[int, str | None]] = []
            for i in range(0, len(tasks), MAX_PARALLEL_LESSONS):
                batch = tasks[i : i + MAX_PARALLEL_LESSONS]
                batch_results = await asyncio.gather(*batch, return_exceptions=False)
                results.extend(batch_results)
                for idx, lid in batch_results:
                    if lid is not None and idx < len(lesson_titles):
                        previous_titles.append(lesson_titles[idx])
            for _idx, lid in sorted(results, key=lambda t: t[0]):
                if lid is not None:
                    lesson_ids.append(lid)
        else:
            for index, chunk in enumerate(chunks):
                chunk_title: str | None = None
                chunk_text: str = ""
                if isinstance(chunk, dict):
                    chunk_title = chunk.get("title")
                    chunk_text = str(chunk.get("chunk_text", ""))
                title = chunk_title or (lesson_titles[index] if index < len(lesson_titles) else f"Lesson {index + 1}")
                core_concept = title
                prior_context = "Previously in this unit: " + ", ".join(previous_titles) + ".\n\n" if previous_titles else ""
                lesson_source_material = f"{prior_context}{chunk_text}" if chunk_text else prior_context
                lesson_req = CreateLessonRequest(
                    title=title,
                    core_concept=core_concept,
                    source_material=lesson_source_material,
                    user_level=request.user_level,
                    domain=request.domain or "General",
                )
                lesson_result = await self._call_create_lesson_with_fast_flag(lesson_req, request.use_fast_flow)
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

    # ======================
    # Mobile unit creation
    # ======================
    class MobileUnitCreationResult(BaseModel):
        """Result of mobile unit creation request."""

        unit_id: str
        title: str
        status: str  # Unit status (in_progress initially)

    async def create_unit_from_mobile(self, topic: str, difficulty: str = "beginner", target_lesson_count: int | None = None) -> "ContentCreatorService.MobileUnitCreationResult":
        """
        Create a unit from mobile app with background processing.

        This method:
        1. Creates a unit record with "in_progress" status immediately
        2. Starts background processing to generate the unit content
        3. Returns immediately so the mobile app doesn't have to wait

        Args:
            topic: The topic for the unit
            difficulty: Difficulty level (beginner, intermediate, advanced)
            target_lesson_count: Optional target number of lessons

        Returns:
            MobileUnitCreationResult with unit info and in_progress status
        """
        logger.info(f"🔥 Starting mobile unit creation: topic='{topic}', difficulty='{difficulty}'")

        # Create unit record immediately with in_progress status
        unit_id = str(uuid.uuid4())
        title = f"Learning Unit: {topic}"

        unit_data = UnitCreate(
            id=unit_id,
            title=title,
            description=f"A learning unit about {topic}",
            difficulty=difficulty,
            lesson_order=[],
            learning_objectives=None,
            target_lesson_count=target_lesson_count,
            source_material=None,
            generated_from_topic=True,
            flow_type="fast",
        )

        # Create the unit in the database with in_progress status
        created_unit = self.content.create_unit(unit_data)

        # Update status to in_progress (the unit is created with completed status by default)
        self.content.update_unit_status(unit_id=created_unit.id, status=UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "starting", "message": "Initializing unit creation..."})

        # Store the unit_id for background processing
        unit_id = created_unit.id

        # Return immediately to avoid holding the request session
        # The background processing will happen with a fresh session
        logger.info(f"✅ Mobile unit creation initiated: unit_id={unit_id}")

        # Start background processing with fresh session (fire and forget)
        task = asyncio.create_task(self._execute_background_unit_creation_with_fresh_session(unit_id=unit_id, topic=topic, difficulty=difficulty, target_lesson_count=target_lesson_count))
        # Store task reference to prevent garbage collection
        self._background_tasks: set[asyncio.Task[Any]] = getattr(self, "_background_tasks", set())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        return self.MobileUnitCreationResult(unit_id=unit_id, title=title, status=UnitStatus.IN_PROGRESS.value)

    # Removed: FastAPI BackgroundTasks path (unused/never worked). Use ARQ path instead.

    async def create_unit_from_mobile_with_arq(self, topic: str, difficulty: str, target_lesson_count: int | None) -> "ContentCreatorService.MobileUnitCreationResult":
        """Create a unit from mobile app using ARQ for reliable background processing."""
        logger.info(f"🔥 Starting mobile unit creation with ARQ: topic='{topic}', difficulty='{difficulty}'")

        # Generate unit ID and title
        unit_id = str(uuid.uuid4())
        title = f"Learning Unit: {topic}"

        # Create unit with initial status
        unit_data = UnitCreate(
            id=unit_id,
            title=title,
            description=f"A learning unit about {topic}",
            difficulty=difficulty,
            lesson_order=[],
            learning_objectives=None,
            target_lesson_count=target_lesson_count,
            source_material=None,
            generated_from_topic=True,
            flow_type="fast",
        )

        created_unit = self.content.create_unit(unit_data)
        logger.info(f"✅ Created unit in database: {created_unit.id}")

        # Update status to in_progress (the unit is created with completed status by default)
        self.content.update_unit_status(unit_id=created_unit.id, status=UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "starting", "message": "Initializing unit creation..."})

        # Submit to ARQ for background processing
        task_queue_service = task_queue_provider()

        # Submit generic content_creator task type to ARQ
        task_result = await task_queue_service.submit_flow_task(
            flow_name="content_creator.unit_creation",
            flow_run_id=uuid.UUID(unit_id),
            inputs={
                "unit_id": unit_id,
                "topic": topic,
                "difficulty": difficulty,
                "target_lesson_count": target_lesson_count,
                "task_type": "content_creator.unit_creation",
            },
        )

        logger.info(f"✅ Mobile unit creation submitted to ARQ: unit_id={unit_id}, task_id={task_result.task_id}")

        return self.MobileUnitCreationResult(unit_id=unit_id, title=title, status=UnitStatus.IN_PROGRESS.value)

    def _execute_background_unit_creation_sync_wrapper(self, unit_id: str, topic: str, difficulty: str, target_lesson_count: int | None) -> None:
        """Deprecated background sync wrapper (legacy). Not used in ARQ path."""

        logger.info(f"🚀 FASTAPI BACKGROUND TASK SYNC WRAPPER CALLED for unit {unit_id}")

        # Create a new event loop for this background task
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._execute_background_unit_creation_with_fresh_session(unit_id, topic, difficulty, target_lesson_count))
        except Exception as e:
            logger.error(f"❌ Background task sync wrapper failed for unit {unit_id}: {e}")
        finally:
            loop.close()

    async def _execute_background_unit_creation_with_fresh_session(self, unit_id: str, topic: str, difficulty: str, target_lesson_count: int | None) -> None:
        """Execute background unit creation with a completely fresh database session to avoid connection pool issues."""
        logger.info(f"🚀 FASTAPI BACKGROUND TASK CALLED for unit {unit_id}")
        try:
            logger.info(f"🎬 BACKGROUND TASK STARTED with fresh session for unit {unit_id}")

            # Get fresh infrastructure and content provider for background execution
            infra = infrastructure_provider()
            infra.initialize()

            # Execute in a separate session to avoid conflicts with the original request session
            with infra.get_session_context() as db_session:
                content = content_provider(db_session)

                # Update status to show the task is running
                content.update_unit_status(unit_id=unit_id, status=UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "processing", "message": "Generating unit content..."})

                # Now call the existing background unit creation logic
                await self._execute_background_unit_creation_logic(content, unit_id, topic, difficulty, target_lesson_count)

        except Exception as e:
            logger.error(f"❌ Background unit creation failed for unit {unit_id}: {e}")
            logger.exception("Full exception details:")

            # Handle errors with fresh session for error updates
            try:
                infra = infrastructure_provider()
                infra.initialize()
                with infra.get_session_context() as error_session:
                    error_content = content_provider(error_session)
                    error_content.update_unit_status(unit_id=unit_id, status=UnitStatus.FAILED.value, error_message=str(e), creation_progress={"stage": "failed", "message": f"Creation failed: {e!s}"})
            except Exception as error_update_exception:
                logger.error(f"❌ Failed to update error status for unit {unit_id}: {error_update_exception}")

    async def _execute_background_unit_creation_logic(self, content: ContentProvider, unit_id: str, topic: str, difficulty: str, target_lesson_count: int | None) -> None:
        """Core logic for background unit creation - extracted to be reusable with different content providers."""
        logger.info(f"⚙️ Executing background unit creation logic for unit {unit_id}")

        # Run the flow to generate lessons but don't create a new unit
        logger.info(f"🔧 Starting flow execution for unit {unit_id}")

        flow = FastUnitCreationFlow()
        flow_result = await flow.execute(
            {
                "topic": topic,
                "target_lesson_count": target_lesson_count,
                "user_level": difficulty,
                "domain": None,
            }
        )
        logger.info(f"🔧 Flow execution completed for unit {unit_id}")

        # Create lessons from the flow result
        lessons_data = flow_result.get("lessons", [])
        logger.info(f"🔧 Flow generated {len(lessons_data)} lessons for unit {unit_id}")

        lesson_ids = []
        for i, lesson_wrapper in enumerate(lessons_data):
            try:
                logger.info(f"🔧 Creating lesson {i + 1}/{len(lessons_data)} for unit {unit_id}")

                # Extract the actual lesson data from the wrapper
                lesson_title = lesson_wrapper.get("title", f"Lesson {i + 1}")
                lesson_result = lesson_wrapper.get("result", {})

                logger.info(f"🔧 Lesson {i + 1} title: {lesson_title}")
                logger.info(f"🔧 Lesson {i + 1} result keys: {list(lesson_result.keys())}")

                # Generate a database-safe lesson id (<=36 chars)
                db_lesson_id = str(uuid.uuid4())

                # Transform flow result into LessonPackage format
                # Create Meta object (keep IDs consistent with DB id)
                meta = Meta(lesson_id=db_lesson_id, title=lesson_title, core_concept=lesson_result.get("core_concept", lesson_title), user_level=difficulty, domain="General")

                # Transform learning_objectives to objectives
                objectives: list[Objective] = []
                for lo_data in lesson_result.get("learning_objectives", []):
                    objectives.append(Objective(id=lo_data.get("id", f"lo_{len(objectives) + 1}"), text=lo_data.get("text", "")))
                # Ensure at least one objective exists
                if not objectives:
                    objectives.append(Objective(id="lo_1", text=lesson_result.get("core_concept", lesson_title)))

                # Prepare mapping for LO ids (case/format-insensitive)
                def _normalize_lo_id(value: str) -> str:
                    v = value.strip()
                    m = re.match(r"^lo[_-]?(\d+)$", v, flags=re.IGNORECASE)
                    if m:
                        return f"lo_{m.group(1)}".lower()
                    return v.lower()

                objective_id_map: dict[str, str] = {obj.id.lower(): obj.id for obj in objectives}
                # Also map normalized numeric forms (e.g., LO1 -> lo_1)
                for obj in objectives:
                    m2 = re.match(r"^lo[_-]?(\d+)$", obj.id, flags=re.IGNORECASE)
                    if m2:
                        objective_id_map[f"lo_{m2.group(1)}".lower()] = obj.id

                # Transform glossary
                glossary_terms: list[GlossaryTerm] = []
                for term_data in lesson_result.get("glossary", {}).get("terms", []):
                    glossary_terms.append(GlossaryTerm(id=term_data.get("id", f"term_{len(glossary_terms) + 1}"), term=term_data.get("term", ""), definition=term_data.get("definition", "")))
                glossary = {"terms": glossary_terms}

                # Transform didactic_snippet
                didactic_data = lesson_result.get("didactic_snippet", {})
                # Coerce None values to valid defaults for strict pydantic validation
                plain_explanation = didactic_data.get("plain_explanation") or ""
                key_takeaways = didactic_data.get("key_takeaways") or []
                didactic_snippet = DidacticSnippet(
                    id=didactic_data.get("id", "lesson_explanation"),
                    plain_explanation=plain_explanation,
                    key_takeaways=key_takeaways,
                )

                # Transform exercises
                exercises: list[MCQExercise] = []
                for ex_data in lesson_result.get("exercises", []):
                    # Create MCQExercise from the exercise data
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

                # Create the complete lesson package
                lesson_package = LessonPackage(
                    meta=meta, objectives=objectives, glossary=glossary, didactic_snippet=didactic_snippet, exercises=exercises, misconceptions=lesson_result.get("misconceptions", []), confusables=lesson_result.get("confusables", [])
                )

                # Create lesson using the properly formatted package
                lesson_create = LessonCreate(
                    id=db_lesson_id,
                    title=lesson_title,
                    core_concept=lesson_result.get("core_concept", lesson_title),
                    user_level=difficulty,
                    package=lesson_package,
                )

                created_lesson = content.save_lesson(lesson_create)
                lesson_ids.append(created_lesson.id)
                logger.info(f"🔧 Created lesson {created_lesson.id} for unit {unit_id}")

            except Exception as e:
                logger.error(f"❌ Failed to create lesson {i + 1} for unit {unit_id}: {e}")
                logger.exception("Full exception details:")
                # Ensure the DB session is usable for subsequent operations
                try:
                    maybe_repo = getattr(cast(Any, content), "repo", None)
                    maybe_session = getattr(maybe_repo, "s", None)
                    if maybe_session is not None and hasattr(maybe_session, "rollback"):
                        maybe_session.rollback()
                except Exception as rb_e:  # pragma: no cover - defensive
                    logger.warning(f"⚠️ Rollback after lesson failure also failed: {rb_e}")
                continue

        # Update the existing unit with the generated content
        if lesson_ids:
            logger.info(f"🔧 Assigning {len(lesson_ids)} lessons to unit {unit_id}: {lesson_ids}")
            result_unit = content.assign_lessons_to_unit(unit_id, lesson_ids)
            logger.info(f"🔧 Lesson assignment completed for unit {unit_id}")

            # Verify the assignment worked
            if result_unit:
                logger.info(f"🔧 Unit {unit_id} now has lesson_order: {result_unit.lesson_order}")
                # Double-check by querying lessons
                unit_lessons = content.get_lessons_by_unit(unit_id)
                logger.info(f"🔧 Unit {unit_id} has {len(unit_lessons)} lessons in database")
            else:
                logger.error(f"❌ Failed to assign lessons to unit {unit_id} - unit not found")
        else:
            logger.warning(f"⚠️ No lessons were created for unit {unit_id}")

        # Mark as completed
        logger.info(f"🔧 Marking unit {unit_id} as completed")
        content.update_unit_status(unit_id=unit_id, status=UnitStatus.COMPLETED.value, creation_progress={"stage": "completed", "message": "Unit creation completed successfully"})
        logger.info(f"🔧 Unit {unit_id} status updated to completed")

        logger.info(f"✅ Background unit creation completed for unit {unit_id}")

    async def _start_background_unit_creation(self, unit_id: str, topic: str, difficulty: str, target_lesson_count: int | None) -> None:
        """Start background task to create unit content."""
        logger.info(f"🔧 Starting background task creation for unit {unit_id}")

        # Try a simpler approach - just call the method directly without asyncio.create_task
        # This might work better in the FastAPI context
        try:
            # Schedule the task to run "soon" but don't await it
            future = asyncio.ensure_future(self._execute_background_unit_creation(unit_id=unit_id, topic=topic, difficulty=difficulty, target_lesson_count=target_lesson_count))
            # Store future reference to prevent garbage collection
            self._background_futures: set[asyncio.Future[Any]] = getattr(self, "_background_futures", set())
            self._background_futures.add(future)
            future.add_done_callback(self._background_futures.discard)
            logger.info(f"🚀 Background unit creation scheduled for unit {unit_id}")
        except Exception as e:
            logger.error(f"❌ Failed to schedule background task for unit {unit_id}: {e}")

    async def _execute_background_unit_creation(self, unit_id: str, topic: str, difficulty: str, target_lesson_count: int | None) -> None:
        """Execute the actual unit creation in the background with fresh database session."""
        logger.info(f"🎬 BACKGROUND TASK STARTED for unit {unit_id}")

        # Immediately update status to show the task is running
        try:
            infra = infrastructure_provider()
            infra.initialize()
            with infra.get_session_context() as test_session:
                test_content = content_provider(test_session)
                test_content.update_unit_status(unit_id=unit_id, status=UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "task_started", "message": "Background task is running!"})
                logger.info(f"🎬 BACKGROUND TASK STATUS UPDATED for unit {unit_id}")
        except Exception as e:
            logger.error(f"❌ Failed to update initial status for unit {unit_id}: {e}")

        try:
            logger.info(f"⚙️ Executing background unit creation for unit {unit_id}")

            # Get fresh infrastructure and content provider for background execution
            logger.info(f"🔧 Setting up fresh infrastructure for unit {unit_id}")
            infra = infrastructure_provider()
            infra.initialize()

            # Execute in a separate session to avoid conflicts with the original request session
            logger.info(f"🔧 Creating fresh database session for unit {unit_id}")
            with infra.get_session_context() as db_session:
                content = content_provider(db_session)

                # We have a fresh content provider with the background session
                logger.info(f"🔧 Using fresh content provider for unit {unit_id}")

                # Update progress
                content.update_unit_status(unit_id=unit_id, status=UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "planning", "message": "Planning unit structure..."})

                # Update progress
                content.update_unit_status(unit_id=unit_id, status=UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "generating", "message": "Generating lessons..."})

                # Run the flow to generate lessons but don't create a new unit
                logger.info(f"🔧 Starting flow execution for unit {unit_id}")
                flow = FastUnitCreationFlow()
                flow_result = await flow.execute(
                    {
                        "topic": topic,
                        "target_lesson_count": target_lesson_count,
                        "user_level": difficulty,
                        "domain": None,
                    }
                )
                logger.info(f"🔧 Flow execution completed for unit {unit_id}")

                # Create lessons from the flow result
                lessons_data = flow_result.get("lessons", [])
                logger.info(f"🔧 Flow generated {len(lessons_data)} lessons for unit {unit_id}")

                lesson_ids = []
                for i, lesson_wrapper in enumerate(lessons_data):
                    try:
                        logger.info(f"🔧 Creating lesson {i + 1}/{len(lessons_data)} for unit {unit_id}")

                        # Extract the actual lesson data from the wrapper
                        lesson_title = lesson_wrapper.get("title", f"Lesson {i + 1}")
                        lesson_result = lesson_wrapper.get("result", {})

                        logger.info(f"🔧 Lesson {i + 1} title: {lesson_title}")
                        logger.info(f"🔧 Lesson {i + 1} result keys: {list(lesson_result.keys())}")

                        # Transform flow result into LessonPackage format
                        # Create Meta object
                        meta = Meta(lesson_id=f"lesson-{unit_id}-{i + 1}", title=lesson_title, core_concept=lesson_result.get("core_concept", lesson_title), user_level=difficulty, domain="General")

                        # Transform learning_objectives to objectives
                        objectives: list[Objective] = []
                        for lo_data in lesson_result.get("learning_objectives", []):
                            objectives.append(Objective(id=lo_data.get("id", f"lo_{len(objectives) + 1}"), text=lo_data.get("text", "")))

                        # Transform glossary
                        glossary_terms: list[GlossaryTerm] = []
                        for term_data in lesson_result.get("glossary", {}).get("terms", []):
                            glossary_terms.append(GlossaryTerm(id=term_data.get("id", f"term_{len(glossary_terms) + 1}"), term=term_data.get("term", ""), definition=term_data.get("definition", "")))
                        glossary = {"terms": glossary_terms}

                        # Transform didactic_snippet
                        didactic_data = lesson_result.get("didactic_snippet", {})
                        didactic_snippet = DidacticSnippet(id=didactic_data.get("id", "lesson_explanation"), plain_explanation=didactic_data.get("plain_explanation", ""), key_takeaways=didactic_data.get("key_takeaways", []))

                        # Transform exercises
                        exercises: list[MCQExercise] = []
                        for ex_data in lesson_result.get("exercises", []):
                            # Create MCQExercise from the exercise data
                            exercises.append(
                                MCQExercise(
                                    id=ex_data.get("id", f"ex_{len(exercises) + 1}"),
                                    exercise_type=ex_data.get("exercise_type", "mcq"),
                                    lo_id=ex_data.get("lo_id", objectives[0].id if objectives else "lo_1"),
                                    cognitive_level=ex_data.get("cognitive_level", "remember"),
                                    estimated_difficulty=ex_data.get("estimated_difficulty", "easy"),
                                    misconceptions_used=ex_data.get("misconceptions_used", []),
                                    stem=ex_data.get("stem", ""),
                                    options=ex_data.get("options", []),
                                    answer_key=ex_data.get("answer_key", {}),
                                )
                            )

                        # Create the complete lesson package
                        lesson_package = LessonPackage(
                            meta=meta, objectives=objectives, glossary=glossary, didactic_snippet=didactic_snippet, exercises=exercises, misconceptions=lesson_result.get("misconceptions", []), confusables=lesson_result.get("confusables", [])
                        )

                        # Create lesson using the properly formatted package
                        lesson_create = LessonCreate(
                            id=f"lesson-{unit_id}-{i + 1}",
                            title=lesson_title,
                            core_concept=lesson_result.get("core_concept", lesson_title),
                            user_level=difficulty,
                            package=lesson_package,
                        )

                        created_lesson = content.save_lesson(lesson_create)
                        lesson_ids.append(created_lesson.id)
                        logger.info(f"🔧 Created lesson {created_lesson.id} for unit {unit_id}")

                    except Exception as e:
                        logger.error(f"❌ Failed to create lesson {i + 1} for unit {unit_id}: {e}")
                        logger.exception("Full exception details:")
                        continue

                # Update the existing unit with the generated content
                if lesson_ids:
                    logger.info(f"🔧 Assigning {len(lesson_ids)} lessons to unit {unit_id}: {lesson_ids}")
                    result_unit = content.assign_lessons_to_unit(unit_id, lesson_ids)
                    logger.info(f"🔧 Lesson assignment completed for unit {unit_id}")

                    # Verify the assignment worked
                    if result_unit:
                        logger.info(f"🔧 Unit {unit_id} now has lesson_order: {result_unit.lesson_order}")
                        # Double-check by querying lessons
                        unit_lessons = content.get_lessons_by_unit(unit_id)
                        logger.info(f"🔧 Unit {unit_id} has {len(unit_lessons)} lessons in database")
                    else:
                        logger.error(f"❌ Failed to assign lessons to unit {unit_id} - unit not found")
                else:
                    logger.warning(f"⚠️ No lessons were created for unit {unit_id}")

                # Mark as completed
                logger.info(f"🔧 Marking unit {unit_id} as completed")
                content.update_unit_status(unit_id=unit_id, status=UnitStatus.COMPLETED.value, creation_progress={"stage": "completed", "message": "Unit creation completed successfully"})
                logger.info(f"🔧 Unit {unit_id} status updated to completed")

                logger.info(f"✅ Background unit creation completed for unit {unit_id}")

        except Exception as e:
            logger.error(f"❌ Background unit creation failed for unit {unit_id}: {e}")

            # For error handling, we need another fresh session since the previous one might be rolled back
            try:
                infra = infrastructure_provider()
                infra.initialize()
                with infra.get_session_context() as error_db_session:
                    error_content = content_provider(error_db_session)
                    # Mark as failed
                    error_content.update_unit_status(unit_id=unit_id, status=UnitStatus.FAILED.value, error_message=str(e), creation_progress={"stage": "failed", "message": f"Creation failed: {e!s}"})
            except Exception as error_update_error:
                logger.error(f"❌ Failed to update unit status to failed for unit {unit_id}: {error_update_error}")

            # Don't re-raise - this is a background task

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

        # Start background processing again
        await self._start_background_unit_creation(unit_id=unit_id, topic=topic, difficulty=difficulty, target_lesson_count=target_lesson_count)

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
