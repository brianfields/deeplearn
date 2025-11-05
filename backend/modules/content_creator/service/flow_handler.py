"""Flow orchestration helpers for the content creator service."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
import uuid

from modules.content.package_models import (
    Exercise,
    ExerciseAnswerKey,
    ExerciseOption,
    LessonPackage,
    Meta,
    QuizCoverageByConcept,
    QuizCoverageByLO,
    QuizMetadata,
    RefinedConcept,
    WrongAnswerWithRationale,
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

        def _normalize_exercise_type(raw_type: str | None) -> str:
            value = (raw_type or "").strip().lower().replace("_", "-")
            if value in {"multiple-choice", "multiple choice", "mcq"}:
                return "mcq"
            if value in {"short-answer", "short answer", "sa"}:
                return "short_answer"
            return value or "short_answer"

        def _normalize_category(raw_category: str | None) -> str:
            value = (raw_category or "comprehension").strip().lower()
            return value if value in {"comprehension", "transfer"} else "comprehension"

        db_lesson_id = str(uuid.uuid4())
        meta = Meta(
            lesson_id=db_lesson_id,
            title=lesson_title,
            learner_level=learner_level,
            package_schema_version=2,
            content_version=1,
        )

        mini_lesson_text = str(md_res.get("mini_lesson") or "")
        podcast_lesson, lesson_podcast_result = await self._media_handler.generate_lesson_podcast(
            lesson_index=lesson_index,
            lesson_title=lesson_title,
            lesson_objective=lesson_objective_text,
            mini_lesson=mini_lesson_text,
            voice_label=str(md_res.get("voice") or "Plain"),
            arq_task_id=arq_task_id,
        )

        concept_items = md_res.get("concept_glossary", []) or []
        refined_concepts: list[RefinedConcept] = []
        for idx, concept in enumerate(concept_items):
            difficulty_potential = concept.get("difficulty_potential")
            if isinstance(difficulty_potential, dict):
                normalized_difficulty = {str(k): str(v) for k, v in difficulty_potential.items()}
            else:
                normalized_difficulty = None

            refined_concepts.append(
                RefinedConcept(
                    id=str(concept.get("id") or f"concept_{idx + 1}"),
                    term=str(concept.get("term") or ""),
                    slug=str(concept.get("slug") or ""),
                    aliases=list(concept.get("aliases", []) or []),
                    definition=str(concept.get("definition") or ""),
                    example_from_source=concept.get("example_from_source"),
                    source_span=concept.get("source_span"),
                    category=concept.get("category"),
                    centrality=int(concept.get("centrality") or 0),
                    distinctiveness=int(concept.get("distinctiveness") or 0),
                    transferability=int(concept.get("transferability") or 0),
                    clarity=int(concept.get("clarity") or 0),
                    assessment_potential=int(concept.get("assessment_potential") or 0),
                    cognitive_domain=str(concept.get("cognitive_domain") or ""),
                    difficulty_potential=normalized_difficulty,
                    learning_role=concept.get("learning_role"),
                    aligned_learning_objectives=list(concept.get("aligned_learning_objectives", []) or []),
                    canonical_answer=str(concept.get("canonical_answer") or concept.get("term") or ""),
                    accepted_phrases=list(concept.get("accepted_phrases", []) or []),
                    answer_type=str(concept.get("answer_type") or "closed"),
                    closed_answer=bool(concept.get("closed_answer", True)),
                    example_question_stem=concept.get("example_question_stem") or concept.get("example_exercise_stem"),
                    plausible_distractors=list(concept.get("plausible_distractors", []) or []),
                    misconception_note=concept.get("misconception_note"),
                    contrast_with=list(concept.get("contrast_with", []) or []),
                    related_concepts=list(concept.get("related_concepts", []) or []),
                    review_notes=concept.get("review_notes"),
                    source_reference=concept.get("source_reference"),
                    version=str(concept.get("version") or ""),
                )
            )

        exercise_items = md_res.get("exercise_bank", []) or []
        exercise_bank: list[Exercise] = []
        for idx, exercise_data in enumerate(exercise_items):
            exercise_id = str(exercise_data.get("id") or f"exercise_{idx + 1}")
            exercise_type = _normalize_exercise_type(exercise_data.get("type"))
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

            cognitive_level = str(exercise_data.get("cognitive_level") or "Recall")
            difficulty = str(exercise_data.get("difficulty") or "medium").lower()

            options: list[ExerciseOption] | None = None
            answer_key_obj: ExerciseAnswerKey | None = None
            if exercise_type == "mcq":
                option_id_map: dict[str, str] = {}
                options = []
                for opt_index, opt in enumerate(exercise_data.get("options", []) or []):
                    label = str(opt.get("label") or chr(65 + opt_index)).upper()
                    option_id = f"{exercise_id}_{label.lower()}"
                    option_id_map[label] = option_id
                    options.append(
                        ExerciseOption(
                            id=option_id,
                            label=label,
                            text=str(opt.get("text") or ""),
                            rationale_wrong=opt.get("rationale_wrong"),
                        )
                    )

                answer_key_data = exercise_data.get("answer_key") or {}
                key_label = str(answer_key_data.get("label") or "A").upper()
                answer_key_obj = ExerciseAnswerKey(
                    label=key_label,
                    option_id=option_id_map.get(key_label),
                    rationale_right=answer_key_data.get("rationale_right"),
                )

            wrong_answers_payload = exercise_data.get("wrong_answers", []) or []
            wrong_answers = [
                WrongAnswerWithRationale(
                    answer=str(item.get("answer") or ""),
                    rationale_wrong=str(item.get("rationale_wrong") or ""),
                    misconception_ids=list(item.get("misconception_ids", []) or []),
                )
                for item in wrong_answers_payload
            ]

            acceptable_answers = list(exercise_data.get("acceptable_answers", []) or [])
            explanation_correct = exercise_data.get("rationale_right")

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
                "canonical_answer": None,
                "acceptable_answers": [],
                "wrong_answers": [],
                "explanation_correct": None,
            }

            if exercise_type == "short_answer":
                canonical_answer = str(exercise_data.get("canonical_answer") or exercise_data.get("concept_term") or "")
                exercise_kwargs.update(
                    {
                        "canonical_answer": canonical_answer,
                        "acceptable_answers": acceptable_answers,
                        "wrong_answers": wrong_answers,
                        "explanation_correct": str(explanation_correct or ""),
                    }
                )

            exercise_bank.append(Exercise(**exercise_kwargs))

        quiz_ids = [str(ex_id) for ex_id in md_res.get("quiz", []) or []]
        quiz_meta_payload = md_res.get("quiz_metadata") or {}

        difficulty_distribution_target = {str(key): float(value) for key, value in (quiz_meta_payload.get("difficulty_distribution_target") or {}).items()}
        difficulty_distribution_actual = {str(key): float(value) for key, value in (quiz_meta_payload.get("difficulty_distribution_actual") or {}).items()}
        cognitive_mix_target = {str(key): float(value) for key, value in (quiz_meta_payload.get("cognitive_mix_target") or {}).items()}
        cognitive_mix_actual = {str(key): float(value) for key, value in (quiz_meta_payload.get("cognitive_mix_actual") or {}).items()}

        coverage_by_lo = {
            str(lo_id): QuizCoverageByLO(
                exercise_ids=[str(ex_id) for ex_id in (entry or {}).get("exercise_ids", [])],
                concepts=[str(concept) for concept in (entry or {}).get("concepts", [])],
            )
            for lo_id, entry in (quiz_meta_payload.get("coverage_by_LO") or {}).items()
        }

        coverage_by_concept = {}
        for concept_slug, entry in (quiz_meta_payload.get("coverage_by_concept") or {}).items():
            normalized_types = [_normalize_exercise_type(t) for t in (entry or {}).get("types", [])]
            coverage_by_concept[str(concept_slug)] = QuizCoverageByConcept(
                exercise_ids=[str(ex_id) for ex_id in (entry or {}).get("exercise_ids", [])],
                types=normalized_types,
            )

        quiz_metadata = QuizMetadata(
            quiz_type=str(quiz_meta_payload.get("quiz_type") or "Formative"),
            total_items=int(quiz_meta_payload.get("total_items") or len(quiz_ids)),
            difficulty_distribution_target=difficulty_distribution_target,
            difficulty_distribution_actual=difficulty_distribution_actual,
            cognitive_mix_target=cognitive_mix_target,
            cognitive_mix_actual=cognitive_mix_actual,
            coverage_by_LO=coverage_by_lo,
            coverage_by_concept=coverage_by_concept,
            normalizations_applied=list(quiz_meta_payload.get("normalizations_applied", []) or []),
            selection_rationale=list(quiz_meta_payload.get("selection_rationale", []) or []),
            gaps_identified=list(quiz_meta_payload.get("gaps_identified", []) or []),
        )

        lesson_package = LessonPackage(
            meta=meta,
            unit_learning_objective_ids=lesson_lo_ids,
            mini_lesson=mini_lesson_text,
            concept_glossary=refined_concepts,
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
                    learner_level=learner_level,
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
        return created_lesson.id, podcast_lesson, lesson_podcast_result.voice, covered_lo_ids
