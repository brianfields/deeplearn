#!/usr/bin/env python3
"""
Seed Data Creation Script

Creates sample unit and lesson data using the canonical package structure
(didactic_snippet, exercises, glossary) without making actual LLM calls.
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
import traceback
from typing import Any
import uuid

# Add the backend directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.content.models import LessonModel
from modules.content.package_models import DidacticSnippet, GlossaryTerm, LengthBudgets, LessonPackage, MCQAnswerKey, MCQExercise, MCQOption, Meta, Objective
from modules.flow_engine.models import FlowRunModel, FlowStepRunModel
from modules.infrastructure.public import infrastructure_provider
from modules.llm_services.models import LLMRequestModel
from modules.content.models import UnitModel  # Import UnitModel so SQLAlchemy knows about the units table


def create_sample_lesson_package(
    lesson_id: str,
    title: str = "Cross-Entropy Loss in Deep Learning",
    core_concept: str = "Cross-Entropy Loss Function",
    user_level: str = "intermediate",
    domain: str = "Machine Learning",
) -> LessonPackage:
    """Create sample lesson package with all components."""

    # Create metadata
    meta = Meta(
        lesson_id=lesson_id, title=title, core_concept=core_concept, user_level=user_level, domain=domain, package_schema_version=1, content_version=1, length_budgets=LengthBudgets(stem_max_words=35, vignette_max_words=80, option_max_words=12)
    )

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

    # Create lesson-wide didactic snippet (new mobile-friendly structure)
    lesson_didactic_snippet = DidacticSnippet(
        id="lesson_explanation",
        plain_explanation="""Cross-entropy loss is a fundamental concept in machine learning that measures how different your model's predictions are from the actual answers.

Think of it like a scoring system for classification tasks. When your model is confident and correct, the loss is very low. When it's confident but wrong, the loss becomes very high, sending a strong signal to improve.

Cross-entropy works by comparing probability distributions. Your model outputs probabilities for each possible class, and cross-entropy measures how far these are from the true "one-hot" distribution where the correct class has probability 1.

In practice, cross-entropy is the go-to loss function for classification because it provides strong learning signals and has nice mathematical properties that make optimization reliable.""",
        key_takeaways=[
            "Cross-entropy measures the difference between predicted and actual probability distributions",
            "It provides strong gradients when predictions are wrong, helping models learn faster",
            "The loss approaches zero when predictions are correct and confident",
            "It's the standard choice for classification tasks in neural networks",
        ],
        worked_example="For a 3-class problem with true label [0,1,0] and prediction [0.2,0.7,0.1], cross-entropy = -(0*log(0.2) + 1*log(0.7) + 0*log(0.1)) = -log(0.7) ≈ 0.357",
    )

    # Create exercises directly as proper MCQExercise objects
    exercises = [
        MCQExercise(
            id="mcq_1",
            lo_id="lo_1",
            cognitive_level="Remember",
            estimated_difficulty="Medium",
            misconceptions_used=["mc_1", "mc_2"],
            stem="What is the mathematical formula for cross-entropy loss for a single sample?",
            options=[
                MCQOption(id="mcq_1_a", label="A", text="L = ∑(y_i * log(ŷ_i))", rationale_wrong="Missing negative sign; this would give positive loss values"),
                MCQOption(id="mcq_1_b", label="B", text="L = -∑(y_i * log(ŷ_i))", rationale_wrong=None),
                MCQOption(id="mcq_1_c", label="C", text="L = ∑(y_i - ŷ_i)²", rationale_wrong="This is mean squared error, not cross-entropy loss"),
                MCQOption(id="mcq_1_d", label="D", text="L = |y_i - ŷ_i|", rationale_wrong="This is mean absolute error, not cross-entropy loss"),
            ],
            answer_key=MCQAnswerKey(label="B", rationale_right="Cross-entropy loss requires the negative log-likelihood formulation"),
        ),
        MCQExercise(
            id="mcq_2",
            lo_id="lo_2",
            cognitive_level="Understand",
            estimated_difficulty="Medium",
            misconceptions_used=["mc_3"],
            stem="Why is cross-entropy loss particularly suitable for classification tasks?",
            options=[
                MCQOption(id="mcq_2_a", label="A", text="It's computationally efficient", rationale_wrong="Efficiency alone doesn't explain its suitability for classification"),
                MCQOption(id="mcq_2_b", label="B", text="It provides probabilistic interpretation and strong gradients", rationale_wrong=None),
                MCQOption(id="mcq_2_c", label="C", text="It works only with binary classification", rationale_wrong="Cross-entropy works for multi-class classification too"),
                MCQOption(id="mcq_2_d", label="D", text="It doesn't require gradient computation", rationale_wrong="All neural network training requires gradients"),
            ],
            answer_key=MCQAnswerKey(label="B", rationale_right="Cross-entropy naturally outputs probabilities and provides strong learning signals"),
        ),
        MCQExercise(
            id="mcq_3",
            lo_id="lo_3",
            cognitive_level="Apply",
            estimated_difficulty="Easy",
            misconceptions_used=["mc_4"],
            stem="In PyTorch, which function implements cross-entropy loss?",
            options=[
                MCQOption(id="mcq_3_a", label="A", text="nn.MSELoss()", rationale_wrong="MSELoss is for regression, not classification"),
                MCQOption(id="mcq_3_b", label="B", text="nn.CrossEntropyLoss()", rationale_wrong=None),
                MCQOption(id="mcq_3_c", label="C", text="nn.BCELoss()", rationale_wrong="BCELoss is for binary classification only"),
                MCQOption(id="mcq_3_d", label="D", text="nn.L1Loss()", rationale_wrong="L1Loss is for regression, not classification"),
            ],
            answer_key=MCQAnswerKey(label="B", rationale_right="nn.CrossEntropyLoss() combines softmax and cross-entropy in one function"),
        ),
        MCQExercise(
            id="mcq_4",
            lo_id="lo_4",
            cognitive_level="Analyze",
            estimated_difficulty="Hard",
            misconceptions_used=["mc_5"],
            stem="How does cross-entropy loss compare to mean squared error for classification?",
            options=[
                MCQOption(id="mcq_4_a", label="A", text="MSE is always better for classification", rationale_wrong="MSE provides weaker gradients and no probabilistic interpretation"),
                MCQOption(id="mcq_4_b", label="B", text="Cross-entropy provides better gradients and probabilistic interpretation", rationale_wrong=None),
                MCQOption(id="mcq_4_c", label="C", text="They are equivalent for classification tasks", rationale_wrong="Cross-entropy is specifically designed for classification"),
                MCQOption(id="mcq_4_d", label="D", text="MSE is faster to compute", rationale_wrong="Computational speed isn't the main consideration for loss choice"),
            ],
            answer_key=MCQAnswerKey(label="B", rationale_right="Cross-entropy gives stronger gradients when confident but wrong, ideal for classification"),
        ),
        MCQExercise(
            id="mcq_5",
            lo_id="lo_5",
            cognitive_level="Apply",
            estimated_difficulty="Medium",
            misconceptions_used=["mc_6"],
            stem="What happens to cross-entropy loss when the model predicts the correct class with high confidence?",
            options=[
                MCQOption(id="mcq_5_a", label="A", text="Loss increases significantly", rationale_wrong="Correct predictions with high confidence should decrease loss"),
                MCQOption(id="mcq_5_b", label="B", text="Loss approaches zero", rationale_wrong=None),
                MCQOption(id="mcq_5_c", label="C", text="Loss becomes negative", rationale_wrong="Cross-entropy loss is always non-negative"),
                MCQOption(id="mcq_5_d", label="D", text="Loss remains constant", rationale_wrong="Loss varies with prediction confidence"),
            ],
            answer_key=MCQAnswerKey(label="B", rationale_right="High confidence correct predictions minimize the negative log-likelihood"),
        ),
    ]

    # Create misconceptions referenced in MCQs
    misconceptions = [
        {"mc_id": "mc_1", "concept": "Cross-entropy formula", "misbelief": "Cross-entropy should be positive like other loss functions"},
        {"mc_id": "mc_2", "concept": "Loss function types", "misbelief": "All loss functions have the same mathematical form"},
        {"mc_id": "mc_3", "concept": "Classification vs regression", "misbelief": "Any loss function can be used for any task"},
        {"mc_id": "mc_4", "concept": "PyTorch loss functions", "misbelief": "BCELoss and CrossEntropyLoss are interchangeable"},
        {"mc_id": "mc_5", "concept": "Loss function comparison", "misbelief": "MSE and cross-entropy are equivalent for classification"},
        {"mc_id": "mc_6", "concept": "Loss behavior", "misbelief": "Loss functions can become negative"},
    ]

    # Create confusables (commonly confused concepts)
    confusables = [
        {"concept_a": "Cross-entropy loss", "concept_b": "Mean squared error", "distinction": "Cross-entropy for classification, MSE for regression"},
        {"concept_b": "Binary cross-entropy", "concept_a": "Categorical cross-entropy", "distinction": "Binary for 2 classes, categorical for multiple classes"},
        {"concept_a": "Log-likelihood", "concept_b": "Cross-entropy", "distinction": "Cross-entropy is negative log-likelihood"},
    ]

    # Create the complete lesson package with new structure
    return LessonPackage(
        meta=meta,
        objectives=objectives,
        glossary={"terms": glossary_terms},
        didactic_snippet=lesson_didactic_snippet,
        exercises=exercises,
        misconceptions=misconceptions,
        confusables=confusables,
    )


def create_sample_lesson_data(
    lesson_id: str,
    title: str = "Cross-Entropy Loss in Deep Learning",
    core_concept: str = "Cross-Entropy Loss Function",
    user_level: str = "intermediate",
    domain: str = "Machine Learning",
    flow_run_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Create sample lesson data structure with package."""

    # Create the lesson package
    package = create_sample_lesson_package(lesson_id, title, core_concept, user_level, domain)

    return {
        "id": lesson_id,
        "flow_run_id": flow_run_id,
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


# All content fields are embedded in the lesson package; no separate component list


def create_sample_flow_run(flow_run_id: uuid.UUID, lesson_id: str, lesson_data: dict[str, Any]) -> dict[str, Any]:
    """Create sample flow run data."""
    now = datetime.now(UTC)

    # Extract package data for outputs
    package = lesson_data["package"]

    return {
        "id": flow_run_id,
        "user_id": None,  # No user for seed data
        "flow_name": "lesson_creation",
        "status": "completed",
        "execution_mode": "sync",
        "current_step": None,
        "step_progress": 5,  # 1 metadata + 1 misconception_bank + 1 didactic + 1 glossary + 1 MCQs
        "total_steps": 5,
        "progress_percentage": 100.0,
        "created_at": now,
        "updated_at": now,
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
            "didactic_snippet": package["didactic_snippet"],
            "exercises": package["exercises"],
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

    # Get the original exercises from the lesson data creation
    # We'll create a simplified version for the step outputs
    sample_exercises = [
        {"lo_id": "lo_1", "stem": "What is cross-entropy loss?", "options": ["Option A", "Option B", "Option C"], "correct_answer": "B"},
        {"lo_id": "lo_2", "stem": "Why use cross-entropy?", "options": ["Option A", "Option B", "Option C"], "correct_answer": "B"},
        {"lo_id": "lo_3", "stem": "PyTorch function?", "options": ["Option A", "Option B", "Option C"], "correct_answer": "B"},
        {"lo_id": "lo_4", "stem": "Compare to MSE?", "options": ["Option A", "Option B", "Option C"], "correct_answer": "B"},
        {"lo_id": "lo_5", "stem": "High confidence?", "options": ["Option A", "Option B", "Option C"], "correct_answer": "B"},
    ]

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
            "updated_at": now,
            "completed_at": now,
        }
    )

    # Step 2: Generate misconception bank
    step_runs.append(
        {
            "id": uuid.uuid4(),
            "flow_run_id": flow_run_id,
            "llm_request_id": uuid.uuid4(),
            "step_name": "generate_misconception_bank",
            "step_order": 2,
            "status": "completed",
            "inputs": {
                "core_concept": lesson_data["core_concept"],
                "learning_objectives": [obj["text"] for obj in package["objectives"]],
                "key_concepts": [term["term"] for term in package["glossary"]["terms"][:3]],
            },
            "outputs": {
                "by_lo": [
                    {
                        "lo_id": f"lo_{i + 1}",
                        "distractors": [
                            {"text": f"Distractor {j + 1} for LO {i + 1}", "maps_to_mc_id": f"mc_{j + 1}"}
                            for j in range(2)  # 2 distractors per LO
                        ],
                    }
                    for i in range(len(package["objectives"]))
                ]
            },
            "tokens_used": 2200,
            "cost_estimate": 0.011,
            "execution_time_ms": 5000,
            "error_message": None,
            "step_metadata": {"prompt_file": "generate_misconception_bank.md"},
            "created_at": now,
            "updated_at": now,
            "completed_at": now,
        }
    )

    # Step 3: Generate lesson-wide didactic snippet
    didactic_snippet = package["didactic_snippet"]
    step_runs.append(
        {
            "id": uuid.uuid4(),
            "flow_run_id": flow_run_id,
            "llm_request_id": uuid.uuid4(),
            "step_name": "generate_didactic_snippet",
            "step_order": 3,
            "status": "completed",
            "inputs": {
                "lesson_title": lesson_data["title"],
                "core_concept": lesson_data["core_concept"],
                "learning_objectives": [obj["text"] for obj in package["objectives"]],
                "key_concepts": [term["term"] for term in package["glossary"]["terms"][:3]],
            },
            "outputs": {
                "introduction": "Cross-entropy loss is a fundamental concept in machine learning...",
                "core_explanation": didactic_snippet["plain_explanation"],
                "key_points": didactic_snippet["key_takeaways"],
                "practical_context": "In practice, cross-entropy is the go-to loss function for classification...",
                "worked_example": didactic_snippet.get("worked_example"),
            },
            "tokens_used": 1800,
            "cost_estimate": 0.009,
            "execution_time_ms": 4200,
            "error_message": None,
            "step_metadata": {"prompt_file": "generate_didactic_snippet.md"},
            "created_at": now,
            "updated_at": now,
            "completed_at": now,
        }
    )

    # Step 4: Generate glossary
    step_runs.append(
        {
            "id": uuid.uuid4(),
            "flow_run_id": flow_run_id,
            "llm_request_id": uuid.uuid4(),
            "step_name": "generate_glossary",
            "step_order": 4,
            "status": "completed",
            "inputs": {"lesson_title": lesson_data["title"], "key_concepts": [term["term"] for term in package["glossary"]["terms"]]},
            "outputs": {"terms": package["glossary"]["terms"]},
            "tokens_used": 1600,
            "cost_estimate": 0.008,
            "execution_time_ms": 3800,
            "error_message": None,
            "step_metadata": {"prompt_file": "generate_glossary.md"},
            "created_at": now,
            "updated_at": now,
            "completed_at": now,
        }
    )

    # Step 5: Generate all exercises in one call
    step_runs.append(
        {
            "id": uuid.uuid4(),
            "flow_run_id": flow_run_id,
            "llm_request_id": uuid.uuid4(),
            "step_name": "generate_mcqs",  # Updated to match new step name
            "step_order": 5,
            "status": "completed",
            "inputs": {
                "lesson_title": lesson_data["title"],
                "learning_objectives": [obj["text"] for obj in package["objectives"]],
                "distractor_pools": {},  # Simplified for seed data
            },
            "outputs": {"exercises": sample_exercises},
            "tokens_used": 3500,  # Higher token count for generating multiple MCQs
            "cost_estimate": 0.0175,
            "execution_time_ms": 8000,  # Longer execution time for multiple MCQs
            "error_message": None,
            "step_metadata": {"prompt_file": "generate_mcq.md"},
            "created_at": now,
            "updated_at": now,
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
            elif step_run["step_name"] == "generate_misconception_bank":
                messages = [
                    {"role": "system", "content": "You are an expert educational content creator."},
                    {"role": "user", "content": "Generate misconceptions and distractors for Cross-Entropy Loss..."},
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
            elif step_run["step_name"] == "generate_mcqs":  # Updated step name
                messages = [
                    {"role": "system", "content": "You are an expert educational content creator."},
                    {"role": "user", "content": f"Generate multiple choice questions for all learning objectives in the lesson: {step_run['inputs'].get('lesson_title', 'Unknown')}"},
                ]
                response_content = json.dumps(step_run["outputs"])
            else:  # fallback for any other steps
                messages = [
                    {"role": "system", "content": "You are an expert educational content creator."},
                    {"role": "user", "content": f"Process step: {step_run['step_name']}"},
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
                    "updated_at": now,
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
    # Unit-related options
    parser.add_argument("--unit-title", default="Introduction to Machine Learning", help="Unit title for grouping lessons")
    parser.add_argument("--unit-description", default="Foundational concepts and probability tools", help="Unit description")
    parser.add_argument("--unit-difficulty", default="beginner", choices=["beginner", "intermediate", "advanced"], help="Unit difficulty")

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

        # Create a unit to group lessons
        unit_id = str(uuid.uuid4())
        if args.verbose:
            print(f"🧱 Creating unit: {args.unit_title} ({args.unit_difficulty})")

        # Generate first lesson (from args)
        lesson_id_1 = str(uuid.uuid4())
        flow_run_id_1 = uuid.uuid4()
        if args.verbose:
            print("📚 Creating lesson 1 data with package...")
        lesson_data_1 = create_sample_lesson_data(lesson_id_1, args.lesson, args.concept, args.level, args.domain, flow_run_id_1)
        flow_run_data_1 = create_sample_flow_run(flow_run_id_1, lesson_id_1, lesson_data_1)
        step_runs_1 = create_sample_step_runs(flow_run_data_1["id"], lesson_data_1)
        llm_requests_1 = create_sample_llm_requests(step_runs_1)

        # Generate a second related lesson to demonstrate multi-lesson units
        lesson_id_2 = str(uuid.uuid4())
        flow_run_id_2 = uuid.uuid4()
        if args.verbose:
            print("📚 Creating lesson 2 data with package...")
        lesson_data_2 = create_sample_lesson_data(
            lesson_id_2,
            title="Softmax and Probabilities",
            core_concept="Softmax Function",
            user_level=args.level,
            domain=args.domain,
            flow_run_id=flow_run_id_2,
        )
        flow_run_data_2 = create_sample_flow_run(flow_run_id_2, lesson_id_2, lesson_data_2)
        step_runs_2 = create_sample_step_runs(flow_run_data_2["id"], lesson_data_2)
        llm_requests_2 = create_sample_llm_requests(step_runs_2)

        # Save to database
        with infra.get_session_context() as db_session:
            # Create flow run first (required for foreign key constraint)
            if args.verbose:
                print("💾 Saving flow runs...")
            flow_run_1 = FlowRunModel(**flow_run_data_1)
            flow_run_2 = FlowRunModel(**flow_run_data_2)
            db_session.add(flow_run_1)
            db_session.add(flow_run_2)
            db_session.flush()  # Ensure flow runs are persisted before creating lessons

            if args.verbose:
                print("💾 Saving lessons with packages to database...")

            # Create unit
            unit = UnitModel(
                id=unit_id,
                title=args.unit_title,
                description=args.unit_description,
                difficulty=args.unit_difficulty,
                lesson_order=[lesson_id_1, lesson_id_2],
            )
            db_session.add(unit)

            # Create lessons with embedded packages and link to unit
            lesson_1 = LessonModel(**{**lesson_data_1, "unit_id": unit_id})
            lesson_2 = LessonModel(**{**lesson_data_2, "unit_id": unit_id})
            db_session.add(lesson_1)
            db_session.add(lesson_2)

            # Create LLM requests first (required for step run foreign key constraint)
            if args.verbose:
                print(f"💾 Saving {len(llm_requests_1) + len(llm_requests_2)} LLM requests...")
            for llm_request_data in [*llm_requests_1, *llm_requests_2]:
                llm_request = LLMRequestModel(**llm_request_data)
                db_session.add(llm_request)
            db_session.flush()  # Ensure LLM requests are persisted before creating step runs

            # Create step runs (references LLM requests)
            if args.verbose:
                print(f"💾 Saving {len(step_runs_1) + len(step_runs_2)} step runs...")
            for step_run_data in [*step_runs_1, *step_runs_2]:
                step_run = FlowStepRunModel(**step_run_data)
                db_session.add(step_run)

            # Commit all changes
            if args.verbose:
                print("💾 Committing changes...")

        # Report package content counts by type
        package_1 = lesson_data_1["package"]
        package_2 = lesson_data_2["package"]
        exercises_count_1 = len(package_1["exercises"])
        glossary_terms_count_1 = len(package_1["glossary"]["terms"])
        exercises_count_2 = len(package_2["exercises"])
        glossary_terms_count_2 = len(package_2["glossary"]["terms"])

        print("✅ Seed data created successfully!")
        print(f"   • Unit ID: {unit_id}")
        print(f"   • Unit: {args.unit_title} — lessons: 2")
        print(f"   • Lesson 1 ID: {lesson_id_1} — {lesson_data_1['title']}")
        print(f"     • Exercises: {exercises_count_1}; Glossary terms: {glossary_terms_count_1}")
        print(f"   • Lesson 2 ID: {lesson_id_2} — {lesson_data_2['title']}")
        print(f"     • Exercises: {exercises_count_2}; Glossary terms: {glossary_terms_count_2}")
        print(f"   • Package versions: {lesson_data_1['package_version']}, {lesson_data_2['package_version']}")
        print("   • Flow runs: 2")
        print(f"   • Step runs: {len(step_runs_1) + len(step_runs_2)}")
        print(f"   • LLM requests: {len(llm_requests_1) + len(llm_requests_2)}")
        print(f"   • Frontend URL (lesson 1): http://localhost:3000/learn/{lesson_id_1}?mode=learning")

        # Save summary if requested
        if args.output:
            summary = {
                "unit": {
                    "id": unit_id,
                    "title": args.unit_title,
                    "description": args.unit_description,
                    "difficulty": args.unit_difficulty,
                    "lesson_order": [lesson_id_1, lesson_id_2],
                },
                "lessons": [
                    {
                        "lesson_id": lesson_id_1,
                        "title": lesson_data_1["title"],
                        "concept": lesson_data_1["core_concept"],
                        "user_level": args.level,
                        "domain": args.domain,
                        "package_version": lesson_data_1["package_version"],
                        "objectives_count": len(package_1["objectives"]),
                        "glossary_terms_count": len(package_1["glossary"]["terms"]),
                        "exercises_count": len(package_1["exercises"]),
                        "didactic_snippet_present": bool(package_1.get("didactic_snippet")),
                    },
                    {
                        "lesson_id": lesson_id_2,
                        "title": lesson_data_2["title"],
                        "concept": lesson_data_2["core_concept"],
                        "user_level": args.level,
                        "domain": args.domain,
                        "package_version": lesson_data_2["package_version"],
                        "objectives_count": len(package_2["objectives"]),
                        "glossary_terms_count": len(package_2["glossary"]["terms"]),
                        "exercises_count": len(package_2["exercises"]),
                        "didactic_snippet_present": bool(package_2.get("didactic_snippet")),
                    },
                ],
                "created_with": "seed_data_script_package_model_units",
            }

            with Path(args.output).open("w") as f:
                json.dump(summary, f, indent=2, default=str)
            print(f"📁 Summary saved to: {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
