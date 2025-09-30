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
    ExtractLessonMetadataStep,
    ExtractUnitMetadataStep,
    GenerateMCQStep,
    GenerateUnitArtDescriptionStep,
    GenerateUnitArtImageStep,
    GenerateUnitPodcastTranscriptStep,
    GenerateUnitSourceMaterialStep,
    PodcastLessonInput,
    SynthesizePodcastAudioStep,
)

logger = logging.getLogger(__name__)


class LessonCreationFlow(BaseFlow):
    """Create a complete lesson using lesson metadata extraction + MCQs.

    Pipeline:
    1) Extract lesson metadata and mini-lesson from unit source material
    2) Generate 5 MCQs that cover the provided learning objectives
    """

    flow_name = "lesson_creation"

    class Inputs(BaseModel):
        topic: str
        learner_level: str
        voice: str
        learning_objectives: list[str]
        lesson_objective: str
        unit_source_material: str

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"🧪 Lesson Creation Flow - {inputs.get('topic', 'Unknown')}")

        # Step 1: Extract lesson metadata and mini-lesson
        md_result = await ExtractLessonMetadataStep().execute(
            {
                "topic": inputs["topic"],
                "learner_level": inputs["learner_level"],
                "voice": inputs["voice"],
                "learning_objectives": inputs["learning_objectives"],
                "lesson_objective": inputs["lesson_objective"],
                "unit_source_material": inputs["unit_source_material"],
            }
        )
        lesson_md = md_result.output_content

        # Step 2: Generate MCQs for this lesson
        mcq_result = await GenerateMCQStep().execute(
            {
                "learner_level": inputs["learner_level"],
                "voice": inputs["voice"],
                "lesson_title": inputs["topic"],
                "lesson_objective": inputs["lesson_objective"],
                "learning_objectives": inputs["learning_objectives"],
                "mini_lesson": lesson_md.mini_lesson,
                "misconceptions": lesson_md.misconceptions,
                "confusables": lesson_md.confusables,
                "glossary": lesson_md.glossary,
            }
        )
        mcq_out = mcq_result.output_content

        return {
            "topic": lesson_md.topic,
            "learner_level": lesson_md.learner_level,
            "voice": lesson_md.voice,
            "learning_objectives": list(lesson_md.learning_objectives),
            "misconceptions": [m.model_dump() for m in lesson_md.misconceptions],
            "confusables": [c.model_dump() for c in lesson_md.confusables],
            "glossary": [g.model_dump() for g in lesson_md.glossary],
            "mini_lesson": lesson_md.mini_lesson,
            "mcqs": [it.model_dump() for it in mcq_out.mcqs],
        }


class UnitCreationFlow(BaseFlow):
    """Create a coherent learning unit using only the active steps.

    Pipeline:
    1) Generate unit source material if not provided
    2) Extract unit-level metadata (title, objectives, lessons, count)
    """

    flow_name = "unit_creation"

    class Inputs(BaseModel):
        topic: str
        unit_source_material: str | None = None
        target_lesson_count: int | None = None
        learner_level: str = "beginner"

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
        material: str | None = inputs.get("unit_source_material")
        topic: str | None = inputs.get("topic")
        if not material:
            logger.info("📝 Generating source material from topic…")
            gen_result = await GenerateUnitSourceMaterialStep().execute(
                {
                    "topic": topic or "",
                    "target_lesson_count": inputs.get("target_lesson_count"),
                    "learner_level": inputs.get("learner_level", "beginner"),
                }
            )
            material = str(gen_result.output_content)

        assert material is not None  # for type checkers

        # Step 1: Extract unit metadata (LOs, lesson plan)
        logger.info("📋 Extracting unit metadata…")
        md_result = await ExtractUnitMetadataStep().execute(
            {
                "topic": topic or "",
                "learner_level": inputs.get("learner_level", "beginner"),
                "target_lesson_count": inputs.get("target_lesson_count"),
                "unit_source_material": material,
            }
        )
        unit_md = md_result.output_content

        # Final assembly (no chunking in active prompt set)
        return {
            "unit_title": unit_md.unit_title,
            "learning_objectives": [lo.model_dump() for lo in unit_md.learning_objectives],
            "lessons": [ls.model_dump() for ls in unit_md.lessons],
            "lesson_count": int(unit_md.lesson_count),
            "unit_source_material": material,
        }


class UnitPodcastFlow(BaseFlow):
    """Generate a narrated podcast by orchestrating transcript and audio steps."""

    flow_name = "unit_podcast"

    class Inputs(BaseModel):
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
        unit_title: str
        unit_description: str | None = None
        learning_objectives: list[str] = []
        key_concepts: list[str] = []
        style_hint: str | None = None

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info("🖼️ Unit Art Flow - %s", inputs.get("unit_title", "Unknown"))

        description_inputs = {
            "unit_title": inputs.get("unit_title", ""),
            "unit_description": inputs.get("unit_description"),
            "learning_objectives": list(inputs.get("learning_objectives") or []),
            "key_concepts": list(inputs.get("key_concepts") or []),
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
        if inputs.get("style_hint"):
            image_inputs["style"] = inputs.get("style_hint")

        image_result = await GenerateUnitArtImageStep().execute(image_inputs)

        return {
            "art_description": {
                "prompt": prompt_text,
                "alt_text": getattr(description_content, "alt_text", ""),
                "palette": list(getattr(description_content, "palette", []) or []),
            },
            "image": image_result.output_content,
        }
