"""Flow orchestration helpers for the content creator service."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, cast
import uuid

from pydantic import ValidationError

from modules.content.package_models import (
    Exercise,
    ExerciseAnswerKey,
    ExerciseOption,
    LessonPackage,
    Meta,
    QuizCoverageByLO,
    QuizMetadata,
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
        learner_desires: str,
        learning_objectives: list,
        target_lesson_count: int | None,
        source_material: str | None = None,
        arq_task_id: str | None = None,
    ) -> UnitCreationResult:
        """Execute the end-to-end unit creation pipeline.

        All parameters are required because the learning coach must finalize them
        before unit creation is allowed.
        """

        logger.info("=" * 80)
        logger.info("🧱 UNIT CREATION START")
        logger.info(f"   Unit ID: {unit_id}")
        logger.info(f"   Learner Desires: {learner_desires[:50]}...")
        logger.info(f"   Learning Objectives PARAM: {learning_objectives}")
        logger.info(f"   Learning Objectives COUNT: {len(learning_objectives) if learning_objectives else 0}")
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

        # Build flow inputs with coach-provided context
        # Handle both UnitLearningObjective objects and dicts
        coach_los = []
        for lo in learning_objectives or []:
            if isinstance(lo, dict):
                coach_los.append(lo)
            else:
                coach_los.append(lo.model_dump())

        # Store original coach LOs for fallback
        original_coach_los = coach_los.copy()

        flow_inputs: dict[str, Any] = {
            "learner_desires": learner_desires,
            "coach_learning_objectives": coach_los,
            "source_material": source_material,
            "target_lesson_count": target_lesson_count,
        }

        unit_plan = await flow.execute(flow_inputs, arq_task_id=arq_task_id)

        final_title = str(unit_plan.get("unit_title") or "Unit")
        logger.info(f"   ✓ Unit title: {final_title}")
        # Always use original coach LOs (flow should return them but we use originals as source of truth)
        raw_unit_learning_objectives = original_coach_los if original_coach_los else (unit_plan.get("learning_objectives") or [])
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
                unit_learning_objectives.append(UnitLearningObjective.model_validate({"id": str(item), "title": text_value, "description": text_value}))

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

        unit_los: dict[str, dict[str, Any]] = {lo.id: {"id": lo.id, "title": lo.title, "description": lo.description} for lo in unit_learning_objectives}

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
                self._create_single_lesson_with_retry(
                    lesson_plan=lp,
                    lesson_index=i,
                    unit_los=unit_los,
                    unit_material=unit_material,
                    learner_desires=learner_desires,
                    lessons_plan=lessons_plan,
                    arq_task_id=arq_task_id,
                    max_retries=3,
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

                # Type narrowing: result is now tuple[str, PodcastLesson, str, list[str]]
                lesson_id, podcast_lesson, podcast_voice, lesson_covered_los = cast(tuple[str, PodcastLesson, str, list[str]], result)
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
                    learner_desires=learner_desires,
                    unit_title=final_title,
                    voice_label=podcast_voice_label or "Plain",
                    unit_summary=summary_text,
                    lessons=podcast_lessons,
                    arq_task_id=arq_task_id,
                )
                # Delegate intro lesson creation to content service via media handler
                await self._media_handler.save_unit_podcast(unit_id, podcast)
                logger.info("   ✓ Unit podcast + intro lesson complete")
            except Exception as exc:  # pragma: no cover - podcast generation should not block unit creation
                logger.warning(
                    "   ⚠️ Failed to generate unit podcast/intro lesson: %s",
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
        final_status = UnitStatus.COMPLETED.value

        if failed_lessons:
            completion_message += f" with {len(failed_lessons)} lesson failure(s)"
            # Mark as partial if some but not all lessons failed
            if len(lesson_ids) > 0:
                final_status = UnitStatus.PARTIAL.value
                logger.warning(
                    "⚠️  Unit %s marked as 'partial' - %s/%s lessons succeeded",
                    unit_id,
                    len(lesson_ids),
                    len(lessons_plan),
                )
            else:
                # All lessons failed
                final_status = UnitStatus.FAILED.value
                completion_message = "Unit creation failed - all lessons failed"

        await self._content.update_unit_status(
            unit_id,
            final_status,
            creation_progress={
                "stage": "completed" if final_status == UnitStatus.COMPLETED.value else "partial" if final_status == UnitStatus.PARTIAL.value else "failed",
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
            learning_objectives=cast(list[dict[str, Any]], [lo.model_dump() for lo in unit_learning_objectives]),
            lessons=lessons_plan,
        )

    async def _create_single_lesson_with_retry(
        self,
        *,
        lesson_plan: dict[str, Any],
        lesson_index: int,
        unit_los: dict[str, dict[str, Any]],
        unit_material: str,
        learner_desires: str,
        lessons_plan: list[dict],
        arq_task_id: str | None = None,
        max_retries: int = 3,
    ) -> tuple[str, PodcastLesson, str, list[str]]:
        """Wrapper for _create_single_lesson with retry logic for validation errors."""
        lesson_num = lesson_index + 1
        lesson_title = lesson_plan.get("title") or f"Lesson {lesson_num}"

        for attempt in range(1, max_retries + 1):
            try:
                return await self._create_single_lesson(
                    lesson_plan=lesson_plan,
                    lesson_index=lesson_index,
                    unit_los=unit_los,
                    unit_material=unit_material,
                    learner_desires=learner_desires,
                    lessons_plan=lessons_plan,
                    arq_task_id=arq_task_id,
                )
            except ValidationError as exc:
                # Extract validation error details for logging
                error_details = []
                for error in exc.errors():
                    error_details.append(f"{error['loc']}: {error['msg']}")
                error_summary = "; ".join(error_details)

                if attempt < max_retries:
                    logger.warning(
                        "⚠️  Validation error in lesson %s (attempt %s/%s): %s. Retrying...",
                        lesson_num,
                        attempt,
                        max_retries,
                        error_summary,
                    )
                    # Add a small delay before retrying
                    await asyncio.sleep(1.0)
                else:
                    logger.error(
                        "❌ Validation error in lesson %s after %s attempts: %s",
                        lesson_num,
                        max_retries,
                        error_summary,
                    )
                    raise ValueError(f"Lesson {lesson_num} ({lesson_title}) failed validation after {max_retries} attempts: {error_summary}") from exc
            except Exception as exc:
                # For non-validation errors, don't retry - fail immediately
                logger.error(
                    "❌ Non-validation error in lesson %s: %s",
                    lesson_num,
                    exc,
                    exc_info=True,
                )
                raise

        # Should never reach here, but satisfy type checker
        raise RuntimeError(f"Lesson {lesson_num} ({lesson_title}) creation failed unexpectedly")

    async def _create_single_lesson(
        self,
        *,
        lesson_plan: dict[str, Any],
        lesson_index: int,
        unit_los: dict[str, dict[str, Any]],
        unit_material: str,
        learner_desires: str,
        lessons_plan: list[dict[str, Any]],
        arq_task_id: str | None,
    ) -> tuple[str, PodcastLesson, str, list[str]]:
        """Create a single lesson and return (lesson_id, podcast_lesson, voice, covered_lo_ids)."""

        lesson_title = lesson_plan.get("title") or f"Lesson {lesson_index + 1}"
        lesson_lo_ids: list[str] = list(lesson_plan.get("learning_objective_ids", []) or [])

        # Build lesson LO objects — require that all LO IDs exist in unit_los
        lesson_lo_objects: list[dict] = []
        missing_los = [lid for lid in lesson_lo_ids if lid not in unit_los]
        if missing_los:
            raise ValueError(
                f"Lesson {lesson_index + 1} ({lesson_title}) references learning objectives "
                f"{missing_los} that are not defined in the unit. "
                f"Available LOs: {list(unit_los.keys())}. "
                f"This indicates a mismatch between lesson plan and unit learning objectives."
            )

        for lid in lesson_lo_ids:
            lesson_lo_objects.append(unit_los[lid])

        lesson_objective_text: str = lesson_plan.get("lesson_objective", "")

        logger.info(f"      📝 Lesson {lesson_index + 1}: {lesson_title[:60]}{'...' if len(lesson_title) > 60 else ''}")

        sibling_context = [
            {
                "title": str(item.get("title", "")),
                "lesson_objective": str(item.get("lesson_objective", "")),
            }
            for item in lessons_plan
            if item is not lesson_plan
        ]

        md_res = await LessonCreationFlow().execute(
            {
                "learner_desires": learner_desires,
                "learning_objectives": lesson_lo_objects,
                "learning_objective_ids": lesson_lo_ids,
                "lesson_objective": lesson_objective_text,
                "source_material": unit_material,
                "lesson_title": lesson_title,
                "lesson_number": lesson_index + 1,
                "sibling_lessons": sibling_context,
            },
            arq_task_id=arq_task_id,
        )

        def _normalize_exercise_type(raw_type: str | None) -> str:
            value = (raw_type or "mcq").strip().lower().replace("_", "-")
            return "mcq" if value != "short-answer" else "short_answer"

        def _normalize_category(raw_category: str | None) -> str:
            value = (raw_category or "comprehension").strip().lower()
            return value if value in {"comprehension", "transfer"} else "comprehension"

        db_lesson_id = str(uuid.uuid4())
        # Extract learner level from learner_desires or use value from flow response
        extracted_learner_level = "intermediate"
        meta = Meta(
            lesson_id=db_lesson_id,
            title=lesson_title,
            learner_level=extracted_learner_level,
            package_schema_version=2,
            content_version=1,
        )

        podcast_transcript = str(md_res.get("podcast_transcript") or "")
        voice_label = "Plain"
        podcast_lesson, lesson_podcast_result = await self._media_handler.generate_lesson_podcast(
            learner_desires=learner_desires,
            lesson_index=lesson_index,
            lesson_title=lesson_title,
            lesson_objective=lesson_objective_text,
            voice_label=voice_label,
            podcast_transcript=podcast_transcript,
            learning_objectives=lesson_lo_objects,
            sibling_lessons=sibling_context,
            source_material=unit_material,
            arq_task_id=arq_task_id,
        )

        exercise_items = md_res.get("exercise_bank", []) or []
        exercise_bank: list[Exercise] = []
        for idx, exercise_data in enumerate(exercise_items):
            exercise_id = str(exercise_data.get("id") or f"exercise_{idx + 1}")
            exercise_type = _normalize_exercise_type(exercise_data.get("exercise_type"))
            exercise_category = _normalize_category(exercise_data.get("exercise_category"))
            aligned_lo = str(exercise_data.get("aligned_learning_objective") or "")
            if aligned_lo not in lesson_lo_ids:
                if lesson_lo_ids:
                    logger.warning(
                        "Exercise %s in lesson %s referenced invalid LO '%s', defaulting to %s",
                        exercise_id,
                        lesson_index + 1,
                        aligned_lo,
                        lesson_lo_ids[0],
                    )
                    aligned_lo = lesson_lo_ids[0]
                else:
                    aligned_lo = "lo_1"
                    logger.error(
                        "Exercise %s in lesson %s has no valid LO IDs, using fallback 'lo_1'",
                        exercise_id,
                        lesson_index + 1,
                    )

            cognitive_level = str(exercise_data.get("cognitive_level") or "Comprehension")
            difficulty = str(exercise_data.get("difficulty") or "medium").lower()

            options: list[ExerciseOption] | None = None
            answer_key_obj: ExerciseAnswerKey | None = None
            if exercise_type == "mcq":
                option_id_map: dict[str, str] = {}
                options = []
                correct_option_label: str | None = None
                correct_option_id: str | None = None
                rationale_right: str | None = None

                for opt_index, opt in enumerate(exercise_data.get("options", []) or []):
                    label = str(opt.get("label") or chr(65 + opt_index)).upper()
                    option_id = f"{exercise_id}_{label.lower()}"
                    option_id_map[label] = option_id
                    is_correct = opt.get("is_correct", False)

                    # Track the correct answer
                    if is_correct:
                        correct_option_label = label
                        correct_option_id = option_id
                        rationale_right = opt.get("rationale")

                    options.append(
                        ExerciseOption(
                            id=option_id,
                            label=label,
                            text=str(opt.get("text") or ""),
                            rationale_wrong=opt.get("rationale") if not is_correct else None,
                        )
                    )

                # Build answer_key from the correct option
                if correct_option_label:
                    answer_key_obj = ExerciseAnswerKey(
                        label=correct_option_label,
                        option_id=correct_option_id,
                        rationale_right=rationale_right,
                    )
                else:
                    # Fallback: no correct answer found, default to A
                    logger.warning(
                        "Exercise %s in lesson %s has no option marked is_correct=true, defaulting to A",
                        exercise_id,
                        lesson_index + 1,
                    )
                    answer_key_obj = ExerciseAnswerKey(
                        label="A",
                        option_id=option_id_map.get("A"),
                        rationale_right=None,
                    )

            exercise_kwargs: dict[str, Any] = {
                "id": exercise_id,
                "exercise_type": exercise_type,
                "exercise_category": exercise_category,
                "aligned_learning_objective": aligned_lo,
                "cognitive_level": cognitive_level,
                "difficulty": difficulty,
                "stem": str(exercise_data.get("stem") or ""),
                "options": options,
                "answer_key": answer_key_obj,
            }

            exercise_bank.append(Exercise(**exercise_kwargs))

        quiz_ids = [str(ex_id) for ex_id in md_res.get("quiz", []) or []]
        quiz_meta_payload = md_res.get("quiz_metadata") or {}
        difficulty_keys = ["easy", "medium", "hard"]
        diff_counts: dict[str, int] = dict.fromkeys(difficulty_keys, 0)
        for exercise in exercise_bank:
            key = exercise.difficulty.lower()
            if key in diff_counts:
                diff_counts[key] += 1

        total_exercises = len(exercise_bank) or 1
        difficulty_distribution_actual = {key: diff_counts[key] / total_exercises for key in difficulty_keys}
        difficulty_distribution_target = dict(difficulty_distribution_actual)

        cognitive_keys = ["Recall", "Comprehension", "Application", "Transfer"]
        cognitive_counts: dict[str, int] = dict.fromkeys(cognitive_keys, 0)
        for exercise in exercise_bank:
            if exercise.cognitive_level in cognitive_counts:
                cognitive_counts[exercise.cognitive_level] += 1
        cognitive_mix_actual = {key: cognitive_counts[key] / total_exercises for key in cognitive_keys}
        cognitive_mix_target = dict(cognitive_mix_actual)

        coverage_by_lo: dict[str, QuizCoverageByLO] = {}
        for exercise in exercise_bank:
            lo_id = exercise.aligned_learning_objective
            coverage_entry = coverage_by_lo.setdefault(lo_id, QuizCoverageByLO())
            coverage_entry.exercise_ids.append(exercise.id)

        reasoning_note = str(quiz_meta_payload.get("reasoning") or "").strip()
        selection_rationale = [reasoning_note] if reasoning_note else []

        quiz_metadata = QuizMetadata(
            quiz_type=str(quiz_meta_payload.get("quiz_type") or "lesson_assessment"),
            total_items=int(quiz_meta_payload.get("total_items") or len(quiz_ids)),
            difficulty_distribution_target=difficulty_distribution_target,
            difficulty_distribution_actual=difficulty_distribution_actual,
            cognitive_mix_target=cognitive_mix_target,
            cognitive_mix_actual=cognitive_mix_actual,
            coverage_by_LO=coverage_by_lo,
            coverage_by_concept={},
            normalizations_applied=[],
            selection_rationale=selection_rationale,
            gaps_identified=[],
        )

        lesson_package = LessonPackage(
            meta=meta,
            unit_learning_objective_ids=lesson_lo_ids,
            exercise_bank=exercise_bank,
            quiz=quiz_ids,
            quiz_metadata=quiz_metadata,
        )

        infra = infrastructure_provider()
        infra.initialize()
        async with infra.get_async_session_context() as session:
            content = content_provider(session)
            created_lesson = await content.save_lesson(
                LessonCreate(
                    id=db_lesson_id,
                    title=lesson_title,
                    learner_level=extracted_learner_level,
                    package=lesson_package,
                )
            )
            await self._media_handler.save_lesson_podcast(content, created_lesson.id, lesson_podcast_result)

        covered_lo_ids = {str(exercise.aligned_learning_objective) for exercise in exercise_bank if getattr(exercise, "aligned_learning_objective", None)}

        logger.debug(
            "         ✓ Lesson %s complete - %s exercises, %s LOs covered",
            lesson_index + 1,
            len(exercise_bank),
            len(covered_lo_ids),
        )
        return created_lesson.id, podcast_lesson, lesson_podcast_result.voice, list(covered_lo_ids)
