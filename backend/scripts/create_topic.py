#!/usr/bin/env python3
"""
Proper Topic Creation Script

Creates a complete learning topic using the BiteSizedTopicService to generate real content from source material:
1. Generate complete topic content from source material (didactic snippet, glossary, MCQs)
2. Save everything to database

Usage:
    python scripts/create_topic.py \
        --topic "PyTorch Cross-Entropy Loss" \
        --concept "Cross-Entropy Loss Function" \
        --material scripts/examples/cross_entropy_material.txt \
        --verbose
"""

import argparse
import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
import uuid

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.llm_client import LLMClient
from src.core.service_base import ServiceConfig
from src.data_structures import BiteSizedComponent, BiteSizedTopic
from src.database_service import DatabaseService
from src.llm_interface import LLMConfig, LLMProviderType
from src.modules.content_creation.service import BiteSizedTopicContent, BiteSizedTopicService


async def save_complete_topic_to_database(
    db_service: DatabaseService,
    topic_content: BiteSizedTopicContent,
    topic_title: str,
    core_concept: str,
    user_level: str,
    source_material: str,
    domain: str,
    verbose: bool = False,
) -> str:
    """Save the complete topic and all components to database."""
    topic_id = str(uuid.uuid4())

    if verbose:
        print(f"🔄 Saving complete topic to database with ID: {topic_id}")

    # Extract learning objectives from didactic snippet or use defaults
    learning_objectives = getattr(topic_content.didactic_snippet, "learning_objectives", [core_concept])
    if not learning_objectives:
        learning_objectives = [core_concept]

    # Create topic
    topic = BiteSizedTopic(
        id=topic_id,
        title=topic_title,
        core_concept=core_concept,
        user_level=user_level,
        learning_objectives=learning_objectives,
        key_concepts=[core_concept],
        source_material=source_material,
        source_domain=domain,
        source_level=user_level,
        refined_material={},  # Not directly accessible from the service result
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Create components
    components = []

    # Didactic snippet component
    didactic_component = BiteSizedComponent(
        id=str(uuid.uuid4()),
        topic_id=topic_id,
        component_type="didactic_snippet",
        title=topic_content.didactic_snippet.title,
        content=topic_content.didactic_snippet.model_dump(),  # Convert Pydantic object to dict for storage
    )
    components.append(didactic_component)

    # Glossary component
    glossary_component = BiteSizedComponent(
        id=str(uuid.uuid4()),
        topic_id=topic_id,
        component_type="glossary",
        title=f"Glossary for {topic_title}",
        content=topic_content.glossary.model_dump(),  # Convert Pydantic object to dict for storage
    )
    components.append(glossary_component)

    # MCQ components (one for each MCQ)
    for mcq_question in topic_content.multiple_choice_questions:
        mcq_component = BiteSizedComponent(
            id=str(uuid.uuid4()),
            topic_id=topic_id,
            component_type="mcq",
            title=f"MCQ: {mcq_question.title}",
            content=mcq_question.model_dump(),  # Convert Pydantic object to dict for storage
        )
        components.append(mcq_component)

    # Attach components to topic
    topic.components = components

    # Save to database
    if db_service.save_bite_sized_topic(topic):
        if verbose:
            print(f"✅ Saved topic: {topic_title}")
            print("✅ Saved didactic snippet component")
            print(f"✅ Saved glossary component with {len(topic_content.glossary.glossary_entries)} entries")
            print(f"✅ Saved {len(topic_content.multiple_choice_questions)} MCQ components")
            print(f"🎉 Complete topic saved with {len(components)} components!")
        return topic_id
    else:
        raise Exception("Failed to save topic to database")


async def main() -> None:  # noqa: PLR0915
    # Parse arguments first to check verbose setting
    parser = argparse.ArgumentParser(description="Create complete learning topic using AI services")
    parser.add_argument("--topic", required=True, help="Topic title")
    parser.add_argument("--concept", required=True, help="Core concept to focus on")
    parser.add_argument("--material", required=True, help="Path to source material text file")
    parser.add_argument(
        "--level",
        default="intermediate",
        choices=["beginner", "intermediate", "advanced"],
        help="Target user level",
    )
    parser.add_argument("--domain", default="Machine Learning", help="Subject domain")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress and service logs")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging (includes OpenAI API calls)")
    parser.add_argument("--output", help="Save content to JSON file for inspection")

    args = parser.parse_args()

    # Configure logging based on verbose/debug settings
    if args.debug:
        log_level = logging.DEBUG
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        print("🔧 Debug mode: All service logs including OpenAI API calls enabled")
    elif args.verbose:
        log_level = logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        print("🔧 Verbose mode: Detailed service logs enabled")
    else:
        # Only show warnings and errors from services
        logging.basicConfig(level=logging.WARNING)

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
        llm_config = LLMConfig(provider=LLMProviderType.OPENAI, model="gpt-4o", temperature=0.7)
        llm_client = LLMClient(llm_config)
        config = ServiceConfig(llm_config=llm_config)

        topic_service = BiteSizedTopicService(config, llm_client)
        db_service = DatabaseService()

        # Generate complete topic content using the new service method
        if args.verbose:
            print("🔄 Generating complete topic content...")

        topic_content = await topic_service.create_complete_bite_sized_topic(
            topic_title=args.topic,
            core_concept=args.concept,
            source_material=source_material,
            user_level=args.level,
            domain=args.domain,
        )

        if args.verbose:
            print("✅ Generated complete topic content!")
            print(f"   • Didactic snippet: {topic_content.didactic_snippet.title}")
            print(f"   • Glossary entries: {len(topic_content.glossary.glossary_entries)}")
            print(f"   • Multiple choice questions: {len(topic_content.multiple_choice_questions)}")

        # Save everything to database
        topic_id = await save_complete_topic_to_database(
            db_service=db_service,
            topic_content=topic_content,
            topic_title=args.topic,
            core_concept=args.concept,
            user_level=args.level,
            source_material=source_material,
            domain=args.domain,
            verbose=args.verbose,
        )

        print("🎉 Topic created successfully with AI-generated content!")
        print(f"   • Topic ID: {topic_id}")
        print(f"   • Components: didactic snippet + glossary + {len(topic_content.multiple_choice_questions)} MCQs")
        print(f"   • Frontend URL: http://localhost:3000/learn/{topic_id}?mode=learning")

        # Optionally save to JSON file for inspection
        if args.output:
            output_data = {
                "topic_id": topic_id,
                "title": args.topic,
                "concept": args.concept,
                "didactic_snippet": topic_content.didactic_snippet.dict(),
                "glossary": topic_content.glossary.dict(),
                "mcqs": [mcq.dict() for mcq in topic_content.multiple_choice_questions],
            }

            with Path.open(args.output, "w") as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"📁 Content also saved to: {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback  # noqa: PLC0415

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
