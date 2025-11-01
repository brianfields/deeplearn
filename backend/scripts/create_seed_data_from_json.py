#!/usr/bin/env python3
"""
Seed Data Creation Script (JSON-based)

Loads seed data from JSON files in the seed_data directory and creates database records.

Usage:
    python scripts/create_seed_data.py --verbose
    python scripts/create_seed_data.py --unit-file seed_data/units/my-unit.json
"""

import argparse
from datetime import UTC, datetime, timedelta
import json
import logging
import os
from pathlib import Path
import sys
import traceback
from typing import Any, cast
import uuid

# Add the backend directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete

from modules.content.models import (
    LessonModel,
    UnitModel,
    UnitResourceModel,
)
from modules.content.package_models import (
    GlossaryTerm,
    LessonPackage,
    MCQAnswerKey,
    MCQExercise,
    MCQOption,
    Meta,
    ShortAnswerExercise,
    WrongAnswer,
)
from modules.conversation_engine.models import ConversationMessageModel, ConversationModel
from modules.flow_engine.models import FlowRunModel, FlowStepRunModel
from modules.infrastructure.public import infrastructure_provider
from modules.llm_services.models import LLMRequestModel
from modules.object_store.models import AudioModel, DocumentModel, ImageModel
from modules.resource.models import ResourceModel
from modules.user.repo import UserRepo
from modules.user.service import UserService


def load_json_file(file_path: Path) -> Any:
    """Load and parse a JSON file."""
    with file_path.open("r") as f:
        return json.load(f)


def build_lesson_package(
    lesson_id: str,
    *,
    title: str,
    learner_level: str,
    objectives: list[dict[str, str]],
    glossary_terms: list[dict[str, str]],
    mini_lesson: str,
    mcqs: list[dict[str, Any]],
    short_answers: list[dict[str, Any]] | None = None,
    misconceptions: list[dict[str, str]] | None = None,
    confusables: list[dict[str, str]] | None = None,
) -> LessonPackage:
    """Build a structured lesson package from declarative descriptors."""

    meta = Meta(
        lesson_id=lesson_id,
        title=title,
        learner_level=learner_level,
        package_schema_version=1,
        content_version=1,
    )

    unit_lo_ids: list[str] = []
    for idx, obj in enumerate(objectives, start=1):
        lo_id = obj.get("id") or f"{lesson_id}_lo_{idx}"
        unit_lo_ids.append(lo_id)

    glossary_models = [
        GlossaryTerm(
            id=f"{lesson_id}_term_{idx}",
            term=term["term"],
            definition=term["definition"],
            micro_check=term.get("micro_check"),
        )
        for idx, term in enumerate(glossary_terms, start=1)
    ]

    exercises: list[MCQExercise | ShortAnswerExercise] = []
    for idx, mcq in enumerate(mcqs, start=1):
        if unit_lo_ids:
            lo_index = max(1, min(mcq.get("lo_index", 1), len(unit_lo_ids)))
            lo_id = unit_lo_ids[lo_index - 1]
        else:
            lo_id = f"{lesson_id}_lo_{idx}"

        options: list[MCQOption] = []
        correct_index = mcq.get("correct_index", 0)
        for option_idx, option in enumerate(mcq["options"], start=0):
            label = chr(ord("A") + option_idx)
            option_id = f"{lesson_id}_mcq_{idx}_{label.lower()}"
            rationale_wrong = option.get("rationale_wrong") if option_idx != correct_index else None
            options.append(
                MCQOption(
                    id=option_id,
                    label=label,
                    text=option["text"],
                    rationale_wrong=rationale_wrong,
                )
            )

        correct_label = chr(ord("A") + correct_index)
        correct_option_id = options[correct_index].id if options else None

        exercises.append(
            MCQExercise(
                id=f"{lesson_id}_mcq_{idx}",
                lo_id=lo_id,
                cognitive_level=mcq.get("cognitive_level"),
                estimated_difficulty=mcq.get("difficulty", "Medium"),
                misconceptions_used=mcq.get("misconceptions", []),
                stem=mcq["stem"],
                options=options,
                answer_key=MCQAnswerKey(
                    label=correct_label,
                    option_id=correct_option_id,
                    rationale_right=mcq.get("correct_rationale"),
                ),
            )
        )

    for idx, short_answer in enumerate(short_answers or [], start=1):
        lo_candidates = list(short_answer.get("learning_objectives_covered", []))
        sa_lo_id: str | None = None

        if unit_lo_ids:
            sa_lo_id = next((candidate for candidate in lo_candidates if candidate in unit_lo_ids), None)
            if sa_lo_id is None:
                lo_index = short_answer.get("lo_index")
                sa_lo_id = unit_lo_ids[lo_index - 1] if isinstance(lo_index, int) and 1 <= lo_index <= len(unit_lo_ids) else unit_lo_ids[0]
        else:
            sa_lo_id = short_answer.get("lo_id")

        if not sa_lo_id:
            sa_lo_id = unit_lo_ids[0] if unit_lo_ids else f"{lesson_id}_lo_{idx}"

        wrong_answers = [
            WrongAnswer(
                answer=wrong.get("answer", ""),
                explanation=wrong.get("explanation", ""),
                misconception_ids=list(wrong.get("misconception_ids", []) or []),
            )
            for wrong in short_answer.get("wrong_answers", [])
        ]

        exercises.append(
            ShortAnswerExercise(
                id=f"{lesson_id}_sa_{idx}",
                lo_id=sa_lo_id,
                cognitive_level=short_answer.get("cognitive_level"),
                estimated_difficulty=short_answer.get("difficulty"),
                misconceptions_used=list(short_answer.get("misconceptions", [])),
                stem=short_answer.get("stem", ""),
                canonical_answer=short_answer.get("canonical_answer", ""),
                acceptable_answers=list(short_answer.get("acceptable_answers", [])),
                wrong_answers=wrong_answers,
                explanation_correct=short_answer.get("explanation_correct", ""),
            )
        )

    return LessonPackage(
        meta=meta,
        unit_learning_objective_ids=unit_lo_ids,
        glossary={"terms": glossary_models},
        mini_lesson=mini_lesson,
        exercises=exercises,
        misconceptions=misconceptions or [],
        confusables=confusables or [],
    )


def create_lesson_data(
    lesson_id: str,
    *,
    title: str,
    learner_level: str,
    source_material: str,
    package: LessonPackage,
    flow_run_id: uuid.UUID | None = None,
    unit_learning_objectives: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create an ORM-ready lesson dictionary from a package."""

    return {
        "id": lesson_id,
        "flow_run_id": flow_run_id,
        "title": title,
        "learner_level": learner_level,
        "source_material": source_material,
        "package": package.model_dump(),
        "package_version": 1,
        "unit_learning_objectives": unit_learning_objectives,
    }


def create_sample_flow_run(
    flow_run_id: uuid.UUID,
    lesson_id: str,
    lesson_data: dict[str, Any],
    *,
    user_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Create a completed flow run record for a lesson."""

    now = datetime.now(UTC)
    package = lesson_data["package"]
    raw_unit_objectives = lesson_data.get("unit_learning_objectives", []) or []
    objectives = [obj.get("text") if isinstance(obj, dict) else str(obj) for obj in raw_unit_objectives]
    objective_ids = [obj.get("id") for obj in raw_unit_objectives if isinstance(obj, dict) and obj.get("id") is not None]
    key_terms = [term["term"] for term in package.get("glossary", {}).get("terms", [])]
    exercises = package.get("exercises", [])
    mcq_exercises = [ex for ex in exercises if ex.get("exercise_type") == "mcq"]
    short_answer_exercises = [ex for ex in exercises if ex.get("exercise_type") == "short_answer"]
    total_mcqs = len(mcq_exercises)
    total_short_answers = len(short_answer_exercises)
    lo_coverage = len({exercise.get("lo_id") for exercise in exercises if exercise.get("lo_id")}) if exercises else 0

    return {
        "id": flow_run_id,
        "user_id": user_id,
        "flow_name": "lesson_creation",
        "status": "completed",
        "execution_mode": "sync",
        "current_step": None,
        "step_progress": 6,
        "total_steps": 6,
        "progress_percentage": 100.0,
        "created_at": now,
        "updated_at": now,
        "started_at": now,
        "completed_at": now,
        "last_heartbeat": now,
        "total_tokens": 15420,
        "total_cost": 0.0771,
        "execution_time_ms": 45000,
        "inputs": {
            "topic": lesson_data["title"],
            "source_material": lesson_data["source_material"],
            "learner_level": lesson_data["learner_level"],
            "voice": "narrative",
            "learning_objectives": objectives,
            "lesson_objective": objectives[0] if objectives else "",
            "learning_objective_ids": objective_ids,
        },
        "outputs": {
            "topic": lesson_data["title"],
            "learner_level": lesson_data["learner_level"],
            "voice": "narrative",
            "learning_objectives": objectives,
            "learning_objective_ids": objective_ids,
            "key_concepts": key_terms,
            "misconceptions": package.get("misconceptions", []),
            "confusables": package.get("confusables", []),
            "glossary": package.get("glossary", {}),
            "mini_lesson": package.get("mini_lesson"),
            "mcqs": {
                "metadata": {"total_mcqs": total_mcqs, "lo_coverage": lo_coverage},
                "mcqs": mcq_exercises,
            },
            "short_answers": {
                "metadata": {"total_short_answers": total_short_answers},
                "short_answers": short_answer_exercises,
            },
        },
        "flow_metadata": {"lesson_id": lesson_id, "package_version": lesson_data.get("package_version", 1)},
        "error_message": None,
    }


def create_sample_step_runs(flow_run_id: uuid.UUID, lesson_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Create representative step run records for a completed flow."""

    now = datetime.now(UTC)
    package = lesson_data["package"]
    raw_unit_objectives = lesson_data.get("unit_learning_objectives", []) or []
    objectives = [obj.get("text") if isinstance(obj, dict) else str(obj) for obj in raw_unit_objectives]
    objective_ids = [obj.get("id") for obj in raw_unit_objectives if isinstance(obj, dict) and obj.get("id") is not None]
    key_terms = [term["term"] for term in package.get("glossary", {}).get("terms", [])]
    exercises = package.get("exercises", [])
    mcq_exercises = [ex for ex in exercises if ex.get("exercise_type") == "mcq"]
    short_answer_exercises = [ex for ex in exercises if ex.get("exercise_type") == "short_answer"]
    short_answer_lo_coverage = len({ex.get("lo_id") for ex in short_answer_exercises if ex.get("lo_id")}) if short_answer_exercises else 0
    misconceptions = package.get("misconceptions", [])
    confusables = package.get("confusables", [])

    step_definitions = [
        {
            "step_name": "extract_lesson_metadata",
            "step_order": 1,
            "inputs": {"title": lesson_data["title"]},
            "outputs": {
                "learning_objectives": objectives,
                "learning_objective_ids": objective_ids,
                "key_concepts": key_terms[:3],
            },
            "prompt_file": "extract_lesson_metadata.md",
            "tokens_used": 2100,
            "cost_estimate": 0.0105,
            "execution_time_ms": 3500,
        },
        {
            "step_name": "generate_misconception_bank",
            "step_order": 2,
            "inputs": {
                "learning_objectives": objectives,
                "learning_objective_ids": objective_ids,
                "key_concepts": key_terms[:3],
            },
            "outputs": {"misconceptions": misconceptions},
            "prompt_file": "generate_misconception_bank.md",
            "tokens_used": 2200,
            "cost_estimate": 0.011,
            "execution_time_ms": 5000,
        },
        {
            "step_name": "generate_mini_lesson",
            "step_order": 3,
            "inputs": {
                "topic": lesson_data["title"],
                "learner_level": lesson_data["learner_level"],
                "voice": "narrative",
                "learning_objectives": objectives,
                "learning_objective_ids": objective_ids,
                "source_material": lesson_data["source_material"],
            },
            "outputs": {"mini_lesson": package.get("mini_lesson")},
            "prompt_file": "generate_mini_lesson.md",
            "tokens_used": 1800,
            "cost_estimate": 0.009,
            "execution_time_ms": 4200,
        },
        {
            "step_name": "generate_glossary",
            "step_order": 4,
            "inputs": {
                "lesson_title": lesson_data["title"],
                "key_concepts": key_terms,
            },
            "outputs": {"terms": package.get("glossary", {}).get("terms", [])},
            "prompt_file": "generate_glossary.md",
            "tokens_used": 1600,
            "cost_estimate": 0.008,
            "execution_time_ms": 3800,
        },
        {
            "step_name": "generate_mcqs",
            "step_order": 5,
            "inputs": {
                "topic": lesson_data["title"],
                "learner_level": lesson_data["learner_level"],
                "voice": "narrative",
                "learning_objectives": objectives,
                "learning_objective_ids": objective_ids,
                "misconceptions": misconceptions,
                "confusables": confusables,
                "glossary": package.get("glossary", {}),
            },
            "outputs": {
                "metadata": {
                    "total_mcqs": len(mcq_exercises),
                    "lo_coverage": len({ex.get("lo_id") for ex in mcq_exercises if ex.get("lo_id")}) if mcq_exercises else 0,
                },
                "mcqs": mcq_exercises,
            },
            "prompt_file": "generate_mcqs.md",
            "tokens_used": 3500,
            "cost_estimate": 0.0175,
            "execution_time_ms": 8000,
        },
        {
            "step_name": "generate_short_answers",
            "step_order": 6,
            "inputs": {
                "lesson_title": lesson_data["title"],
                "lesson_objective": objectives[0] if objectives else "",
                "learner_level": lesson_data["learner_level"],
                "voice": "narrative",
                "learning_objectives": objectives,
                "learning_objective_ids": objective_ids,
                "mini_lesson": package.get("mini_lesson"),
                "glossary": package.get("glossary", {}),
                "misconceptions": misconceptions,
                "mcq_stems": [ex.get("stem") for ex in mcq_exercises],
            },
            "outputs": {
                "metadata": {
                    "total_short_answers": len(short_answer_exercises),
                    "lo_coverage": short_answer_lo_coverage,
                },
                "short_answers": short_answer_exercises,
            },
            "prompt_file": "generate_short_answers.md",
            "tokens_used": 3200,
            "cost_estimate": 0.016,
            "execution_time_ms": 6500,
        },
    ]

    step_runs: list[dict[str, Any]] = []
    for definition in step_definitions:
        step_runs.append(
            {
                "id": uuid.uuid4(),
                "flow_run_id": flow_run_id,
                "llm_request_id": uuid.uuid4(),
                "step_name": definition["step_name"],
                "step_order": definition["step_order"],
                "status": "completed",
                "inputs": definition["inputs"],
                "outputs": definition["outputs"],
                "tokens_used": definition["tokens_used"],
                "cost_estimate": definition["cost_estimate"],
                "execution_time_ms": definition["execution_time_ms"],
                "error_message": None,
                "step_metadata": {"prompt_file": definition["prompt_file"]},
                "created_at": now,
                "updated_at": now,
                "completed_at": now,
            }
        )

    return step_runs


def create_sample_llm_requests(
    step_runs: list[dict[str, Any]],
    *,
    user_id: uuid.UUID | None = None,
    lesson_title: str,
) -> list[dict[str, Any]]:
    """Create LLM request records that mirror the step runs."""

    now = datetime.now(UTC)
    llm_requests: list[dict[str, Any]] = []

    prompt_map = {
        "extract_lesson_metadata": "Extract learning objectives and key concepts from the provided source material.",
        "generate_misconception_bank": "Produce likely misconceptions learners might hold about this lesson.",
        "generate_mini_lesson": "Write a cohesive mini-lesson covering the key ideas.",
        "generate_glossary": "Assemble a concise glossary for the important terms.",
        "generate_mcqs": "Create multiple-choice questions with rationales and metadata for each objective.",
        "generate_short_answers": "Craft short-answer questions with canonical, acceptable, and common wrong responses.",
    }

    for step_run in step_runs:
        llm_request_id = step_run["llm_request_id"]
        if not llm_request_id:
            continue

        step_name = step_run["step_name"]
        description = prompt_map.get(step_name, f"Process step: {step_name}.")
        user_message = f"Lesson title: {lesson_title}. {description} Use the latest inputs and maintain a helpful tone."

        messages = [
            {"role": "system", "content": "You are an expert educational content creator."},
            {"role": "user", "content": user_message},
        ]

        llm_requests.append(
            {
                "id": llm_request_id,
                "user_id": user_id,
                "api_variant": "responses",
                "provider": "openai",
                "model": "gpt-5-nano",
                "provider_response_id": f"chatcmpl-{uuid.uuid4().hex[:20]}",
                "system_fingerprint": "fp_" + uuid.uuid4().hex[:10],
                "temperature": 0.7,
                "max_output_tokens": 2000,
                "messages": messages,
                "additional_params": {},
                "request_payload": {
                    "model": "gpt-5-nano",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
                "response_content": json.dumps(step_run["outputs"]),
                "response_raw": step_run["outputs"],
                "tokens_used": step_run.get("tokens_used", 0),
                "input_tokens": None,
                "output_tokens": None,
                "cost_estimate": step_run.get("cost_estimate", 0.0),
                "status": "completed",
                "execution_time_ms": step_run.get("execution_time_ms", 0),
                "error_message": None,
                "error_type": None,
                "retry_attempt": 1,
                "cached": False,
                "response_created_at": now,
                "created_at": now,
                "updated_at": now,
            }
        )

    return llm_requests


async def load_and_create_users(db_session: Any, users_file: Path, args: Any) -> tuple[dict[str, int], dict[str, dict[str, Any]]]:
    """Load users from JSON and create them in the database."""
    users_data = load_json_file(users_file)

    sample_user_ids: dict[str, int] = {}
    user_snapshots: dict[str, dict[str, Any]] = {}

    user_repo = UserRepo(db_session)
    user_service = UserService(user_repo)

    if args.verbose:
        print(f"👥 Creating {len(users_data)} users...")

    for user_spec in users_data:
        key = user_spec["key"]
        email = user_spec["email"]

        # Check if user already exists
        existing_user = user_repo.by_email(email)
        if existing_user:
            if args.verbose:
                print(f"   • User {email} already exists, reusing...")
            user = existing_user
        else:
            password_hash = user_service._hash_password(user_spec["password"])
            user = user_repo.create(
                email=email,
                password_hash=password_hash,
                name=user_spec["name"],
                role=user_spec.get("role", "learner"),
                is_active=user_spec.get("is_active", True),
            )
            if args.verbose:
                print(f"   • Created user {email}")

        user_id = cast(int, user.id)
        sample_user_ids[key] = user_id
        user_snapshots[key] = {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }

    return sample_user_ids, user_snapshots


async def process_unit_from_json(
    db_session: Any,
    unit_spec: dict[str, Any],
    user_ids: dict[str, int],
    args: Any,
) -> dict[str, Any]:
    """Process a single unit from JSON spec and create all related records."""

    if args.verbose:
        print(f"\n📦 Processing unit: {unit_spec['title']}")

    # Resolve owner
    owner_key = unit_spec.get("owner_key", "brian")
    owner_id = user_ids.get(owner_key)
    if not owner_id:
        raise ValueError(f"Unknown owner_key: {owner_key}")

    seed_timestamp = datetime.utcnow()
    bucket_name = os.getenv("OBJECT_STORE_BUCKET", "lantern-room")

    # Generate IDs if not provided
    unit_id = unit_spec.get("id") or str(uuid.uuid4())

    # Clean up existing unit if it exists
    existing_unit = await db_session.get(UnitModel, unit_id)
    if existing_unit:
        if args.verbose:
            print(f"   • Deleting existing unit: {existing_unit.title}")
        # Delete in correct order to avoid FK violations
        from modules.content.models import UserMyUnitModel
        from modules.learning_session.models import LearningSessionModel, UnitSessionModel

        await db_session.execute(delete(UserMyUnitModel).where(UserMyUnitModel.unit_id == unit_id))
        await db_session.execute(delete(LearningSessionModel).where(LearningSessionModel.unit_id == unit_id))
        await db_session.execute(delete(UnitSessionModel).where(UnitSessionModel.unit_id == unit_id))
        await db_session.execute(delete(LessonModel).where(LessonModel.unit_id == unit_id))
        await db_session.execute(delete(UnitResourceModel).where(UnitResourceModel.unit_id == unit_id))
        await db_session.delete(existing_unit)
        await db_session.flush()

    # Process art image if provided
    art_image_id = None
    if unit_spec.get("art_image"):
        img_spec = unit_spec["art_image"]
        art_image_id = uuid.UUID(img_spec["id"]) if "id" in img_spec else uuid.uuid4()

        # Delete existing image if it exists
        existing_image = await db_session.get(ImageModel, art_image_id)
        if existing_image:
            await db_session.delete(existing_image)
            await db_session.flush()

        image_model = ImageModel(
            id=art_image_id,
            user_id=owner_id,
            s3_key=img_spec["s3_key"],
            s3_bucket=img_spec.get("s3_bucket", bucket_name),
            filename=img_spec["filename"],
            content_type=img_spec["content_type"],
            file_size=img_spec["file_size"],
            width=img_spec.get("width"),
            height=img_spec.get("height"),
            alt_text=img_spec.get("alt_text"),
            description=img_spec.get("description"),
            created_at=seed_timestamp,
            updated_at=seed_timestamp,
        )
        db_session.add(image_model)
        await db_session.flush()

    # Process podcast audio if provided
    podcast_audio_id = None
    if unit_spec.get("podcast_audio"):
        audio_spec = unit_spec["podcast_audio"]
        podcast_audio_id = uuid.UUID(audio_spec["id"]) if "id" in audio_spec else uuid.uuid4()

        # Delete existing audio if it exists
        existing_audio = await db_session.get(AudioModel, podcast_audio_id)
        if existing_audio:
            await db_session.delete(existing_audio)
            await db_session.flush()

        audio_model = AudioModel(
            id=podcast_audio_id,
            user_id=owner_id,
            s3_key=audio_spec["s3_key"],
            s3_bucket=audio_spec.get("s3_bucket", bucket_name),
            filename=audio_spec["filename"],
            content_type=audio_spec["content_type"],
            file_size=audio_spec["file_size"],
            duration_seconds=audio_spec.get("duration_seconds"),
            bitrate_kbps=audio_spec.get("bitrate_kbps"),
            sample_rate_hz=audio_spec.get("sample_rate_hz"),
            transcript=unit_spec.get("podcast_transcript"),
            created_at=seed_timestamp,
            updated_at=seed_timestamp,
        )
        db_session.add(audio_model)
        await db_session.flush()

    # Create unit model
    lesson_ids = []
    for lesson_spec in unit_spec.get("lessons", []):
        lesson_id = lesson_spec.get("id") or str(uuid.uuid4())
        lesson_ids.append(lesson_id)

    unit_model = UnitModel(
        id=unit_id,
        title=unit_spec["title"],
        description=unit_spec["description"],
        learner_level=unit_spec["learner_level"],
        lesson_order=lesson_ids,
        learning_objectives=unit_spec.get("learning_objectives", []),
        target_lesson_count=unit_spec.get("target_lesson_count", len(lesson_ids)),
        source_material=unit_spec.get("source_material"),
        generated_from_topic=unit_spec.get("generated_from_topic", True),
        flow_type="standard",
        status="completed",
        creation_progress=None,
        error_message=None,
        user_id=owner_id,
        is_global=unit_spec.get("is_global", False),
        art_image_description=unit_spec.get("art_image_description"),
        podcast_transcript=unit_spec.get("podcast_transcript"),
        podcast_voice=unit_spec.get("podcast_voice"),
        podcast_generated_at=seed_timestamp,
        art_image_id=art_image_id,
        podcast_audio_object_id=podcast_audio_id,
    )
    db_session.add(unit_model)
    await db_session.flush()

    # Process lessons
    for lesson_spec in unit_spec.get("lessons", []):
        lesson_id = lesson_spec.get("id") or str(uuid.uuid4())
        flow_run_id = uuid.uuid4()

        package = build_lesson_package(
            lesson_id,
            title=lesson_spec["title"],
            learner_level=lesson_spec["learner_level"],
            objectives=lesson_spec.get("objectives", []),
            glossary_terms=lesson_spec.get("glossary_terms", []),
            mini_lesson=lesson_spec.get("mini_lesson", ""),
            mcqs=lesson_spec.get("mcqs", []),
            short_answers=lesson_spec.get("short_answers", []),
            misconceptions=lesson_spec.get("misconceptions"),
            confusables=lesson_spec.get("confusables"),
        )

        lesson_data = create_lesson_data(
            lesson_id,
            title=lesson_spec["title"],
            learner_level=lesson_spec["learner_level"],
            source_material=lesson_spec.get("source_material"),
            package=package,
            flow_run_id=flow_run_id,
            unit_learning_objectives=lesson_spec.get("objectives"),
        )

        # Create flow run, step runs, and LLM requests
        flow_run_data = create_sample_flow_run(flow_run_id, lesson_id, lesson_data, user_id=None)
        step_runs = create_sample_step_runs(flow_run_id, lesson_data)
        llm_requests = create_sample_llm_requests(step_runs, user_id=None, lesson_title=lesson_spec["title"])

        db_session.add(FlowRunModel(**flow_run_data))
        await db_session.flush()

        for llm_data in llm_requests:
            db_session.add(LLMRequestModel(**llm_data))
        await db_session.flush()

        for step_data in step_runs:
            db_session.add(FlowStepRunModel(**step_data))
        await db_session.flush()

        # Create lesson
        lesson_db_dict = {key: value for key, value in lesson_data.items() if key != "unit_learning_objectives"}
        lesson_db_dict["unit_id"] = unit_id
        lesson_db_dict["podcast_transcript"] = unit_spec.get("podcast_transcript")
        lesson_db_dict["podcast_voice"] = unit_spec.get("podcast_voice")
        lesson_db_dict["podcast_audio_object_id"] = podcast_audio_id
        lesson_db_dict["podcast_generated_at"] = seed_timestamp
        lesson_db_dict["podcast_duration_seconds"] = lesson_spec.get("podcast_duration_seconds", 180)

        db_session.add(LessonModel(**lesson_db_dict))
        await db_session.flush()

        if args.verbose:
            print(f"   • Created lesson: {lesson_spec['title']}")

    # Process resources if provided
    photo_resource_ids: list[uuid.UUID] = []
    for resource_spec in unit_spec.get("resources", []):
        resource_id = uuid.UUID(resource_spec["resource_id"]) if "resource_id" in resource_spec else uuid.uuid4()

        # Clean up existing
        await db_session.execute(delete(UnitResourceModel).where(UnitResourceModel.resource_id == resource_id))
        existing_resource = await db_session.get(ResourceModel, resource_id)
        if existing_resource:
            await db_session.delete(existing_resource)
            await db_session.flush()

        # Create document if provided
        document_id = None
        if resource_spec.get("document"):
            doc_spec = resource_spec["document"]
            document_id = uuid.UUID(doc_spec["id"]) if "id" in doc_spec else uuid.uuid4()

            # Check if document already exists - if so, we'll reuse it
            existing_doc = await db_session.get(DocumentModel, document_id)
            if not existing_doc:
                document_model = DocumentModel(
                    id=document_id,
                    user_id=owner_id,
                    s3_key=doc_spec["s3_key"],
                    s3_bucket=doc_spec.get("s3_bucket", bucket_name),
                    filename=doc_spec["filename"],
                    content_type=doc_spec["content_type"],
                    file_size=doc_spec["file_size"],
                    created_at=seed_timestamp,
                    updated_at=seed_timestamp,
                )
                db_session.add(document_model)
                await db_session.flush()

        image_id: uuid.UUID | None = None
        if resource_spec.get("object_store_image_id"):
            image_id = uuid.UUID(str(resource_spec["object_store_image_id"]))

        if resource_spec.get("image"):
            img_spec = resource_spec["image"]
            image_id = image_id or (uuid.UUID(img_spec["id"]) if "id" in img_spec else uuid.uuid4())
            existing_image = await db_session.get(ImageModel, image_id)
            if not existing_image:
                image_model = ImageModel(
                    id=image_id,
                    user_id=img_spec.get("user_id", owner_id),
                    s3_key=img_spec["s3_key"],
                    s3_bucket=img_spec.get("s3_bucket", bucket_name),
                    filename=img_spec["filename"],
                    content_type=img_spec.get("content_type", "image/jpeg"),
                    file_size=img_spec.get("file_size", resource_spec.get("file_size", 0) or 0),
                    width=img_spec.get("width"),
                    height=img_spec.get("height"),
                    alt_text=img_spec.get("alt_text"),
                    description=img_spec.get("description"),
                    created_at=seed_timestamp,
                    updated_at=seed_timestamp,
                )
                db_session.add(image_model)
                await db_session.flush()

        if resource_spec.get("resource_type") == "photo" and image_id is not None:
            photo_resource_ids.append(resource_id)

        # Create resource
        resource_model = ResourceModel(
            id=resource_id,
            user_id=owner_id,
            resource_type=resource_spec["resource_type"],
            filename=resource_spec.get("filename"),
            source_url=resource_spec.get("source_url"),
            extracted_text=resource_spec.get("extracted_text", ""),
            extraction_metadata=resource_spec.get("metadata", {}),
            file_size=resource_spec.get("file_size"),
            object_store_document_id=document_id,
            object_store_image_id=image_id,
            created_at=seed_timestamp,
            updated_at=seed_timestamp,
        )
        db_session.add(resource_model)
        await db_session.flush()

        # Link to unit
        db_session.add(UnitResourceModel(unit_id=unit_id, resource_id=resource_id))
        await db_session.flush()

        if args.verbose:
            label = resource_spec.get("filename") or resource_spec.get("source_url") or str(resource_id)
            print(f"   • Created resource: {label} ({resource_spec['resource_type']})")

    # Seed optional learning conversations (coach) tied to the new resources
    conversations_section = unit_spec.get("learning_conversations") or {}
    if isinstance(conversations_section, dict):
        coach_conversations = conversations_section.get("coach", [])
    else:
        coach_conversations = []

    # Support legacy key until all seed files migrate
    if not coach_conversations:
        coach_conversations = unit_spec.get("learning_coach_conversations", [])

    for conversation_spec in coach_conversations:
        conversation_id = uuid.UUID(conversation_spec["id"]) if "id" in conversation_spec else uuid.uuid4()
        existing_conversation = await db_session.get(ConversationModel, conversation_id)
        if existing_conversation:
            await db_session.delete(existing_conversation)
            await db_session.flush()

        participant_key = conversation_spec.get("user_key", owner_key)
        participant_id = user_ids.get(participant_key)
        if not participant_id:
            raise ValueError(f"Unknown user_key for conversation: {participant_key}")

        metadata = dict(conversation_spec.get("metadata", {}))
        resource_ids = [uuid.UUID(str(value)) for value in conversation_spec.get("resource_ids", [])]
        if resource_ids:
            metadata.setdefault("resource_ids", [str(resource_id) for resource_id in resource_ids])

        messages = conversation_spec.get("messages", [])
        message_count = len(messages)
        conversation = ConversationModel(
            id=conversation_id,
            user_id=participant_id,
            conversation_type="learning_coach",
            title=conversation_spec.get("title"),
            status=conversation_spec.get("status", "active"),
            conversation_metadata=metadata,
            message_count=message_count,
            created_at=seed_timestamp,
            updated_at=seed_timestamp,
            last_message_at=seed_timestamp if message_count else None,
        )
        db_session.add(conversation)
        await db_session.flush()

        message_base_time = seed_timestamp
        for index, message_spec in enumerate(messages, start=1):
            offset_seconds = message_spec.get("offset_seconds")
            message_time = message_base_time if offset_seconds is None else message_base_time + timedelta(seconds=float(offset_seconds))
            conversation_message = ConversationMessageModel(
                conversation_id=conversation_id,
                role=message_spec["role"],
                content=message_spec["content"],
                message_order=index,
                llm_request_id=None,
                tokens_used=message_spec.get("tokens_used"),
                cost_estimate=message_spec.get("cost_estimate"),
                message_metadata=message_spec.get("metadata"),
                created_at=message_time,
                updated_at=message_time,
            )
            db_session.add(conversation_message)
            conversation.last_message_at = message_time
            conversation.updated_at = message_time

        if resource_ids:
            missing_photos = [resource_id for resource_id in resource_ids if resource_id not in photo_resource_ids]
            if missing_photos and args.verbose:
                print(
                    "   • Conversation references non-photo resources:",
                    ", ".join(str(value) for value in missing_photos),
                )
        if args.verbose:
            print(f"   • Seeded learning coach conversation: {conversation.title or conversation_id}")

    await db_session.flush()

    return {
        "unit_id": unit_id,
        "title": unit_spec["title"],
        "lessons_count": len(unit_spec.get("lessons", [])),
        "resources_count": len(unit_spec.get("resources", [])),
    }


async def main() -> None:
    """Main function to create seed data from JSON files."""

    parser = argparse.ArgumentParser(description="Create seed data from JSON files")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress logs")
    parser.add_argument("--seed-data-dir", default="seed_data", help="Directory containing seed data JSON files")
    parser.add_argument("--unit-file", help="Process a specific unit JSON file")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        print("🔧 Verbose mode enabled")

    seed_data_dir = Path(args.seed_data_dir)
    if not seed_data_dir.is_absolute():
        seed_data_dir = Path(__file__).parent.parent / seed_data_dir

    print(f"🌱 Creating seed data from {seed_data_dir}")
    print()

    try:
        infra = infrastructure_provider()
        if args.verbose:
            print("🔄 Initializing infrastructure...")
        infra.initialize()

        # Load and create users
        with infra.get_session_context() as sync_session:
            users_file = seed_data_dir / "users.json"
            if not users_file.exists():
                print(f"❌ Users file not found: {users_file}")
                sys.exit(1)

            sample_user_ids, user_snapshots = await load_and_create_users(sync_session, users_file, args)

        # Process units
        async with infra.get_async_session_context() as db_session:
            units_processed = []

            if args.unit_file:
                # Process single unit file
                unit_file = Path(args.unit_file)
                if not unit_file.is_absolute():
                    unit_file = seed_data_dir / "units" / unit_file

                if not unit_file.exists():
                    print(f"❌ Unit file not found: {unit_file}")
                    sys.exit(1)

                unit_spec = load_json_file(unit_file)
                result = await process_unit_from_json(db_session, unit_spec, sample_user_ids, args)
                units_processed.append(result)
            else:
                # Process all unit files in the units directory
                units_dir = seed_data_dir / "units"
                if not units_dir.exists():
                    print(f"⚠️  Units directory not found: {units_dir}")
                else:
                    unit_files = sorted(units_dir.glob("*.json"))
                    # Skip template files
                    unit_files = [f for f in unit_files if not f.name.startswith("_")]

                    for unit_file in unit_files:
                        unit_spec = load_json_file(unit_file)
                        result = await process_unit_from_json(db_session, unit_spec, sample_user_ids, args)
                        units_processed.append(result)

            await db_session.commit()

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    # Print summary
    print("\n✅ Seed data created successfully!")
    print(f"   • Users: {len(user_snapshots)}")
    for snapshot in user_snapshots.values():
        role_label = "Admin" if snapshot["role"] == "admin" else "Learner"
        print(f"     - {role_label}: {snapshot['name']} <{snapshot['email']}>")

    print(f"\n   • Units: {len(units_processed)}")
    for unit_info in units_processed:
        print(f"     - {unit_info['title']} ({unit_info['lessons_count']} lessons, {unit_info['resources_count']} resources)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
