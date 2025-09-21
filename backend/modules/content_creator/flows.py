# /backend/modules/content_creator/flows.py
"""Content creation flows using flow engine infrastructure."""

import asyncio
import logging
from typing import Any

from pydantic import BaseModel

from modules.flow_engine.public import BaseFlow

from .steps import (
    ChunkSourceMaterialStep,
    ExtractLessonMetadataStep,
    ExtractUnitMetadataStep,
    FastLessonMetadataStep,
    GenerateDidacticSnippetStep,
    GenerateGlossaryStep,
    GenerateMCQStep,
    GenerateMisconceptionBankStep,
    GenerateUnitSourceMaterialStep,
)

logger = logging.getLogger(__name__)

# Local default used only within flows; service controls user-facing parallelism
DEFAULT_MAX_PARALLEL_LESSONS = 4


class LessonCreationFlow(BaseFlow):
    """Multi-step flow that creates a complete lesson with all components."""

    flow_name = "lesson_creation"

    class Inputs(BaseModel):
        title: str
        core_concept: str
        source_material: str
        user_level: str = "intermediate"
        domain: str = "General"

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"📚 Lesson Creation Flow - Processing: {inputs.get('title', 'Unknown Lesson')}")

        # Step 1: Extract metadata
        logger.info("📋 Step 1: Extracting lesson metadata...")
        metadata_result = await ExtractLessonMetadataStep().execute(inputs)
        md = metadata_result.output_content
        logger.info(f"✅ Extracted {len(md.learning_objectives)} LOs, {len(md.key_concepts)} key concepts, {len(md.misconceptions)} misconceptions")

        # Step 2: Misconception bank
        logger.info("🧩 Step 2: Building misconception & distractor bank...")
        bank_result = await GenerateMisconceptionBankStep().execute(
            {
                "core_concept": md.core_concept,
                "user_level": md.user_level,
                "learning_objectives": md.learning_objectives,
                "key_concepts": md.key_concepts,
                "misconceptions": md.misconceptions,
                "confusables": md.confusables,
                "length_budgets": md.length_budgets,
            }
        )
        bank_by_lo = {blk.lo_id: blk.distractors for blk in bank_result.output_content.by_lo}

        # Step 3: Generate single didactic snippet for entire lesson
        logger.info("📖 Step 3: Generating lesson didactic snippet...")
        didactic_input = {
            "lesson_title": inputs["title"],
            "core_concept": inputs["core_concept"],
            "learning_objectives": [lo.text for lo in md.learning_objectives],
            "key_concepts": [kc.term for kc in md.key_concepts],
            "user_level": inputs["user_level"],
            "length_budgets": md.length_budgets,
        }
        didactic_result = await GenerateDidacticSnippetStep().execute(didactic_input)
        lesson_didactic = didactic_result.output_content

        # Step 4: Glossary (simple list of terms)
        logger.info("📚 Step 4: Generating glossary...")
        glossary_input = {
            "lesson_title": inputs["title"],
            "core_concept": inputs["core_concept"],
            "key_concepts": [kc.term for kc in md.key_concepts],
            "user_level": inputs["user_level"],
        }
        glossary_result = await GenerateGlossaryStep().execute(glossary_input)

        # Step 5: Generate all MCQs in one call
        logger.info(f"❓ Step 5: Generating {len(md.learning_objectives)} MCQs in single call...")
        mcq_input = {
            "lesson_title": inputs["title"],
            "core_concept": inputs["core_concept"],
            "learning_objectives": md.learning_objectives,
            "user_level": inputs["user_level"],
            "length_budgets": md.length_budgets,
            "didactic_context": lesson_didactic,
            "distractor_pools": bank_by_lo,
        }
        mcq_result = await GenerateMCQStep().execute(mcq_input)
        mcq_items = mcq_result.output_content.mcqs
        logger.info(f"✅ Generated {len(mcq_items)} MCQs successfully")

        # Convert MCQs to exercises
        exercises = []
        for i, mcq in enumerate(mcq_items):
            # Convert MCQItem to MCQExercise format
            # Generate a unique ID since MCQItem doesn't have one
            exercise_id = f"mcq_{i + 1}"

            # Convert options and add missing IDs
            options_with_ids = []
            for opt in mcq.options:
                option_dict = opt.model_dump()
                option_dict["id"] = f"{exercise_id}_{opt.label.lower()}"  # e.g., "mcq_1_a"
                options_with_ids.append(option_dict)

            exercise = {
                "id": exercise_id,
                "exercise_type": "mcq",
                "lo_id": mcq.lo_id,
                "cognitive_level": mcq.cognitive_level,
                "estimated_difficulty": mcq.estimated_difficulty,
                "misconceptions_used": mcq.misconceptions_used,
                "stem": mcq.stem,
                "options": options_with_ids,
                "answer_key": mcq.answer_key.model_dump(),
            }
            exercises.append(exercise)

        # Final assembly
        return {
            "learning_objectives": [lo.model_dump() for lo in md.learning_objectives],
            "key_concepts": [kc.model_dump() for kc in md.key_concepts],
            "misconceptions": [m.model_dump() for m in md.misconceptions],
            "confusables": [c.model_dump() for c in md.confusables],
            "refined_material": md.refined_material.model_dump(),
            "length_budgets": md.length_budgets.model_dump(),
            "glossary": glossary_result.output_content.model_dump(),
            "didactic_snippet": lesson_didactic.model_dump(),
            "exercises": exercises,
        }


class UnitCreationFlow(BaseFlow):
    """
    Create a coherent learning unit from either a topic or provided source material.

    This flow orchestrates three major steps:
    1) Generate comprehensive source material when only a topic is provided
    2) Extract unit-level metadata (learning objectives, lesson titles/count, summary)
    3) Chunk the source material into lesson-sized segments aligned to the plan

    Returns a structured dictionary suitable for persisting a `Unit` in the
    content module, including unit title, objectives, lesson plan, and chunks.
    """

    flow_name = "unit_creation"

    class Inputs(BaseModel):
        topic: str | None = None
        source_material: str | None = None
        target_lesson_count: int | None = None
        user_level: str = "beginner"
        domain: str | None = None

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the unit creation pipeline.

        Args:
            inputs: Dictionary matching `Inputs` with optional `topic` or
                `source_material`, plus user context and duration targets.

        Returns:
            Dict containing unit metadata and chunked lesson materials.
        """
        logger.info("🧱 Unit Creation Flow - Starting")

        # Step 0: Ensure we have source material
        material: str | None = inputs.get("source_material")
        topic: str | None = inputs.get("topic")
        if not material:
            if not topic:
                raise ValueError("Either 'source_material' or 'topic' must be provided")
            logger.info("📝 Generating source material from topic…")
            gen_result = await GenerateUnitSourceMaterialStep().execute(
                {
                    "topic": topic,
                    "target_lesson_count": inputs.get("target_lesson_count"),
                    "user_level": inputs.get("user_level", "beginner"),
                    "domain": inputs.get("domain"),
                }
            )
            material = str(gen_result.output_content)

        assert material is not None  # for type checkers

        # Step 1: Extract unit metadata (LOs, lesson plan)
        logger.info("📋 Extracting unit metadata…")
        md_result = await ExtractUnitMetadataStep().execute(
            {
                "topic": topic or "",
                "source_material": material,
                "target_lesson_count": inputs.get("target_lesson_count"),
                "user_level": inputs.get("user_level", "beginner"),
                "domain": inputs.get("domain"),
            }
        )
        unit_md = md_result.output_content

        # Step 2: Chunk source material into lesson-sized chunks
        logger.info("📦 Chunking source material into lessons…")
        chunk_result = await ChunkSourceMaterialStep().execute(
            {
                "source_material": material,
                "lesson_titles": unit_md.lesson_titles,
                "lesson_count": unit_md.lesson_count,
                "target_lesson_count": inputs.get("target_lesson_count"),
                "per_lesson_minutes": getattr(unit_md, "recommended_per_lesson_minutes", 5),
                "user_level": inputs.get("user_level", "beginner"),
            }
        )

        # Final assembly
        chunks_out = [c.model_dump() for c in chunk_result.output_content.chunks]
        return {
            "unit_title": unit_md.unit_title,
            "learning_objectives": [lo.model_dump() for lo in unit_md.learning_objectives],
            "lesson_titles": list(unit_md.lesson_titles),
            "lesson_count": int(unit_md.lesson_count),
            "recommended_per_lesson_minutes": int(getattr(unit_md, "recommended_per_lesson_minutes", 5)),
            "target_lesson_count": inputs.get("target_lesson_count"),
            "source_material": material,
            "summary": getattr(unit_md, "summary", None),
            "chunks": chunks_out,
        }


class FastLessonCreationFlow(BaseFlow):
    """Two-step fast lesson creation: combined metadata step + MCQs."""

    flow_name = "fast_lesson_creation"

    class Inputs(BaseModel):
        title: str
        core_concept: str
        source_material: str
        user_level: str = "intermediate"
        domain: str = "General"

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"⚡ Fast Lesson Creation Flow - {inputs.get('title', 'Unknown')}")

        # Combined step
        combo_result = await FastLessonMetadataStep().execute(inputs)
        combo = combo_result.output_content

        # Prepare distractor pools keyed by LO id
        bank_by_lo = {blk.lo_id: blk.distractors for blk in getattr(combo, "by_lo", [])}

        # MCQs in single call
        mcq_input = {
            "lesson_title": inputs["title"],
            "core_concept": inputs["core_concept"],
            "learning_objectives": combo.learning_objectives,
            "user_level": inputs["user_level"],
            "length_budgets": combo.length_budgets,
            "didactic_context": combo.didactic_snippet,
            "distractor_pools": bank_by_lo,
        }
        mcq_result = await GenerateMCQStep().execute(mcq_input)
        mcq_items = mcq_result.output_content.mcqs

        # Convert MCQs to exercise dicts
        exercises: list[dict[str, Any]] = []
        for i, mcq in enumerate(mcq_items):
            exercise_id = f"mcq_{i + 1}"
            options_with_ids = []
            for opt in mcq.options:
                od = opt.model_dump()
                od["id"] = f"{exercise_id}_{opt.label.lower()}"
                options_with_ids.append(od)
            exercises.append(
                {
                    "id": exercise_id,
                    "exercise_type": "mcq",
                    "lo_id": mcq.lo_id,
                    "cognitive_level": mcq.cognitive_level,
                    "estimated_difficulty": mcq.estimated_difficulty,
                    "misconceptions_used": mcq.misconceptions_used,
                    "stem": mcq.stem,
                    "options": options_with_ids,
                    "answer_key": mcq.answer_key.model_dump(),
                }
            )

        return {
            "learning_objectives": [lo.model_dump() for lo in combo.learning_objectives],
            "key_concepts": [kc.model_dump() for kc in combo.key_concepts],
            "misconceptions": [m.model_dump() for m in combo.misconceptions],
            "confusables": [c.model_dump() for c in combo.confusables],
            "refined_material": combo.refined_material.model_dump(),
            "length_budgets": combo.length_budgets.model_dump(),
            "glossary": {"terms": [t.model_dump() for t in getattr(combo, "glossary", [])]},
            "didactic_snippet": combo.didactic_snippet.model_dump(),
            "exercises": exercises,
        }


class FastUnitCreationFlow(BaseFlow):
    """Fast unit creation that parallelizes lesson creation and tracks flow type."""

    flow_name = "fast_unit_creation"

    class Inputs(BaseModel):
        topic: str | None = None
        source_material: str | None = None
        target_lesson_count: int | None = None
        user_level: str = "beginner"
        domain: str | None = None
        # Optional override for internal batching; primarily for testing
        max_parallel_lessons: int | None = None

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        # Step 0-2: Reuse UnitCreationFlow to generate unit plan and chunks
        base = UnitCreationFlow()
        unit_plan = await base.execute(
            {
                "topic": inputs.get("topic"),
                "source_material": inputs.get("source_material"),
                "target_lesson_count": inputs.get("target_lesson_count"),
                "user_level": inputs.get("user_level", "beginner"),
                "domain": inputs.get("domain"),
            }
        )

        # Parallelize lesson content creation using the fast lesson flow
        lesson_titles: list[str] = list(unit_plan.get("lesson_titles", []) or [])
        chunks: list[dict[str, Any]] = list(unit_plan.get("chunks", []) or [])

        if not chunks:
            # Nothing to generate; return the plan as-is
            return unit_plan

        max_parallel = int(inputs.get("max_parallel_lessons") or DEFAULT_MAX_PARALLEL_LESSONS)

        previous_titles: list[str] = []

        async def _create_one(index: int, chunk: dict[str, Any], prior_titles: list[str]) -> tuple[int, dict[str, Any] | None]:
            title_in_chunk = chunk.get("title") if isinstance(chunk.get("title"), str) else None
            chunk_text_raw = chunk.get("chunk_text")
            chunk_text = str(chunk_text_raw) if chunk_text_raw is not None else ""
            title = title_in_chunk or (lesson_titles[index] if index < len(lesson_titles) else f"Lesson {index + 1}")
            core_concept = title
            prior_context = ("Previously in this unit: " + ", ".join(prior_titles) + ".\n\n") if prior_titles else ""
            lesson_source_material = f"{prior_context}{chunk_text}" if chunk_text else prior_context

            try:
                lesson_flow = FastLessonCreationFlow()
                result = await lesson_flow.execute(
                    {
                        "title": title,
                        "core_concept": core_concept,
                        "source_material": lesson_source_material,
                        "user_level": inputs.get("user_level", "beginner"),
                        "domain": inputs.get("domain", "General") or "General",
                    }
                )
                return (index, {"title": title, "result": result})
            except Exception as _e:
                logger.exception("Fast lesson creation failed for index %s (title=%s)", index, title)
                return (index, None)

        tasks: list[tuple[int, dict[str, Any]] | asyncio.Task] = []
        results: list[tuple[int, dict[str, Any] | None]] = []
        for i, c in enumerate(chunks):
            # We'll lazily build tasks per batch to embed updated prior context
            tasks.append((i, {"_raw": c}))

        # Execute in batches to limit concurrency and allow sequential context updates
        for batch_start in range(0, len(tasks), max_parallel):
            batch_slice = tasks[batch_start : batch_start + max_parallel]
            batch_tasks: list[asyncio.Task] = []
            for idx, payload in batch_slice:
                chunk_dict: dict[str, Any] = payload.get("_raw", {})
                # Capture a snapshot of prior titles for this batch
                snapshot_prior = list(previous_titles)
                batch_tasks.append(asyncio.create_task(_create_one(idx, chunk_dict, snapshot_prior)))

            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=False)
            # Update prior titles best-effort for subsequent batches
            for idx, lesson_res in batch_results:
                if lesson_res is not None and idx < len(lesson_titles):
                    previous_titles.append(lesson_titles[idx])
            results.extend(batch_results)

        # Collate successful lessons in order
        lessons_out: list[dict[str, Any]] = []
        for _idx, lesson_res in sorted(results, key=lambda t: t[0]):
            if lesson_res is not None:
                lessons_out.append(lesson_res)

        # Return base plan plus the generated lesson payloads
        enriched: dict[str, Any] = dict(unit_plan)
        enriched["lessons"] = lessons_out
        return enriched
