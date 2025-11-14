# /backend/modules/content_creator/steps.py
"""Content creation steps for the four active prompts."""

import logging
import time
from typing import Any
import uuid

from pydantic import BaseModel, Field

from modules.flow_engine.base_step import StepResult

logger = logging.getLogger(__name__)

import asyncio
import secrets

import httpx

from modules.flow_engine.context import FlowContext
from modules.flow_engine.public import AudioStep, ImageStep, StructuredStep, TranscribeAudioStep, UnstructuredStep
from modules.llm_services.exceptions import LLMTimeoutError, LLMValidationError


# ---------- 1) Generate Unit Source Material ----------
class GenerateUnitSourceMaterialStep(UnstructuredStep):
    """Generate comprehensive source material for a unit from learner context.

    Output is plain-text with markdown headings as described in the prompt.
    Accepts learner_desires (unified context) instead of separate topic/learner_level.
    """

    step_name = "generate_source_material"
    prompt_file = "generate_source_material.md"
    reasoning_effort = "low"
    verbosity = "low"
    model = "gemini-2.5-flash"

    class Inputs(BaseModel):
        learner_desires: str
        target_lesson_count: int | None = None


class GenerateSupplementalSourceMaterialStep(UnstructuredStep):
    """Generate supplemental source material for uncovered learning objectives."""

    step_name = "generate_supplemental_source_material"
    prompt_file = "generate_supplemental_source_material.md"
    reasoning_effort = "low"
    verbosity = "low"
    model = "gemini-2.5-flash"

    class Inputs(BaseModel):
        learner_desires: str
        target_lesson_count: int | None = None
        objectives_outline: str


# ---------- 2) Extract Unit Metadata ----------
class UnitLearningObjective(BaseModel):
    id: str = Field(..., max_length=50)
    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    bloom_level: str | None = Field(None, max_length=20)
    evidence_of_mastery: str | None = Field(None, max_length=300)

    class Config:
        populate_by_name = True  # Allow both field name and alias

    def __init__(self, **data: dict) -> None:
        # For backward compatibility: map old field names to current names
        # Old prompts may return 'lo_id' → 'id' or 'text' → 'description'
        if "lo_id" in data and "id" not in data:
            data["id"] = data.pop("lo_id")
        if "text" in data and "description" not in data:
            data["description"] = data.pop("text")
        super().__init__(**data)


class LessonPlanItem(BaseModel):
    title: str
    lesson_objective: str
    learning_objective_ids: list[str]


class ExtractUnitMetadataStep(StructuredStep):
    """Extract unit-level metadata and ordered lesson plan as strict JSON.

    Takes complete learning objectives from the coach (with bloom_level and evidence_of_mastery).
    Focuses solely on generating a lesson plan that covers all coach LOs.
    The LO output is optional and should match coach input if present (for validation only).
    """

    step_name = "extract_unit_metadata"
    prompt_file = "extract_unit_metadata.md"
    reasoning_effort = "low"
    model = "gemini-2.5-pro"
    verbosity = "low"

    class Inputs(BaseModel):
        learner_desires: str
        coach_learning_objectives: list[dict]
        target_lesson_count: int | None = None
        source_material: str

    class Outputs(BaseModel):
        unit_title: str
        # NOTE: LOs are returned for validation but should match coach input
        learning_objectives: list[UnitLearningObjective] = []
        lessons: list[LessonPlanItem]
        lesson_count: int


# ---------- 3) Lesson Podcast & Assessment Steps ----------
class GenerateLessonPodcastTranscriptStep(UnstructuredStep):
    """Generate an instructional podcast transcript for a single lesson."""

    step_name = "generate_lesson_podcast_transcript"
    prompt_file = "generate_lesson_podcast_transcript_instructional.md"
    reasoning_effort = "medium"
    verbosity = "low"
    model = "gemini-2.5-flash"
    max_retries = 0  # Too expensive to retry

    class Inputs(BaseModel):
        learner_desires: str
        lesson_title: str
        lesson_objective: str
        learning_objectives: list[dict] = Field(default_factory=list)
        source_material: str
        sibling_lessons: list[dict] = Field(default_factory=list)
        lesson_number: int | None = None
        voice: str | None = None


class GenerateMCQsUnstructuredStep(UnstructuredStep):
    """Draft ten MCQs (5 comprehension, 5 transfer) prior to validation."""

    step_name = "generate_mcqs_unstructured"
    prompt_file = "generate_mcqs_unstructured.md"
    reasoning_effort = "high"
    verbosity = "low"
    model = "gemini-2.5-flash"

    class Inputs(BaseModel):
        learner_desires: str
        lesson_objective: str
        learning_objectives: list[dict] = Field(default_factory=list)
        sibling_lessons: list[dict] = Field(default_factory=list)
        podcast_transcript: str
        source_material: str


class MCQOption(BaseModel):
    label: str
    text: str
    is_correct: bool
    rationale: str | None = None


class StructuredMCQExercise(BaseModel):
    id: str = Field(default="")  # Generated by backend if empty
    exercise_type: str = Field(default="mcq")  # Always "mcq"
    exercise_category: str
    aligned_learning_objective: str
    cognitive_level: str
    difficulty: str
    stem: str
    options: list[MCQOption] = Field(default_factory=list)


class MCQValidationOutputs(BaseModel):
    reasoning: str
    exercises: list[StructuredMCQExercise] = Field(default_factory=list)


class ValidateAndStructureMCQsStep(StructuredStep):
    """Validate MCQs and return structured quiz artifacts."""

    step_name = "validate_and_structure_mcqs"
    prompt_file = "validate_and_structure_mcqs.md"
    reasoning_effort = "medium"
    verbosity = "low"
    model = "gemini-2.5-flash"
    max_output_tokens = 12000

    class Inputs(BaseModel):
        unstructured_mcqs: str
        podcast_transcript: str
        learning_objectives: list[dict] = Field(default_factory=list)

    class Outputs(MCQValidationOutputs):
        pass


# ---------- 5) Generate Unit Podcast Transcript ----------
class PodcastLessonInput(BaseModel):
    title: str
    podcast_transcript: str


class GenerateUnitPodcastTranscriptStep(UnstructuredStep):
    """Generate an intro-style podcast transcript that teases the full unit."""

    step_name = "generate_unit_podcast_transcript"
    prompt_file = "generate_intro_podcast_transcript.md"
    reasoning_effort = "medium"
    verbosity = "low"
    model = "gemini-2.5-flash"
    max_retries = 0  # Too expensive to retry

    class Inputs(BaseModel):
        learner_desires: str
        unit_title: str
        voice: str
        unit_summary: str
        lessons: list[PodcastLessonInput]


class SynthesizePodcastAudioStep(AudioStep):
    """Synthesize narrated audio for the generated podcast transcript."""

    step_name = "synthesize_unit_podcast_audio"

    class Inputs(BaseModel):
        text: str
        voice: str
        model: str = "tts-1-hd"
        format: str = "mp3"
        speed: float | None = None


# ---------- 6) Generate Unit Art ----------
class GenerateUnitArtDescriptionStep(StructuredStep):
    """Produce a Weimar Edge styled art prompt for a learning unit."""

    step_name = "generate_unit_art_description"
    prompt_file = "unit_art_description.md"
    reasoning_effort = "medium"
    model = "gemini-2.5-flash"
    verbosity = "low"

    class Inputs(BaseModel):
        learner_desires: str
        unit_title: str
        unit_description: str | None = None
        learning_objectives: str = ""
        key_concepts: str = ""

    class Outputs(BaseModel):
        prompt: str
        alt_text: str
        palette: list[str]


class GenerateUnitArtImageStep(ImageStep):
    """Generate a hero image for the unit using the crafted prompt."""

    step_name = "generate_unit_art_image"

    class Inputs(BaseModel):
        prompt: str
        size: str = "256x256"
        quality: str = "standard"
        style: str | None = "natural"


# ---------- 7) Transcribe Podcast Audio ----------
class PodcastTranscriptSegmentOutput(BaseModel):
    """Timed transcript segment for synchronized highlighting."""

    text: str
    start: float
    end: float


def _truncate_for_logging(obj: Any, max_len: int = 100) -> Any:
    """Recursively truncate objects for logging to avoid excessive size."""
    if isinstance(obj, str):
        return obj[:max_len] + "..." if len(obj) > max_len else obj
    elif isinstance(obj, dict):
        return {k: _truncate_for_logging(v, max_len) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_truncate_for_logging(item, max_len) for item in obj]
    return obj


class TranscribePodcastStep(TranscribeAudioStep):
    """Transcribe podcast audio into timed segments for synchronized display.

    This step transcribes generated podcast audio using Whisper to produce
    timed transcript segments that can be used for synchronized highlighting
    in the mobile app during playback.
    """

    step_name = "transcribe_podcast_audio"
    model = "whisper-1"  # Always use OpenAI's Whisper for transcription

    class Inputs(BaseModel):
        audio_bytes: bytes
        audio_format: str = "mp3"  # Used to generate appropriate filename hint
        model: str | None = None  # Optional: specify transcription model (default: whisper-1)
        language: str | None = None  # Optional: specify language code (e.g., "en") for better accuracy
        prompt: str | None = None  # Optional: guide transcription with context/terminology

    async def execute(self, inputs: dict[str, Any]) -> StepResult:
        """Override execute to handle binary audio_bytes without JSON serialization issues."""

        # Ensure model defaults to whisper-1 if not specified
        if "model" not in inputs or inputs["model"] is None:
            inputs = {**inputs, "model": self.model}

        # Validate full inputs including audio_bytes
        validated_inputs = self.inputs_model(**inputs)

        # Create sanitized inputs for database (exclude binary data)
        sanitized_inputs = validated_inputs.model_dump(exclude={"audio_bytes"})

        # Get infrastructure from context
        context = FlowContext.current()

        # Retry loop for transient failures
        last_error: Exception | None = None
        first_step_run_id: uuid.UUID | None = None

        for attempt in range(self.max_retries + 1):
            start_time = time.time()
            step_run_id: uuid.UUID | None = None

            try:
                logger.info(f"🔧 Starting step: {self.step_name}" + (f" (attempt {attempt + 1}/{self.max_retries + 1})" if attempt > 0 else ""))
                logger.debug(f"Step inputs: {list(sanitized_inputs.keys())}")

                # Create step run record with sanitized inputs (no binary data)
                step_run_id = await context.service.create_step_run_record(
                    flow_run_id=context.flow_run_id,
                    step_name=self.step_name,
                    step_order=context.get_next_step_order(),
                    inputs=sanitized_inputs,  # Use sanitized version for DB
                    retry_attempt=attempt,
                    retry_of_step_run_id=first_step_run_id,
                )

                # Track first attempt for retry linking
                if attempt == 0:
                    first_step_run_id = step_run_id

                # Execute step-specific logic with full validated_inputs
                logger.debug(f"Executing step logic: {self.step_name}")
                logger.debug(f"Step inputs: {_truncate_for_logging(sanitized_inputs)}")
                output_content, llm_request_id = await self._execute_step_logic(validated_inputs, context)
                logger.debug(f"Step output type: {type(output_content).__name__}")
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Step output (truncated): {_truncate_for_logging(output_content)}")

                # Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)

                # Prepare outputs for database
                outputs: dict[str, Any]
                if hasattr(output_content, "model_dump") and callable(output_content.model_dump):
                    outputs = output_content.model_dump()  # type: ignore[union-attr]
                elif isinstance(output_content, dict):
                    outputs = output_content
                else:
                    outputs = {"content": str(output_content)}

                # Update step run with success
                await context.service.update_step_run_success(
                    step_run_id=step_run_id, outputs=outputs, tokens_used=context.last_tokens_used, cost_estimate=context.last_cost_estimate, execution_time_ms=execution_time_ms, llm_request_id=llm_request_id
                )

                # Update flow progress
                await context.service.update_flow_progress(flow_run_id=context.flow_run_id, current_step=self.step_name, step_progress=context.step_counter)

                logger.info(f"✅ Step completed: {self.step_name} - Time: {execution_time_ms}ms, Tokens: {context.last_tokens_used or 0}" + (f" (succeeded on attempt {attempt + 1})" if attempt > 0 else ""))

                # Create result
                return StepResult(
                    step_name=self.step_name,
                    output_content=output_content,
                    metadata={
                        "step_run_id": str(step_run_id),
                        "tokens_used": context.last_tokens_used,
                        "cost_estimate": context.last_cost_estimate,
                        "execution_time_ms": execution_time_ms,
                    },
                )

            except (httpx.TimeoutException, LLMTimeoutError, LLMValidationError) as e:
                # Retryable errors
                last_error = e
                execution_time_ms = int((time.time() - start_time) * 1000)
                if step_run_id:
                    await context.service.update_step_run_error(step_run_id, str(e), execution_time_ms)
                if attempt < self.max_retries:
                    wait_time = (2**attempt) + secrets.randbelow(1000) / 1000.0
                    logger.warning(f"🔄 Retrying step {self.step_name} (attempt {attempt + 1}) after {wait_time:.1f}s: {type(e).__name__}: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                # Non-retryable errors
                last_error = e
                execution_time_ms = int((time.time() - start_time) * 1000)
                if step_run_id:
                    await context.service.update_step_run_error(step_run_id, str(e), execution_time_ms)
                raise

        # If we get here, all retries failed
        raise last_error or RuntimeError("Step execution failed with no recorded error")
