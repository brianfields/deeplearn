"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

import logging
import uuid

# FastAPI BackgroundTasks path was removed; keep import set minimal
from pydantic import BaseModel

from modules.content.package_models import (
    GlossaryTerm,
    LessonPackage,
    MCQAnswerKey,
    MCQExercise,
    MCQOption,
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
    """Request to create a lesson using the new prompt-aligned flow."""

    topic: str
    unit_source_material: str
    learner_level: str = "intermediate"
    voice: str = "Plain"
    learning_objectives: list[str]
    lesson_objective: str


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
        logger.info(f"🎯 Creating lesson: {request.topic} (ID: {lesson_id})")

        # Run lesson creation flow using new prompt-aligned inputs
        flow = LessonCreationFlow()
        logger.info("🔄 Starting %s...", flow.flow_name)
        flow_result = await flow.execute(
            {
                "topic": request.topic,
                "learner_level": request.learner_level,
                "voice": request.voice,
                "learning_objectives": request.learning_objectives,
                "lesson_objective": request.lesson_objective,
                "unit_source_material": request.unit_source_material,
            }
        )
        logger.info("✅ LessonCreationFlow completed successfully")

        meta = Meta(
            lesson_id=lesson_id,
            title=request.topic,
            learner_level=request.learner_level,
            package_schema_version=1,
            content_version=1,
        )

        # Build lesson-level objectives from request.learning_objectives (texts)
        objectives: list[Objective] = []
        for i, lo_text in enumerate(request.learning_objectives):
            objectives.append(Objective(id=f"lo_{i + 1}", text=str(lo_text)))

        # Build glossary from flow result (list of terms)
        glossary_terms: list[GlossaryTerm] = []
        for i, term_data in enumerate(flow_result.get("glossary", []) or []):
            if isinstance(term_data, dict):
                glossary_terms.append(
                    GlossaryTerm(
                        id=f"term_{i + 1}",
                        term=term_data.get("term", f"Term {i + 1}"),
                        definition=term_data.get("definition", ""),
                        micro_check=term_data.get("micro_check"),
                    )
                )
            else:
                glossary_terms.append(GlossaryTerm(id=f"term_{i + 1}", term=str(term_data), definition=""))

        mini_lesson_text = str(flow_result.get("mini_lesson") or "")

        # Build exercises from MCQs
        exercises: list[MCQExercise] = []
        mcqs = flow_result.get("mcqs", {}) or {}
        mcqs = mcqs.get("mcqs", []) or []
        for idx, mcq in enumerate(mcqs):
            exercise_id = f"mcq_{idx + 1}"
            options_with_ids: list[MCQOption] = []
            option_id_map: dict[str, str] = {}
            for opt in mcq.get("options", []):
                opt_label = opt.get("label", "").upper()
                gen_opt_id = f"{exercise_id}_{opt_label.lower()}"
                option_id_map[opt_label] = gen_opt_id
                options_with_ids.append(
                    MCQOption(
                        id=gen_opt_id,
                        label=opt_label,
                        text=opt.get("text", ""),
                        rationale_wrong=opt.get("rationale_wrong"),
                    )
                )
            ak = mcq.get("answer_key", {}) or {}
            key_label = str(ak.get("label", "")).upper()
            answer_key = MCQAnswerKey(label=key_label, option_id=option_id_map.get(key_label), rationale_right=ak.get("rationale_right"))
            # Choose a primary LO id from lesson objectives (first)
            lo_id = objectives[0].id if objectives else "lo_1"

            exercises.append(
                MCQExercise(
                    id=exercise_id,
                    exercise_type="mcq",
                    lo_id=lo_id,
                    cognitive_level=None,
                    estimated_difficulty=None,
                    misconceptions_used=mcq.get("misconceptions_used", []),
                    stem=mcq.get("stem", ""),
                    options=options_with_ids,
                    answer_key=answer_key,
                )
            )

        # Build complete lesson package
        # Normalize misconceptions/confusables to dicts
        _misconceptions: list[dict[str, str]] = []
        for m in flow_result.get("misconceptions", []) or []:
            if isinstance(m, dict):
                _misconceptions.append(m)
            elif hasattr(m, "model_dump"):
                _misconceptions.append(m.model_dump())
        _confusables: list[dict[str, str]] = []
        for c in flow_result.get("confusables", []) or []:
            if isinstance(c, dict):
                _confusables.append(c)
            elif hasattr(c, "model_dump"):
                _confusables.append(c.model_dump())

        package = LessonPackage(
            meta=meta,
            objectives=objectives,
            glossary={"terms": glossary_terms},
            mini_lesson=mini_lesson_text,
            exercises=exercises,
            misconceptions=_misconceptions,
            confusables=_confusables,
        )

        # Create lesson with package
        lesson_data = LessonCreate(
            id=lesson_id,
            title=request.topic,
            learner_level=request.learner_level,
            source_material=request.unit_source_material,
            package=package,
            package_version=1,
        )

        logger.info("💾 Saving lesson with package to database...")
        self.content.save_lesson(lesson_data)

        logger.info(f"🎉 Lesson creation completed! Package contains {len(objectives)} objectives, {len(glossary_terms)} terms, {len(exercises)} exercises")
        return LessonCreationResult(lesson_id=lesson_id, title=request.topic, package_version=1, objectives_count=len(objectives), glossary_terms_count=len(glossary_terms), mcqs_count=len(exercises))

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
        learner_level: str = "beginner",
    ) -> "ContentCreatorService.UnitCreationResult | ContentCreatorService.MobileUnitCreationResult":
        """Create a learning unit (foreground or background).

        Args:
            topic: Topic used to generate or contextualize the unit.
            source_material: Optional pre-provided material. If None, it will be generated.
            background: If True, enqueue and return immediately with in_progress status.
            target_lesson_count: Optional target number of lessons.
            learner_level: Difficulty level.
        """
        # Pre-create the shell unit for both paths
        provisional_title = f"Learning Unit: {topic}"
        unit = self.content.create_unit(
            UnitCreate(
                title=provisional_title,
                description=f"A learning unit about {topic}",
                learner_level=learner_level,
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
                    "unit_source_material": source_material,
                    "target_lesson_count": target_lesson_count,
                    "learner_level": learner_level,
                },
            )
            return self.MobileUnitCreationResult(unit_id=unit.id, title=unit.title, status=UnitStatus.IN_PROGRESS.value)

        # Foreground execution
        return await self._execute_unit_creation_pipeline(
            unit_id=unit.id,
            topic=topic,
            source_material=source_material,
            target_lesson_count=target_lesson_count,
            learner_level=learner_level,
        )

    async def _execute_unit_creation_pipeline(
        self,
        *,
        unit_id: str,
        topic: str,
        source_material: str | None,
        target_lesson_count: int | None,
        learner_level: str,
    ) -> "ContentCreatorService.UnitCreationResult":
        """Execute the end-to-end unit creation using the active prompt-aligned flows."""
        logger.info(f"🧱 Executing unit creation pipeline for unit {unit_id}")
        self.content.update_unit_status(unit_id, UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "planning", "message": "Planning unit structure..."})

        flow = UnitCreationFlow()
        unit_plan = await flow.execute(
            {
                "topic": topic,
                "unit_source_material": source_material,
                "target_lesson_count": target_lesson_count,
                "learner_level": learner_level,
            }
        )

        # Update unit metadata from plan
        final_title = str(unit_plan.get("unit_title") or f"Learning Unit: {topic}")
        self.content.update_unit_status(unit_id, UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "generating", "message": "Generating lessons..."})

        # Prepare look-up of unit-level LO texts by id
        unit_los: dict[str, str] = {}
        for lo in unit_plan.get("learning_objectives", []) or []:
            if isinstance(lo, dict):
                unit_los[lo.get("lo_id", "")] = lo.get("text", "")

        lesson_ids: list[str] = []
        unit_material: str = str(unit_plan.get("unit_source_material") or source_material or "")
        lessons_plan = unit_plan.get("lessons", []) or []

        for i, lp in enumerate(lessons_plan):
            lesson_title = lp.get("title") or f"Lesson {i + 1}"
            lesson_lo_ids: list[str] = list(lp.get("learning_objectives", []) or [])
            lesson_lo_texts: list[str] = [unit_los.get(lid, lid) for lid in lesson_lo_ids]
            lesson_objective_text: str = lp.get("lesson_objective", "")

            # Extract lesson metadata
            md_res = await LessonCreationFlow().execute(
                {
                    "topic": lesson_title,
                    "learner_level": learner_level,
                    "voice": "Plain",
                    "learning_objectives": lesson_lo_texts,
                    "lesson_objective": lesson_objective_text,
                    "unit_source_material": unit_material,
                }
            )

            # Build package for lesson
            db_lesson_id = str(uuid.uuid4())
            meta = Meta(lesson_id=db_lesson_id, title=lesson_title, learner_level=learner_level, package_schema_version=1, content_version=1)

            # Objectives for lesson
            objectives: list[Objective] = []
            for j, lo_text in enumerate(lesson_lo_texts):
                objectives.append(Objective(id=f"lo_{j + 1}", text=str(lo_text)))

            # Glossary
            glossary_terms: list[GlossaryTerm] = []
            for k, term in enumerate(md_res.get("glossary", []) or []):
                glossary_terms.append(GlossaryTerm(id=f"term_{k + 1}", term=term.get("term", f"Term {k + 1}"), definition=term.get("definition", "")))
            glossary = {"terms": glossary_terms}

            # Mini lesson text
            mini_lesson_text = str(md_res.get("mini_lesson") or "")

            # MCQ exercises
            exercises: list[MCQExercise] = []
            # Flow returns either a dict { metadata, mcqs: [...] } or a bare list
            mcqs_container = md_res.get("mcqs", {}) or {}
            mcq_items = mcqs_container.get("mcqs", []) if isinstance(mcqs_container, dict) else (mcqs_container or [])
            for idx, mcq in enumerate(mcq_items):
                if not isinstance(mcq, dict):
                    # Skip malformed entries
                    continue
                exercise_id = f"mcq_{idx + 1}"
                options_with_ids: list[MCQOption] = []
                option_id_map: dict[str, str] = {}
                for opt in mcq.get("options", []):
                    opt_label = opt.get("label", "").upper()
                    gen_opt_id = f"{exercise_id}_{opt_label.lower()}"
                    option_id_map[opt_label] = gen_opt_id
                    options_with_ids.append(
                        MCQOption(
                            id=gen_opt_id,
                            label=opt_label,
                            text=opt.get("text", ""),
                            rationale_wrong=opt.get("rationale_wrong"),
                        )
                    )
                ak = mcq.get("answer_key", {}) or {}
                key_label = str(ak.get("label", "")).upper()
                answer_key = MCQAnswerKey(
                    label=key_label,
                    option_id=option_id_map.get(key_label),
                    rationale_right=ak.get("rationale_right"),
                )

                exercises.append(
                    MCQExercise(
                        id=exercise_id,
                        exercise_type="mcq",
                        lo_id=objectives[0].id if objectives else "lo_1",
                        cognitive_level=None,
                        estimated_difficulty=None,
                        misconceptions_used=mcq.get("misconceptions_used", []),
                        stem=mcq.get("stem", ""),
                        options=options_with_ids,
                        answer_key=answer_key,
                    )
                )

            lesson_package = LessonPackage(
                meta=meta,
                objectives=objectives,
                glossary=glossary,
                mini_lesson=mini_lesson_text,
                exercises=exercises,
                misconceptions=md_res.get("misconceptions", []),
                confusables=md_res.get("confusables", []),
            )

            created_lesson = self.content.save_lesson(
                LessonCreate(
                    id=db_lesson_id,
                    title=lesson_title,
                    learner_level=learner_level,
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
            lesson_titles=[lp.get("title", "") for lp in lessons_plan],
            lesson_count=len(lesson_ids),
            target_lesson_count=unit_plan.get("lesson_count"),
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
        learner_level = unit.learner_level
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
                "learner_level": learner_level,
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
