"""Flow orchestration helpers for the content creator service."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
import uuid

from modules.content.package_models import (
    GlossaryTerm,
    LessonPackage,
    MCQAnswerKey,
    MCQExercise,
    MCQOption,
    Meta,
    ShortAnswerExercise,
    WrongAnswer,
)
from modules.content.public import ContentProvider, LessonCreate, UnitStatus, content_provider
from modules.infrastructure.public import infrastructure_provider

from ..flows import LessonCreationFlow, UnitCreationFlow
from ..podcast import PodcastLesson
from ..steps import UnitLearningObjective
from .dtos import UnitCreationResult
from .media_handler import MediaHandler
from .prompt_handler import PromptHandler

logger = logging.getLogger(__name__)

MAX_PARALLEL_LESSONS = 4


class FlowHandler:
    """Execute the long-running generation flows for the content creator module."""

    def __init__(
        self,
        content: ContentProvider,
        prompt_handler: PromptHandler,
        media_handler: MediaHandler,
    ) -> None:
        self._content = content
        self._prompt_handler = prompt_handler
        self._media_handler = media_handler

    async def execute_unit_creation_pipeline(
        self,
        *,
        unit_id: str,
        topic: str,
        source_material: str | None,
        target_lesson_count: int | None,
        learner_level: str,
        arq_task_id: str | None = None,
    ) -> UnitCreationResult:
        """Execute the end-to-end unit creation using the active prompt-aligned flows."""

        logger.info("=" * 80)
        logger.info("🧱 UNIT CREATION START")
        logger.info(f"   Unit ID: {unit_id}")
        logger.info(f"   Topic: {topic}")
        logger.info(f"   Level: {learner_level}")
        logger.info(f"   Target Lessons: {target_lesson_count or 'auto'}")
        logger.info(f"   Source Material: {'provided' if source_material else 'will generate'}")
        logger.info("=" * 80)

        await self._content.update_unit_status(
            unit_id,
            UnitStatus.IN_PROGRESS.value,
            creation_progress={"stage": "planning", "message": "Planning unit structure..."},
        )
        await self._content.commit_session()

        logger.info("📋 Phase 1: Unit Planning")
        flow = UnitCreationFlow()
        unit_plan = await flow.execute(
            {
                "topic": topic,
                "source_material": source_material,
                "target_lesson_count": target_lesson_count,
                "learner_level": learner_level,
            },
            arq_task_id=arq_task_id,
        )

        final_title = str(unit_plan.get("unit_title") or f"{topic}")
        logger.info(f"   ✓ Unit title: {final_title}")
        raw_unit_learning_objectives = unit_plan.get("learning_objectives", []) or []
        unit_learning_objectives: list[UnitLearningObjective] = []
        for item in raw_unit_learning_objectives:
            if isinstance(item, UnitLearningObjective):
                unit_learning_objectives.append(item)
            elif isinstance(item, dict):
                payload = dict(item)
                raw_id = payload.get("id") or payload.get("lo_id")
                inferred_title = payload.get("title") or payload.get("short_title")
                if inferred_title is None:
                    inferred_title = payload.get("description") or raw_id or f"lo_{len(unit_learning_objectives) + 1}"
                description = payload.get("description") or inferred_title
                payload.setdefault("id", str(raw_id or f"lo_{len(unit_learning_objectives) + 1}"))
                payload["title"] = str(inferred_title)
                payload["description"] = str(description)
                unit_learning_objectives.append(UnitLearningObjective.model_validate(payload))
            else:
                text_value = str(item)
                unit_learning_objectives.append(UnitLearningObjective(id=str(item), title=text_value, description=text_value))

        await self._content.update_unit_metadata(
            unit_id,
            title=final_title,
            learning_objectives=unit_learning_objectives,
        )
        logger.info(f"   ✓ Learning objectives: {len(unit_learning_objectives)}")

        await self._content.update_unit_status(
            unit_id,
            UnitStatus.IN_PROGRESS.value,
            creation_progress={"stage": "generating", "message": "Generating lessons..."},
        )
        await self._content.commit_session()

        unit_los: dict[str, str] = {lo.id: lo.description for lo in unit_learning_objectives}

        lesson_ids: list[str] = []
        podcast_lessons: list[PodcastLesson] = []
        podcast_voice_label: str | None = None
        unit_material: str = str(unit_plan.get("source_material") or source_material or "")
        lessons_plan = unit_plan.get("lessons", []) or []
        covered_lo_ids: set[str] = set()
        failed_lessons: list[dict[str, Any]] = []

        logger.info("")
        logger.info(f"📚 Phase 2: Lesson Generation ({len(lessons_plan)} lessons)")
        logger.info(f"   Batch size: {MAX_PARALLEL_LESSONS}")
        logger.info("")

        for batch_start in range(0, len(lessons_plan), MAX_PARALLEL_LESSONS):
            batch_end = min(batch_start + MAX_PARALLEL_LESSONS, len(lessons_plan))
            batch = lessons_plan[batch_start:batch_end]

            batch_num = (batch_start // MAX_PARALLEL_LESSONS) + 1
            total_batches = (len(lessons_plan) + MAX_PARALLEL_LESSONS - 1) // MAX_PARALLEL_LESSONS
            logger.info(f"   📦 Batch {batch_num}/{total_batches}: Processing lessons {batch_start + 1}-{batch_end}")

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

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(batch_results):
                lesson_num = batch_start + i + 1
                lesson_plan_item = batch[i]
                lesson_title = lesson_plan_item.get("title") or f"Lesson {lesson_num}"

                if isinstance(result, Exception):
                    error_msg = str(result)
                    error_type = type(result).__name__
                    logger.error("❌ Failed to create lesson %s: %s", lesson_num, result, exc_info=result)
                    failed_lessons.append(
                        {
                            "lesson_number": lesson_num,
                            "lesson_title": lesson_title,
                            "error_type": error_type,
                            "error_message": error_msg,
                        }
                    )
                    continue

                lesson_id, podcast_lesson, podcast_voice, lesson_covered_los = result
                lesson_ids.append(lesson_id)
                podcast_lessons.append(podcast_lesson)
                if podcast_voice_label is None:
                    podcast_voice_label = podcast_voice
                covered_lo_ids.update(lesson_covered_los)

            progress_pct = (batch_end / max(len(lessons_plan), 1)) * 100
            logger.info(f"      ✓ Batch complete: {len(lesson_ids)}/{len(lessons_plan)} lessons ({progress_pct:.0f}%)")
            if failed_lessons:
                logger.warning(f"      ⚠️  {len(failed_lessons)} lesson(s) failed in this unit")

            progress_msg = f"Generated {len(lesson_ids)}/{len(lessons_plan)} lessons"
            if failed_lessons:
                progress_msg += f" ({len(failed_lessons)} failed)"
            progress_msg += f" ({progress_pct:.0f}%)..."

            await self._content.update_unit_status(
                unit_id,
                UnitStatus.IN_PROGRESS.value,
                creation_progress={
                    "stage": "generating",
                    "message": progress_msg,
                    "lesson_failures": failed_lessons if failed_lessons else None,
                },
            )
            await self._content.commit_session()

        logger.info("")
        logger.info(f"✅ Lesson generation complete: {len(lesson_ids)}/{len(lessons_plan)} succeeded")
        if failed_lessons:
            logger.warning(
                "⚠️ Unit %s completed with %s lesson failure(s)",
                unit_id,
                len(failed_lessons),
            )

        if unit_learning_objectives and lesson_ids:
            filtered_learning_objectives = [lo for lo in unit_learning_objectives if lo.id in covered_lo_ids]
            if len(filtered_learning_objectives) != len(unit_learning_objectives):
                unit_learning_objectives = filtered_learning_objectives
                await self._content.update_unit_metadata(
                    unit_id,
                    learning_objectives=filtered_learning_objectives,
                )

        if lesson_ids:
            await self._content.assign_lessons_to_unit(unit_id, lesson_ids)

        summary_text = self._prompt_handler.summarize_unit_plan(unit_plan, lessons_plan)

        logger.info("")
        logger.info("🎨 Phase 3: Media Generation")

        async def _generate_podcast() -> None:
            if not podcast_lessons:
                return
            try:
                logger.info("   🎧 Generating unit intro podcast...")
                podcast = await self._media_handler.generate_unit_podcast(
                    unit_title=final_title,
                    voice_label=podcast_voice_label or "Plain",
                    unit_summary=summary_text,
                    lessons=podcast_lessons,
                    arq_task_id=arq_task_id,
                )
                await self._media_handler.save_unit_podcast(unit_id, podcast)
                logger.info("   ✓ Unit podcast complete")
            except Exception as exc:  # pragma: no cover - podcast generation should not block unit creation
                logger.warning(
                    "   ⚠️ Failed to generate unit podcast: %s",
                    str(exc)[:100],
                )

        async def _generate_art() -> None:
            try:
                logger.info("   🖼️ Generating unit artwork...")
                await self._content.update_unit_status(
                    unit_id,
                    UnitStatus.IN_PROGRESS.value,
                    creation_progress={"stage": "artwork", "message": "Rendering hero artwork..."},
                )
                await self._content.commit_session()
                await self._media_handler.create_unit_art(unit_id, arq_task_id=arq_task_id)
                logger.info("   ✓ Unit artwork complete")
            except Exception as exc:  # pragma: no cover - art generation should not block unit creation
                logger.warning(
                    "   ⚠️ Failed to generate unit artwork: %s",
                    str(exc)[:100],
                )

        await asyncio.gather(_generate_podcast(), _generate_art(), return_exceptions=True)

        completion_message = "Unit creation completed"
        if failed_lessons:
            completion_message += f" with {len(failed_lessons)} lesson failure(s)"

        await self._content.update_unit_status(
            unit_id,
            UnitStatus.COMPLETED.value,
            creation_progress={
                "stage": "completed",
                "message": completion_message,
                "lesson_failures": failed_lessons if failed_lessons else None,
            },
        )

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ UNIT CREATION COMPLETE")
        logger.info(f"   Unit ID: {unit_id}")
        logger.info(f"   Title: {final_title}")
        logger.info(f"   Lessons: {len(lesson_ids)}/{len(lessons_plan)}")
        if failed_lessons:
            logger.warning(f"   ⚠️  Failures: {len(failed_lessons)}")
        logger.info("=" * 80)

        return UnitCreationResult(
            unit_id=unit_id,
            title=final_title,
            lesson_titles=[lp.get("title", "") for lp in lessons_plan],
            lesson_count=len(lesson_ids),
            target_lesson_count=unit_plan.get("lesson_count"),
            generated_from_topic=(source_material is None),
            lesson_ids=lesson_ids,
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
    ) -> tuple[str, PodcastLesson, str, set[str]]:
        """Create a single lesson and return (lesson_id, podcast_lesson, voice, covered_lo_ids)."""

        lesson_title = lesson_plan.get("title") or f"Lesson {lesson_index + 1}"
        lesson_lo_ids: list[str] = list(lesson_plan.get("learning_objective_ids", []) or [])
        lesson_lo_descriptions: list[str] = [unit_los.get(lid, lid) for lid in lesson_lo_ids]
        lesson_objective_text: str = lesson_plan.get("lesson_objective", "")

        logger.info(f"      📝 Lesson {lesson_index + 1}: {lesson_title[:60]}{'...' if len(lesson_title) > 60 else ''}")

        md_res = await LessonCreationFlow().execute(
            {
                "topic": lesson_title,
                "learner_level": learner_level,
                "voice": "Plain",
                "learning_objectives": lesson_lo_descriptions,
                "learning_objective_ids": lesson_lo_ids,
                "lesson_objective": lesson_objective_text,
                "source_material": unit_material,
            },
            arq_task_id=arq_task_id,
        )

        db_lesson_id = str(uuid.uuid4())
        meta = Meta(
            lesson_id=db_lesson_id,
            title=lesson_title,
            learner_level=learner_level,
            package_schema_version=1,
            content_version=1,
        )

        glossary_terms: list[GlossaryTerm] = []
        for k, term in enumerate(md_res.get("glossary", []) or []):
            glossary_terms.append(
                GlossaryTerm(
                    id=f"term_{k + 1}",
                    term=term.get("term", f"Term {k + 1}"),
                    definition=term.get("definition", ""),
                )
            )
        glossary = {"terms": glossary_terms}

        mini_lesson_text = str(md_res.get("mini_lesson") or "")
        podcast_lesson, lesson_podcast_result = await self._media_handler.generate_lesson_podcast(
            lesson_index=lesson_index,
            lesson_title=lesson_title,
            lesson_objective=lesson_objective_text,
            mini_lesson=mini_lesson_text,
            voice_label=str(md_res.get("voice") or "Plain"),
            arq_task_id=arq_task_id,
        )

        exercises: list[MCQExercise | ShortAnswerExercise] = []
        for idx, mcq in enumerate(md_res.get("mcqs", []) or []):
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

            lo_candidates = mcq.get("learning_objectives_covered", []) or []
            valid_lo_id: str | None = None

            for candidate_lo in lo_candidates:
                candidate_str = str(candidate_lo)
                if candidate_str in lesson_lo_ids:
                    valid_lo_id = candidate_str
                    break

            if valid_lo_id is None:
                if lesson_lo_ids:
                    valid_lo_id = lesson_lo_ids[0]
                    logger.warning(
                        "MCQ %s in lesson %s referenced invalid LO IDs %s, falling back to %s",
                        exercise_id,
                        lesson_index + 1,
                        lo_candidates,
                        valid_lo_id,
                    )
                else:
                    valid_lo_id = "lo_1"
                    logger.error(
                        "MCQ %s in lesson %s has no valid LO IDs, using fallback 'lo_1'",
                        exercise_id,
                        lesson_index + 1,
                    )

            exercises.append(
                MCQExercise(
                    id=exercise_id,
                    exercise_type="mcq",
                    lo_id=valid_lo_id,
                    cognitive_level=None,
                    estimated_difficulty=None,
                    misconceptions_used=mcq.get("misconceptions_used", []),
                    stem=mcq.get("stem", ""),
                    options=options_with_ids,
                    answer_key=answer_key,
                )
            )

        short_answers = md_res.get("short_answers", []) or []
        for idx, sa in enumerate(short_answers):
            exercise_id = f"sa_{idx + 1}"

            lo_candidates = sa.get("learning_objectives_covered", []) or []
            sa_lo_id: str | None = None
            for candidate_lo in lo_candidates:
                candidate_str = str(candidate_lo)
                if candidate_str in lesson_lo_ids:
                    sa_lo_id = candidate_str
                    break

            if sa_lo_id is None:
                if lesson_lo_ids:
                    sa_lo_id = lesson_lo_ids[0]
                    logger.warning(
                        "Short answer %s in lesson %s referenced invalid LO IDs %s, falling back to %s",
                        exercise_id,
                        lesson_index + 1,
                        lo_candidates,
                        sa_lo_id,
                    )
                else:
                    sa_lo_id = "lo_1"
                    logger.error(
                        "Short answer %s in lesson %s has no valid LO IDs, using fallback 'lo_1'",
                        exercise_id,
                        lesson_index + 1,
                    )

            wrong_answers: list[WrongAnswer] = []
            for wrong in sa.get("wrong_answers", []) or []:
                wrong_answers.append(
                    WrongAnswer(
                        answer=wrong.get("answer", ""),
                        explanation=wrong.get("explanation", ""),
                        misconception_ids=list(wrong.get("misconception_ids", []) or []),
                    )
                )

            exercises.append(
                ShortAnswerExercise(
                    id=exercise_id,
                    lo_id=sa_lo_id,
                    cognitive_level=sa.get("cognitive_level"),
                    estimated_difficulty=None,
                    misconceptions_used=list(sa.get("misconceptions_used", []) or []),
                    stem=sa.get("stem", ""),
                    canonical_answer=sa.get("canonical_answer", ""),
                    acceptable_answers=list(sa.get("acceptable_answers", []) or []),
                    wrong_answers=wrong_answers,
                    explanation_correct=sa.get("explanation_correct", ""),
                )
            )

        lesson_package = LessonPackage(
            meta=meta,
            unit_learning_objective_ids=lesson_lo_ids,
            glossary=glossary,
            mini_lesson=mini_lesson_text,
            exercises=exercises,
            misconceptions=md_res.get("misconceptions", []),
            confusables=md_res.get("confusables", []),
        )

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
            await self._media_handler.save_lesson_podcast(content, created_lesson.id, lesson_podcast_result)

        covered_lo_ids = {str(exercise.lo_id) for exercise in exercises if getattr(exercise, "lo_id", None)}

        logger.debug(f"         ✓ Lesson {lesson_index + 1} complete - {len(exercises)} exercises, {len(covered_lo_ids)} LOs covered")
        return created_lesson.id, podcast_lesson, lesson_podcast_result.voice, covered_lo_ids
