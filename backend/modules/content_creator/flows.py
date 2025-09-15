# /backend/modules/content_creator/flows.py
"""Content creation flows using flow engine infrastructure."""

import logging
from typing import Any

from pydantic import BaseModel

from modules.flow_engine.public import BaseFlow

from .steps import (
    ExtractLessonMetadataStep,
    GenerateDidacticSnippetStep,
    GenerateGlossaryStep,
    GenerateMCQStep,
    GenerateMisconceptionBankStep,
)

logger = logging.getLogger(__name__)


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
            for j, opt in enumerate(mcq.options):
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
