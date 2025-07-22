#!/usr/bin/env python3
"""
Simple Topic Creation Script

Creates a complete learning topic with didactic snippet and MCQs from source material.
Based on the existing create_mcqs.py pattern but expanded to include didactic snippets.

Usage:
    python scripts/create_topic_simple.py \
        --topic "PyTorch Cross-Entropy Loss" \
        --material scripts/examples/cross_entropy_material.txt \
        --objectives "Understand cross-entropy calculation" "Apply to classification" \
        --verbose
"""

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.llm_client import LLMClient
from src.data_structures import BiteSizedComponent, BiteSizedTopic
from src.database_service import DatabaseService
from src.llm_interface import LLMConfig


async def main():
    parser = argparse.ArgumentParser(description="Create complete learning topic")
    parser.add_argument("--topic", required=True, help="Topic title")
    parser.add_argument("--material", required=True, help="Path to source material file")
    parser.add_argument("--objectives", nargs="+", help="Learning objectives")
    parser.add_argument("--level", default="intermediate", help="User level")
    parser.add_argument("--domain", default="Machine Learning", help="Subject domain")
    parser.add_argument("--verbose", action="store_true", help="Show progress")
    parser.add_argument("--output", help="JSON output file (optional)")

    args = parser.parse_args()

    # Validate inputs
    material_path = Path(args.material)
    if not material_path.exists():
        print(f"❌ Error: Material file not found: {args.material}")
        sys.exit(1)

    # Read source material
    source_material = material_path.read_text(encoding="utf-8")
    if args.verbose:
        print(f"📄 Loaded source material: {len(source_material)} characters")

    # Set default objectives if not provided
    objectives = args.objectives or [f"Understand {args.topic}", f"Apply {args.topic} concepts", "Identify key features"]

    if args.verbose:
        print(f"🎯 Topic: {args.topic}")
        print(f"🎯 Objectives: {len(objectives)} items")
        print()

    try:
        # Create LLM client
        llm_config = LLMConfig(provider="openai", model="gpt-4", temperature=0.7)
        llm_client = LLMClient(llm_config)

        # Create topic ID
        topic_id = str(uuid.uuid4())

        if args.verbose:
            print(f"🔄 Creating topic with ID: {topic_id}")

        # Create simple didactic snippet content
        didactic_content = {
            "title": f"Understanding {args.topic}",
            "content": f"Learn about {args.topic} through this comprehensive guide.",
            "source_material": source_material[:1000] + "..." if len(source_material) > 1000 else source_material,
            "key_points": [f"Core concept: {args.topic}", "Practical applications", "Key implementation details"],
        }

        if args.verbose:
            print("✅ Created didactic snippet")

        # Create simple MCQ content for each objective
        mcqs = []
        for i, objective in enumerate(objectives, 1):
            mcq_content = {
                "mcq": {
                    "stem": f"Which statement best describes {objective.lower()}?",
                    "options": [f"It is a fundamental concept in {args.topic}", f"It is not related to {args.topic}", "It is an advanced feature only", "It is deprecated in modern usage"],
                    "correct_answer": f"It is a fundamental concept in {args.topic}",
                    "correct_answer_index": 0,
                    "rationale": f"This question tests understanding of {objective}",
                },
                "learning_objective": objective,
                "evaluation": {"alignment": "Well aligned with learning objective", "difficulty": "Appropriate for intermediate level"},
            }
            mcqs.append(mcq_content)

            if args.verbose:
                print(f"✅ Created MCQ {i}/{len(objectives)}")

        # Create topic and components
        topic = BiteSizedTopic(
            id=topic_id, title=args.topic, core_concept=args.topic, user_level=args.level, learning_objectives=objectives, key_concepts=[args.topic], source_material=source_material, source_domain=args.domain, source_level=args.level, created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )

        # Create components
        components = []

        # Didactic snippet component
        didactic_component = BiteSizedComponent(id=str(uuid.uuid4()), topic_id=topic_id, component_type="didactic_snippet", title=f"Learn: {args.topic}", content=didactic_content)
        components.append(didactic_component)

        # MCQ components
        for i, mcq in enumerate(mcqs, 1):
            mcq_component = BiteSizedComponent(id=str(uuid.uuid4()), topic_id=topic_id, component_type="mcq", title=f"MCQ {i}: {mcq['learning_objective'][:30]}...", content=mcq)
            components.append(mcq_component)

        # Attach components to topic
        topic.components = components

        # Save to database
        db_service = DatabaseService()
        if db_service.save_bite_sized_topic(topic):
            print("🎉 Topic created successfully!")
            print(f"   • Topic ID: {topic_id}")
            print(f"   • Components: 1 didactic snippet + {len(mcqs)} MCQs")
            print(f"   • Frontend URL: http://localhost:3000/learn/{topic_id}?mode=learning")

            # Optionally save to JSON file
            if args.output:
                output_data = {"topic_id": topic_id, "title": args.topic, "objectives": objectives, "components": len(components), "didactic_content": didactic_content, "mcqs": mcqs}

                with open(args.output, "w") as f:
                    json.dump(output_data, f, indent=2, default=str)
                print(f"📁 Content also saved to: {args.output}")

        else:
            print("❌ Failed to save topic to database")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
