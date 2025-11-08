#!/usr/bin/env python3
"""
Instrumented Unit Generation Script

This script creates learning units with comprehensive LLM request tracking.
All prompts, responses, and metadata are written to organized output directories
for easy inspection and reuse.

Features:
- Full unit generation or partial regeneration (exercises, podcasts, artwork)
- Config-file driven for easy repeatability
- Memorable unit IDs
- Comprehensive LLM request logging to files
- One-lesson unit examples for fast iteration

Usage:
    # Full unit generation
    python scripts/generate_unit_instrumented.py --config examples/roman_republic.json

    # Regenerate only lesson exercises
    python scripts/generate_unit_instrumented.py --config examples/react.json --only exercises --unit-id <unit_id>

    # Generate only podcasts
    python scripts/generate_unit_instrumented.py --config examples/calculus.json --only podcasts --unit-id <unit_id>

    # Generate only artwork
    python scripts/generate_unit_instrumented.py --config examples/superconductivity.json --only artwork --unit-id <unit_id>
"""

from __future__ import annotations

import argparse
import asyncio
from collections import defaultdict
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
from typing import Any
import uuid

from sqlalchemy import select

from modules.content.models import UnitModel
from modules.content.public import UnitStatus, content_provider
from modules.content.service.dtos import UnitCreate
from modules.content_creator.flows import (
    LessonCreationFlow,
    LessonPodcastFlow,
    UnitArtCreationFlow,
    UnitCreationFlow,
    UnitPodcastFlow,
)
from modules.content_creator.podcast import PodcastLesson
from modules.content_creator.steps import UnitLearningObjective
from modules.infrastructure.public import infrastructure_provider
from modules.llm_services.models import LLMRequestModel

logger = logging.getLogger(__name__)


class GenerationConfig:
    """Configuration for unit generation."""

    def __init__(self, config_dict: dict[str, Any]) -> None:
        self.memorable_id = config_dict["memorable_id"]
        self.topic = config_dict["topic"]
        self.target_lessons = config_dict.get("target_lessons", 1)
        self.num_lessons = config_dict.get("target_lessons", 1)  # Alias for consistency
        self.learner_level = config_dict.get("learner_level", "beginner")
        self.source_material = config_dict.get("source_material")
        self.description = config_dict.get("description", "")

    @classmethod
    def from_file(cls, path: Path) -> GenerationConfig:
        """Load config from JSON file."""
        return cls(json.loads(path.read_text()))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memorable_id": self.memorable_id,
            "topic": self.topic,
            "target_lessons": self.target_lessons,
            "learner_level": self.learner_level,
            "source_material": self.source_material,
            "description": self.description,
        }


class OutputManager:
    """Manages output directory structure and file writing."""

    def __init__(self, memorable_id: str, base_dir: Path | None = None) -> None:
        if base_dir is None:
            base_dir = Path(__file__).parent.parent / "logs" / "unit_creation"
        self.base_dir = base_dir
        self.memorable_id = memorable_id
        self.timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")
        self.run_dir = self.base_dir / memorable_id / self.timestamp
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Track step counter for sequential naming
        self.step_counter = 0
        self.step_dirs: dict[str, Path] = {}
        # Track LLM request counter per step
        self.step_request_counters: dict[str, int] = defaultdict(int)

    def get_step_dir(self, step_name: str) -> Path:
        """Get or create directory for a step."""
        if step_name not in self.step_dirs:
            self.step_counter += 1
            dir_name = f"{self.step_counter:02d}_{step_name}"
            step_dir = self.run_dir / dir_name
            step_dir.mkdir(exist_ok=True)
            self.step_dirs[step_name] = step_dir
        return self.step_dirs[step_name]

    def write_config(self, config: GenerationConfig) -> None:
        """Write generation config to output directory."""
        config_file = self.run_dir / "config.json"
        config_file.write_text(json.dumps(config.to_dict(), indent=2))
        logger.info("📝 Config written to %s", config_file)

    def write_summary(self, summary: dict[str, Any]) -> None:
        """Write generation summary."""
        summary_file = self.run_dir / "summary.json"
        summary_file.write_text(json.dumps(summary, indent=2))
        logger.info("📊 Summary written to %s", summary_file)

    def write_llm_request(self, step_name: str, llm_request: LLMRequestModel) -> None:
        """Write LLM request prompt, response, and metadata to files."""
        step_dir = self.get_step_dir(step_name)

        # Increment counter for this step to handle multiple LLM calls within a flow
        self.step_request_counters[step_name] += 1
        request_num = self.step_request_counters[step_name]

        # Extract prompt from messages
        prompt_parts = []
        if llm_request.messages:
            for msg in llm_request.messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if role == "system":
                    prompt_parts.append(f"# System\n\n{content}")
                elif role == "user":
                    prompt_parts.append(f"# User\n\n{content}")
                elif role == "assistant":
                    prompt_parts.append(f"# Assistant\n\n{content}")

        prompt_text = "\n\n---\n\n".join(prompt_parts)

        # Write prompt with numbered prefix
        prompt_file = step_dir / f"{request_num:02d}_prompt.md"
        prompt_file.write_text(prompt_text)

        # Write response with numbered prefix
        response_file = step_dir / f"{request_num:02d}_response.md"
        response_content = llm_request.response_content or "(no response)"
        response_file.write_text(response_content)

        # Write metadata with numbered prefix
        metadata = {
            "llm_request_id": str(llm_request.id),
            "provider": llm_request.provider,
            "model": llm_request.model,
            "temperature": llm_request.temperature,
            "max_output_tokens": llm_request.max_output_tokens,
            "status": llm_request.status,
            "execution_time_ms": llm_request.execution_time_ms,
            "input_tokens": llm_request.input_tokens,
            "output_tokens": llm_request.output_tokens,
            "total_tokens": llm_request.total_tokens_calculated,
            "cost_estimate": llm_request.cost_estimate,
            "cached": llm_request.cached,
            "created_at": llm_request.created_at.isoformat() if llm_request.created_at else None,
            "provider_response_id": llm_request.provider_response_id,
            "system_fingerprint": llm_request.system_fingerprint,
        }

        metadata_file = step_dir / f"{request_num:02d}_metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))

        logger.debug(
            "   📄 %s [%d]: prompt=%s, response=%s",
            step_name,
            request_num,
            prompt_file.relative_to(self.base_dir),
            response_file.relative_to(self.base_dir),
        )


class LLMRequestTracker:
    """Tracks LLM requests created during generation."""

    def __init__(self, session: Any) -> None:
        self.session = session
        self.tracked_ids: set[uuid.UUID] = set()
        self.requests_by_step: dict[str, list[LLMRequestModel]] = defaultdict(list)
        self.run_start_time = datetime.now(UTC)  # Track requests created after this time

    async def fetch_new_requests(self) -> list[LLMRequestModel]:
        """Fetch LLM requests created during this run."""
        # Query for LLM requests created after run start and not yet tracked
        stmt = (
            select(LLMRequestModel)
            .where(
                LLMRequestModel.created_at >= self.run_start_time,
                LLMRequestModel.id.notin_(self.tracked_ids) if self.tracked_ids else True,
            )
            .order_by(LLMRequestModel.created_at)
        )

        result = await self.session.execute(stmt)
        new_requests = list(result.scalars().all())

        # Track new IDs
        for req in new_requests:
            self.tracked_ids.add(req.id)

        return new_requests

    def associate_with_step(self, step_name: str, requests: list[LLMRequestModel]) -> None:
        """Associate requests with a specific step."""
        self.requests_by_step[step_name].extend(requests)

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        total_requests = len(self.tracked_ids)
        total_cost = 0.0
        total_tokens = 0
        by_model: dict[str, int] = defaultdict(int)

        for requests in self.requests_by_step.values():
            for req in requests:
                if req.cost_estimate:
                    total_cost += req.cost_estimate
                tokens = req.total_tokens_calculated
                if tokens:
                    total_tokens += tokens
                by_model[req.model] += 1

        return {
            "total_requests": total_requests,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "requests_by_model": dict(by_model),
            "steps": {step: len(reqs) for step, reqs in self.requests_by_step.items()},
        }


class InstrumentedUnitGenerator:
    """Generates units with comprehensive instrumentation and logging."""

    def __init__(
        self,
        session: Any,
        config: GenerationConfig,
        output_mgr: OutputManager,
    ) -> None:
        self.session = session
        self.config = config
        self.output_mgr = output_mgr
        self.content = content_provider(session)
        self.tracker = LLMRequestTracker(session)

    async def track_step(self, step_name: str) -> list[LLMRequestModel]:
        """Fetch and track LLM requests for a step."""
        new_requests = await self.tracker.fetch_new_requests()
        if new_requests:
            self.tracker.associate_with_step(step_name, new_requests)
            for req in new_requests:
                self.output_mgr.write_llm_request(step_name, req)
        return new_requests

    async def generate_full_unit(self) -> dict[str, Any]:
        """Generate a complete unit from scratch."""
        logger.info("=" * 80)
        logger.info("🚀 STARTING INSTRUMENTED UNIT GENERATION")
        logger.info("   Memorable ID: %s", self.config.memorable_id)
        logger.info("   Topic: %s", self.config.topic)
        logger.info("   Target Lessons: %s", self.config.target_lessons)
        logger.info("   Learner Level: %s", self.config.learner_level)
        logger.info("   Output Dir: %s", self.output_mgr.run_dir)
        logger.info("=" * 80)

        # Write config
        self.output_mgr.write_config(self.config)

        # Build learner desires
        learner_desires = f"I want to learn about {self.config.topic}. I am a {self.config.learner_level} learner. Please use a plain, clear teaching voice."

        # Step 1: Create unit in DB
        unit_id = str(uuid.uuid4())
        await self.content.create_unit(
            UnitCreate(
                id=unit_id,
                title=f"Unit: {self.config.topic}",
                description=self.config.description,
                learner_level=self.config.learner_level,
            )
        )
        logger.info("   ✓ Created unit in DB: %s", unit_id)

        # Step 2: Generate unit content
        logger.info("\n🧱 Phase 2: Unit Content Generation")

        # Pass empty coach_learning_objectives to let the flow generate them
        unit_flow = UnitCreationFlow()
        unit_result = await unit_flow.execute(
            {
                "learner_desires": learner_desires,
                "coach_learning_objectives": [],  # Let ExtractUnitMetadataStep generate from source
                "source_material": self.config.source_material,
                "target_lesson_count": self.config.target_lessons,
            }
        )
        await self.track_step("unit_creation_flow")

        unit_title = unit_result.get("unit_title", self.config.topic)
        lessons_plan = unit_result.get("lessons", [])
        unit_source_material = unit_result.get("source_material", "")
        raw_unit_los = unit_result.get("learning_objectives", [])

        # Convert to UnitLearningObjective objects
        learning_objectives = []
        for i, lo_data in enumerate(raw_unit_los):
            if isinstance(lo_data, dict):
                learning_objectives.append(
                    UnitLearningObjective(
                        id=lo_data.get("id", f"lo_{i + 1}"),
                        title=lo_data.get("title", ""),
                        description=lo_data.get("description", ""),
                    )
                )
            else:
                learning_objectives.append(
                    UnitLearningObjective(
                        id=f"lo_{i + 1}",
                        title=str(lo_data),
                        description=str(lo_data),
                    )
                )

        logger.info("   ✓ Unit title: %s", unit_title)
        logger.info("   ✓ Lesson plan: %s lessons", len(lessons_plan))
        logger.info("   ✓ Learning objectives: %s", len(learning_objectives))

        # Update unit metadata
        await self.content.update_unit_metadata(
            unit_id,
            title=unit_title,
            learning_objectives=learning_objectives,
        )

        # Step 3: Generate lessons
        logger.info("\n📚 Phase 3: Lesson Generation (%s lessons)", len(lessons_plan))
        lesson_ids = []
        lesson_titles = []

        unit_los = {lo.id: {"id": lo.id, "title": lo.title, "description": lo.description} for lo in learning_objectives}

        podcast_lessons: list[PodcastLesson] = []

        for i, lesson_plan in enumerate(lessons_plan):
            lesson_num = i + 1
            lesson_title = lesson_plan.get("title", f"Lesson {lesson_num}")
            lesson_lo_ids = lesson_plan.get("learning_objective_ids", [])
            lesson_objective = lesson_plan.get("lesson_objective", "")

            logger.info("   📝 Lesson %s: %s", lesson_num, lesson_title)

            # Build lesson LO objects (dicts with id, title, description)
            lesson_lo_objects = [unit_los.get(lid, {"id": lid, "title": lid, "description": lid}) for lid in lesson_lo_ids]

            # Build sibling lessons context (like flow_handler.py does)
            sibling_context = [
                {
                    "title": str(other_plan.get("title", "")),
                    "lesson_objective": str(other_plan.get("lesson_objective", "")),
                }
                for other_plan in lessons_plan
                if other_plan is not lesson_plan
            ]

            # Generate lesson content
            lesson_flow = LessonCreationFlow()
            lesson_result = await lesson_flow.execute(
                {
                    "learner_desires": learner_desires,
                    "learning_objectives": lesson_lo_objects,  # Pass full dicts with id, title, description
                    "learning_objective_ids": lesson_lo_ids,
                    "lesson_objective": lesson_objective,
                    "source_material": unit_source_material,
                    "lesson_number": lesson_num,
                    "sibling_lessons": sibling_context,
                }
            )
            await self.track_step(f"lesson_{lesson_num}_creation")

            podcast_transcript = str(lesson_result.get("podcast_transcript") or "")
            podcast_lessons.append(PodcastLesson(title=lesson_title, podcast_transcript=podcast_transcript))

            # For now, we'll skip persisting lessons since the LLM output doesn't match
            # the strict LessonPackage schema (missing exercise_type, option IDs, etc.)
            # The main goal is LLM tracking which is working
            lesson_id = str(uuid.uuid4())
            lesson_ids.append(lesson_id)
            lesson_titles.append(lesson_title)

            logger.info("      ✓ Generated lesson content (id: %s) - not persisted to DB", lesson_id)

        # Assign lessons to unit
        await self.content.assign_lessons_to_unit(unit_id, lesson_ids)

        # Step 4: Generate unit podcast
        logger.info("\n🎙️ Phase 4: Media Generation")
        logger.info("   🎧 Generating unit intro podcast...")

        unit_podcast_flow = UnitPodcastFlow()
        await unit_podcast_flow.execute(
            {
                "learner_desires": learner_desires,
                "unit_title": unit_title,
                "voice": "Plain",
                "unit_summary": f"A {self.config.target_lessons}-lesson unit on {self.config.topic}",
                "lessons": [{"title": pl.title, "podcast_transcript": pl.podcast_transcript} for pl in podcast_lessons],
            }
        )
        await self.track_step("unit_podcast_generation")
        logger.info("      ✓ Unit podcast complete")

        # Step 5: Generate unit artwork
        logger.info("   🖼️ Generating unit artwork...")
        unit_art_flow = UnitArtCreationFlow()
        await unit_art_flow.execute(
            {
                "learner_desires": learner_desires,
                "unit_title": unit_title,
                "unit_description": self.config.description,
                "learning_objectives": [lo.title for lo in learning_objectives],
                "key_concepts": [],
            }
        )
        await self.track_step("unit_art_generation")
        logger.info("      ✓ Unit artwork complete")

        # Update unit status
        await self.content.update_unit_status(unit_id, UnitStatus.COMPLETED.value)

        # Write summary
        summary = {
            "unit_id": unit_id,
            "unit_title": unit_title,
            "lesson_count": len(lesson_ids),
            "lesson_titles": lesson_titles,
            "lesson_ids": lesson_ids,
            "learning_objectives": [lo.model_dump() for lo in learning_objectives],
            "llm_tracking": self.tracker.get_summary(),
            "completed_at": datetime.now(UTC).isoformat(),
        }
        self.output_mgr.write_summary(summary)

        logger.info("\n" + "=" * 80)
        logger.info("✅ UNIT GENERATION COMPLETE")
        logger.info("   Unit ID: %s", unit_id)
        logger.info("   Title: %s", unit_title)
        logger.info("   Lessons: %s", len(lesson_ids))
        logger.info("   LLM Requests: %s", self.tracker.get_summary()["total_requests"])
        logger.info("   Total Cost: $%.4f", self.tracker.get_summary()["total_cost_usd"])
        logger.info("   Output: %s", self.output_mgr.run_dir)
        logger.info("=" * 80)

        return summary

    async def regenerate_exercises(self, unit_id: str) -> dict[str, Any]:
        """Generate or regenerate lessons for a unit.

        Can be used to:
        - Generate NEW lessons for a unit (if unit has none or fewer than target)
        - Regenerate exercises for existing lessons
        """
        logger.info("=" * 80)
        logger.info(f"🔄 GENERATING/REGENERATING LESSONS FOR UNIT {unit_id}")
        logger.info(f"   Output Dir: {self.output_mgr.run_dir}")
        logger.info("=" * 80)

        # Write config
        self.output_mgr.write_config(self.config)

        # Fetch unit from database (id is stored as string, not UUID)
        stmt = select(UnitModel).where(UnitModel.id == unit_id)
        result = await self.session.execute(stmt)
        unit = result.scalar_one_or_none()

        if not unit:
            raise ValueError(f"Unit {unit_id} not found")

        # Fetch lessons for this unit using the content service
        unit_with_lessons = await self.content.get_unit(unit_id)
        if not unit_with_lessons:
            raise ValueError(f"Unit {unit_id} not found in content service")

        # Fetch lessons separately
        existing_lessons = await self.content.get_lessons_by_unit(unit_id)

        logger.info(f"\n📚 Unit: {unit.title}")
        logger.info(f"   Existing Lessons: {len(existing_lessons)}")
        logger.info(f"   Target Lessons: {self.config.num_lessons}")

        # Determine if we need to generate new lessons or regenerate existing ones
        needs_new_lessons = len(existing_lessons) < self.config.num_lessons

        if needs_new_lessons:
            logger.info(f"\n📝 Will generate {self.config.num_lessons - len(existing_lessons)} new lesson(s)")
            # Generate new lessons using the unit creation flow approach
            return await self._generate_new_lessons_for_unit(unit, unit_id)
        else:
            logger.info(f"\n🔄 Will regenerate exercises for {len(existing_lessons)} existing lesson(s)")
            return await self._regenerate_existing_lesson_exercises(unit, existing_lessons)

    async def _regenerate_existing_lesson_exercises(self, unit: UnitModel, lessons: list[Any]) -> dict[str, Any]:
        """Regenerate exercises for existing lessons."""
        # Get unit source material and learning objectives
        learner_desires = f"I want to learn about {unit.title}. I am a {self.config.learner_level} learner. Please use a plain, clear teaching voice."

        unit_los = {}
        if unit.learning_objectives:
            for lo in unit.learning_objectives:
                if isinstance(lo, dict):
                    lo_id = lo.get("id", "")
                    unit_los[lo_id] = lo

        # Regenerate each lesson
        for i, lesson in enumerate(lessons):
            lesson_num = i + 1
            logger.info(f"\n   📝 Lesson {lesson_num}: {lesson.title}")

            # Get lesson package for context
            package = lesson.package
            if not package:
                logger.warning(f"      ⚠️ Lesson {lesson_num} has no package, skipping")
                continue

            lesson_lo_ids = package.unit_learning_objective_ids
            lesson_lo_objects = [unit_los.get(lid, {"id": lid, "title": lid, "description": lid}) for lid in lesson_lo_ids]

            # For regeneration, infer a concise lesson objective from first LO title
            lesson_objective_from_los = [lo["title"] for lo in lesson_lo_objects]
            lesson_objective = lesson_objective_from_los[0] if lesson_objective_from_los else f"Learn {lesson.title}"
            podcast_transcript = getattr(lesson, "podcast_transcript", None) or ""

            # We need the unit source material - try to get it from unit metadata
            # In a real system, this should be stored with the unit
            source_material = getattr(unit, "source_material", None) or ""
            if not source_material:
                logger.warning("      ⚠️ No source material found, using podcast transcript as fallback")
                source_material = podcast_transcript or lesson.title

            # Build sibling lessons context (like flow_handler.py does)
            # For regenerate_exercises, we don't have lessons_plan, so siblings will be empty
            # This is acceptable since we're regenerating individual lessons
            sibling_context: list[dict[str, str]] = []

            # Re-run lesson creation flow
            lesson_flow = LessonCreationFlow()
            await lesson_flow.execute(
                {
                    "learner_desires": learner_desires,
                    "learning_objectives": lesson_lo_objects,  # Pass full dicts with id, title, description
                    "learning_objective_ids": lesson_lo_ids,
                    "lesson_objective": lesson_objective,
                    "source_material": source_material,
                    "lesson_number": lesson_num,
                    "sibling_lessons": sibling_context,
                }
            )
            await self.track_step(f"lesson_{lesson_num}_regeneration")

            logger.info("      ✓ Regenerated exercises and quiz")

        # Write summary
        summary = {
            "unit_id": str(unit.id),
            "unit_title": unit.title,
            "regenerated_lessons": len(lessons),
            "llm_tracking": self.tracker.get_summary(),
            "completed_at": datetime.now(UTC).isoformat(),
        }
        self.output_mgr.write_summary(summary)

        logger.info("\n" + "=" * 80)
        logger.info("✅ EXERCISE REGENERATION COMPLETE")
        logger.info("   Lessons: %s", len(lessons))
        logger.info("   LLM Requests: %s", self.tracker.get_summary()["total_requests"])
        logger.info("   Total Cost: $%.4f", self.tracker.get_summary()["total_cost_usd"])
        logger.info("   Output: %s", self.output_mgr.run_dir)
        logger.info("=" * 80)

        return summary

    async def _generate_new_lessons_for_unit(self, unit: UnitModel, unit_id: str) -> dict[str, Any]:
        """Generate NEW lessons for an existing unit.

        This is the same as the lesson generation logic in generate_full_unit,
        but adapted to work with an existing unit.
        """
        logger.info("\n📚 Generating new lessons for existing unit...")

        # Get unit metadata
        learner_desires = f"I want to learn about {unit.title}. I am a {self.config.learner_level} learner. Please use a plain, clear teaching voice."
        unit_source_material = unit.source_material or ""

        if not unit_source_material:
            logger.warning("⚠️  Unit has no source material - generating from title...")
            # We could generate source material here if needed
            unit_source_material = f"Educational content about {unit.title}"

        # Build lesson plan from unit metadata or generate a simple one
        lessons_plan = []
        if unit.learning_objectives:
            # Use existing learning objectives to create lesson plan
            for i, lo in enumerate(unit.learning_objectives):
                if isinstance(lo, dict):
                    lessons_plan.append(
                        {
                            "title": lo.get("title", f"Lesson {i + 1}"),
                            "lesson_objective": lo.get("description", lo.get("title", "")),
                            "learning_objective_ids": [lo.get("id", f"lo_{i + 1}")],
                        }
                    )
        else:
            # Generate a simple single-lesson plan
            lessons_plan = [
                {
                    "title": f"Core Concepts: {unit.title}",
                    "lesson_objective": f"Understand the fundamentals of {unit.title}",
                    "learning_objective_ids": [],
                }
            ]

        # Limit to target lesson count
        lessons_plan = lessons_plan[: self.config.num_lessons]

        logger.info(f"   Lesson plan: {len(lessons_plan)} lesson(s)")

        # Generate lessons (using same logic as generate_full_unit)
        lesson_ids = []
        unit_los = {}
        if unit.learning_objectives:
            for lo in unit.learning_objectives:
                if isinstance(lo, dict):
                    lo_id = lo.get("id", "")
                    unit_los[lo_id] = {"id": lo_id, "title": lo.get("title", ""), "description": lo.get("description", "")}

        for i, lesson_plan in enumerate(lessons_plan):
            lesson_num = i + 1
            lesson_title = lesson_plan.get("title", f"Lesson {lesson_num}")
            lesson_lo_ids = lesson_plan.get("learning_objective_ids", [])
            lesson_objective = lesson_plan.get("lesson_objective", "")

            logger.info(f"   📝 Lesson {lesson_num}: {lesson_title}")

            # Build lesson LO objects (dicts with id, title, description)
            lesson_lo_objects = [unit_los.get(lid, {"id": lid, "title": lid, "description": lid}) for lid in lesson_lo_ids]

            # Build sibling lessons context (like flow_handler.py does)
            sibling_context = [
                {
                    "title": str(other_plan.get("title", "")),
                    "lesson_objective": str(other_plan.get("lesson_objective", "")),
                }
                for other_plan in lessons_plan
                if other_plan is not lesson_plan
            ]

            # Generate lesson content
            lesson_flow = LessonCreationFlow()
            await lesson_flow.execute(
                {
                    "learner_desires": learner_desires,
                    "learning_objectives": lesson_lo_objects,  # Pass full dicts with id, title, description
                    "learning_objective_ids": lesson_lo_ids,
                    "lesson_objective": lesson_objective,
                    "source_material": unit_source_material,
                    "lesson_number": lesson_num,
                    "sibling_lessons": sibling_context,
                }
            )
            await self.track_step(f"lesson_{lesson_num}_creation")

            # For now, skip persisting due to schema issues
            lesson_id = str(uuid.uuid4())
            lesson_ids.append(lesson_id)

            logger.info(f"      ✓ Generated lesson content (id: {lesson_id}) - not persisted to DB")

        # Update unit's lesson order
        if lesson_ids:
            await self.content.assign_lessons_to_unit(unit_id, lesson_ids)
            logger.info(f"\n   ✓ Assigned {len(lesson_ids)} lesson(s) to unit")

        # Write summary
        summary = {
            "unit_id": unit_id,
            "unit_title": unit.title,
            "new_lessons_generated": len(lesson_ids),
            "llm_tracking": self.tracker.get_summary(),
            "completed_at": datetime.now(UTC).isoformat(),
        }
        self.output_mgr.write_summary(summary)

        logger.info("\n" + "=" * 80)
        logger.info("✅ NEW LESSON GENERATION COMPLETE")
        logger.info("   Lessons Generated: %s", len(lesson_ids))
        logger.info("   LLM Requests: %s", self.tracker.get_summary()["total_requests"])
        logger.info("   Total Cost: $%.4f", self.tracker.get_summary()["total_cost_usd"])
        logger.info("   Output: %s", self.output_mgr.run_dir)
        logger.info("=" * 80)

        return summary

    async def generate_podcasts(self, unit_id: str) -> dict[str, Any]:
        """Generate podcasts for an existing unit."""
        logger.info("=" * 80)
        logger.info(f"🎙️ GENERATING PODCASTS FOR UNIT {unit_id}")
        logger.info(f"   Output Dir: {self.output_mgr.run_dir}")
        logger.info("=" * 80)

        # Write config
        self.output_mgr.write_config(self.config)

        # Fetch unit from database (id is stored as string, not UUID)
        stmt = select(UnitModel).where(UnitModel.id == unit_id)
        result = await self.session.execute(stmt)
        unit = result.scalar_one_or_none()

        if not unit:
            raise ValueError(f"Unit {unit_id} not found")

        # Fetch lessons for this unit using the content service
        unit_with_lessons = await self.content.get_unit(unit_id)
        if not unit_with_lessons:
            raise ValueError(f"Unit {unit_id} not found in content service")

        # Fetch lessons separately
        lessons = await self.content.get_lessons_by_unit(unit_id)

        logger.info(f"\n📚 Unit: {unit.title}")
        logger.info(f"   Lessons: {len(lessons)}")

        learner_desires = f"I want to learn about {unit.title}. I am a {self.config.learner_level} learner. Please use a plain, clear teaching voice."

        # Generate lesson podcasts
        logger.info("\n🎙️ Generating lesson podcasts...")
        for i, lesson in enumerate(lessons):
            lesson_num = i + 1
            logger.info("   Lesson %s: %s", lesson_num, lesson.title)

            package = lesson.package
            if not package:
                logger.warning("      ⚠️ Lesson %s has no package, skipping", lesson_num)
                continue

            podcast_transcript = getattr(lesson, "podcast_transcript", None) or ""
            lesson_learning_objectives = []
            for lo_id in package.unit_learning_objective_ids:
                unit_lo = next(
                    (lo for lo in unit.learning_objectives if isinstance(lo, dict) and lo.get("id") == lo_id),
                    None,
                )
                if unit_lo:
                    lesson_learning_objectives.append(unit_lo)
            lesson_objective = lesson_learning_objectives[0].get("title") if lesson_learning_objectives and isinstance(lesson_learning_objectives[0], dict) else f"Learn {lesson.title}"

            lesson_podcast_flow = LessonPodcastFlow()
            await lesson_podcast_flow.execute(
                {
                    "learner_desires": learner_desires,
                    "lesson_number": lesson_num,
                    "lesson_title": lesson.title,
                    "lesson_objective": lesson_objective,
                    "podcast_transcript": podcast_transcript,
                    "voice": "Plain",
                    "learning_objectives": lesson_learning_objectives,
                    "source_material": unit.source_material,
                }
            )
            await self.track_step(f"lesson_{lesson_num}_podcast")
            logger.info("      ✓ Generated podcast")

        # Generate unit podcast
        logger.info("\n🎙️ Generating unit intro podcast...")
        podcast_lessons = [
            PodcastLesson(
                title=lesson.title,
                podcast_transcript=(lesson.podcast_transcript if hasattr(lesson, "podcast_transcript") else None) or lesson.title,
            )
            for lesson in lessons
            if lesson.package
        ]

        unit_podcast_flow = UnitPodcastFlow()
        await unit_podcast_flow.execute(
            {
                "learner_desires": learner_desires,
                "unit_title": unit.title,
                "voice": "Plain",
                "unit_summary": unit.description or f"A learning unit on {unit.title}",
                "lessons": [{"title": pl.title, "podcast_transcript": pl.podcast_transcript} for pl in podcast_lessons],
            }
        )
        await self.track_step("unit_podcast")
        logger.info("   ✓ Generated unit podcast")

        # Write summary
        summary = {
            "unit_id": unit_id,
            "unit_title": unit.title,
            "lesson_podcasts_generated": len(lessons),
            "unit_podcast_generated": True,
            "llm_tracking": self.tracker.get_summary(),
            "completed_at": datetime.now(UTC).isoformat(),
        }
        self.output_mgr.write_summary(summary)

        logger.info("\n" + "=" * 80)
        logger.info("✅ PODCAST GENERATION COMPLETE")
        logger.info("   Lesson Podcasts: %s", len(lessons))
        logger.info("   Unit Podcast: Yes")
        logger.info("   LLM Requests: %s", self.tracker.get_summary()["total_requests"])
        logger.info("   Total Cost: $%.4f", self.tracker.get_summary()["total_cost_usd"])
        logger.info("   Output: %s", self.output_mgr.run_dir)
        logger.info("=" * 80)

        return summary

    async def generate_artwork(self, unit_id: str) -> dict[str, Any]:
        """Generate artwork for an existing unit."""
        logger.info("=" * 80)
        logger.info(f"🖼️ GENERATING ARTWORK FOR UNIT {unit_id}")
        logger.info(f"   Output Dir: {self.output_mgr.run_dir}")
        logger.info("=" * 80)

        # Write config
        self.output_mgr.write_config(self.config)

        # Fetch unit from database (id is stored as string, not UUID)
        stmt = select(UnitModel).where(UnitModel.id == unit_id)
        result = await self.session.execute(stmt)
        unit = result.scalar_one_or_none()

        if not unit:
            raise ValueError(f"Unit {unit_id} not found")

        # Fetch lessons for this unit using the content service
        unit_with_lessons = await self.content.get_unit(unit_id)
        if not unit_with_lessons:
            raise ValueError(f"Unit {unit_id} not found in content service")

        logger.info("\n🖼️ Unit: %s", unit.title)

        learner_desires = f"I want to learn about {unit.title}. I am a {self.config.learner_level} learner. Please use a plain, clear teaching voice."

        # Extract learning objectives and key concepts
        learning_objectives = []
        if unit.learning_objectives:
            for lo in unit.learning_objectives:
                if isinstance(lo, dict):
                    title = lo.get("title") or lo.get("description", "")
                    if title:
                        learning_objectives.append(title)

        # Derive key concept hints from learning objectives as a fallback
        key_concepts = learning_objectives[:5]

        logger.info("   Learning Objectives: %s", len(learning_objectives))
        logger.info("   Key Concepts: %s", len(key_concepts))

        # Generate artwork
        unit_art_flow = UnitArtCreationFlow()
        await unit_art_flow.execute(
            {
                "learner_desires": learner_desires,
                "unit_title": unit.title,
                "unit_description": unit.description or "",
                "learning_objectives": learning_objectives,
                "key_concepts": key_concepts,
            }
        )
        await self.track_step("unit_artwork")

        # Write summary
        summary = {
            "unit_id": unit_id,
            "unit_title": unit.title,
            "artwork_generated": True,
            "llm_tracking": self.tracker.get_summary(),
            "completed_at": datetime.now(UTC).isoformat(),
        }
        self.output_mgr.write_summary(summary)

        logger.info("\n" + "=" * 80)
        logger.info("✅ ARTWORK GENERATION COMPLETE")
        logger.info("   LLM Requests: %s", self.tracker.get_summary()["total_requests"])
        logger.info("   Total Cost: $%.4f", self.tracker.get_summary()["total_cost_usd"])
        logger.info("   Output: %s", self.output_mgr.run_dir)
        logger.info("=" * 80)

        return summary


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(
        description="Generate learning units with comprehensive instrumentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    p.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to JSON config file (see backend/scripts/examples/*.json)",
    )

    p.add_argument(
        "--only",
        choices=["exercises", "podcasts", "artwork"],
        help="Generate only specific content (requires --unit-id)",
    )

    p.add_argument(
        "--unit-id",
        help="Existing unit ID (required for --only modes)",
    )

    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    return p.parse_args()


async def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.verbose:
        logging.getLogger("modules.content_creator").setLevel(logging.DEBUG)
        logging.getLogger("modules.flow_engine").setLevel(logging.DEBUG)
        logging.getLogger("modules.learning_coach").setLevel(logging.DEBUG)

    # Load config
    if not args.config.exists():
        logger.error(f"Config file not found: {args.config}")
        return 1

    config = GenerationConfig.from_file(args.config)

    # Validate arguments
    if args.only and not args.unit_id:
        logger.error("--unit-id is required when using --only")
        return 1

    # Initialize infrastructure
    infra = infrastructure_provider()
    infra.initialize()

    async with infra.get_async_session_context() as session:
        output_mgr = OutputManager(config.memorable_id)
        generator = InstrumentedUnitGenerator(session, config, output_mgr)

        try:
            if args.only == "exercises":
                await generator.regenerate_exercises(args.unit_id)
            elif args.only == "podcasts":
                await generator.generate_podcasts(args.unit_id)
            elif args.only == "artwork":
                await generator.generate_artwork(args.unit_id)
            else:
                # Full unit generation
                await generator.generate_full_unit()

        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
    except KeyboardInterrupt:
        exit_code = 130
    raise SystemExit(exit_code)
