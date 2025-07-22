#!/usr/bin/env python3
"""
Complete Topic Creation Script

This script creates a complete learning topic with:
1. Topic metadata and learning objectives
2. Didactic snippet for concept explanation
3. Individual MCQs for each learning objective
4. All content saved to the database

Example Usage:
    # Create complete topic from source material
    python scripts/create_complete_topic.py \
        --topic "PyTorch Tensors" \
        --concept "Cross-Entropy Loss Function" \
        --level intermediate \
        --material scripts/examples/pytorch_tensor_material.txt \
        --objectives "Understand cross-entropy calculation" "Apply loss to classification" \
        --verbose

    # Minimal usage
    python scripts/create_complete_topic.py \
        --topic "Your Topic" \
        --concept "Core Concept" \
        --material your_material.txt

Arguments:
    --topic: Topic title (required)
    --concept: Core concept (required)
    --material: Path to source material text file (required)
    --level: User level (beginner/intermediate/advanced, default: intermediate)
    --objectives: Learning objectives (can specify multiple)
    --domain: Subject domain (optional)
    --model: LLM model to use (default: gpt-4)
    --verbose: Show detailed progress
    --dry-run: Generate content but don't save to database
"""

import argparse
import asyncio
import json
import sys
from tkinter.constants import E
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.llm_client import LLMClient
from src.core.service_base import ServiceConfig
from src.data_structures import BiteSizedComponent, BiteSizedTopic
from src.database_service import DatabaseService
from src.modules.lesson_planning.bite_sized_topics.mcq_service import MCQService
from src.modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService


async def create_didactic_snippet(topic_service: BiteSizedTopicService, topic_title: str, core_concept: str, user_level: str, source_material: str, learning_objectives: list[str], verbose: bool = False) -> dict[str, Any]:
    """Create a didactic snippet component."""
    if verbose:
        print(f"🔄 Creating didactic snippet for '{core_concept}'...")

    snippet = await topic_service.create_didactic_snippet(topic_title=topic_title, core_concept=core_concept, user_level=user_level, source_material=source_material, learning_objectives=learning_objectives)

    if verbose:
        print(f"✅ Created didactic snippet: {len(snippet.get('content', ''))} characters")

    return snippet


async def create_mcqs_for_objectives(mcq_service: MCQService, topic_title: str, core_concept: str, user_level: str, source_material: str, learning_objectives: list[str], verbose: bool = False) -> list[dict[str, Any]]:
    """Create individual MCQs for each learning objective."""
    mcqs = []

    for i, objective in enumerate(learning_objectives, 1):
        if verbose:
            print(f"🔄 Creating MCQ {i}/{len(learning_objectives)} for objective: '{objective}'...")

        try:
            # Create refined material first
            refined_material = await mcq_service.extract_refined_material(topic_title=topic_title, source_material=source_material, domain=core_concept, user_level=user_level)

            # Create MCQ for this specific objective
            mcq = await mcq_service.create_single_mcq(learning_objective=objective, refined_material=refined_material, topic_title=topic_title, core_concept=core_concept, user_level=user_level)

            mcqs.append(mcq)

            if verbose:
                question = mcq.get("mcq", {}).get("stem", "Unknown question")
                print(f"✅ Created MCQ {i}: {question[:50]}...")

        except Exception as e:
            print(f"❌ Error creating MCQ for objective '{objective}': {e}")
            if verbose:
                import traceback

                traceback.print_exc()

    return mcqs


async def save_topic_to_database(db_service: DatabaseService, topic_title: str, core_concept: str, user_level: str, learning_objectives: list[str], source_material: str, domain: str, didactic_snippet: dict[str, Any], mcqs: list[dict[str, Any]], verbose: bool = False) -> str:
    """Save the complete topic and all components to the database."""
    topic_id = str(uuid.uuid4())

    if verbose:
        print(f"🔄 Saving topic to database with ID: {topic_id}")

    # Create topic
    topic = BiteSizedTopic(
        id=topic_id, title=topic_title, core_concept=core_concept, user_level=user_level, learning_objectives=learning_objectives, key_concepts=[core_concept], source_material=source_material, source_domain=domain, source_level=user_level, created_at=datetime.utcnow(), updated_at=datetime.utcnow()
    )

    # Save topic first
    if not db_service.save_bite_sized_topic(topic):
        raise Exception("Failed to save topic to database")

    if verbose:
        print(f"✅ Saved topic: {topic_title}")

    # Create all components first
    components = []

    # Create didactic snippet component
    didactic_component = BiteSizedComponent(id=str(uuid.uuid4()), topic_id=topic_id, component_type="didactic_snippet", title=f"Learn: {core_concept}", content=didactic_snippet)
    components.append(didactic_component)

    # Create MCQ components
    for i, mcq in enumerate(mcqs, 1):
        mcq_title = mcq.get("mcq", {}).get("stem", f"Question {i}")[:50] + "..."

        mcq_component = BiteSizedComponent(id=str(uuid.uuid4()), topic_id=topic_id, component_type="mcq", title=f"MCQ: {mcq_title}", content=mcq)
        components.append(mcq_component)

    # Attach components to topic before saving
    topic.components = components

    if verbose:
        print("✅ Saved didactic snippet component")
        print(f"✅ Saved {len(mcqs)} MCQ components")
        print(f"🎉 Complete topic saved with {1 + len(mcqs)} components!")

    return topic_id


async def main():
    parser = argparse.ArgumentParser(description="Create complete learning topic with didactic snippet and MCQs")
    parser.add_argument("--topic", required=True, help="Topic title")
    parser.add_argument("--concept", required=True, help="Core concept")
    parser.add_argument("--material", required=True, help="Path to source material text file")
    parser.add_argument("--level", default="intermediate", choices=["beginner", "intermediate", "advanced"], help="Target user level")
    parser.add_argument("--objectives", nargs="+", help="Learning objectives (can specify multiple)")
    parser.add_argument("--domain", default="", help="Subject domain")
    parser.add_argument("--model", default="gpt-4", help="LLM model to use")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")
    parser.add_argument("--dry-run", action="store_true", help="Generate content but don't save to database")

    args = parser.parse_args()

    # Validate inputs
    material_path = Path(args.material)
    if not material_path.exists():
        print(f"❌ Error: Material file not found: {args.material}")
        sys.exit(1)

    # Read source material
    try:
        source_material = material_path.read_text(encoding="utf-8")
        if args.verbose:
            print(f"📄 Loaded source material: {len(source_material)} characters")
    except Exception as e:
        print(f"❌ Error reading material file: {e}")
        sys.exit(1)

    # Set default learning objectives if not provided
    learning_objectives = args.objectives or [f"Understand the core concept of {args.concept}", f"Apply {args.concept} in practical scenarios", f"Identify key features of {args.concept}"]

    if args.verbose:
        print(f"🎯 Topic: {args.topic}")
        print(f"🎯 Core Concept: {args.concept}")
        print(f"🎯 User Level: {args.level}")
        print(f"🎯 Learning Objectives ({len(learning_objectives)}):")
        for i, obj in enumerate(learning_objectives, 1):
            print(f"   {i}. {obj}")
        print()

    try:
        # Initialize services
        llm_client = LLMClient(model=args.model)
        config = ServiceConfig()
        topic_service = BiteSizedTopicService(config, llm_client)
        mcq_service = MCQService(llm_client)

        if not args.dry_run:
            db_service = DatabaseService()

        # Create didactic snippet
        didactic_snippet = await create_didactic_snippet(topic_service=topic_service, topic_title=args.topic, core_concept=args.concept, user_level=args.level, source_material=source_material, learning_objectives=learning_objectives, verbose=args.verbose)

        # Create MCQs for each learning objective
        mcqs = await create_mcqs_for_objectives(mcq_service=mcq_service, topic_title=args.topic, core_concept=args.concept, user_level=args.level, source_material=source_material, learning_objectives=learning_objectives, verbose=args.verbose)

        if args.dry_run:
            print("🔍 DRY RUN - Generated content summary:")
            print(f"   • Didactic snippet: {len(didactic_snippet.get('content', ''))} characters")
            print(f"   • MCQs created: {len(mcqs)}")

            # Save to JSON for inspection
            output = {"topic": args.topic, "concept": args.concept, "level": args.level, "objectives": learning_objectives, "didactic_snippet": didactic_snippet, "mcqs": mcqs}

            output_file = f"topic_preview_{args.topic.replace(' ', '_').lower()}.json"
            with open(output_file, "w") as f:
                json.dump(output, f, indent=2)

            print(f"📁 Content saved to {output_file} for review")
        else:
            # Save to database
            topic_id = await save_topic_to_database(
                db_service=db_service, topic_title=args.topic, core_concept=args.concept, user_level=args.level, learning_objectives=learning_objectives, source_material=source_material, domain=args.domain, didactic_snippet=didactic_snippet, mcqs=mcqs, verbose=args.verbose
            )

            print("🎉 Topic created successfully!")
            print(f"   • Topic ID: {topic_id}")
            print(f"   • Components: 1 didactic snippet + {len(mcqs)} MCQs")
            print(f"   • Access at: http://localhost:3000/learn/{topic_id}?mode=learning")

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
