#!/usr/bin/env python3
"""
Topic Creation Script - Updated for New Module Architecture

Creates a complete learning topic using the new content_creator module.
This script demonstrates the clean separation between content creation and storage.

Usage:
    python scripts/create_topic.py \
        --topic "PyTorch Cross-Entropy Loss" \
        --concept "Cross-Entropy Loss Function" \
        --material scripts/examples/cross_entropy_material.txt \
        --verbose

    python scripts/create_topic.py \
        --topic "React Native Views & Styles" \
        --concept "React Native Views & Styles" \
        --material scripts/examples/react_native_views.txt \
        --verbose
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
import sys

# Add the backend directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.content.public import content_provider
from modules.content_creator.public import content_creator_provider
from modules.content_creator.service import CreateTopicRequest
from modules.infrastructure.public import infrastructure_provider


async def main() -> None:
    """Main function to create topic using new module architecture."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Create complete learning topic using new module architecture")
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
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--output", help="Save content summary to JSON file")

    args = parser.parse_args()

    # Configure logging
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        print("🔧 Debug mode: All service logs enabled")
    elif args.verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        print("🔧 Verbose mode: Service logs enabled")
    else:
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
        # Get content creator service using new module architecture
        if args.verbose:
            print("🔄 Initializing content creator service...")

        # Initialize infrastructure and use a managed DB session so writes commit
        infra = infrastructure_provider()
        infra.initialize()
        if args.verbose:
            print(f"🗄️  Database URL: {infra.get_database_url()}")

        with infra.get_session_context() as db_session:
            content_service = content_provider(db_session)
            creator = content_creator_provider(content=content_service)

            # Create topic request
            request = CreateTopicRequest(title=args.topic, core_concept=args.concept, source_material=source_material, user_level=args.level, domain=args.domain)

            # Generate complete topic content
            if args.verbose:
                print("🔄 Generating complete topic with AI-powered content...")

            result = await creator.create_topic_from_source_material(request)
            if args.verbose:
                exists = content_service.topic_exists(result.topic_id)
                comps = content_service.get_components_by_topic(result.topic_id)
                print(f"🔎 DB verification before commit: topic_exists={exists}, components={len(comps)}")

        if args.verbose:
            print("✅ Generated complete topic content!")
            print(f"   • Topic ID: {result.topic_id}")
            print(f"   • Components created: {result.components_created}")

        print("🎉 Topic created successfully with AI-generated content!")
        print(f"   • Topic ID: {result.topic_id}")
        print(f"   • Title: {result.title}")
        print(f"   • Components: {result.components_created}")
        print(f"   • Frontend URL: http://localhost:3000/learn/{result.topic_id}?mode=learning")

        # Optionally save summary to JSON file
        if args.output:
            output_data = {"topic_id": result.topic_id, "title": result.title, "concept": args.concept, "user_level": args.level, "domain": args.domain, "components_created": result.components_created, "created_with": "new_module_architecture"}

            with Path.open(args.output, "w") as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"📁 Summary saved to: {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose or args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
