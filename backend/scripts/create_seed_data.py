#!/usr/bin/env python3
"""
Seed Data Creation Script

Creates sample lesson data with all components without making actual LLM calls.
This creates realistic seed data for development and testing purposes.

Usage:
    python scripts/create_seed_data.py --verbose
    python scripts/create_seed_data.py --lesson "Neural Networks Basics" --concept "Backpropagation" --verbose
"""

import argparse
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
import sys
from typing import Any
import uuid

# Add the backend directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.content.models import LessonModel
from modules.content.package_models import DidacticSnippet, GlossaryTerm, LengthBudgets, LessonPackage, MCQAnswerKey, MCQItem, MCQOption, Meta, Objective
from modules.flow_engine.models import FlowRunModel, FlowStepRunModel
from modules.infrastructure.public import infrastructure_provider
from modules.llm_services.models import LLMRequestModel


def create_sample_lesson_package(
    lesson_id: str,
    title: str = "Cross-Entropy Loss in Deep Learning",
    core_concept: str = "Cross-Entropy Loss Function",
    user_level: str = "intermediate",
    domain: str = "Machine Learning",
) -> LessonPackage:
    """Create sample lesson package with all components."""

    # Create metadata
    meta = Meta(lesson_id=lesson_id, title=title, core_concept=core_concept, user_level=user_level, domain=domain, package_schema_version=1, content_version=1, length_budgets=LengthBudgets())

    # Create learning objectives
    objectives = [
        Objective(id="lo_1", text="Understand the mathematical definition of cross-entropy loss"),
        Objective(id="lo_2", text="Explain why cross-entropy is suitable for classification tasks"),
        Objective(id="lo_3", text="Implement cross-entropy loss in PyTorch"),
        Objective(id="lo_4", text="Compare cross-entropy with other loss functions"),
        Objective(id="lo_5", text="Apply cross-entropy loss to multi-class problems"),
    ]

    # Create glossary terms
    glossary_terms = [
        GlossaryTerm(id="term_1", term="Cross-entropy loss", definition="A measure of difference between two probability distributions", relation_to_core="Core concept of the lesson"),
        GlossaryTerm(id="term_2", term="One-hot encoding", definition="A representation where only one element is 1 and others are 0", relation_to_core="Used to represent true labels in cross-entropy calculation"),
        GlossaryTerm(id="term_3", term="Softmax", definition="A function that converts logits to probabilities", relation_to_core="Often used before cross-entropy loss in neural networks"),
        GlossaryTerm(id="term_4", term="Gradient descent", definition="An optimization algorithm that minimizes loss functions", relation_to_core="Algorithm used to minimize cross-entropy loss"),
        GlossaryTerm(id="term_5", term="Convex function", definition="A function with a single global minimum", relation_to_core="Cross-entropy loss is convex, ensuring reliable optimization"),
    ]

    # Create didactic snippet
    didactic_snippet = DidacticSnippet(
        id="didactic_lo_1",
        plain_explanation="Cross-entropy loss is a measure of the difference between two probability distributions. In machine learning, it quantifies how far our predicted probabilities are from the actual labels.",
        key_takeaways=["Cross-entropy is always non-negative", "It reaches zero when predictions are perfect", "It's convex, ensuring a single global minimum", "It provides strong gradients for incorrect predictions"],
        worked_example="For a 3-class problem with true label [0,1,0] and prediction [0.2,0.7,0.1], cross-entropy = -(0*log(0.2) + 1*log(0.7) + 0*log(0.1)) = -log(0.7) ≈ 0.357",
    )

    # Create MCQ questions
    mcqs = [
        MCQItem(
            id="mcq_1",
            lo_id="lo_1",
            stem="What is the mathematical formula for cross-entropy loss for a single sample?",
            options=[
                MCQOption(id="mcq_1_a", label="A", text="L = ∑(y_i * log(ŷ_i))"),
                MCQOption(id="mcq_1_b", label="B", text="L = -∑(y_i * log(ŷ_i))"),
                MCQOption(id="mcq_1_c", label="C", text="L = ∑(y_i - ŷ_i)²"),
                MCQOption(id="mcq_1_d", label="D", text="L = |y_i - ŷ_i|"),
            ],
            answer_key=MCQAnswerKey(label="B"),
        ),
        MCQItem(
            id="mcq_2",
            lo_id="lo_2",
            stem="Why is cross-entropy loss particularly suitable for classification tasks?",
            options=[
                MCQOption(id="mcq_2_a", label="A", text="It's computationally efficient"),
                MCQOption(id="mcq_2_b", label="B", text="It provides probabilistic interpretation and strong gradients"),
                MCQOption(id="mcq_2_c", label="C", text="It works only with binary classification"),
                MCQOption(id="mcq_2_d", label="D", text="It doesn't require gradient computation"),
            ],
            answer_key=MCQAnswerKey(label="B"),
        ),
        MCQItem(
            id="mcq_3",
            lo_id="lo_3",
            stem="In PyTorch, which function implements cross-entropy loss?",
            options=[
                MCQOption(id="mcq_3_a", label="A", text="nn.MSELoss()"),
                MCQOption(id="mcq_3_b", label="B", text="nn.CrossEntropyLoss()"),
                MCQOption(id="mcq_3_c", label="C", text="nn.BCELoss()"),
                MCQOption(id="mcq_3_d", label="D", text="nn.L1Loss()"),
            ],
            answer_key=MCQAnswerKey(label="B"),
        ),
        MCQItem(
            id="mcq_4",
            lo_id="lo_4",
            stem="How does cross-entropy loss compare to mean squared error for classification?",
            options=[
                MCQOption(id="mcq_4_a", label="A", text="MSE is always better for classification"),
                MCQOption(id="mcq_4_b", label="B", text="Cross-entropy provides better gradients and probabilistic interpretation"),
                MCQOption(id="mcq_4_c", label="C", text="They are equivalent for classification tasks"),
                MCQOption(id="mcq_4_d", label="D", text="MSE is faster to compute"),
            ],
            answer_key=MCQAnswerKey(label="B"),
        ),
        MCQItem(
            id="mcq_5",
            lo_id="lo_5",
            stem="What happens to cross-entropy loss when the model predicts the correct class with high confidence?",
            options=[
                MCQOption(id="mcq_5_a", label="A", text="Loss increases significantly"),
                MCQOption(id="mcq_5_b", label="B", text="Loss approaches zero"),
                MCQOption(id="mcq_5_c", label="C", text="Loss becomes negative"),
                MCQOption(id="mcq_5_d", label="D", text="Loss remains constant"),
            ],
            answer_key=MCQAnswerKey(label="B"),
        ),
    ]

    # Create the complete lesson package
    return LessonPackage(meta=meta, objectives=objectives, glossary={"terms": glossary_terms}, didactic={"by_lo": {"lo_1": didactic_snippet}}, mcqs=mcqs, misconceptions=[], confusables=[])


def create_sample_lesson_data(
    lesson_id: str,
    title: str = "Cross-Entropy Loss in Deep Learning",
    core_concept: str = "Cross-Entropy Loss Function",
    user_level: str = "intermediate",
    domain: str = "Machine Learning",
) -> dict[str, Any]:
    """Create sample lesson data structure with package."""

    # Create the lesson package
    package = create_sample_lesson_package(lesson_id, title, core_concept, user_level, domain)

    return {
        "id": lesson_id,
        "title": title,
        "core_concept": core_concept,
        "user_level": user_level,
        "source_material": """
        # Cross-Entropy Loss in Deep Learning

        Cross-entropy loss is a fundamental loss function used in classification tasks,
        particularly in neural networks. It measures the difference between the predicted
        probability distribution and the true distribution.

        ## Mathematical Definition

        For a single sample, cross-entropy loss is defined as:
        L = -∑(y_i * log(ŷ_i))

        Where:
        - y_i is the true label (one-hot encoded)
        - ŷ_i is the predicted probability for class i
        """,
        "source_domain": domain,
        "source_level": user_level,
        "refined_material": {
            "outline_bullets": [
                "Mathematical Foundation: Cross-entropy measures information content and difference between probability distributions",
                "Implementation: PyTorch provides nn.CrossEntropyLoss() for numerically stable computation",
                "Applications: Essential for multi-class classification tasks in neural networks",
            ],
            "evidence_anchors": [
                "Cross-entropy quantifies how far predicted probabilities are from actual labels",
                "Combines softmax activation and cross-entropy loss in single function",
                "Used in multi-class classification where each sample belongs to exactly one class",
            ],
        },
        "package": package.model_dump(),
        "package_version": 1,
    }


# Components are now embedded in the lesson package, no separate function needed


def create_sample_flow_run(lesson_id: str, lesson_data: dict[str, Any]) -> dict[str, Any]:
    """Create sample flow run data."""
    now = datetime.now(UTC)
    flow_run_id = uuid.uuid4()

    # Extract package data for outputs
    package = lesson_data["package"]

    return {
        "id": flow_run_id,
        "user_id": None,  # No user for seed data
        "flow_name": "lesson_creation",
        "status": "completed",
        "execution_mode": "sync",
        "current_step": None,
        "step_progress": 8,  # 1 metadata + 1 didactic + 1 glossary + 5 MCQs
        "total_steps": 8,
        "progress_percentage": 100.0,
        "created_at": now,
        "started_at": now,
        "completed_at": now,
        "last_heartbeat": now,
        "total_tokens": 15420,  # Realistic token count
        "total_cost": 0.0771,  # Realistic cost estimate
        "execution_time_ms": 45000,  # 45 seconds
        "inputs": {
            "title": lesson_data["title"],
            "core_concept": lesson_data["core_concept"],
            "source_material": lesson_data["source_material"],
            "user_level": lesson_data["user_level"],
            "domain": lesson_data["source_domain"],
        },
        "outputs": {
            "learning_objectives": [obj["text"] for obj in package["objectives"]],
            "glossary": package["glossary"],
            "didactic_snippet": package["didactic"]["by_lo"]["lo_1"],
            "mcqs": package["mcqs"],
            "refined_material": lesson_data["refined_material"],
        },
        "flow_metadata": {"lesson_id": lesson_id, "package_version": 1},
        "error_message": None,
    }


def create_sample_step_runs(flow_run_id: uuid.UUID, lesson_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Create sample flow step run data."""
    now = datetime.now(UTC)
    step_runs = []

    # Extract package data
    package = lesson_data["package"]

    # Step 1: Extract lesson metadata
    step_runs.append(
        {
            "id": uuid.uuid4(),
            "flow_run_id": flow_run_id,
            "llm_request_id": uuid.uuid4(),  # Will create corresponding LLM request
            "step_name": "extract_lesson_metadata",
            "step_order": 1,
            "status": "completed",
            "inputs": {"title": lesson_data["title"], "core_concept": lesson_data["core_concept"]},
            "outputs": {
                "learning_objectives": [obj["text"] for obj in package["objectives"]],
                "key_concepts": [term["term"] for term in package["glossary"]["terms"][:3]],  # First 3 terms
            },
            "tokens_used": 2100,
            "cost_estimate": 0.0105,
            "execution_time_ms": 3500,
            "error_message": None,
            "step_metadata": {"prompt_file": "extract_lesson_metadata.md"},
            "created_at": now,
            "completed_at": now,
        }
    )

    # Step 2: Generate didactic snippet
    didactic_snippet = package["didactic"]["by_lo"]["lo_1"]
    step_runs.append(
        {
            "id": uuid.uuid4(),
            "flow_run_id": flow_run_id,
            "llm_request_id": uuid.uuid4(),
            "step_name": "generate_didactic_snippet",
            "step_order": 2,
            "status": "completed",
            "inputs": {"lesson_title": lesson_data["title"], "core_concept": lesson_data["core_concept"]},
            "outputs": {"explanation": didactic_snippet["plain_explanation"], "key_takeaways": didactic_snippet["key_takeaways"], "worked_example": didactic_snippet.get("worked_example")},
            "tokens_used": 1800,
            "cost_estimate": 0.009,
            "execution_time_ms": 4200,
            "error_message": None,
            "step_metadata": {"prompt_file": "generate_didactic_snippet.md"},
            "created_at": now,
            "completed_at": now,
        }
    )

    # Step 3: Generate glossary
    step_runs.append(
        {
            "id": uuid.uuid4(),
            "flow_run_id": flow_run_id,
            "llm_request_id": uuid.uuid4(),
            "step_name": "generate_glossary",
            "step_order": 3,
            "status": "completed",
            "inputs": {"lesson_title": lesson_data["title"], "key_concepts": [term["term"] for term in package["glossary"]["terms"]]},
            "outputs": {"terms": package["glossary"]["terms"]},
            "tokens_used": 1600,
            "cost_estimate": 0.008,
            "execution_time_ms": 3800,
            "error_message": None,
            "step_metadata": {"prompt_file": "generate_glossary.md"},
            "created_at": now,
            "completed_at": now,
        }
    )

    # Steps 4-8: Generate MCQs
    mcqs = package["mcqs"]
    for i, mcq in enumerate(mcqs):
        # Find the corresponding objective
        objective_text = next((obj["text"] for obj in package["objectives"] if obj["id"] == mcq["lo_id"]), "Unknown objective")

        step_runs.append(
            {
                "id": uuid.uuid4(),
                "flow_run_id": flow_run_id,
                "llm_request_id": uuid.uuid4(),
                "step_name": "generate_mcq",
                "step_order": 4 + i,
                "status": "completed",
                "inputs": {"lesson_title": lesson_data["title"], "learning_objective": objective_text},
                "outputs": {"question": mcq["stem"], "options": [opt["text"] for opt in mcq["options"]], "correct_answer": mcq["answer_key"]["label"]},
                "tokens_used": 1800 + (i * 50),  # Slight variation
                "cost_estimate": 0.009 + (i * 0.0005),
                "execution_time_ms": 4000 + (i * 200),
                "error_message": None,
                "step_metadata": {"prompt_file": "generate_mcq.md"},
                "created_at": now,
                "completed_at": now,
            }
        )

    return step_runs


def create_sample_llm_requests(step_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create sample LLM request data for each step that uses LLM."""
    now = datetime.now(UTC)
    llm_requests = []

    for step_run in step_runs:
        if step_run["llm_request_id"]:
            # Create realistic request data based on step type
            if step_run["step_name"] == "extract_lesson_metadata":
                messages = [
                    {"role": "system", "content": "You are an expert educational content creator."},
                    {"role": "user", "content": "Extract learning objectives and key concepts from this material about Cross-Entropy Loss..."},
                ]
                response_content = json.dumps(step_run["outputs"])
            elif step_run["step_name"] == "generate_didactic_snippet":
                messages = [
                    {"role": "system", "content": "You are an expert educational content creator."},
                    {"role": "user", "content": "Generate an educational explanation for Cross-Entropy Loss..."},
                ]
                response_content = json.dumps(step_run["outputs"])
            elif step_run["step_name"] == "generate_glossary":
                messages = [
                    {"role": "system", "content": "You are an expert educational content creator."},
                    {"role": "user", "content": "Generate a glossary of key terms for Cross-Entropy Loss..."},
                ]
                response_content = json.dumps(step_run["outputs"])
            else:  # generate_mcq
                messages = [
                    {"role": "system", "content": "You are an expert educational content creator."},
                    {"role": "user", "content": f"Generate a multiple choice question for: {step_run['inputs'].get('learning_objective', 'Unknown')}"},
                ]
                response_content = json.dumps(step_run["outputs"])

            llm_requests.append(
                {
                    "id": step_run["llm_request_id"],
                    "user_id": None,
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
                    "response_content": response_content,
                    "response_raw": {"choices": [{"message": {"content": response_content}}]},
                    "response_output": step_run["outputs"],
                    "tokens_used": step_run["tokens_used"],
                    "input_tokens": int(step_run["tokens_used"] * 0.6),  # Approximate split
                    "output_tokens": int(step_run["tokens_used"] * 0.4),
                    "cost_estimate": step_run["cost_estimate"],
                    "response_created_at": now,
                    "status": "completed",
                    "execution_time_ms": step_run["execution_time_ms"],
                    "error_message": None,
                    "error_type": None,
                    "retry_attempt": 1,
                    "cached": False,
                    "created_at": now,
                }
            )

    return llm_requests


async def main() -> None:
    """Main function to create seed data."""
    parser = argparse.ArgumentParser(description="Create seed data for development and testing")
    parser.add_argument("--lesson", default="Cross-Entropy Loss in Deep Learning", help="Lesson title")
    parser.add_argument("--concept", default="Cross-Entropy Loss Function", help="Core concept")
    parser.add_argument("--level", default="intermediate", choices=["beginner", "intermediate", "advanced"], help="User level")
    parser.add_argument("--domain", default="Machine Learning", help="Subject domain")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")
    parser.add_argument("--output", help="Save summary to JSON file")

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        print("🔧 Verbose mode enabled")

    print(f"🌱 Creating seed data for lesson: {args.lesson}")
    print(f"🎯 Core concept: {args.concept}")
    print(f"📊 Level: {args.level}, Domain: {args.domain}")
    print()

    try:
        # Initialize infrastructure
        if args.verbose:
            print("🔄 Initializing infrastructure...")
        infra = infrastructure_provider()
        infra.initialize()

        # Generate lesson ID
        lesson_id = str(uuid.uuid4())

        # Create sample data
        if args.verbose:
            print("📚 Creating lesson data with package...")
        lesson_data = create_sample_lesson_data(lesson_id, args.lesson, args.concept, args.level, args.domain)

        if args.verbose:
            print("🔄 Creating flow run data...")
        flow_run_data = create_sample_flow_run(lesson_id, lesson_data)

        if args.verbose:
            print("👣 Creating step run data...")
        step_runs = create_sample_step_runs(flow_run_data["id"], lesson_data)

        if args.verbose:
            print("🤖 Creating LLM request data...")
        llm_requests = create_sample_llm_requests(step_runs)

        # Save to database
        with infra.get_session_context() as db_session:
            if args.verbose:
                print("💾 Saving lesson with package to database...")

            # Create lesson with embedded package
            lesson = LessonModel(**lesson_data)
            db_session.add(lesson)

            # Create flow run
            if args.verbose:
                print("💾 Saving flow run...")
            flow_run = FlowRunModel(**flow_run_data)
            db_session.add(flow_run)

            # Create step runs
            if args.verbose:
                print(f"💾 Saving {len(step_runs)} step runs...")
            for step_run_data in step_runs:
                step_run = FlowStepRunModel(**step_run_data)
                db_session.add(step_run)

            # Create LLM requests
            if args.verbose:
                print(f"💾 Saving {len(llm_requests)} LLM requests...")
            for llm_request_data in llm_requests:
                llm_request = LLMRequestModel(**llm_request_data)
                db_session.add(llm_request)

            # Commit all changes
            if args.verbose:
                print("💾 Committing changes...")

        # Calculate component counts from package
        package = lesson_data["package"]
        component_count = len(package["mcqs"]) + len(package["didactic"]["by_lo"]) + len(package["glossary"]["terms"])

        print("✅ Seed data created successfully!")
        print(f"   • Lesson ID: {lesson_id}")
        print(f"   • Title: {lesson_data['title']}")
        print(f"   • Package components: {component_count} (5 MCQs, 1 didactic, 5 glossary terms)")
        print(f"   • Package version: {lesson_data['package_version']}")
        print("   • Flow runs: 1")
        print(f"   • Step runs: {len(step_runs)}")
        print(f"   • LLM requests: {len(llm_requests)}")
        print(f"   • Total tokens: {flow_run_data['total_tokens']}")
        print(f"   • Total cost: ${flow_run_data['total_cost']:.4f}")
        print(f"   • Frontend URL: http://localhost:3000/learn/{lesson_id}?mode=learning")

        # Save summary if requested
        if args.output:
            summary = {
                "lesson_id": lesson_id,
                "title": lesson_data["title"],
                "concept": args.concept,
                "user_level": args.level,
                "domain": args.domain,
                "package_version": lesson_data["package_version"],
                "package_components": component_count,
                "objectives_count": len(package["objectives"]),
                "glossary_terms_count": len(package["glossary"]["terms"]),
                "mcqs_count": len(package["mcqs"]),
                "flow_runs": 1,
                "step_runs": len(step_runs),
                "llm_requests": len(llm_requests),
                "total_tokens": flow_run_data["total_tokens"],
                "total_cost": flow_run_data["total_cost"],
                "created_with": "seed_data_script_package_model",
            }

            with open(args.output, "w") as f:
                json.dump(summary, f, indent=2, default=str)
            print(f"📁 Summary saved to: {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
