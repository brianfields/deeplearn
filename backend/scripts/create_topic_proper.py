#!/usr/bin/env python3
"""
Proper Topic Creation Script

Creates a complete learning topic using AI services to generate real content from source material:
1. Extract refined material with learning objectives
2. Create didactic snippet using AI
3. Create MCQs for each learning objective using AI
4. Save everything to database

Usage:
    python scripts/create_topic_proper.py \
        --topic "PyTorch Cross-Entropy Loss" \
        --concept "Cross-Entropy Loss Function" \
        --material scripts/examples/cross_entropy_material.txt \
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
from src.core.prompt_base import PromptContext
from src.core.service_base import ServiceConfig
from src.data_structures import BiteSizedComponent, BiteSizedTopic
from src.database_service import DatabaseService
from src.llm_interface import LLMConfig, LLMProviderType
from src.modules.lesson_planning.bite_sized_topics.mcq_service import MCQService
from src.modules.lesson_planning.bite_sized_topics.models import DidacticSnippet
from src.modules.lesson_planning.bite_sized_topics.refined_material_service import RefinedMaterialService
from src.modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService


async def extract_refined_material_and_mcqs(mcq_service: MCQService, source_material: str, topic_title: str, domain: str, user_level: str, verbose: bool = False) -> tuple[dict, list[dict]]:
    """Extract refined material and create MCQs using the two-pass approach."""
    if verbose:
        print("🔄 Extracting refined material and creating MCQs...")

    # Create context for the services
    context = PromptContext(user_level=user_level, time_constraint=15)

    # Get the llm_client from the mcq_service
    llm_client = mcq_service.llm_client

    # Step 1: Extract refined material
    refined_material_service = RefinedMaterialService(llm_client)
    refined_material = await refined_material_service.extract_refined_material(source_material=source_material, domain=domain, user_level=user_level, context=context)

    # Step 2: Create MCQs from refined material
    mcqs_with_evaluations = await mcq_service.create_mcqs_from_refined_material(refined_material=refined_material, context=context)

    if verbose:
        print(f"✅ Extracted refined material with {len(refined_material.get('topics', []))} topics")
        print(f"✅ Created {len(mcqs_with_evaluations)} MCQs")

        # Show learning objectives that were identified
        all_objectives = []
        for topic in refined_material.get("topics", []):
            objectives = topic.get("learning_objectives", [])
            all_objectives.extend(objectives)

        if all_objectives:
            print("📋 Identified learning objectives:")
            for i, obj in enumerate(all_objectives, 1):
                print(f"   {i}. {obj}")

    return refined_material, mcqs_with_evaluations


async def create_didactic_snippet_with_ai(topic_service: BiteSizedTopicService, topic_title: str, core_concept: str, user_level: str, source_material: str, learning_objectives: list[str], verbose: bool = False) -> DidacticSnippet:
    """Create a didactic snippet using the AI service."""
    if verbose:
        print("🔄 Creating didactic snippet using AI...")

    # Use the actual service to create didactic snippet
    didactic_snippet = await topic_service.create_didactic_snippet(topic_title=topic_title, key_concept=core_concept, user_level=user_level, concept_context=source_material[:500] + "..." if len(source_material) > 500 else source_material, learning_objectives=learning_objectives)

    if verbose:
        snippet_preview = didactic_snippet.snippet[:100] + "..." if len(didactic_snippet.snippet) > 100 else didactic_snippet.snippet
        print(f"✅ Created didactic snippet: {snippet_preview}")

    return didactic_snippet


async def save_complete_topic_to_database(db_service: DatabaseService, topic_title: str, core_concept: str, user_level: str, source_material: str, domain: str, refined_material: dict, didactic_snippet: DidacticSnippet, mcqs_with_evaluations: list[dict], verbose: bool = False) -> str:
    """Save the complete topic and all components to database."""
    topic_id = str(uuid.uuid4())

    if verbose:
        print(f"🔄 Saving complete topic to database with ID: {topic_id}")

    # Extract all learning objectives from refined material
    all_learning_objectives = []
    for topic in refined_material.get("topics", []):
        objectives = topic.get("learning_objectives", [])
        all_learning_objectives.extend(objectives)

    # Create topic with extracted learning objectives
    topic = BiteSizedTopic(
        id=topic_id,
        title=topic_title,
        core_concept=core_concept,
        user_level=user_level,
        learning_objectives=all_learning_objectives,
        key_concepts=[core_concept],
        source_material=source_material,
        source_domain=domain,
        source_level=user_level,
        refined_material=refined_material,  # Store the extracted refined material
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Create components
    components = []

    # Didactic snippet component - convert DidacticSnippet to dict for storage
    didactic_component = BiteSizedComponent(
        id=str(uuid.uuid4()),
        topic_id=topic_id,
        component_type="didactic_snippet",
        title=didactic_snippet.title,
        content=didactic_snippet.dict(),  # Convert Pydantic object to dict for storage
    )
    components.append(didactic_component)

    # MCQ components (one for each MCQ with evaluation)
    for i, mcq_data in enumerate(mcqs_with_evaluations, 1):
        mcq = mcq_data["mcq"]
        evaluation = mcq_data["evaluation"]
        learning_objective = mcq_data.get("learning_objective", f"Objective {i}")

        # Create the MCQ content in the format expected by the frontend
        mcq_content = {"mcq": mcq, "evaluation": evaluation, "learning_objective": learning_objective}

        mcq_title = mcq.get("stem", f"Question {i}")[:50] + "..." if len(mcq.get("stem", "")) > 50 else mcq.get("stem", f"Question {i}")

        mcq_component = BiteSizedComponent(id=str(uuid.uuid4()), topic_id=topic_id, component_type="mcq", title=f"MCQ: {mcq_title}", content=mcq_content)
        components.append(mcq_component)

    # Attach components to topic
    topic.components = components

    # Save to database
    if db_service.save_bite_sized_topic(topic):
        if verbose:
            print(f"✅ Saved topic: {topic_title}")
            print("✅ Saved didactic snippet component")
            print(f"✅ Saved {len(mcqs_with_evaluations)} MCQ components")
            print(f"🎉 Complete topic saved with {1 + len(mcqs_with_evaluations)} components!")
        return topic_id
    else:
        raise Exception("Failed to save topic to database")


async def main():
    parser = argparse.ArgumentParser(description="Create complete learning topic using AI services")
    parser.add_argument("--topic", required=True, help="Topic title")
    parser.add_argument("--concept", required=True, help="Core concept to focus on")
    parser.add_argument("--material", required=True, help="Path to source material text file")
    parser.add_argument("--level", default="intermediate", choices=["beginner", "intermediate", "advanced"], help="Target user level")
    parser.add_argument("--domain", default="Machine Learning", help="Subject domain")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")
    parser.add_argument("--output", help="Save content to JSON file for inspection")

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

    if args.verbose:
        print(f"🎯 Topic: {args.topic}")
        print(f"🎯 Core Concept: {args.concept}")
        print(f"🎯 User Level: {args.level}")
        print(f"🎯 Domain: {args.domain}")
        print()

    try:
        # Initialize services
        llm_config = LLMConfig(provider=LLMProviderType.OPENAI, model="gpt-4", temperature=0.7)
        llm_client = LLMClient(llm_config)
        config = ServiceConfig(llm_config=llm_config)

        topic_service = BiteSizedTopicService(config, llm_client)
        mcq_service = MCQService(llm_client)
        db_service = DatabaseService()

        # Step 1: Extract refined material
        refined_material_service = RefinedMaterialService(llm_client)
        refined_material = await refined_material_service.extract_refined_material(source_material=source_material, domain=args.domain, user_level=args.level, context=PromptContext(user_level=args.level, time_constraint=15))

        # Step 2: Create MCQs from refined material
        mcqs_with_evaluations = await mcq_service.create_mcqs_from_refined_material(refined_material=refined_material, context=PromptContext(user_level=args.level, time_constraint=15))

        # Extract learning objectives for didactic snippet
        all_learning_objectives = []
        for topic in refined_material.get("topics", []):
            objectives = topic.get("learning_objectives", [])
            all_learning_objectives.extend(objectives)

        # Step 2: Create didactic snippet using AI
        didactic_snippet = await create_didactic_snippet_with_ai(topic_service=topic_service, topic_title=args.topic, core_concept=args.concept, user_level=args.level, source_material=source_material, learning_objectives=all_learning_objectives, verbose=args.verbose)

        # Step 3: Save everything to database
        topic_id = await save_complete_topic_to_database(
            db_service=db_service, topic_title=args.topic, core_concept=args.concept, user_level=args.level, source_material=source_material, domain=args.domain, refined_material=refined_material, didactic_snippet=didactic_snippet, mcqs_with_evaluations=mcqs_with_evaluations, verbose=args.verbose
        )

        print("🎉 Topic created successfully with AI-generated content!")
        print(f"   • Topic ID: {topic_id}")
        print(f"   • Learning Objectives: {len(all_learning_objectives)}")
        print(f"   • Components: 1 didactic snippet + {len(mcqs_with_evaluations)} MCQs")
        print(f"   • Frontend URL: http://localhost:3000/learn/{topic_id}?mode=learning")

        # Optionally save to JSON file for inspection
        if args.output:
            output_data = {"topic_id": topic_id, "title": args.topic, "concept": args.concept, "refined_material": refined_material, "learning_objectives": all_learning_objectives, "didactic_snippet": didactic_snippet, "mcqs_count": len(mcqs_with_evaluations), "mcqs": mcqs_with_evaluations}

            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"📁 Content also saved to: {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
