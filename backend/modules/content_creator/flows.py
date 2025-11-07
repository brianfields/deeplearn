# /backend/modules/content_creator/flows.py
"""Content creation flows using flow engine infrastructure.

Simplified to use the previously 'fast' logic as the default implementation.
Removes separate Fast* flow types and slow multi-step lesson flows.
Uses the previously fast behavior as the canonical default.
"""

import logging
from typing import Any

from pydantic import BaseModel

from modules.flow_engine.public import BaseFlow

from .steps import (
    AnnotateConceptGlossaryStep,
    ExtractConceptGlossaryStep,
    ExtractLessonMetadataStep,
    ExtractUnitMetadataStep,
    GenerateComprehensionExercisesStep,
    GenerateLessonPodcastTranscriptStep,
    GenerateQuizFromExercisesStep,
    GenerateTransferExercisesStep,
    GenerateUnitArtDescriptionStep,
    GenerateUnitArtImageStep,
    GenerateUnitPodcastTranscriptStep,
    GenerateUnitSourceMaterialStep,
    PodcastLessonInput,
    SynthesizePodcastAudioStep,
)

logger = logging.getLogger(__name__)


class LessonCreationFlow(BaseFlow):
    """Create a complete lesson using the concept-driven pipeline.

    Pipeline:
    1) Extract lesson metadata and scoped source material
    2) Build full learning objective objects
    3) Extract and annotate the concept glossary
    4) Generate comprehension and transfer exercises
    5) Assemble a balanced quiz from the exercise bank
    """

    flow_name = "lesson_creation"

    class Inputs(BaseModel):
        learner_desires: str  # Replaces topic + learner_level + voice
        learning_objectives: list[str] | list[dict]  # Now accepts full LO objects or strings
        learning_objective_ids: list[str]
        lesson_objective: str
        source_material: str

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"🧪 Lesson Creation Flow - {inputs.get('learner_desires', 'Unknown')[:50]}")

        # Step 1: Extract lesson metadata and scoped source material
        md_result = await ExtractLessonMetadataStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "learning_objectives": inputs["learning_objectives"],
                "learning_objective_ids": inputs["learning_objective_ids"],
                "lesson_objective": inputs["lesson_objective"],
                "source_material": inputs["source_material"],
            }
        )
        lesson_md = md_result.output_content

        # Step 2: Build full lesson learning objective objects
        lesson_lo_ids = list(inputs.get("learning_objective_ids", []))
        raw_los = list(inputs.get("learning_objectives", []))
        lesson_learning_objectives: list[dict[str, str]] = []
        for idx, lo_id in enumerate(lesson_lo_ids):
            raw_item = raw_los[idx] if idx < len(raw_los) else lo_id
            if isinstance(raw_item, dict):
                title = str(raw_item.get("title") or raw_item.get("name") or raw_item.get("short_title") or raw_item.get("description") or lo_id)
                description = str(raw_item.get("description") or title)
            else:
                text_value = str(raw_item)
                title = text_value
                description = text_value
            lesson_learning_objectives.append({"id": str(lo_id), "title": title, "description": description})

        # Step 3: Extract concept glossary
        concept_result = await ExtractConceptGlossaryStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "topic": lesson_md.topic,
                "lesson_objective": inputs["lesson_objective"],
                "lesson_source_material": lesson_md.lesson_source_material,
                "lesson_learning_objectives": lesson_learning_objectives,
            }
        )
        concept_output = concept_result.output_content
        concept_glossary_payload = [concept.model_dump() for concept in concept_output.concepts]

        # Step 4: Annotate concept glossary
        refined_result = await AnnotateConceptGlossaryStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "topic": lesson_md.topic,
                "lesson_objective": inputs["lesson_objective"],
                "lesson_source_material": lesson_md.lesson_source_material,
                "concept_glossary": concept_glossary_payload,
                "lesson_learning_objectives": lesson_learning_objectives,
            }
        )
        refined_output = refined_result.output_content
        refined_concepts_payload = [concept.model_dump() for concept in refined_output.refined_concepts]

        # Step 5: Generate comprehension exercises
        comprehension_result = await GenerateComprehensionExercisesStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "topic": lesson_md.topic,
                "lesson_objective": inputs["lesson_objective"],
                "lesson_source_material": lesson_md.lesson_source_material,
                "refined_concept_glossary": refined_concepts_payload,
                "lesson_learning_objectives": lesson_learning_objectives,
            }
        )
        comprehension_output = comprehension_result.output_content

        # Step 6: Generate transfer exercises
        transfer_result = await GenerateTransferExercisesStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "topic": lesson_md.topic,
                "lesson_objective": inputs["lesson_objective"],
                "lesson_source_material": lesson_md.lesson_source_material,
                "refined_concept_glossary": refined_concepts_payload,
                "lesson_learning_objectives": lesson_learning_objectives,
            }
        )
        transfer_output = transfer_result.output_content

        comprehension_payload = [exercise.model_dump() for exercise in comprehension_output.exercises]
        transfer_payload = [exercise.model_dump() for exercise in transfer_output.exercises]
        exercise_bank_payload = comprehension_payload + transfer_payload

        # Step 7: Assemble quiz from combined exercise bank
        quiz_result = await GenerateQuizFromExercisesStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "exercise_bank": exercise_bank_payload,
                "refined_concept_glossary": refined_concepts_payload,
                "lesson_learning_objectives": lesson_learning_objectives,
                "target_question_count": len(exercise_bank_payload),
            }
        )
        quiz_output = quiz_result.output_content

        return {
            "topic": lesson_md.topic,
            "learner_level": lesson_md.learner_level,
            "voice": lesson_md.voice,
            "learning_objectives": list(lesson_md.learning_objectives),
            "learning_objective_ids": list(lesson_md.learning_objective_ids),
            "lesson_source_material": lesson_md.lesson_source_material,
            "mini_lesson": lesson_md.mini_lesson,
            "concept_glossary": refined_concepts_payload,
            "exercise_bank": exercise_bank_payload,
            "quiz": list(quiz_output.quiz),
            "quiz_metadata": quiz_output.meta.model_dump(),
        }


class UnitCreationFlow(BaseFlow):
    """Create a coherent learning unit using only the active steps.

    Pipeline:
    1) Generate unit source material if not provided
    2) Extract unit-level metadata (title, lesson plan) using coach-provided LOs
    """

    flow_name = "unit_creation"

    class Inputs(BaseModel):
        learner_desires: str
        coach_learning_objectives: list[dict]
        source_material: str | None = None
        target_lesson_count: int | None = None

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the unit creation pipeline.

        Args:
            inputs: Dictionary with:
              - learner_desires: str (unified learner context)
              - coach_learning_objectives: list[dict] (LOs from coach)
              - source_material: optional pre-generated material
              - target_lesson_count: optional lesson count target

        Returns:
            Dict containing unit metadata and chunked lesson materials.
        """
        logger.info("🧱 Unit Creation Flow - Starting")

        learner_desires: str = inputs.get("learner_desires") or ""
        coach_learning_objectives: list[dict] = inputs.get("coach_learning_objectives") or []

        # Step 0: Ensure we have source material
        material: str | None = inputs.get("source_material")

        if not material:
            logger.info("📝 Generating source material…")
            gen_result = await GenerateUnitSourceMaterialStep().execute(
                {
                    "learner_desires": learner_desires,
                    "target_lesson_count": inputs.get("target_lesson_count"),
                }
            )
            material = str(gen_result.output_content)

        assert material is not None  # for type checkers

        # Step 1: Extract unit metadata (lesson plan using coach LOs)
        logger.info("📋 Extracting unit metadata…")
        md_result = await ExtractUnitMetadataStep().execute(
            {
                "learner_desires": learner_desires,
                "coach_learning_objectives": coach_learning_objectives,
                "target_lesson_count": inputs.get("target_lesson_count"),
                "source_material": material,
            }
        )
        unit_md = md_result.output_content

        # Final assembly - use coach LOs directly (no regeneration)
        return {
            "unit_title": unit_md.unit_title,
            "learning_objectives": coach_learning_objectives,
            "lessons": [ls.model_dump() for ls in unit_md.lessons],
            "lesson_count": int(unit_md.lesson_count),
            "source_material": material,
        }


class LessonPodcastFlow(BaseFlow):
    """Generate a narrated podcast for a single lesson."""

    flow_name = "lesson_podcast"

    class Inputs(BaseModel):
        learner_desires: str
        lesson_number: int
        lesson_title: str
        lesson_objective: str
        mini_lesson: str
        voice: str
        audio_model: str = "tts-1-hd"
        audio_format: str = "mp3"
        audio_speed: float | None = None

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info(
            "🎙️ Lesson Podcast Flow - Lesson %s: %s",
            inputs.get("lesson_number"),
            inputs.get("lesson_title", "Unknown"),
        )

        transcript_result = await GenerateLessonPodcastTranscriptStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "lesson_number": inputs["lesson_number"],
                "lesson_title": inputs["lesson_title"],
                "lesson_objective": inputs["lesson_objective"],
                "mini_lesson": inputs["mini_lesson"],
                "voice": inputs["voice"],
            }
        )
        transcript_text = str(transcript_result.output_content or "").strip()
        if not transcript_text:
            raise RuntimeError("Lesson podcast transcript generation returned empty content")

        audio_inputs = {
            "text": transcript_text,
            "voice": inputs["voice"],
            "model": inputs.get("audio_model", "tts-1-hd"),
            "format": inputs.get("audio_format", "mp3"),
            "speed": inputs.get("audio_speed"),
        }
        audio_result = await SynthesizePodcastAudioStep().execute(audio_inputs)

        return {
            "transcript": transcript_text,
            "audio": audio_result.output_content,
        }


class UnitPodcastFlow(BaseFlow):
    """Generate an intro-style narrated podcast for the unit."""

    flow_name = "unit_podcast"

    class Inputs(BaseModel):
        learner_desires: str
        unit_title: str
        voice: str
        unit_summary: str
        lessons: list[PodcastLessonInput]
        audio_model: str = "tts-1-hd"
        audio_format: str = "mp3"
        audio_speed: float | None = None

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"🎙️ Unit Podcast Flow - {inputs.get('unit_title', 'Unknown')}")

        transcript_result = await GenerateUnitPodcastTranscriptStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "unit_title": inputs["unit_title"],
                "voice": inputs["voice"],
                "unit_summary": inputs["unit_summary"],
                "lessons": inputs["lessons"],
            }
        )
        transcript_text = str(transcript_result.output_content or "").strip()
        if not transcript_text:
            raise RuntimeError("Podcast transcript generation returned empty content")

        audio_inputs = {
            "text": transcript_text,
            "voice": inputs["voice"],
            "model": inputs.get("audio_model", "gpt-4o-mini-tts"),
            "format": inputs.get("audio_format", "mp3"),
            "speed": inputs.get("audio_speed"),
        }
        audio_result = await SynthesizePodcastAudioStep().execute(audio_inputs)

        return {
            "transcript": transcript_text,
            "audio": audio_result.output_content,
        }


class UnitArtCreationFlow(BaseFlow):
    """Generate Weimar Edge artwork prompt and image for a unit."""

    flow_name = "unit_art_creation"

    class Inputs(BaseModel):
        learner_desires: str
        unit_title: str
        unit_description: str | None = None
        learning_objectives: list[str] = []
        key_concepts: list[str] = []
        style_hint: str | None = None

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info("🖼️ Unit Art Flow - %s", inputs.get("unit_title", "Unknown"))

        # Format lists as bullet-point strings for the prompt template
        learning_objectives = inputs.get("learning_objectives") or []
        key_concepts = inputs.get("key_concepts") or []

        learning_objectives_str = "\n".join(f"- {obj}" for obj in learning_objectives) if learning_objectives else "- (None specified)"
        key_concepts_str = "\n".join(f"- {concept}" for concept in key_concepts) if key_concepts else "- (None specified)"

        description_inputs = {
            "learner_desires": inputs.get("learner_desires", ""),
            "unit_title": inputs.get("unit_title", ""),
            "unit_description": inputs.get("unit_description"),
            "learning_objectives": learning_objectives_str,
            "key_concepts": key_concepts_str,
        }

        description_result = await GenerateUnitArtDescriptionStep().execute(description_inputs)
        description_content = description_result.output_content
        prompt_text = str(getattr(description_content, "prompt", "")).strip()
        if not prompt_text:
            raise RuntimeError("Unit art description step returned an empty prompt")

        image_inputs = {
            "prompt": prompt_text,
            "size": "1024x1024",
            "quality": "standard",
        }
        style_hint = inputs.get("style_hint")
        if isinstance(style_hint, str) and style_hint:
            image_inputs["style"] = style_hint

        image_result = await GenerateUnitArtImageStep().execute(image_inputs)

        return {
            "art_description": {
                "prompt": prompt_text,
                "alt_text": getattr(description_content, "alt_text", ""),
                "palette": list(getattr(description_content, "palette", []) or []),
            },
            "image": image_result.output_content,
        }
