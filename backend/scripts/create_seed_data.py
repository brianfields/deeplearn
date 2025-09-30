#!/usr/bin/env python3
"""
Seed Data Creation Script

Summary of created artifacts:
- 4 users seeded with hashed passwords (credentials for local login):
  • Admin — Brian Fields (thecriticalpath@gmail.com) / password: epsilon
  • Admin — Eylem Ozaslan (eylem.ozaslan@gmail.com) / password: epsilon
  • Learner — Epsilon cat (epsilon.cat@example.com) / password: epsilon
  • Learner — Nova cat (nova.cat@example.com) / password: epsilon
- 1 completed global unit about “Cats in Istanbul” shared by Eylem and containing three fully packaged lessons.
- 1 completed private unit about “Gradient Descent Mastery” owned by Brian with two packaged lessons.
- Per-lesson flow runs, step runs, and LLM request records mirroring the lesson generation pipeline.
- Learning sessions and unit sessions for the learners so UI dashboards have ready-made progress data.

Creates sample unit and lesson data using the canonical package structure
without making actual LLM calls.
This creates realistic seed data for development and testing purposes.

Usage:
    python scripts/create_seed_data.py --verbose
    python scripts/create_seed_data.py --lesson "Neural Networks Basics" --concept "Backpropagation" --verbose
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

from modules.content.models import (
    LessonModel,
    UnitModel,  # Import UnitModel so SQLAlchemy knows about the units table
)
from modules.content.package_models import GlossaryTerm, LessonPackage, MCQAnswerKey, MCQExercise, MCQOption, Meta, Objective
from modules.flow_engine.models import FlowRunModel, FlowStepRunModel
from modules.infrastructure.public import infrastructure_provider
from modules.learning_session.models import LearningSessionModel, SessionStatus, UnitSessionModel
from modules.llm_services.models import LLMRequestModel
from modules.object_store.models import AudioModel, ImageModel
from modules.user.repo import UserRepo
from modules.user.service import UserService


def build_lesson_package(
    lesson_id: str,
    *,
    title: str,
    learner_level: str,
    objectives: list[dict[str, str]],
    glossary_terms: list[dict[str, str]],
    mini_lesson: str,
    mcqs: list[dict[str, Any]],
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

    objective_models = [
        Objective(
            id=f"{lesson_id}_lo_{idx}",
            text=obj["text"],
            bloom_level=obj.get("bloom_level"),
        )
        for idx, obj in enumerate(objectives, start=1)
    ]

    glossary_models = [
        GlossaryTerm(
            id=f"{lesson_id}_term_{idx}",
            term=term["term"],
            definition=term["definition"],
            micro_check=term.get("micro_check"),
        )
        for idx, term in enumerate(glossary_terms, start=1)
    ]

    exercises: list[MCQExercise] = []
    for idx, mcq in enumerate(mcqs, start=1):
        if objective_models:
            lo_index = max(1, min(mcq.get("lo_index", 1), len(objective_models)))
            lo_id = objective_models[lo_index - 1].id
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

    return LessonPackage(
        meta=meta,
        objectives=objective_models,
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
    objectives = [obj["text"] for obj in package.get("objectives", [])]
    key_terms = [term["term"] for term in package.get("glossary", {}).get("terms", [])]
    total_mcqs = len(package.get("exercises", []))
    lo_coverage = len({exercise["lo_id"] for exercise in package.get("exercises", [])}) if total_mcqs else 0

    return {
        "id": flow_run_id,
        "user_id": user_id,
        "flow_name": "lesson_creation",
        "status": "completed",
        "execution_mode": "sync",
        "current_step": None,
        "step_progress": total_mcqs,
        "total_steps": 5,
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
            "unit_source_material": lesson_data["source_material"],
            "learner_level": lesson_data["learner_level"],
            "voice": "narrative",
            "learning_objectives": objectives,
            "lesson_objective": objectives[0] if objectives else "",
        },
        "outputs": {
            "topic": lesson_data["title"],
            "learner_level": lesson_data["learner_level"],
            "voice": "narrative",
            "learning_objectives": objectives,
            "key_concepts": key_terms,
            "misconceptions": package.get("misconceptions", []),
            "confusables": package.get("confusables", []),
            "glossary": package.get("glossary", {}),
            "mini_lesson": package.get("mini_lesson"),
            "mcqs": {
                "metadata": {"total_mcqs": total_mcqs, "lo_coverage": lo_coverage},
                "mcqs": package.get("exercises", []),
            },
        },
        "flow_metadata": {"lesson_id": lesson_id, "package_version": lesson_data.get("package_version", 1)},
        "error_message": None,
    }


def create_sample_step_runs(flow_run_id: uuid.UUID, lesson_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Create representative step run records for a completed flow."""

    now = datetime.now(UTC)
    package = lesson_data["package"]
    objectives = [obj["text"] for obj in package.get("objectives", [])]
    key_terms = [term["term"] for term in package.get("glossary", {}).get("terms", [])]
    exercises = package.get("exercises", [])
    misconceptions = package.get("misconceptions", [])
    confusables = package.get("confusables", [])

    step_definitions = [
        {
            "step_name": "extract_lesson_metadata",
            "step_order": 1,
            "inputs": {"title": lesson_data["title"]},
            "outputs": {
                "learning_objectives": objectives,
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
                "unit_source_material": lesson_data["source_material"],
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
                "misconceptions": misconceptions,
                "confusables": confusables,
                "glossary": package.get("glossary", {}),
            },
            "outputs": {
                "mcqs": {
                    "metadata": {
                        "total_mcqs": len(exercises),
                        "lo_coverage": len({exercise["lo_id"] for exercise in exercises}) if exercises else 0,
                    },
                    "mcqs": exercises,
                }
            },
            "prompt_file": "generate_mcqs.md",
            "tokens_used": 3500,
            "cost_estimate": 0.0175,
            "execution_time_ms": 8000,
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


async def main() -> None:
    """Main function to create seed data."""

    parser = argparse.ArgumentParser(description="Create seed data for development and testing")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress logs")
    parser.add_argument("--output", help="Save a JSON summary of created entities")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        print("🔧 Verbose mode enabled")

    print("🌱 Creating seed data: Cats in Istanbul (global) + Gradient Descent (private)")
    print()

    sample_user_ids: dict[str, int] = {}
    user_snapshots: dict[str, dict[str, Any]] = {}
    units_output: list[dict[str, Any]] = []
    users_created_count = 0
    global_units_count = 0
    personal_units_count = 0
    learning_session_statuses: list[str] = []
    unit_session_statuses: list[str] = []

    try:
        infra = infrastructure_provider()
        if args.verbose:
            print("🔄 Initializing infrastructure...")
        infra.initialize()

        with infra.get_session_context() as sync_session:
            user_repo = UserRepo(sync_session)
            user_service = UserService(user_repo)

            if args.verbose:
                print("👥 Creating sample users (admins + learners)...")

            def _create_user(
                key: str,
                *,
                email: str,
                name: str,
                password: str,
                role: str = "learner",
                is_active: bool = True,
            ) -> int:
                password_hash = user_service._hash_password(password)
                user = user_repo.create(
                    email=email,
                    password_hash=password_hash,
                    name=name,
                    role=role,
                    is_active=is_active,
                )
                user_id = cast(int, user.id)
                sample_user_ids[key] = user_id
                user_snapshots[key] = {
                    "id": user_id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                }
                return user_id

            brian_admin_id = _create_user(
                "brian",
                email="thecriticalpath@gmail.com",
                name="Brian Fields",
                password="epsilon",
                role="admin",
            )
            _eylem_admin = _create_user(
                "eylem",
                email="eylem.ozaslan@gmail.com",
                name="Eylem Ozaslan",
                password="epsilon",
                role="admin",
            )
            epsilon_learner_id = _create_user(
                "epsilon",
                email="epsilon.cat@example.com",
                name="Epsilon cat",
                password="epsilon",
            )
            nova_learner_id = _create_user(
                "nova",
                email="nova.cat@example.com",
                name="Nova cat",
                password="epsilon",
            )

        if args.verbose:
            print("📦 Building lesson packages and database records...")

        async with infra.get_async_session_context() as db_session:
            units_spec = [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Cats in Istanbul: City Companions",
                    "description": "Discover how Istanbul's street cats thrive alongside the city's residents.",
                    "learner_level": "beginner",
                    "learning_objectives": [
                        {"lo_id": "cat_unit_lo_1", "text": "Describe the cultural role of Istanbul's street cats", "bloom_level": "Understand"},
                        {"lo_id": "cat_unit_lo_2", "text": "Identify best practices for caring for community cats", "bloom_level": "Apply"},
                        {"lo_id": "cat_unit_lo_3", "text": "Explain how urban planning supports feline welfare", "bloom_level": "Analyze"},
                    ],
                    "target_lesson_count": 3,
                    "source_material": "City reports on community cats, volunteer diaries, and Istanbul tourism guides.",
                    "generated_from_topic": True,
                    "is_global": True,
                    "owner_key": "eylem",
                    "lessons": [
                        {
                            "title": "Street Cat Legends of Kadıköy",
                            "learner_level": "beginner",
                            "source_material": "Community stories describing the famous fish market felines of Kadıköy.",
                            "objectives": [
                                {"text": "Summarize why Kadıköy is known for friendly street cats", "bloom_level": "Remember"},
                                {"text": "List community habits that keep cat colonies healthy", "bloom_level": "Understand"},
                            ],
                            "glossary_terms": [
                                {"term": "Kadıköy", "definition": "A vibrant district on Istanbul's Asian side known for its markets and resident cats."},
                                {"term": "Colony Care", "definition": "Daily routines locals follow to feed and monitor a group of community cats."},
                                {"term": "Sahiplenmek", "definition": "Turkish for adopting or taking responsibility for an animal."},
                            ],
                            "mini_lesson": "Kadıköy's fish market blends aromas of the sea with the patter of paws. Residents and vendors place bowls of anchovies beside their stalls, making the cats unofficial mascots. Volunteers organize feeding schedules, rotate water bowls, and ensure every cat has a sheltered nook away from traffic. As a result, locals view community cats as neighbors—protectors of the market and keepers of tradition.",
                            "mcqs": [
                                {
                                    "stem": "Which daily practice keeps the Kadıköy cat colony thriving?",
                                    "options": [
                                        {"text": "Volunteers share feeding and water duties"},
                                        {"text": "Cats are confined indoors during market hours", "rationale_wrong": "The cats roam freely; confinement would disrupt the tradition."},
                                        {"text": "Vendors discourage tourists from interacting", "rationale_wrong": "Tourists are encouraged to meet the cats respectfully."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": "Understand",
                                    "difficulty": "Easy",
                                    "misconceptions": ["cats_need_no_care"],
                                    "correct_rationale": "Shared feeding schedules keep every cat healthy and visible to caretakers.",
                                },
                                {
                                    "stem": "Why do locals say the cats are part of Kadıköy's identity?",
                                    "options": [
                                        {"text": "They guard the fish market at night"},
                                        {"text": "They appear in city council meetings", "rationale_wrong": "Cats are beloved but do not attend council meetings."},
                                        {"text": "They symbolize kindness between residents and animals"},
                                    ],
                                    "correct_index": 2,
                                    "cognitive_level": "Analyze",
                                    "difficulty": "Medium",
                                    "misconceptions": ["cats_are_pests"],
                                    "correct_rationale": "The cats reflect everyday compassion in Kadıköy's community life.",
                                },
                            ],
                        },
                        {
                            "title": "Galata's Rooftop Guardians",
                            "learner_level": "beginner",
                            "source_material": "Travel journals describing sunset photography tours featuring Galata Tower cats.",
                            "objectives": [
                                {"text": "Explain how rooftop habitats keep cats safe", "bloom_level": "Understand"},
                                {"text": "Identify respectful ways visitors interact with Galata cats", "bloom_level": "Apply"},
                            ],
                            "glossary_terms": [
                                {"term": "Galata Tower", "definition": "Historic watchtower overlooking the Bosphorus, home to many friendly cats."},
                                {"term": "Sunset Stewards", "definition": "Volunteers who provide water and shaded rest stops during evening tours."},
                                {"term": "Rooftop Habitat", "definition": "Elevated resting spots built to keep cats away from narrow traffic lanes."},
                            ],
                            "mini_lesson": "As the sun dips behind the Bosphorus, photographers gather near Galata Tower. Locals quietly lay out cushions on rooftops, guiding the cats to safe perches away from crowded stairwells. Visitors learn that a slow blink and a gentle approach keep the cats calm. The tower's caretakers chart feeding stations on a shared map so every cat receives care, even during the busiest tourist season.",
                            "mcqs": [
                                {
                                    "stem": "What is the main purpose of Galata's rooftop habitats?",
                                    "options": [
                                        {"text": "To provide elevated shelters away from traffic"},
                                        {"text": "To display cats as part of a paid exhibit", "rationale_wrong": "Habitat spaces are free community efforts, not exhibits."},
                                        {"text": "To keep cats from interacting with visitors", "rationale_wrong": "Visitors are encouraged to interact calmly with the cats."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": "Apply",
                                    "difficulty": "Easy",
                                    "misconceptions": ["cats_prefer_ground"],
                                    "correct_rationale": "Elevated shelters keep cats safe from sudden traffic and provide shade.",
                                },
                                {
                                    "stem": "How should tourists greet the Galata cats during sunset tours?",
                                    "options": [
                                        {"text": "Approach slowly and offer a relaxed blink"},
                                        {"text": "Pick them up immediately for photos", "rationale_wrong": "Picking up cats without consent can stress them."},
                                        {"text": "Use flash photography to capture attention", "rationale_wrong": "Flash startles cats and is discouraged."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": "Apply",
                                    "difficulty": "Easy",
                                    "misconceptions": ["cats_like_flash"],
                                    "correct_rationale": "A calm greeting mirrors how volunteers interact with the rooftop guardians.",
                                },
                            ],
                        },
                        {
                            "title": "Bosphorus Ferry Felines",
                            "learner_level": "beginner",
                            "source_material": "Transport authority memos and conductor notes on caring for ferry cats.",
                            "objectives": [
                                {"text": "Describe the ferry schedule that supports feeding routines", "bloom_level": "Understand"},
                                {"text": "Recognize community partnerships that sponsor veterinary care", "bloom_level": "Remember"},
                            ],
                            "glossary_terms": [
                                {"term": "Vapur", "definition": "Turkish word for traditional passenger ferries crossing the Bosphorus."},
                                {"term": "Harbor Haven", "definition": "Designated corner of the ferry terminal reserved for cat shelters."},
                                {"term": "Evening Clinic", "definition": "Weekly veterinary check run by volunteers after the last ferry."},
                            ],
                            "mini_lesson": "Ferry conductors know their feline passengers by name. Before the morning rush, they place kibble in sheltered crates near the gangway. The harbor authority funds weekly veterinary rounds, while commuters donate blankets during winter. The cats repay the kindness by greeting passengers and keeping warehouses free of rodents, making them cherished crew members.",
                            "mcqs": [
                                {
                                    "stem": "Why do ferry conductors feed cats before the morning rush?",
                                    "options": [
                                        {"text": "To keep the gangway clear and cats satisfied"},
                                        {"text": "To train cats to stay inside the ticket office", "rationale_wrong": "Cats are free to roam the docks."},
                                        {"text": "To encourage cats to board ferries with commuters", "rationale_wrong": "Cats remain near the terminals rather than riding."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": "Understand",
                                    "difficulty": "Easy",
                                    "misconceptions": ["cats_eat_anytime"],
                                    "correct_rationale": "Feeding before rush hour keeps walkways tidy and cats content.",
                                },
                                {
                                    "stem": "Who sponsors veterinary care for the ferry felines?",
                                    "options": [
                                        {"text": "A partnership between the harbor authority and volunteers"},
                                        {"text": "Only private pet clinics", "rationale_wrong": "Public-private collaboration keeps care consistent."},
                                        {"text": "Passengers paying a cat ticket", "rationale_wrong": "There is no separate cat ticket; donations are optional."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": "Remember",
                                    "difficulty": "Medium",
                                    "misconceptions": ["care_is_unfunded"],
                                    "correct_rationale": "Community partnerships ensure regular health checks.",
                                },
                            ],
                        },
                    ],
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Gradient Descent Mastery",
                    "description": "A focused look at optimization fundamentals for machine learning practitioners.",
                    "learner_level": "intermediate",
                    "learning_objectives": [
                        {"lo_id": "grad_unit_lo_1", "text": "Explain how gradient descent updates parameters", "bloom_level": "Understand"},
                        {"lo_id": "grad_unit_lo_2", "text": "Compare batch, stochastic, and mini-batch strategies", "bloom_level": "Analyze"},
                    ],
                    "target_lesson_count": 2,
                    "source_material": "Lecture notes on convex optimization, annotated Python notebooks, and practical training logs.",
                    "generated_from_topic": True,
                    "is_global": False,
                    "owner_key": "brian",
                    "lessons": [
                        {
                            "title": "Gradient Descent Fundamentals",
                            "learner_level": "intermediate",
                            "source_material": "Walk-through of loss landscape intuition with quadratic examples and contour diagrams.",
                            "objectives": [
                                {"text": "State the gradient descent update rule", "bloom_level": "Remember"},
                                {"text": "Interpret learning rate effects on convergence", "bloom_level": "Analyze"},
                            ],
                            "glossary_terms": [
                                {"term": "Learning Rate", "definition": "Scalar that scales the gradient step during optimization."},
                                {"term": "Loss Landscape", "definition": "Surface describing how the loss changes with model parameters."},
                                {"term": "Convergence", "definition": "Process of iteratively approaching an optimum."},
                            ],
                            "mini_lesson": "Gradient descent walks downhill on a loss landscape by following the negative gradient. Choosing the learning rate balances progress with stability. Too small and updates crawl; too large and the algorithm overshoots the valley. Visualizing contour plots helps practitioners tune the step size and anticipate oscillations.",
                            "mcqs": [
                                {
                                    "stem": "What happens when the learning rate is set too high?",
                                    "options": [
                                        {"text": "Updates overshoot and may diverge"},
                                        {"text": "Optimization halts immediately", "rationale_wrong": "Stopping occurs only if gradients become zero or errors occur."},
                                        {"text": "Gradients become zero regardless of the loss", "rationale_wrong": "Gradients depend on the loss surface, not the learning rate."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": "Analyze",
                                    "difficulty": "Medium",
                                    "misconceptions": ["higher_rate_faster"],
                                    "correct_rationale": "Large steps can bounce across the valley and fail to converge.",
                                },
                                {
                                    "stem": "Which equation represents one gradient descent step?",
                                    "options": [
                                        {"text": "θ := θ - α ∇J(θ)"},
                                        {"text": "θ := θ + α θ", "rationale_wrong": "This ignores the gradient information entirely."},
                                        {"text": "θ := θ / α", "rationale_wrong": "Dividing by the learning rate is unrelated to descent."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": "Remember",
                                    "difficulty": "Easy",
                                    "misconceptions": ["missing_gradient"],
                                    "correct_rationale": "The gradient guides the step direction while α scales it.",
                                },
                            ],
                        },
                        {
                            "title": "Mini-Batch Strategies",
                            "learner_level": "intermediate",
                            "source_material": "Case study comparing batch, stochastic, and mini-batch training on image classifiers.",
                            "objectives": [
                                {"text": "Differentiate stochastic and mini-batch gradient descent", "bloom_level": "Analyze"},
                                {"text": "Select batch sizes to balance speed and noise", "bloom_level": "Apply"},
                            ],
                            "glossary_terms": [
                                {"term": "Batch Gradient Descent", "definition": "Optimization that uses the full dataset each update."},
                                {"term": "Stochastic Gradient Descent", "definition": "Optimization using one example per update."},
                                {"term": "Mini-Batch", "definition": "Subset of examples used per update to balance variance and efficiency."},
                            ],
                            "mini_lesson": "Mini-batches blend the stability of batch training with the responsiveness of stochastic updates. Smaller batches introduce gradient noise that can escape shallow minima, while larger batches leverage hardware parallelism. Practitioners often start with powers of two (32, 64, 128) and adjust based on validation loss curves.",
                            "mcqs": [
                                {
                                    "stem": "Why choose mini-batch gradient descent over pure stochastic descent?",
                                    "options": [
                                        {"text": "It smooths gradient noise while remaining efficient"},
                                        {"text": "It eliminates the need for a learning rate", "rationale_wrong": "Learning rate tuning is still required."},
                                        {"text": "It guarantees convergence in one epoch", "rationale_wrong": "Convergence still depends on many factors."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": "Analyze",
                                    "difficulty": "Medium",
                                    "misconceptions": ["mini_batch_is_exact"],
                                    "correct_rationale": "Mini-batches reduce variance while keeping computation tractable.",
                                },
                                {
                                    "stem": "Which batch size balances speed and noise for many image tasks?",
                                    "options": [
                                        {"text": "A power of two such as 64"},
                                        {"text": "Batch size of 1 to avoid memory use", "rationale_wrong": "Size 1 is pure stochastic descent."},
                                        {"text": "Full dataset size each step", "rationale_wrong": "Full batches maximize stability but reduce responsiveness."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": "Apply",
                                    "difficulty": "Easy",
                                    "misconceptions": ["bigger_always_better"],
                                    "correct_rationale": "Powers of two align with hardware and offer a practical trade-off.",
                                },
                            ],
                        },
                    ],
                },
            ]

            for unit_spec in units_spec:
                owner_key = unit_spec["owner_key"]
                unit_spec["owner_id"] = user_snapshots[owner_key]["id"]

            for unit_spec in units_spec:
                for lesson_spec in unit_spec["lessons"]:
                    lesson_spec["id"] = str(uuid.uuid4())
                    lesson_spec["flow_run_id"] = uuid.uuid4()

                unit_entry = {
                    "id": unit_spec["id"],
                    "title": unit_spec["title"],
                    "is_global": unit_spec["is_global"],
                    "owner_key": unit_spec["owner_key"],
                    "owner_id": unit_spec["owner_id"],
                    "lessons": [],
                }
                units_output.append(unit_entry)

                unit_model = UnitModel(
                    id=unit_spec["id"],
                    title=unit_spec["title"],
                    description=unit_spec["description"],
                    learner_level=unit_spec["learner_level"],
                    lesson_order=[lesson["id"] for lesson in unit_spec["lessons"]],
                    learning_objectives=unit_spec["learning_objectives"],
                    target_lesson_count=unit_spec["target_lesson_count"],
                    source_material=unit_spec["source_material"],
                    generated_from_topic=unit_spec["generated_from_topic"],
                    flow_type="standard",
                    status="completed",
                    creation_progress=None,
                    error_message=None,
                    user_id=unit_spec["owner_id"],
                    is_global=unit_spec["is_global"],
                )
                db_session.add(unit_model)

                for lesson_spec in unit_spec["lessons"]:
                    package = build_lesson_package(
                        lesson_spec["id"],
                        title=lesson_spec["title"],
                        learner_level=lesson_spec["learner_level"],
                        objectives=lesson_spec["objectives"],
                        glossary_terms=lesson_spec["glossary_terms"],
                        mini_lesson=lesson_spec["mini_lesson"],
                        mcqs=lesson_spec["mcqs"],
                    )

                    lesson_data = create_lesson_data(
                        lesson_spec["id"],
                        title=lesson_spec["title"],
                        learner_level=lesson_spec["learner_level"],
                        source_material=lesson_spec["source_material"],
                        package=package,
                        flow_run_id=lesson_spec["flow_run_id"],
                    )

                    lesson_dict = {**lesson_data, "unit_id": unit_spec["id"]}
                    flow_run_data = create_sample_flow_run(
                        lesson_spec["flow_run_id"],
                        lesson_spec["id"],
                        lesson_data,
                        user_id=None,
                    )
                    step_runs = create_sample_step_runs(lesson_spec["flow_run_id"], lesson_data)
                    llm_requests = create_sample_llm_requests(
                        step_runs,
                        user_id=None,
                        lesson_title=lesson_spec["title"],
                    )

                    db_session.add(FlowRunModel(**flow_run_data))
                    await db_session.flush()
                    for llm_data in llm_requests:
                        db_session.add(LLMRequestModel(**llm_data))
                    await db_session.flush()
                    for step_data in step_runs:
                        db_session.add(FlowStepRunModel(**step_data))
                    await db_session.flush()

                    db_session.add(LessonModel(**lesson_dict))

                    unit_entry["lessons"].append(
                        {
                            "lesson_id": lesson_spec["id"],
                            "title": lesson_spec["title"],
                            "exercise_count": len(package.exercises),
                            "glossary_count": len(package.glossary["terms"]),
                        }
                    )

            if args.verbose:
                print("📈 Creating learning sessions and unit sessions for sample progress...")

            now = datetime.now(UTC)

            cat_unit = units_spec[0]
            grad_unit = units_spec[1]

            epsilon_session = LearningSessionModel(
                id=str(uuid.uuid4()),
                lesson_id=cat_unit["lessons"][0]["id"],
                unit_id=cat_unit["id"],
                user_id=str(epsilon_learner_id),
                status=SessionStatus.COMPLETED.value,
                started_at=now - timedelta(days=3),
                completed_at=now - timedelta(days=2, hours=5),
                current_exercise_index=3,
                total_exercises=6,
                exercises_completed=6,
                exercises_correct=5,
                progress_percentage=100.0,
                session_data={"notes": "Completed during community volunteer orientation."},
            )

            nova_session = LearningSessionModel(
                id=str(uuid.uuid4()),
                lesson_id=cat_unit["lessons"][1]["id"],
                unit_id=cat_unit["id"],
                user_id=str(nova_learner_id),
                status=SessionStatus.ACTIVE.value,
                started_at=now - timedelta(days=1, hours=4),
                completed_at=None,
                current_exercise_index=1,
                total_exercises=6,
                exercises_completed=2,
                exercises_correct=2,
                progress_percentage=35.0,
                session_data={"active_lesson_segment": "Roof safety tips"},
            )

            brian_session = LearningSessionModel(
                id=str(uuid.uuid4()),
                lesson_id=grad_unit["lessons"][0]["id"],
                unit_id=grad_unit["id"],
                user_id=str(brian_admin_id),
                status=SessionStatus.ACTIVE.value,
                started_at=now - timedelta(days=5),
                completed_at=None,
                current_exercise_index=1,
                total_exercises=4,
                exercises_completed=2,
                exercises_correct=2,
                progress_percentage=55.0,
                session_data={"current_topic": "Learning rate warm-up"},
            )

            db_session.add_all([epsilon_session, nova_session, brian_session])
            await db_session.flush()

            epsilon_unit_session = UnitSessionModel(
                id=str(uuid.uuid4()),
                unit_id=cat_unit["id"],
                user_id=str(epsilon_learner_id),
                status=SessionStatus.COMPLETED.value,
                started_at=now - timedelta(days=4),
                completed_at=now - timedelta(days=2),
                updated_at=now - timedelta(days=2),
                progress_percentage=100.0,
                last_lesson_id=cat_unit["lessons"][2]["id"],
                completed_lesson_ids=[lesson["id"] for lesson in cat_unit["lessons"]],
            )

            brian_unit_session = UnitSessionModel(
                id=str(uuid.uuid4()),
                unit_id=grad_unit["id"],
                user_id=str(brian_admin_id),
                status=SessionStatus.ACTIVE.value,
                started_at=now - timedelta(days=5),
                completed_at=None,
                updated_at=now - timedelta(hours=6),
                progress_percentage=55.0,
                last_lesson_id=grad_unit["lessons"][0]["id"],
                completed_lesson_ids=[grad_unit["lessons"][0]["id"]],
            )

            db_session.add_all([epsilon_unit_session, brian_unit_session])
            await db_session.flush()

            bucket_name = os.getenv("OBJECT_STORE_BUCKET", "digital-innie")
            sample_images = [
                ImageModel(
                    user_id=brian_admin_id,
                    s3_key="seed/brian/cats/kadikoy-plaza.png",
                    s3_bucket=bucket_name,
                    filename="kadikoy-plaza.png",
                    content_type="image/png",
                    file_size=48_512,
                    width=1280,
                    height=720,
                    alt_text="Street cats sunbathing near the Kadıköy fish market",
                    description="Sample image demonstrating the Istanbul cat content used throughout the seed data.",
                ),
                ImageModel(
                    user_id=None,
                    s3_key="seed/system/gradient-descent/contours.png",
                    s3_bucket=bucket_name,
                    filename="gradient-descent-contours.png",
                    content_type="image/png",
                    file_size=32_768,
                    width=1024,
                    height=768,
                    alt_text="Contour plot illustrating gradient descent steps",
                    description="System-wide reference image for optimization lessons.",
                ),
            ]

            sample_audio = [
                AudioModel(
                    user_id=brian_admin_id,
                    s3_key="seed/brian/audio/gradient-intro.mp3",
                    s3_bucket=bucket_name,
                    filename="gradient-intro.mp3",
                    content_type="audio/mpeg",
                    file_size=2_621_440,
                    duration_seconds=95.0,
                    bitrate_kbps=192,
                    sample_rate_hz=44_100,
                    transcript="Welcome to Gradient Descent Mastery. In this lesson we explore step sizes and convergence.",
                ),
                AudioModel(
                    user_id=None,
                    s3_key="seed/system/audio/istanbul-walking-tour.m4a",
                    s3_bucket=bucket_name,
                    filename="istanbul-walking-tour.m4a",
                    content_type="audio/mp4",
                    file_size=1_572_864,
                    duration_seconds=62.0,
                    bitrate_kbps=128,
                    sample_rate_hz=44_100,
                    transcript="Join us on a walking tour describing how Istanbul residents care for community cats.",
                ),
            ]

            db_session.add_all([*sample_images, *sample_audio])
            await db_session.flush()

            users_created_count = len(sample_user_ids)
            global_units_count = sum(1 for unit in units_spec if unit["is_global"])
            personal_units_count = len(units_spec) - global_units_count
            learning_session_statuses = [
                epsilon_session.status,
                nova_session.status,
                brian_session.status,
            ]
            unit_session_statuses = [
                epsilon_unit_session.status,
                brian_unit_session.status,
            ]

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    ordered_user_keys = ["brian", "eylem", "epsilon", "nova"]

    print("✅ Seed data created successfully!")
    print(f"   • Users created: {users_created_count} (admins: 2, learners: 2)")
    for key in ordered_user_keys:
        snapshot = user_snapshots[key]
        role_label = "Admin" if snapshot["role"] == "admin" else "Learner"
        print(f"     - {role_label}: {snapshot['name']} <{snapshot['email']}>")

    print()
    for unit_entry in units_output:
        owner_key = unit_entry["owner_key"]
        owner_name = user_snapshots[owner_key]["name"]
        visibility = "Global" if unit_entry["is_global"] else "Private"
        print(f"   • {visibility} Unit {unit_entry['id']}: {unit_entry['title']} (owner: {owner_name})")
        for lesson in unit_entry["lessons"]:
            print(f"     • Lesson {lesson['lesson_id']}: {lesson['title']} — exercises: {lesson['exercise_count']}, glossary terms: {lesson['glossary_count']}")

    print()
    print(f"   • Global units: {global_units_count}; Private units: {personal_units_count}")
    print(f"   • Learning sessions: {len(learning_session_statuses)} ({', '.join(learning_session_statuses)})")
    print(f"   • Unit sessions: {len(unit_session_statuses)} ({', '.join(unit_session_statuses)})")

    if args.output:
        summary = {
            "users": [
                {
                    "id": snapshot["id"],
                    "name": snapshot["name"],
                    "email": snapshot["email"],
                    "role": snapshot["role"],
                }
                for key, snapshot in user_snapshots.items()
            ],
            "units": [
                {
                    "id": unit_entry["id"],
                    "title": unit_entry["title"],
                    "is_global": unit_entry["is_global"],
                    "owner_name": user_snapshots[unit_entry["owner_key"]]["name"],
                    "lessons": unit_entry["lessons"],
                }
                for unit_entry in units_output
            ],
        }

        with Path(args.output).open("w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"📁 Summary saved to: {args.output}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
