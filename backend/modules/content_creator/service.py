"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

import logging
from typing import Any
import uuid

# FastAPI BackgroundTasks path was removed; keep import set minimal
import httpx

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
from modules.content.public import ContentProvider, LessonCreate, UnitCreate, UnitRead, UnitStatus
from modules.task_queue.public import task_queue_provider

from .flows import LessonCreationFlow, UnitArtCreationFlow, UnitCreationFlow
from .podcast import PodcastLesson, UnitPodcastGenerator

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

    def __init__(
        self,
        content: ContentProvider,
        podcast_generator: UnitPodcastGenerator | None = None,
    ) -> None:
        """Initialize with content storage only - flows handle LLM interactions."""
        self.content = content
        self.podcast_generator = podcast_generator
        # Object store is no longer used here; persistence is delegated to content service
        self._object_store = None

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
        await self.content.save_lesson(lesson_data)

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

    async def create_unit_art(self, unit_id: str) -> UnitRead:
        """Generate and persist Weimar Edge artwork for the specified unit."""

        unit_detail = await self.content.get_unit_detail(unit_id, include_art_presigned_url=False)
        if unit_detail is None:
            raise ValueError("Unit not found")

        learning_objectives = list(getattr(unit_detail, "learning_objectives", []) or [])
        key_concepts = self._extract_key_concepts(unit_detail)

        flow_inputs = {
            "unit_title": unit_detail.title,
            "unit_description": unit_detail.description or "",
            "learning_objectives": learning_objectives,
            "key_concepts": key_concepts,
        }

        flow = UnitArtCreationFlow()
        attempts = 0
        art_payload: dict[str, Any] | None = None
        last_exc: Exception | None = None

        while attempts < 2:
            try:
                art_payload = await flow.execute(flow_inputs)
                break
            except Exception as exc:  # pragma: no cover - LLM/network issues
                attempts += 1
                last_exc = exc
                logger.warning("🖼️ Unit art attempt %s failed for unit %s: %s", attempts, unit_id, exc, exc_info=True)
        if art_payload is None:
            raise RuntimeError("Unit art generation failed") from last_exc

        description_info = art_payload.get("art_description") or {}
        prompt_text = str(description_info.get("prompt", "")).strip()
        alt_text = str(description_info.get("alt_text", "")).strip()

        image_info = art_payload.get("image") or {}
        image_url = image_info.get("image_url")
        if not image_url:
            raise RuntimeError("Image generation returned no URL")

        image_bytes, content_type = await self._download_image(image_url)

        return await self.content.save_unit_art_from_bytes(
            unit_id,
            image_bytes=image_bytes,
            content_type=content_type or "image/png",
            description=prompt_text or None,
            alt_text=alt_text or None,
        )

    async def create_unit(
        self,
        *,
        topic: str,
        source_material: str | None = None,
        background: bool = False,
        target_lesson_count: int | None = None,
        learner_level: str = "beginner",
        user_id: int | None = None,
    ) -> "ContentCreatorService.UnitCreationResult | ContentCreatorService.MobileUnitCreationResult":
        """Create a learning unit (foreground or background).

        Args:
            topic: Topic/description for the unit. Can be detailed text from learning coach.
            source_material: Optional pre-provided material. If None, it will be generated.
            background: If True, enqueue and return immediately with in_progress status.
            target_lesson_count: Optional target number of lessons.
            learner_level: Difficulty level.
        """
        # Pre-create the shell unit for both paths
        # Truncate topic for provisional title (will be replaced by proper title from flow)
        provisional_title = topic[:200] + "..." if len(topic) > 200 else topic
        unit = await self.content.create_unit(
            UnitCreate(
                title=provisional_title,
                description=topic,  # Store full detailed topic in description
                learner_level=learner_level,
                lesson_order=[],
                user_id=user_id,
                learning_objectives=None,
                target_lesson_count=target_lesson_count,
                source_material=source_material,
                generated_from_topic=(source_material is None),
                flow_type="standard",
            )
        )
        await self.content.update_unit_status(
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
        await self.content.update_unit_status(unit_id, UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "planning", "message": "Planning unit structure..."})

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
        final_title = str(unit_plan.get("unit_title") or f"{topic}")
        await self.content.update_unit_status(unit_id, UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "generating", "message": "Generating lessons..."})

        # Prepare look-up of unit-level LO texts by id
        unit_los: dict[str, str] = {}
        for lo in unit_plan.get("learning_objectives", []) or []:
            if isinstance(lo, dict):
                unit_los[lo.get("lo_id", "")] = lo.get("text", "")

        lesson_ids: list[str] = []
        podcast_lessons: list[PodcastLesson] = []
        podcast_voice_label: str | None = None
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
            if podcast_voice_label is None:
                podcast_voice_label = str(md_res.get("voice") or "Plain")
            podcast_lessons.append(PodcastLesson(title=lesson_title, mini_lesson=mini_lesson_text))

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

            created_lesson = await self.content.save_lesson(
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
            await self.content.assign_lessons_to_unit(unit_id, lesson_ids)

        if podcast_lessons:
            generator = self.podcast_generator or UnitPodcastGenerator()
            # Cache the generator for future use to avoid repeated initialization
            self.podcast_generator = generator
            try:
                summary_text = self._summarize_unit_plan(unit_plan, lessons_plan)
                podcast = await generator.create_podcast(
                    unit_title=final_title,
                    voice_label=podcast_voice_label or "Plain",
                    unit_summary=summary_text,
                    lessons=podcast_lessons,
                )
            except Exception as exc:  # pragma: no cover - podcast generation should not block unit creation
                logger.warning("🎧 Failed to generate podcast for unit %s: %s", unit_id, exc, exc_info=True)
            else:
                if podcast.audio_bytes:
                    try:
                        await self.content.save_unit_podcast_from_bytes(
                            unit_id,
                            transcript=podcast.transcript,
                            audio_bytes=podcast.audio_bytes,
                            mime_type=podcast.mime_type,
                            voice=podcast.voice,
                        )
                    except Exception as exc:  # pragma: no cover - network/object store issues
                        logger.warning(
                            "🎧 Failed to persist podcast audio for unit %s: %s",
                            unit_id,
                            exc,
                            exc_info=True,
                        )

        try:
            await self.content.update_unit_status(
                unit_id,
                UnitStatus.IN_PROGRESS.value,
                creation_progress={"stage": "artwork", "message": "Rendering hero artwork..."},
            )
            await self.create_unit_art(unit_id)
        except Exception as exc:  # pragma: no cover - art generation should not block unit creation
            logger.warning("🖼️ Failed to generate unit art for %s: %s", unit_id, exc, exc_info=True)

        await self.content.update_unit_status(unit_id, UnitStatus.COMPLETED.value, creation_progress={"stage": "completed", "message": "Unit creation completed"})

        return self.UnitCreationResult(
            unit_id=unit_id,
            title=final_title,
            lesson_titles=[lp.get("title", "") for lp in lessons_plan],
            lesson_count=len(lesson_ids),
            target_lesson_count=unit_plan.get("lesson_count"),
            generated_from_topic=(source_material is None),
            lesson_ids=lesson_ids,
        )

    def _summarize_unit_plan(self, unit_plan: dict[str, Any], lessons_plan: list[Any]) -> str:
        """Create a concise textual summary of the unit plan for podcast prompting."""

        summary_lines: list[str] = []
        lesson_count = unit_plan.get("lesson_count") or len(lessons_plan)
        summary_lines.append(f"Lesson count: {lesson_count}")

        objective_texts: list[str] = []
        for objective in unit_plan.get("learning_objectives", []) or []:
            if isinstance(objective, dict):
                text = objective.get("text") or objective.get("summary")
                if text:
                    objective_texts.append(str(text))
            elif isinstance(objective, str):
                objective_texts.append(objective)
            else:
                text_attr = getattr(objective, "text", None)
                if text_attr:
                    objective_texts.append(str(text_attr))

        if objective_texts:
            summary_lines.append("Learning objectives:")
            summary_lines.extend(f"- {text}" for text in objective_texts)

        for idx, lesson in enumerate(lessons_plan, start=1):
            if isinstance(lesson, dict):
                title = lesson.get("title") or f"Lesson {idx}"
                objective = lesson.get("lesson_objective")
                if objective:
                    summary_lines.append(f"{idx}. {title} — {objective}")
                else:
                    summary_lines.append(f"{idx}. {title}")
            else:
                summary_lines.append(f"{idx}. Lesson {idx}")

        return "\n".join(summary_lines)

    @staticmethod
    def _build_podcast_filename(unit_id: str, mime_type: str | None) -> str:
        """Construct a reasonable filename for uploaded podcast audio."""

        extension_map = {
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/flac": ".flac",
            "audio/x-flac": ".flac",
            "audio/mp4": ".mp4",
            "audio/m4a": ".m4a",
        }
        suffix = extension_map.get((mime_type or "").lower(), ".bin")
        return f"unit-{unit_id}{suffix}"

    def _extract_key_concepts(self, unit_detail: Any) -> list[str]:
        """Aggregate distinct key concepts across lessons for artwork prompting."""

        concepts: list[str] = []
        lessons = getattr(unit_detail, "lessons", []) or []
        for lesson in lessons:
            lesson_concepts = getattr(lesson, "key_concepts", []) or []
            for concept in lesson_concepts:
                normalized = str(concept)
                if normalized and normalized not in concepts:
                    concepts.append(normalized)
                if len(concepts) >= 8:
                    break
            if len(concepts) >= 8:
                break
        return concepts

    async def _download_image(self, url: str) -> tuple[bytes, str | None]:
        """Fetch binary image data from the generated image URL."""

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content, response.headers.get("content-type")

    async def retry_unit_creation(self, unit_id: str) -> "ContentCreatorService.MobileUnitCreationResult | None":
        """
        Retry failed unit creation.

        This will reset the unit to in_progress status and restart the background creation process
        using the original parameters.
        """
        # Get the existing unit
        unit = await self.content.get_unit(unit_id)
        if not unit:
            return None

        # Only allow retry for failed units
        if unit.status != UnitStatus.FAILED.value:
            raise ValueError(f"Unit {unit_id} is not in failed state (current: {unit.status})")

        # Ensure we have the necessary data for retry
        if not unit.generated_from_topic:
            raise ValueError(f"Unit {unit_id} was not generated from a topic and cannot be retried")

        # Reset the unit status to in_progress
        await self.content.update_unit_status(unit_id=unit_id, status=UnitStatus.IN_PROGRESS.value, error_message=None, creation_progress={"stage": "retrying", "message": "Retrying unit creation..."})

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

    async def dismiss_unit(self, unit_id: str) -> bool:
        """
        Dismiss (delete) a unit.

        This will permanently remove the unit from the database.
        Returns True if successful, False if unit not found.
        """
        # Check if unit exists
        unit = await self.content.get_unit(unit_id)
        if not unit:
            return False

        # Delete the unit
        # Note: We need to add a delete method to content service
        # For now we'll update the status to indicate dismissal
        try:
            # Try to delete via repo if available
            success = await self.content.delete_unit(unit_id)
            logger.info(f"✅ Unit dismissed: unit_id={unit_id}")
            return success
        except AttributeError:
            # Fallback: mark as dismissed in status if delete method doesn't exist yet
            logger.warning(f"Delete method not available, marking unit as dismissed: unit_id={unit_id}")
            result = await self.content.update_unit_status(unit_id=unit_id, status="dismissed", error_message=None, creation_progress={"stage": "dismissed", "message": "Unit dismissed by user"})
            return result is not None
