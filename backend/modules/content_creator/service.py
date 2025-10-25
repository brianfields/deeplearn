"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

import asyncio
from datetime import UTC, datetime, timedelta
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
from modules.content.public import ContentProvider, LessonCreate, UnitCreate, UnitRead, UnitStatus, content_provider
from modules.infrastructure.public import infrastructure_provider
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
        unit_title: str | None = None,
    ) -> "ContentCreatorService.UnitCreationResult | ContentCreatorService.MobileUnitCreationResult":
        """Create a learning unit (foreground or background).

        Args:
            topic: Topic/description for the unit. Can be detailed text from learning coach.
            source_material: Optional pre-provided material. If None, it will be generated.
            background: If True, enqueue and return immediately with in_progress status.
            target_lesson_count: Optional target number of lessons.
            learner_level: Difficulty level.
            user_id: Optional user identifier.
            unit_title: Optional short title (from learning coach). If None, will use topic or flow-generated title.
        """
        # Pre-create the shell unit for both paths
        # Use provided title or truncate topic for provisional title (will be replaced by proper title from flow if not provided)
        provisional_title = unit_title if unit_title else (topic[:200] + "..." if len(topic) > 200 else topic)
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
            task_result = await task_queue_service.submit_flow_task(
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
            await self.content.set_unit_task(unit.id, task_result.task_id)
            return self.MobileUnitCreationResult(unit_id=unit.id, title=unit.title, status=UnitStatus.IN_PROGRESS.value)

        # Foreground execution
        return await self._execute_unit_creation_pipeline(
            unit_id=unit.id,
            topic=topic,
            source_material=source_material,
            target_lesson_count=target_lesson_count,
            learner_level=learner_level,
            arq_task_id=None,
        )

    async def _create_single_lesson(
        self,
        *,
        lesson_plan: dict[str, Any],
        lesson_index: int,
        unit_los: dict[str, str],
        unit_material: str,
        learner_level: str,
        arq_task_id: str | None,
    ) -> tuple[str, PodcastLesson, str]:
        """
        Create a single lesson and return (lesson_id, podcast_lesson, voice).

        This method is designed to be called in parallel for multiple lessons.
        Each invocation uses its own database session to avoid serialization.
        """
        lesson_title = lesson_plan.get("title") or f"Lesson {lesson_index + 1}"
        lesson_lo_ids: list[str] = list(lesson_plan.get("learning_objectives", []) or [])
        lesson_lo_texts: list[str] = [unit_los.get(lid, lid) for lid in lesson_lo_ids]
        lesson_objective_text: str = lesson_plan.get("lesson_objective", "")

        logger.info(f"📝 Creating lesson {lesson_index + 1}: {lesson_title}")

        # Execute flow (creates its own session internally)
        md_res = await LessonCreationFlow().execute(
            {
                "topic": lesson_title,
                "learner_level": learner_level,
                "voice": "Plain",
                "learning_objectives": lesson_lo_texts,
                "lesson_objective": lesson_objective_text,
                "unit_source_material": unit_material,
            },
            arq_task_id=arq_task_id,
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
        podcast_voice_label = str(md_res.get("voice") or "Plain")
        podcast_lesson = PodcastLesson(title=lesson_title, mini_lesson=mini_lesson_text)

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

        # Use a fresh async session for this parallel task to avoid serialization
        infra = infrastructure_provider()
        infra.initialize()
        async with infra.get_async_session_context() as session:
            content = content_provider(session)
            created_lesson = await content.save_lesson(
                LessonCreate(
                    id=db_lesson_id,
                    title=lesson_title,
                    learner_level=learner_level,
                    package=lesson_package,
                )
            )

        logger.info(f"✅ Completed lesson {lesson_index + 1}: {lesson_title}")
        return (created_lesson.id, podcast_lesson, podcast_voice_label)

    async def _execute_unit_creation_pipeline(
        self,
        *,
        unit_id: str,
        topic: str,
        source_material: str | None,
        target_lesson_count: int | None,
        learner_level: str,
        arq_task_id: str | None = None,
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
            },
            arq_task_id=arq_task_id,
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

        # Create lessons in parallel with batching to avoid overwhelming the system
        logger.info(f"🚀 Creating {len(lessons_plan)} lessons in parallel (batch size: {MAX_PARALLEL_LESSONS})")

        for batch_start in range(0, len(lessons_plan), MAX_PARALLEL_LESSONS):
            batch_end = min(batch_start + MAX_PARALLEL_LESSONS, len(lessons_plan))
            batch = lessons_plan[batch_start:batch_end]

            logger.info(f"📦 Processing batch {batch_start // MAX_PARALLEL_LESSONS + 1}: lessons {batch_start + 1}-{batch_end}")

            # Create tasks for parallel execution
            tasks = [
                self._create_single_lesson(
                    lesson_plan=lp,
                    lesson_index=i,
                    unit_los=unit_los,
                    unit_material=unit_material,
                    learner_level=learner_level,
                    arq_task_id=arq_task_id,
                )
                for i, lp in enumerate(batch, start=batch_start)
            ]

            # Execute batch in parallel with error handling
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(batch_results):
                lesson_num = batch_start + i + 1
                if isinstance(result, Exception):
                    logger.error(f"❌ Failed to create lesson {lesson_num}: {result}", exc_info=result)
                    # Continue with other lessons - don't let one failure stop the whole unit
                    continue

                # Type narrowing: result is a tuple here, not an Exception
                lesson_id, podcast_lesson, voice = result  # type: ignore[misc]
                lesson_ids.append(lesson_id)
                podcast_lessons.append(podcast_lesson)
                if podcast_voice_label is None:
                    podcast_voice_label = voice

            # Update progress after each batch
            progress_pct = (batch_end / len(lessons_plan)) * 100
            await self.content.update_unit_status(unit_id, UnitStatus.IN_PROGRESS.value, creation_progress={"stage": "generating", "message": f"Generated {len(lesson_ids)}/{len(lessons_plan)} lessons ({progress_pct:.0f}%)..."})

        logger.info(f"✅ Completed {len(lesson_ids)}/{len(lessons_plan)} lessons")

        # Associate lessons and complete
        if lesson_ids:
            await self.content.assign_lessons_to_unit(unit_id, lesson_ids)

        # Generate podcast and art in parallel (both are independent post-processing tasks)
        async def _generate_podcast() -> None:
            """Generate podcast for the unit."""
            if not podcast_lessons:
                return

            generator = self.podcast_generator or UnitPodcastGenerator()
            # Cache the generator for future use to avoid repeated initialization
            self.podcast_generator = generator
            try:
                logger.info("🎧 Generating unit podcast...")
                summary_text = self._summarize_unit_plan(unit_plan, lessons_plan)
                podcast = await generator.create_podcast(
                    unit_title=final_title,
                    voice_label=podcast_voice_label or "Plain",
                    unit_summary=summary_text,
                    lessons=podcast_lessons,
                )
                if podcast.audio_bytes:
                    await self.content.save_unit_podcast_from_bytes(
                        unit_id,
                        transcript=podcast.transcript,
                        audio_bytes=podcast.audio_bytes,
                        mime_type=podcast.mime_type,
                        voice=podcast.voice,
                    )
                    logger.info("✅ Podcast generation completed")
            except Exception as exc:  # pragma: no cover - podcast generation should not block unit creation
                logger.warning("🎧 Failed to generate podcast for unit %s: %s", unit_id, exc, exc_info=True)

        async def _generate_art() -> None:
            """Generate artwork for the unit."""
            try:
                logger.info("🖼️ Generating unit artwork...")
                await self.content.update_unit_status(
                    unit_id,
                    UnitStatus.IN_PROGRESS.value,
                    creation_progress={"stage": "artwork", "message": "Rendering hero artwork..."},
                )
                await self.create_unit_art(unit_id)
                logger.info("✅ Artwork generation completed")
            except Exception as exc:  # pragma: no cover - art generation should not block unit creation
                logger.warning("🖼️ Failed to generate unit art for %s: %s", unit_id, exc, exc_info=True)

        # Run both post-processing tasks in parallel
        logger.info("🎨 Starting post-processing (podcast + artwork)...")
        await asyncio.gather(
            _generate_podcast(),
            _generate_art(),
            return_exceptions=True,  # Don't let failures block completion
        )

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
        task_result = await task_queue_service.submit_flow_task(
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

        await self.content.set_unit_task(unit_id, task_result.task_id)

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

    async def check_and_timeout_stale_units(self, timeout_seconds: int = 3600) -> int:
        """
        Check for units stuck in 'in_progress' status and mark them as failed if they've timed out.

        This method:
        1. Finds all units with status='in_progress'
        2. Checks if their associated task has failed or doesn't exist
        3. Checks if the unit has been in_progress for longer than timeout_seconds
        4. Marks timed-out units as failed

        Args:
            timeout_seconds: Maximum time a unit can be in_progress (default: 1 hour)

        Returns:
            Number of units that were marked as failed
        """
        logger.info("🔍 Checking for stale in_progress units (timeout: %s seconds)", timeout_seconds)

        # Get all units with in_progress status
        in_progress_units = await self.content.get_units_by_status(UnitStatus.IN_PROGRESS.value, limit=1000)

        if not in_progress_units:
            logger.debug("No in_progress units found")
            return 0

        timeout_threshold = datetime.now(UTC) - timedelta(seconds=timeout_seconds)
        timed_out_count = 0
        task_queue_service = task_queue_provider()

        for unit in in_progress_units:
            try:
                # Check if unit has been in_progress too long
                # Use updated_at as the reference time (when it was last updated)
                unit_age = datetime.now(UTC) - unit.updated_at.replace(tzinfo=UTC)

                # Check task status if we have an arq_task_id
                task_failed = False
                if unit.arq_task_id:
                    task_status = await task_queue_service.get_task_status(unit.arq_task_id)
                    if task_status:
                        if task_status.status == "failed":
                            task_failed = True
                            logger.warning("Unit %s has failed task %s", unit.id, unit.arq_task_id)
                    else:
                        # Task doesn't exist in Redis anymore, likely expired
                        logger.warning("Unit %s has non-existent task %s", unit.id, unit.arq_task_id)
                        if unit_age.total_seconds() > 300:  # Only fail if it's been > 5 minutes
                            task_failed = True

                # Mark as failed if task failed or unit is too old
                should_timeout = task_failed or (unit.updated_at.replace(tzinfo=UTC) < timeout_threshold)

                if should_timeout:
                    error_reason = "Associated task failed" if task_failed else f"Unit creation exceeded timeout ({timeout_seconds} seconds)"
                    logger.warning("⏰ Timing out unit %s: %s (age: %s seconds)", unit.id, error_reason, unit_age.total_seconds())

                    await self.content.update_unit_status(
                        unit_id=unit.id,
                        status=UnitStatus.FAILED.value,
                        error_message=f"Creation timed out: {error_reason}",
                        creation_progress={"stage": "failed", "message": "Creation timed out"},
                    )
                    timed_out_count += 1

            except Exception as e:
                logger.error("Error checking unit %s: %s", unit.id, str(e), exc_info=True)
                continue

        if timed_out_count > 0:
            logger.info("✅ Marked %s stale unit(s) as failed", timed_out_count)
        else:
            logger.debug("No stale units found")

        return timed_out_count
