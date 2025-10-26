#!/usr/bin/env python3
"""
Seed Data Creation Script

Summary of created artifacts:
- 4 users seeded with hashed passwords (credentials for local login):
  • Admin — Brian Fields (thecriticalpath@gmail.com) / password: epsilon
  • Admin — Eylem Ozaslan (eylem.ozaslan@gmail.com) / password: epsilon
  • Learner — Epsilon cat (epsilon.cat@example.com) / password: epsilon
  • Learner — Nova cat (nova.cat@example.com) / password: epsilon
- 2 completed global units ("Street Kittens of Istanbul" and "Community First Aid Playbook") shared by Eylem with packaged lessons, artwork descriptions, and supporting assets.
- 1 completed private unit about "Gradient Descent Mastery" owned by Brian with two packaged lessons.
- Seeded "My Units" memberships so learners have curated catalog items out of the box.
- Per-lesson flow runs, step runs, and LLM request records mirroring the lesson generation pipeline.
- Learning sessions and unit sessions for the learners so UI dashboards have ready-made progress data.
- Sample images and audio files linked to the units.

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

from sqlalchemy import delete

from modules.content.models import (
    LessonModel,
    UnitModel,  # Import UnitModel so SQLAlchemy knows about the units table
    UserMyUnitModel,
)
from modules.content.package_models import GlossaryTerm, LessonPackage, MCQAnswerKey, MCQExercise, MCQOption, Meta
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

    exercises: list[MCQExercise] = []
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
    raw_unit_objectives = lesson_data.get("unit_learning_objectives", []) or []
    objectives = [obj.get("text") if isinstance(obj, dict) else str(obj) for obj in raw_unit_objectives]
    objective_ids = [obj.get("id") for obj in raw_unit_objectives if isinstance(obj, dict) and obj.get("id") is not None]
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
                "learning_objective_ids": objective_ids,
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

    print("🌱 Creating seed data: Street Kittens of Istanbul (global) + Gradient Descent (private)")
    print()

    sample_user_ids: dict[str, int] = {}
    user_snapshots: dict[str, dict[str, Any]] = {}
    units_output: list[dict[str, Any]] = []
    users_created_count = 0
    global_units_count = 0
    personal_units_count = 0
    learning_session_statuses: list[str] = []
    unit_session_statuses: list[str] = []
    my_units_memberships_summary: list[tuple[str, str]] = []

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
                # Check if user already exists
                existing_user = user_repo.by_email(email)
                if existing_user:
                    if args.verbose:
                        print(f"   • User {email} already exists, reusing...")
                    user = existing_user
                else:
                    password_hash = user_service._hash_password(password)
                    user = user_repo.create(
                        email=email,
                        password_hash=password_hash,
                        name=name,
                        role=role,
                        is_active=is_active,
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
                    "id": "9435f1bf-472d-47c5-a759-99beadd98076",
                    "title": "Street Kittens of Istanbul",
                    "description": "A learning unit about Street Kittens of Istanbul",
                    "learner_level": "intermediate",
                    "learning_objectives": [
                        {"id": "lo_1", "text": "Explain the managed-commons context for Istanbul's street kittens, distinguishing stray vs. feral statuses, kitten life-stage bands, key actors, and seasonality.", "bloom_level": None},
                        {"id": "lo_2", "text": "Map a 50–100 m urban microhabitat to identify food sources, shelters, risks, and human–cat interfaces, and recommend placements for shelters and trap sites.", "bloom_level": None},
                        {"id": "lo_3", "text": "Sequence kitten triage in warmth–hydration–respiration–nutrition order and classify cases into urgent, priority, or routine pathways.", "bloom_level": None},
                        {"id": "lo_4", "text": "Specify age-appropriate feeding, micro-shelter features, and a basic vaccination and parasite-control schedule for a given kitten profile.", "bloom_level": None},
                        {"id": "lo_5", "text": "Design a Trap–Neuter–Return (TNR) workflow aligned to seasonality, including ear-tipping, return-to-territory, and simple record-keeping.", "bloom_level": None},
                        {"id": "lo_6", "text": "Identify edge cases such as lactating queens, late pregnancy, panleukopenia outbreaks, or seasonal extremes and specify the required operational adjustments.", "bloom_level": None},
                    ],
                    "target_lesson_count": 2,
                    "source_material": None,
                    "generated_from_topic": True,
                    "is_global": True,
                    "owner_key": "eylem",
                    "podcast_transcript": """Picture Istanbul at dawn. The call to prayer, the hiss of kettles, and in the alley between a bakery and a barber—two wet-nosed kittens blinking into the day. They don't make it because of luck. They make it because a city of humans manages a commons, whether it knows it or not. That's our unit: from seeing the system to working the system.

Start with classification. Strays tolerate us. Ferals don't. That single split decides how close we get, how we feed, how we trap. Then read the clock on a kitten's body. Neonate, zero to two weeks—eyes closed, heat-dependent. Infant, two to four—eyes open, wobble stance. Transitional, four to eight—teething, learning to eat. Juvenile, eight to twenty-four—fast, curious, hitting surgical weight. Seasonality is the drumbeat. Spring and late summer flood the streets with kittens. Winter tests endurance. If you know the rhythm, you can play ahead of it.

Now shrink your world to a 50–100 meter circle. Walk it. Sketch it. Where's food? Dumpsters behind meyhanes, a feeder's mat of bowls under the fig tree, a cafe's crumbs at closing. Where's shelter? The dry corner under the stairs, a basement vent, an old "cat house" near the kiosk. Where's danger? A taxi cut-through, a dog pack's patrol, a gutter that becomes a river when it rains, the shop owner who's had enough. Where do cats meet people? Schools, markets, tourist choke points. Name the actors: the auntie who feeds at dusk, the municipal mobile clinic two streets over, the guy who complains when bowls block his door.

Then place things with intention. Micro-shelters elevated, dry, out of the wind, with two exits. Insulate before the cold; shade and water before the heat. Keep feeding stations tidy and consistent, but not on thresholds. And keep trap sites separate and discreet, pre-baited so trap day isn't a surprise. Four to six weeks before the spring and late-summer waves, turn up the trapping. Prioritize juveniles at weight and intact adults. Lactating queens? Sterilize only if you can return same day to the exact spot.

Lesson two starts with a single rule: triage in order—warmth, hydration, respiration, nutrition. Cold and limp, or breathing hard? That's urgent. Warm first. Don't feed a cold kitten. Stable but snotty eyes, underweight? Priority. Bright-eyed, eating, normal vitals? Routine.

Feed by stage. Neonates get kitten milk replacer by bottle, small and frequent, in warmth and dryness. Two to four weeks, gruel. Four to eight, move to wet food. Eight and up, high-protein wet and dry. Micro-shelters get straw in winter, not fabric. Airflow and shade in heat. Begin core vaccines around eight to nine weeks; boost three to four weeks later. Deworm by weight. Add flea control to cut vectors and protect the group.

TNR is choreography. Pre-bait. Trap. Sterilize. Ear-tip. Vaccinate when possible. Recover. Return to the same territory within 24–48 hours. Time campaigns for late winter and late summer to blunt kitten surges. Track everything: photos, locations, ear-tip status, sex, dates, interventions. That ledger is your memory.

Edge cases change the tempo. Lactating queens—same-day return. Late pregnancy—postpone if you can. Panleukopenia—stop mixing, isolate, bleach. Heatwave—shade and water stations. Winter—elevate shelters, add straw, cut drafts. And watch the socialization window: from roughly two to seven weeks, gentle daily handling can turn a life on the street into a home.

So here's your charge. Map one microhabitat. Place one shelter right. Set one clean feeding routine apart from your future trap line. Run one triage. Plan one season-timed TNR cycle, and write it down. Istanbul's street kittens aren't waiting for perfect. They're waiting for you to start. Next, pick a colony and commit twelve weeks. We'll be here, walking the alley with you.""",
                    "podcast_voice": "Plain",
                    "lessons": [
                        {
                            "title": "Managed Commons in Practice: Context, Seasonality, and Microhabitats",
                            "learner_level": "intermediate",
                            "source_material": None,
                            "objectives": [
                                {"id": "lo_1", "text": "Explain the managed-commons context for Istanbul's street kittens, distinguishing stray vs. feral statuses, kitten life-stage bands, key actors, and seasonality.", "bloom_level": None},
                                {"id": "lo_2", "text": "Map a 50–100 m urban microhabitat to identify food sources, shelters, risks, and human–cat interfaces, and recommend placements for shelters and trap sites.", "bloom_level": None},
                            ],
                            "glossary_terms": [
                                {"term": "Managed commons", "definition": "A shared urban space where cats persist through community care and municipal services under social norms."},
                                {"term": "Seasonality", "definition": "Predictable shifts across the year in breeding, disease, and resource needs."},
                                {"term": "Microhabitat", "definition": "A 50–100 m patch of urban features that shape food, shelter, and risk."},
                                {"term": "Stray", "definition": "Formerly owned or human-acclimated cat living outdoors."},
                                {"term": "Feral", "definition": "Minimally socialized cat that avoids close human contact."},
                                {"term": "Trap–Neuter–Return (TNR)", "definition": "Capture, sterilize, vaccinate when possible, ear-tip, and return to territory."},
                                {"term": "Ear-tipping", "definition": "Small surgical notch marking a sterilized free-roaming cat."},
                            ],
                            "mini_lesson": """Istanbul's street kittens live in a managed commons: survival and population stability come from residents, feeders, and municipal clinics working together. Classify cats first: strays accept human proximity; ferals avoid it. Note kitten life stages—neonate (0–2 w), infant (2–4 w), transitional (4–8 w), juvenile (8–24 w)—because feeding, sheltering, and TNR timing depend on age. Seasonality matters: expect kitten surges in spring and late summer; prepare for thermal stress in winter.

Map a 50–100 m microhabitat. Mark on a sketch: 1) food sources (dumpsters, cafes, feeder spots), 2) shelters (nooks, basements, existing "cat houses"), 3) risks (traffic lanes, dogs, flood paths, conflicts), 4) human–cat interfaces (markets, tourist hubs, schools). Add actors: who feeds, who complains, nearest mobile clinic.

Recommendations:
- Place micro-shelters elevated, dry, wind-sheltered, with two exits; anchor and keep clean. Add insulation before winter; add shade and water in heat.
- Keep feeding stations consistent and tidy away from doorways; separate them from discreet pre-baited trap sites.
- Schedule intensified trapping 4–6 weeks before spring/late-summer surges; prioritize juveniles at surgical weight and visibly intact adults; same-day return for lactating queens.

This map plus rationale guides shelter placement and trap cycles while respecting site fidelity and social license.""",
                            "mcqs": [
                                {
                                    "stem": "Which observation best supports classifying an outdoor cat as a Stray rather than Feral?",
                                    "options": [
                                        {"text": "Approaches people within arm's reach."},
                                        {"text": "Retreats or hides when approached.", "rationale_wrong": "Avoiding humans describes feral behavior, not a socialized stray."},
                                        {"text": "Ear-tipping notch is visible.", "rationale_wrong": "Ear-tipping marks sterilization status, not socialization or temperament."},
                                        {"text": "Mostly active at night.", "rationale_wrong": "Activity timing doesn't define stray versus feral."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": None,
                                    "difficulty": "Medium",
                                    "misconceptions": [],
                                    "correct_rationale": "Strays accept close human proximity; ferals avoid approach. Proximity indicates stray.",
                                },
                                {
                                    "stem": "You find a shivering 1‑week kitten under stairs. What is the best first step?",
                                    "options": [
                                        {"text": "Warm the neonate, then feed kitten milk replacer."},
                                        {"text": "Feed cow's milk immediately.", "rationale_wrong": "Cow's milk causes GI upset and malnutrition; cold kittens shouldn't eat."},
                                        {"text": "Begin Trap–Neuter–Return (TNR) around the nest.", "rationale_wrong": "Trap–Neuter–Return (TNR) targets adults; immediate neonatal priority is warming."},
                                        {"text": "Place in an outdoor shelter and feed later.", "rationale_wrong": "Passive sheltering delays warming; stabilize temperature before any feeding."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": None,
                                    "difficulty": "Medium",
                                    "misconceptions": ["MC3", "MC4"],
                                    "correct_rationale": "Warm first; hypothermic neonates can't digest safely. Use kitten milk replacer.",
                                },
                                {
                                    "stem": "Mapping a 60 m Microhabitat alley, choose the best micro‑shelter location.",
                                    "options": [
                                        {"text": "Beside a busy shop doorway.", "rationale_wrong": "Doorways cause complaints and disruptions; avoid high foot traffic."},
                                        {"text": "Raised, dry stairwell alcove, shielded from wind, two exits."},
                                        {"text": "Under a leaky gutter near a drain path.", "rationale_wrong": "Leakage and flood paths make shelters damp and unsafe."},
                                        {"text": "Along a dog patrol path behind dumpsters.", "rationale_wrong": "Dogs and movement corridors increase stress and risk."},
                                    ],
                                    "correct_index": 1,
                                    "cognitive_level": None,
                                    "difficulty": "Medium",
                                    "misconceptions": [],
                                    "correct_rationale": "Elevated, dry, wind‑sheltered placement with two exits matches guidance.",
                                },
                                {
                                    "stem": "A feeder runs a visible feeding station by a cafe. For Trap–Neuter–Return (TNR), where should you stage traps to reduce trap shyness?",
                                    "options": [
                                        {"text": "Right beside the feeding bowls for consistency.", "rationale_wrong": "Combining sites conditions cats to avoid traps at meals."},
                                        {"text": "At the cafe doorway for easy monitoring.", "rationale_wrong": "Doorways invite conflict and attention, undermining social license."},
                                        {"text": "Discreet, pre‑baited spot away from the feeding station."},
                                        {"text": "Inside a micro‑shelter with two exits.", "rationale_wrong": "Shelters are for protection, not trapping; blocked exits deter use."},
                                    ],
                                    "correct_index": 2,
                                    "cognitive_level": None,
                                    "difficulty": "Medium",
                                    "misconceptions": [],
                                    "correct_rationale": "Trap sites should be discreet and separate from feeding stations.",
                                },
                                {
                                    "stem": "For a 50–100 m Microhabitat in a Managed commons, which annotations best guide shelter placement and Trap–Neuter–Return (TNR) cycles aligned with Seasonality?",
                                    "options": [
                                        {"text": "Food sources, shelters, risks, human–cat interfaces, actors, mobile clinic."},
                                        {"text": "Only feeding spots; other details clutter the map.", "rationale_wrong": "Feeding alone ignores shelter, disease, risks, and community conflicts."},
                                        {"text": "Only shelters and nests; skip human factors.", "rationale_wrong": "Nests are fragile; leaving out human interfaces weakens outcomes."},
                                        {"text": "Only tourist hubs; ignore other interfaces and risks.", "rationale_wrong": "Narrow focus misses risks, resources, and actors needed for planning."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": None,
                                    "difficulty": "Medium",
                                    "misconceptions": ["MC1"],
                                    "correct_rationale": "These capture resources, risks, and actors for shelter and TNR planning.",
                                },
                            ],
                            "misconceptions": [
                                {
                                    "id": "MC1",
                                    "misbelief": "Feeding alone keeps street kittens safe and stable.",
                                    "why_plausible": "Feeding is visible, easy to organize, and shows immediate response from cats.",
                                    "correction": "Survival also depends on shelter, vaccination/parasite control, and TNR; feeding without these can raise disease and conflict risks.",
                                },
                                {
                                    "id": "MC2",
                                    "misbelief": "TNR makes colonies grow because cats are returned.",
                                    "why_plausible": "Returned, ear-tipped cats remain visible in the area.",
                                    "correction": "Sterilized, site-faithful adults prevent new litters and defend territory, which stabilizes or reduces numbers over time.",
                                },
                                {
                                    "id": "MC3",
                                    "misbelief": "Any milk is fine for neonate kittens.",
                                    "why_plausible": "Cow's milk is common and inexpensive.",
                                    "correction": "Use kitten milk replacer; cow's milk causes GI upset and malnutrition.",
                                },
                                {
                                    "id": "MC4",
                                    "misbelief": "Cold, hungry kittens should be fed immediately.",
                                    "why_plausible": "Hunger seems most urgent to bystanders.",
                                    "correction": "Warm first, then feed; hypothermic kittens cannot digest safely and risk aspiration.",
                                },
                            ],
                            "confusables": [
                                {"a": "Stray", "b": "Feral", "contrast": "Strays tolerate human proximity; ferals avoid it and show minimal socialization."},
                                {"a": "Feeding Station", "b": "Trap Site", "contrast": "Feeding stations are stable and visible; trap sites are pre-baited and discreet to reduce trap shyness."},
                                {"a": "Shelter", "b": "Nest", "contrast": "Shelters are human-made and weatherproof; nests are queen-selected natural hideouts that are fragile and hidden."},
                            ],
                        },
                        {
                            "title": "From Triage to TNR: Integrated Care and Control Plan",
                            "learner_level": "intermediate",
                            "source_material": None,
                            "objectives": [
                                {"id": "lo_3", "text": "Sequence triage for kittens using the warmth–hydration–respiration–nutrition order and assign cases to urgent, priority, or routine categories.", "bloom_level": None},
                                {"id": "lo_4", "text": "Specify age-appropriate feeding, micro-shelter features, and a basic vaccination and parasite-control schedule for a given kitten profile.", "bloom_level": None},
                                {"id": "lo_5", "text": "Design a Trap–Neuter–Return (TNR) workflow aligned to seasonality, including ear-tipping, return-to-territory, and simple record-keeping.", "bloom_level": None},
                                {"id": "lo_6", "text": "Identify edge cases (e.g., lactating queens, late pregnancy, panleukopenia outbreaks, heatwaves/winter) and specify the operational adjustment required.", "bloom_level": None},
                            ],
                            "glossary_terms": [
                                {"term": "Triage", "definition": "A prioritization sequence: warmth, hydration, respiration, then nutrition."},
                                {"term": "Kitten Milk Replacer (KMR)", "definition": "Formula designed to substitute for queen's milk."},
                                {"term": "Micro-shelter", "definition": "Simple, weather-resistant housing that reduces exposure to cold, heat, wind, and rain."},
                                {"term": "Ear-tipping", "definition": "Small surgical removal of the ear tip to mark a sterilized free-roaming cat."},
                                {"term": "Trap–Neuter–Return (TNR)", "definition": "Humane population control: trap, sterilize, vaccinate when possible, and return to territory."},
                                {"term": "Socialization Window", "definition": "Peak period (~2–7 weeks) when handling most effectively builds tameness."},
                                {"term": "Herd Effect", "definition": "Lower disease spread when enough individuals are immunized."},
                            ],
                            "mini_lesson": """Start with triage. Sequence needs: warmth → hydration → respiration → nutrition. Urgent: cold, lethargic, or labored breathing; warm to safe temperature before any feeding. Priority: ocular/nasal discharge or low weight but stable breathing. Routine: active, eating, normal vitals.

Match care to age. Neonates (0–2 wks): KMR by bottle, tiny frequent feeds; keep dry, draft-free, and warmed. 2–4 wks: introduce gruel; 4–8 wks: transition to wet food; 8+ wks: high-protein wet/dry. Micro-shelter: elevated, insulated box with wind break, dual exits, shade and airflow in heat; straw (not fabric) for winter moisture.

Disease prevention: begin core vaccines around weaning (e.g., 8–9 wks) with a booster in 3–4 weeks; deworm by weight; add flea control to cut vector risks and build herd effect.

TNR workflow: pre-bait, trap, sterilize, ear-tip, vaccinate as possible, recover, return to the same spot within 24–48 hours. Plan campaigns late winter and late summer to blunt kitten surges; log photos, location, ear-tip status, sex, dates, and interventions.

Edge-case adjustments: lactating queens—same-day return or delay surgery; late pregnancy—postpone when feasible; panleukopenia—isolate and pause mixing; heatwaves—shade and water stations; winter—elevate shelters, use straw.""",
                            "mcqs": [
                                {
                                    "stem": "Triage a 3-week-old kitten: cold, lethargic, stable breathing. What immediate action and urgency fit best?",
                                    "options": [
                                        {"text": "Warm gently; urgent category"},
                                        {"text": "Offer KMR; priority category", "rationale_wrong": "Feeding contradicts triage; cold kittens risk aspiration."},
                                        {"text": "Hydrate orally; routine category", "rationale_wrong": "Hydration follows warming; routine misclassifies a cold kitten."},
                                        {"text": "Start dewormer; routine category", "rationale_wrong": "Deworming is not immediate; routine misses urgent signs."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": None,
                                    "difficulty": "Medium",
                                    "misconceptions": ["MC1"],
                                    "correct_rationale": "Warm first per triage; cold lethargy is urgent.",
                                },
                                {
                                    "stem": "Outdoors in summer, an 8-week-old kitten needs care. Select feeding, micro-shelter feature, and vaccine/parasite plan.",
                                    "options": [
                                        {"text": "High-protein wet/dry; shade and airflow; start core vaccine, deworm"},
                                        {"text": "KMR by bottle; fabric bedding; vaccinate later only", "rationale_wrong": "Neonatal KMR and fabric bedding are inappropriate; vaccines start now."},
                                        {"text": "Wet food only; sealed box; skip vaccines outdoors", "rationale_wrong": "Skipping vaccines outdoors ignores herd effect; sealed shelters trap heat."},
                                        {"text": "Gruel; wind break only; deworm replaces vaccines", "rationale_wrong": "Parasite control complements, not replaces, core vaccination."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": None,
                                    "difficulty": "Medium",
                                    "misconceptions": ["MC2", "MC3"],
                                    "correct_rationale": "At 8 weeks, high-protein diet, ventilated shade, begin core vaccines and deworming.",
                                },
                                {
                                    "stem": "Design a late-winter Trap–Neuter–Return (TNR) plan for a feral colony. Choose steps and logging aligned to site fidelity.",
                                    "options": [
                                        {"text": "Pre-bait, trap, sterilize, ear-tip, vaccinate, return; log ear-tip status"},
                                        {"text": "Trap, sterilize, relocate colony; skip ear-tips; record adopters", "rationale_wrong": "Relocation violates TNR and invites the vacuum effect."},
                                        {"text": "Trap in spring, vaccinate only; release anywhere; no records", "rationale_wrong": "Seasonality off; vaccination-only and no records break workflow."},
                                        {"text": "Pre-bait, trap, ear-tip, return; log photos and location", "rationale_wrong": "Omits sterilization and vaccination; logging is incomplete alone."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": None,
                                    "difficulty": "Medium",
                                    "misconceptions": ["MC4"],
                                    "correct_rationale": "Matches TNR steps, return-to-territory, and essential ear-tip logging.",
                                },
                                {
                                    "stem": "During a heatwave, micro-shelters sit in sun, and a lactating queen is trapped. What adjustment best protects kittens and colony?",
                                    "options": [
                                        {"text": "Same-day return the lactating queen; add shade and water stations"},
                                        {"text": "Relocate queen to cooler site; shelters unchanged", "rationale_wrong": "Relocation risks disorientation and refilling; site fidelity preferred."},
                                        {"text": "Delay surgery; hold nursing queen until kittens wean", "rationale_wrong": "Holding separates queen from kittens during heat; return is safer."},
                                        {"text": "Spay late-term queen immediately; move kittens to new shelter", "rationale_wrong": "Irrelevant to lactation; moving kittens disrupts care under heat stress."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": None,
                                    "difficulty": "Medium",
                                    "misconceptions": ["MC4"],
                                    "correct_rationale": "Return lactating queens promptly; heatwaves require shade and water provisioning.",
                                },
                                {
                                    "stem": "Select the correct triage sequence for kittens.",
                                    "options": [
                                        {"text": "Warmth → Hydration → Respiration → Nutrition"},
                                        {"text": "Nutrition → Hydration → Respiration → Warmth", "rationale_wrong": "Feeding first risks aspiration in cold kittens."},
                                        {"text": "Hydration → Warmth → Nutrition → Respiration", "rationale_wrong": "Warmth precedes hydration; order here is incorrect."},
                                        {"text": "Respiration → Warmth → Hydration → Nutrition", "rationale_wrong": "The protocol places warmth first, not respiration."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": None,
                                    "difficulty": "Medium",
                                    "misconceptions": ["MC1"],
                                    "correct_rationale": "This order prevents aspiration and shock before feeding.",
                                },
                            ],
                            "misconceptions": [
                                {
                                    "id": "MC1",
                                    "misbelief": "Feeding first is safest for weak kittens.",
                                    "why_plausible": "Hunger is visible and feels most urgent.",
                                    "correction": "Triage follows warmth → hydration → respiration → nutrition; warming precedes feeding to prevent aspiration and shock.",
                                },
                                {
                                    "id": "MC2",
                                    "misbelief": "Any milk works for neonates.",
                                    "why_plausible": "Cow's milk is common and inexpensive.",
                                    "correction": "Use kitten milk replacer (KMR); cow's milk causes GI upset and malnutrition.",
                                },
                                {
                                    "id": "MC3",
                                    "misbelief": "Vaccination is optional for outdoor colonies.",
                                    "why_plausible": "Street cats seem hardy and already exposed.",
                                    "correction": "Core vaccines reduce outbreaks; herd effect protects the whole colony.",
                                },
                                {
                                    "id": "MC4",
                                    "misbelief": "Relocating cats is better than returning them.",
                                    "why_plausible": "New location seems safer or cleaner.",
                                    "correction": "TNR returns cats to their territory; site fidelity maintains stability and prevents the vacuum effect.",
                                },
                            ],
                            "confusables": [
                                {"a": "Stray", "b": "Feral", "contrast": "Strays tolerate human proximity; ferals avoid it and show minimal socialization."},
                                {"a": "TNR", "b": "Relocation", "contrast": "TNR sterilizes and returns to origin; relocation moves cats and risks disorientation and colony refill."},
                                {"a": "Core vaccine", "b": "Parasite control", "contrast": "Vaccines prevent viral/bacterial disease; parasite control targets internal/external parasites like worms and fleas."},
                            ],
                        },
                    ],
                },
                {
                    "id": "9435f1bf-472d-47c5-a759-99beadd98077",
                    "title": "Gradient Descent Mastery",
                    "description": "A focused look at optimization fundamentals for machine learning practitioners.",
                    "learner_level": "intermediate",
                    "learning_objectives": [
                        {"id": "grad_unit_lo_1", "text": "Explain how gradient descent updates parameters", "bloom_level": "Understand"},
                        {"id": "grad_unit_lo_2", "text": "Compare batch, stochastic, and mini-batch strategies", "bloom_level": "Analyze"},
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
                                {"id": "grad_unit_lo_1", "text": "State the gradient descent update rule", "bloom_level": "Remember"},
                                {"id": "grad_unit_lo_1", "text": "Interpret learning rate effects on convergence", "bloom_level": "Analyze"},
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
                                {"id": "grad_unit_lo_2", "text": "Differentiate stochastic and mini-batch gradient descent", "bloom_level": "Analyze"},
                                {"id": "grad_unit_lo_2", "text": "Select batch sizes to balance speed and noise", "bloom_level": "Apply"},
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
                {
                    "id": "3b6caa92-0c83-4d5d-bdff-7f1df59fe2f2",
                    "title": "Community First Aid Playbook",
                    "description": "Scenario-based first aid skills for community response teams covering scene safety, stabilization, and escalation decisions.",
                    "learner_level": "beginner",
                    "learning_objectives": [
                        {
                            "id": "first_aid_lo_1",
                            "text": "Stabilize a conscious patient while awaiting emergency services",
                            "bloom_level": "Apply",
                        },
                        {
                            "id": "first_aid_lo_2",
                            "text": "Decide when to escalate to advanced medical support",
                            "bloom_level": "Analyze",
                        },
                        {
                            "id": "first_aid_lo_3",
                            "text": "Communicate a concise hand-off to first responders",
                            "bloom_level": "Apply",
                        },
                    ],
                    "target_lesson_count": 1,
                    "source_material": "Community emergency response drills, FEMA ICS pocket guides, and field debrief notes.",
                    "generated_from_topic": True,
                    "is_global": True,
                    "owner_key": "eylem",
                    "lessons": [
                        {
                            "title": "Stabilize and Signal",
                            "learner_level": "beginner",
                            "source_material": "Annotated community drill checklists and EMS communication templates.",
                            "objectives": [
                                {
                                    "id": "first_aid_lo_1",
                                    "text": "Perform a rapid primary assessment and stabilize airway, breathing, and circulation",
                                    "bloom_level": "Apply",
                                },
                                {
                                    "id": "first_aid_lo_2",
                                    "text": "Determine escalation triggers using SAMPLE history and vital cues",
                                    "bloom_level": "Analyze",
                                },
                                {
                                    "id": "first_aid_lo_3",
                                    "text": "Prepare a concise radio hand-off using the MIST format",
                                    "bloom_level": "Apply",
                                },
                            ],
                            "glossary_terms": [
                                {"term": "SAMPLE", "definition": "Patient history acronym: Symptoms, Allergies, Medications, Past history, Last intake, Events."},
                                {"term": "MIST", "definition": "Medical hand-off format: Mechanism, Injuries, Signs, Treatments."},
                                {"term": "Primary Survey", "definition": "Rapid ABC check to find and treat immediate life threats."},
                            ],
                            "mini_lesson": "Scene size-up keeps volunteers safe: scan hazards, don PPE, and enlist bystanders. The primary survey follows ABC—airway, breathing, circulation—before moving patients. Stabilize the cervical spine only when mechanism suggests injury and you have adequate help. Use SAMPLE to gather clues and track changes. Escalate when airway is compromised, breathing is labored, bleeding is uncontrolled, or mental status worsens. When EMS arrives, hand off with MIST so responders get the essentials in under 30 seconds.",
                            "mcqs": [
                                {
                                    "stem": "Which observation is an immediate trigger to escalate to advanced medical support?",
                                    "options": [
                                        {"text": "Patient becomes disoriented and cannot state their name"},
                                        {"text": "Minor scrape on forearm", "rationale_wrong": "Surface abrasions can be treated on scene without escalation."},
                                        {"text": "Patient reports mild thirst", "rationale_wrong": "Thirst alone is not an escalation trigger."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": "Analyze",
                                    "difficulty": "Easy",
                                    "misconceptions": ["wait_for_visible_bleeding"],
                                    "correct_rationale": "Altered mental status signals compromised perfusion and needs advanced care.",
                                },
                                {
                                    "stem": 'What information belongs in the "M" section of a MIST hand-off?',
                                    "options": [
                                        {"text": "Mechanism of injury"},
                                        {"text": "Medication allergies", "rationale_wrong": "Allergies appear in the SAMPLE history, not MIST's M."},
                                        {"text": "Treatment en route", "rationale_wrong": "Treatments are documented in the T component."},
                                    ],
                                    "correct_index": 0,
                                    "cognitive_level": "Understand",
                                    "difficulty": "Easy",
                                    "misconceptions": ["mist_sections_interchangeable"],
                                    "correct_rationale": "MIST starts with the mechanism so responders anticipate likely injuries.",
                                },
                            ],
                            "misconceptions": [
                                {
                                    "id": "wait_for_visible_bleeding",
                                    "misbelief": "Only visible bleeding demands EMS escalation.",
                                    "why_plausible": "External bleeding is tangible, while mental status changes seem mild.",
                                    "correction": "Altered consciousness, airway compromise, or labored breathing require immediate escalation even without bleeding.",
                                },
                                {
                                    "id": "mist_sections_interchangeable",
                                    "misbelief": "MIST sections are interchangeable and order is optional.",
                                    "why_plausible": "Volunteers focus on content over structure.",
                                    "correction": "The standardized order keeps radio traffic predictable for incoming responders.",
                                },
                            ],
                        },
                    ],
                },
            ]

            for unit_spec in units_spec:
                owner_key = unit_spec["owner_key"]
                unit_spec["owner_id"] = user_snapshots[owner_key]["id"]
                objectives_preview = ", ".join([obj["text"] for obj in unit_spec["learning_objectives"][:2]]) if unit_spec.get("learning_objectives") else "its core learning journey"
                unit_spec["art_image_description"] = f"Weimar Edge illustration of {unit_spec['title']} highlighting {objectives_preview} with petrol blue geometry and gilt accents."

            # Set up IDs for the real Istanbul unit's image and audio
            cat_unit_image_id = uuid.UUID("1a7efaaf-e91d-429b-b032-1a9d08e45af4")
            cat_unit_audio_id = uuid.UUID("b2992f30-f404-43e9-a4fa-dc15c698e025")

            # Create images and audio first (before units that reference them)
            if args.verbose:
                print("🖼️  Creating images and audio files...")

            # Delete existing images and audio with the same IDs if they exist
            existing_cat_image = await db_session.get(ImageModel, cat_unit_image_id)
            if existing_cat_image:
                if args.verbose:
                    print(f"   • Deleting existing image: {existing_cat_image.filename}")
                await db_session.delete(existing_cat_image)
                await db_session.flush()

            existing_cat_audio = await db_session.get(AudioModel, cat_unit_audio_id)
            if existing_cat_audio:
                if args.verbose:
                    print(f"   • Deleting existing audio: {existing_cat_audio.filename}")
                await db_session.delete(existing_cat_audio)
                await db_session.flush()

            bucket_name = os.getenv("OBJECT_STORE_BUCKET", "lantern-room")

            seed_timestamp = datetime.now(UTC)

            sample_images = [
                ImageModel(
                    id=cat_unit_image_id,
                    user_id=sample_user_ids.get("eylem"),
                    s3_key="seed/7cf29b22-58e2-4b16-88af-db5162a151bf.png",
                    s3_bucket="lantern-room",
                    filename="unit-art-9435f1bf-472d-47c5-a759-99beadd98076.png",
                    content_type="image/png",
                    file_size=1991902,
                    width=1024,
                    height=1024,
                    alt_text="Ear‑tipped street kitten on a crate in a petrol‑blue, rain‑slick Istanbul alley under a tight spotlight; thin gilt lines indicate care stations and an open humane trap.",
                    description="Cinematic realism: petrol‑blue, rain‑slick Istanbul alley; ear‑tipped kitten, tiny gauze wrap, on a lacquered crate in a tight spotlight. Hairline gilt lines map care points and humane trap; Art‑Deco geometry, 3% grain.",
                    created_at=seed_timestamp,
                    updated_at=seed_timestamp,
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
                    created_at=seed_timestamp,
                    updated_at=seed_timestamp,
                ),
            ]

            sample_audio = [
                AudioModel(
                    id=cat_unit_audio_id,
                    user_id=sample_user_ids.get("eylem"),
                    s3_key="seed/f2ff972d-b8d1-4549-afd4-0e791bee9882.mp3",
                    s3_bucket="lantern-room",
                    filename="unit-9435f1bf-472d-47c5-a759-99beadd98076.mp3",
                    content_type="audio/mpeg",
                    file_size=4668000,
                    duration_seconds=None,
                    bitrate_kbps=None,
                    sample_rate_hz=None,
                    transcript=units_spec[0].get("podcast_transcript"),
                    created_at=seed_timestamp,
                    updated_at=seed_timestamp,
                ),
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
                    created_at=seed_timestamp,
                    updated_at=seed_timestamp,
                ),
            ]

            db_session.add_all([*sample_images, *sample_audio])
            await db_session.flush()

            # Delete existing units with the same IDs if they exist (to allow re-running the script)
            if args.verbose:
                print("🗑️  Checking for existing units to clean up...")
            for unit_spec in units_spec:
                existing_unit = await db_session.get(UnitModel, unit_spec["id"])
                if existing_unit:
                    if args.verbose:
                        print(f"   • Deleting existing unit: {existing_unit.title}")
                    # Delete associated lessons first

                    await db_session.execute(delete(LessonModel).where(LessonModel.unit_id == unit_spec["id"]))
                    await db_session.delete(existing_unit)
                    await db_session.flush()

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
                    "art_image_description": unit_spec["art_image_description"],
                }
                units_output.append(unit_entry)

                # For the Istanbul unit, set the real art_image_id and podcast_audio_object_id
                is_istanbul_unit = unit_spec["id"] == "9435f1bf-472d-47c5-a759-99beadd98076"

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
                    art_image_description=unit_spec["art_image_description"],
                    podcast_transcript=unit_spec.get("podcast_transcript"),
                    podcast_voice=unit_spec.get("podcast_voice"),
                    art_image_id=cat_unit_image_id if is_istanbul_unit else None,
                    podcast_audio_object_id=cat_unit_audio_id if is_istanbul_unit else None,
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
                        misconceptions=lesson_spec.get("misconceptions"),
                        confusables=lesson_spec.get("confusables"),
                    )

                    lesson_data = create_lesson_data(
                        lesson_spec["id"],
                        title=lesson_spec["title"],
                        learner_level=lesson_spec["learner_level"],
                        source_material=lesson_spec["source_material"],
                        package=package,
                        flow_run_id=lesson_spec["flow_run_id"],
                        unit_learning_objectives=lesson_spec["objectives"],
                    )

                    lesson_db_dict = {key: value for key, value in lesson_data.items() if key != "unit_learning_objectives"}
                    lesson_db_dict["unit_id"] = unit_spec["id"]
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

                    db_session.add(LessonModel(**lesson_db_dict))
                    await db_session.flush()

                    unit_entry["lessons"].append(
                        {
                            "lesson_id": lesson_spec["id"],
                            "title": lesson_spec["title"],
                            "exercise_count": len(package.exercises),
                            "glossary_count": len(package.glossary["terms"]),
                        }
                    )

            await db_session.flush()

            if args.verbose:
                print("🧾  Seeding My Units memberships for learners...")

            learner_member_ids = [epsilon_learner_id, nova_learner_id]
            await db_session.execute(delete(UserMyUnitModel).where(UserMyUnitModel.user_id.in_(learner_member_ids)))
            await db_session.flush()

            street_kittens_unit_id = units_spec[0]["id"]
            street_kittens_title = units_spec[0]["title"]
            community_unit_id = next(unit["id"] for unit in units_spec if unit["title"] == "Community First Aid Playbook")
            community_unit_title = next(unit["title"] for unit in units_spec if unit["id"] == community_unit_id)

            membership_rows = [
                UserMyUnitModel(user_id=epsilon_learner_id, unit_id=street_kittens_unit_id),
                UserMyUnitModel(user_id=nova_learner_id, unit_id=community_unit_id),
            ]
            db_session.add_all(membership_rows)
            await db_session.flush()

            my_units_memberships_summary.extend(
                [
                    (user_snapshots["epsilon"]["name"], street_kittens_title),
                    (user_snapshots["nova"]["name"], community_unit_title),
                ]
            )

            await db_session.commit()

            if args.verbose:
                print("📈 Creating learning sessions and unit sessions for sample progress...")

            # Clean up existing learning sessions and unit sessions for these users and units
            cat_unit_id = units_spec[0]["id"]
            grad_unit_id = units_spec[1]["id"]

            # Delete existing learning sessions for these units
            await db_session.execute(delete(LearningSessionModel).where(LearningSessionModel.unit_id.in_([cat_unit_id, grad_unit_id])))
            # Delete existing unit sessions for these units
            await db_session.execute(delete(UnitSessionModel).where(UnitSessionModel.unit_id.in_([cat_unit_id, grad_unit_id])))
            await db_session.flush()

            now = datetime.utcnow()

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
                last_lesson_id=cat_unit["lessons"][-1]["id"],  # Last lesson in the unit
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
    if my_units_memberships_summary:
        print("   • Sample My Units memberships:")
        for member_name, unit_title in my_units_memberships_summary:
            print(f"     - {member_name} → {unit_title}")

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
            "my_units_memberships": [{"user": member_name, "unit": unit_title} for member_name, unit_title in my_units_memberships_summary],
        }

        with Path(args.output).open("w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"📁 Summary saved to: {args.output}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
