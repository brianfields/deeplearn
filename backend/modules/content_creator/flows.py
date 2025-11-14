# /backend/modules/content_creator/flows.py
"""Content creation flows using flow engine infrastructure.

Simplified to use the previously 'fast' logic as the default implementation.
Removes separate Fast* flow types and slow multi-step lesson flows.
Uses the previously fast behavior as the canonical default.
"""

import logging
from typing import Any

from pydantic import BaseModel, Field

from modules.flow_engine.public import BaseFlow

from .steps import (
    ExtractUnitMetadataStep,
    GenerateLessonPodcastTranscriptStep,
    GenerateMCQsUnstructuredStep,
    GenerateUnitArtDescriptionStep,
    GenerateUnitArtImageStep,
    GenerateUnitPodcastTranscriptStep,
    GenerateUnitSourceMaterialStep,
    MCQValidationOutputs,
    PodcastLessonInput,
    SynthesizePodcastAudioStep,
    TranscribePodcastStep,
    ValidateAndStructureMCQsStep,
)

logger = logging.getLogger(__name__)


class LessonCreationFlow(BaseFlow):
    """Create a lesson using the simplified podcast-first pipeline."""

    flow_name = "lesson_creation"

    class Inputs(BaseModel):
        learner_desires: str
        learning_objectives: list[str] | list[dict]
        learning_objective_ids: list[str]
        lesson_objective: str
        source_material: str
        lesson_title: str | None = None
        lesson_number: int | None = None
        sibling_lessons: list[dict] = Field(default_factory=list)

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info("🧪 Lesson Creation Flow - podcast-first pipeline")

        lesson_lo_ids = list(inputs.get("learning_objective_ids", []))
        raw_los = list(inputs.get("learning_objectives", []))
        lesson_learning_objectives: list[dict[str, str]] = []

        # Check for placeholder LOs (e.g., {"id": "UO1", "title": "UO1", "description": "UO1"})
        placeholder_los = []
        for idx, lo_id in enumerate(lesson_lo_ids):
            raw_item = raw_los[idx] if idx < len(raw_los) else lo_id
            if isinstance(raw_item, dict):
                title = str(raw_item.get("title") or raw_item.get("name") or raw_item.get("short_title") or raw_item.get("description") or lo_id)
                description = str(raw_item.get("description") or title)
                # Detect placeholder pattern: title == id and description == id
                if title == str(lo_id) and description == str(lo_id):
                    placeholder_los.append(lo_id)
            else:
                text_value = str(raw_item)
                title = text_value
                description = text_value
            lesson_learning_objectives.append({"id": str(lo_id), "title": title, "description": description})

        # Warn or fail if placeholder LOs detected
        if placeholder_los:
            logger.error(
                "⚠️  Placeholder learning objectives detected: %s. These LOs have no real description and will result in poor MCQ alignment. Please provide real learning objective data with id, title, and description fields.",
                placeholder_los,
            )
            raise ValueError(
                f"Learning objectives contain placeholders (e.g., {placeholder_los}). "
                f"Please provide real learning objective data with meaningful descriptions. "
                f"Example: {{'id': 'LO1', 'title': 'Understand X', 'description': 'The learner will understand Y because Z...'}}"
            )

        sibling_lessons = [{"title": str(item.get("title", "")), "lesson_objective": str(item.get("lesson_objective", ""))} for item in inputs.get("sibling_lessons", []) or []]

        # Warn if no sibling lessons provided and lesson_number > 1 (suggests missing context)
        lesson_number = inputs.get("lesson_number")
        if not sibling_lessons and lesson_number and lesson_number > 1:
            logger.warning(
                "⚠️  Lesson %s has no sibling lessons provided. This means the podcast transcript won't reference other lessons for scope context. Consider passing sibling lessons from the unit lesson plan to help the LLM understand scope.",
                lesson_number,
            )

        lesson_title = str(inputs.get("lesson_title") or "Lesson")
        transcript_result = await GenerateLessonPodcastTranscriptStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "lesson_title": lesson_title,
                "lesson_objective": inputs["lesson_objective"],
                "learning_objectives": lesson_learning_objectives,
                "source_material": inputs["source_material"],
                "sibling_lessons": sibling_lessons,
                "lesson_number": inputs.get("lesson_number"),
            }
        )
        podcast_transcript = str(transcript_result.output_content or "").strip()
        if not podcast_transcript:
            raise RuntimeError("Lesson podcast transcript generation returned empty content")

        mcq_unstructured = await GenerateMCQsUnstructuredStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "lesson_objective": inputs["lesson_objective"],
                "learning_objectives": lesson_learning_objectives,
                "sibling_lessons": sibling_lessons,
                "podcast_transcript": podcast_transcript,
                "source_material": inputs["source_material"],
            }
        )
        unstructured_mcqs = str(mcq_unstructured.output_content or "").strip()

        validation_result = await ValidateAndStructureMCQsStep().execute(
            {
                "unstructured_mcqs": unstructured_mcqs,
                "podcast_transcript": podcast_transcript,
                "learning_objectives": lesson_learning_objectives,
            }
        )
        structured_output = validation_result.output_content
        if not isinstance(structured_output, MCQValidationOutputs):
            structured_output = MCQValidationOutputs.model_validate(structured_output)

        # Generate IDs for exercises if not provided by LLM
        exercises = list(structured_output.exercises)
        comp_counter = 1
        trans_counter = 1
        for exercise in exercises:
            if not exercise.id:
                category_prefix = "ex-comp-mc" if exercise.exercise_category == "comprehension" else "ex-trans-mc"
                counter = comp_counter if exercise.exercise_category == "comprehension" else trans_counter
                exercise.id = f"{category_prefix}-{counter:03d}"
                if exercise.exercise_category == "comprehension":
                    comp_counter += 1
                else:
                    trans_counter += 1
        exercise_bank_payload = [exercise.model_dump() for exercise in exercises]
        quiz_ids = [exercise.id for exercise in exercises]
        quiz_metadata = {
            "quiz_type": "lesson_assessment",
            "total_items": len(quiz_ids),
            "reasoning": structured_output.reasoning,
        }

        return {
            "podcast_transcript": podcast_transcript,
            "learning_objectives": [item["title"] for item in lesson_learning_objectives],
            "learning_objective_ids": lesson_lo_ids,
            "exercise_bank": exercise_bank_payload,
            "quiz": quiz_ids,
            "quiz_metadata": quiz_metadata,
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

        # Always return the coach-provided learning objectives (not LLM-generated ones)
        # The coach LOs are complete with bloom_level and evidence_of_mastery
        final_learning_objectives = coach_learning_objectives

        return {
            "unit_title": unit_md.unit_title,
            "learning_objectives": final_learning_objectives,
            "lessons": [ls.model_dump() for ls in unit_md.lessons],
            "lesson_count": int(unit_md.lesson_count),
            "source_material": material,
        }


class LessonPodcastFlow(BaseFlow):
    """Generate a narrated podcast for a single lesson."""

    flow_name = "lesson_podcast"

    class Inputs(BaseModel):
        learner_desires: str
        lesson_title: str
        lesson_objective: str
        voice: str
        lesson_number: int | None = None
        podcast_transcript: str | None = None
        learning_objectives: list[dict] = Field(default_factory=list)
        sibling_lessons: list[dict] = Field(default_factory=list)
        source_material: str | None = None
        audio_model: str = "tts-1-hd"
        audio_format: str = "mp3"
        audio_speed: float | None = None

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info(
            "🎙️ Lesson Podcast Flow - Lesson %s: %s",
            inputs.get("lesson_number"),
            inputs.get("lesson_title", "Unknown"),
        )

        transcript_text = str(inputs.get("podcast_transcript") or "").strip()
        if not transcript_text:
            transcript_inputs = {
                "learner_desires": inputs["learner_desires"],
                "lesson_title": inputs["lesson_title"],
                "lesson_objective": inputs["lesson_objective"],
                "learning_objectives": inputs.get("learning_objectives") or [],
                "source_material": inputs.get("source_material") or "",
                "sibling_lessons": inputs.get("sibling_lessons") or [],
                "lesson_number": inputs.get("lesson_number"),
                "voice": inputs.get("voice"),
            }
            transcript_result = await GenerateLessonPodcastTranscriptStep().execute(transcript_inputs)
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

        # Extract audio bytes from the audio response
        audio_payload = audio_result.output_content or {}
        audio_bytes = b""
        if isinstance(audio_payload, dict):
            # Audio response contains base64-encoded audio in 'audio_base64' field
            audio_data = audio_payload.get("audio_base64")
            if audio_data:
                import base64

                audio_bytes = base64.b64decode(audio_data)
                logger.debug(f"✓ Audio synthesis succeeded: decoded {len(audio_bytes)} bytes from base64")
            else:
                logger.warning("⚠️ Audio synthesis returned no audio_base64 data")

        # Transcribe audio to get timed segments
        transcript_segments: list[dict[str, Any]] | None = None
        if audio_bytes:
            audio_format = inputs.get("audio_format", "mp3")
            logger.debug(f"🎙️ Transcribing lesson podcast audio (format={audio_format}, size={len(audio_bytes)} bytes)")

            try:
                transcription_result = await TranscribePodcastStep().execute(
                    {
                        "audio_bytes": audio_bytes,
                        "audio_format": audio_format,
                    }
                )
                transcription_payload = transcription_result.output_content or {}
                segments_data = transcription_payload.get("segments", [])
                logger.debug(f"✓ Transcription step returned {len(segments_data)} raw segments")

                if segments_data:
                    transcript_segments = [
                        {
                            "text": str(seg.get("text", "")).strip(),
                            "start": max(0.0, float(seg.get("start", 0.0))),
                            "end": max(float(seg.get("start", 0.0)), float(seg.get("end", 0.0))),
                        }
                        for seg in segments_data
                        if str(seg.get("text", "")).strip()
                    ]
                    logger.info(f"✅ Lesson podcast: {len(transcript_segments)} transcript segments extracted (filtering empty segments)")
                else:
                    logger.warning("⚠️ Transcription returned empty segments list - lesson will be created without timed transcript highlighting")
            except Exception as exc:
                logger.error(
                    f"❌ TRANSCRIPTION FAILED for lesson podcast - continuing lesson creation without timed segments. Error: {type(exc).__name__}: {exc}",
                    exc_info=True,
                    extra={
                        "audio_size_bytes": len(audio_bytes),
                        "audio_format": audio_format,
                        "error_type": type(exc).__name__,
                    },
                )

        return {
            "transcript": transcript_text,
            "audio": audio_result.output_content,
            "transcript_segments": transcript_segments,
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

        # Extract audio bytes from the audio response
        audio_payload = audio_result.output_content or {}
        audio_bytes = b""
        if isinstance(audio_payload, dict):
            # Audio response contains base64-encoded audio in 'audio_base64' field
            audio_data = audio_payload.get("audio_base64")
            if audio_data:
                import base64

                audio_bytes = base64.b64decode(audio_data)
                logger.debug(f"✓ Audio synthesis succeeded: decoded {len(audio_bytes)} bytes from base64")
            else:
                logger.warning("⚠️ Audio synthesis returned no audio_base64 data")

        # Transcribe audio to get timed segments
        transcript_segments: list[dict[str, Any]] | None = None
        if audio_bytes:
            audio_format = inputs.get("audio_format", "mp3")
            logger.debug(f"🎙️ Transcribing unit podcast audio (format={audio_format}, size={len(audio_bytes)} bytes)")

            try:
                transcription_result = await TranscribePodcastStep().execute(
                    {
                        "audio_bytes": audio_bytes,
                        "audio_format": audio_format,
                    }
                )
                transcription_payload = transcription_result.output_content or {}
                segments_data = transcription_payload.get("segments", [])
                logger.debug(f"✓ Transcription step returned {len(segments_data)} raw segments")

                if segments_data:
                    transcript_segments = [
                        {
                            "text": str(seg.get("text", "")).strip(),
                            "start": max(0.0, float(seg.get("start", 0.0))),
                            "end": max(float(seg.get("start", 0.0)), float(seg.get("end", 0.0))),
                        }
                        for seg in segments_data
                        if str(seg.get("text", "")).strip()
                    ]
                    logger.info(f"✅ Unit podcast: {len(transcript_segments)} transcript segments extracted (filtering empty segments)")
                else:
                    logger.warning("⚠️ Transcription returned empty segments list - unit will be created without timed transcript highlighting")
            except Exception as exc:
                logger.error(
                    f"❌ TRANSCRIPTION FAILED for unit podcast - continuing unit creation without timed segments. Error: {type(exc).__name__}: {exc}",
                    exc_info=True,
                    extra={
                        "audio_size_bytes": len(audio_bytes),
                        "audio_format": audio_format,
                        "error_type": type(exc).__name__,
                    },
                )

        return {
            "transcript": transcript_text,
            "audio": audio_result.output_content,
            "transcript_segments": transcript_segments,
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
