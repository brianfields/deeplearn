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
    GenerateLessonPodcastTranscriptStep,
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
        learning_objective_ids: list[str]
        lesson_objective: str
        source_material: str

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"🧪 Lesson Creation Flow - {inputs.get('topic', 'Unknown')}")

        # Step 1: Extract lesson metadata and mini-lesson
        md_result = await ExtractLessonMetadataStep().execute(
            {
                "topic": inputs["topic"],
                "learner_level": inputs["learner_level"],
                "voice": inputs["voice"],
                "learning_objectives": inputs["learning_objectives"],
                "learning_objective_ids": inputs["learning_objective_ids"],
                "lesson_objective": inputs["lesson_objective"],
                "source_material": inputs["source_material"],
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
            "learning_objective_ids": list(lesson_md.learning_objective_ids),
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
        source_material: str | None = None
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
        material: str | None = inputs.get("source_material")
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
                "source_material": material,
            }
        )
        unit_md = md_result.output_content

        # Final assembly (no chunking in active prompt set)
        return {
            "unit_title": unit_md.unit_title,
            "learning_objectives": [lo.model_dump() for lo in unit_md.learning_objectives],
            "lessons": [ls.model_dump() for ls in unit_md.lessons],
            "lesson_count": int(unit_md.lesson_count),
            "source_material": material,
        }


class LessonPodcastFlow(BaseFlow):
    """Generate a narrated podcast for a single lesson."""

    flow_name = "lesson_podcast"

    class Inputs(BaseModel):
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

        # Format lists as bullet-point strings for the prompt template
        learning_objectives = inputs.get("learning_objectives") or []
        key_concepts = inputs.get("key_concepts") or []

        learning_objectives_str = "\n".join(f"- {obj}" for obj in learning_objectives) if learning_objectives else "- (None specified)"
        key_concepts_str = "\n".join(f"- {concept}" for concept in key_concepts) if key_concepts else "- (None specified)"

        description_inputs = {
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
