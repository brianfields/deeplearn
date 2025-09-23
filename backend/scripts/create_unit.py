#!/usr/bin/env python3
"""
Create Unit Script (UnitCreationFlow)

End-to-end unit generation from either a topic or provided source material,
using the UnitCreationFlow via the content_creator service. By default, creates
a complete unit with all lessons generated and persisted in the database.

Examples:
  # From a topic (creates unit + lessons)
  python scripts/create_unit.py --topic "Cross-Entropy Loss" --target-lessons 5 --user-level beginner

  # From a source file (creates unit + lessons)
  python scripts/create_unit.py --source-file docs/samples/cross_entropy.md --target-lessons 10 --user-level intermediate

  # Enable verbose logging to see detailed progress
  python scripts/create_unit.py --topic "Python Basics" --target-lessons 5 --verbose

  # Use slow mode for higher quality (but slower generation)
  python scripts/create_unit.py --topic "Math Basics" --target-lessons 3 --slow --verbose

Notes:
  - Creates complete units with all lessons generated and persisted.
  - Use --verbose (-v) to see detailed progress information during long-running operations.
  - Uses fast flow by default for efficient generation with parallel lesson creation.
  - Use --slow to use standard flow for potentially higher quality (but slower generation).
  - Requires environment configuration for infrastructure and LLM provider.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from modules.content.public import content_provider
from modules.content_creator.public import content_creator_provider
from modules.content_creator.service import ContentCreatorService
from modules.infrastructure.public import infrastructure_provider


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a learning unit using UnitCreationFlow")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--topic", help="Topic to generate the unit from")
    src.add_argument("--source-file", help="Path to text/markdown file to use as source material")

    p.add_argument("--target-lessons", type=int, default=None, help="Target number of lessons for the unit (e.g., 5, 10, 20)")
    p.add_argument("--user-level", default="beginner", choices=["beginner", "intermediate", "advanced"], help="Target learner level")
    p.add_argument("--domain", default=None, help="Optional domain context (e.g., 'Machine Learning')")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging to see detailed progress")
    p.add_argument("--slow", action="store_true", help="Use standard flow for potentially higher quality (but slower generation)")
    return p.parse_args()


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    if verbose:
        # Set up detailed logging for verbose mode
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
        # Enable debug logging for our modules
        logging.getLogger("modules.content_creator").setLevel(logging.DEBUG)
        logging.getLogger("modules.flow_engine").setLevel(logging.DEBUG)
        logging.getLogger("modules.llm_services").setLevel(logging.DEBUG)
        logging.getLogger("modules.content").setLevel(logging.DEBUG)
        print("🔍 Verbose logging enabled - you'll see detailed progress information")
    else:
        # Quiet mode - only show warnings and errors
        logging.basicConfig(level=logging.WARNING)


async def _run_async() -> int:
    args = parse_args()

    # Setup logging based on verbosity
    setup_logging(args.verbose)

    # Use fast flow by default, unless --slow is specified
    use_fast_flow = not args.slow
    if args.verbose:
        flow_type = "standard (slow)" if args.slow else "fast (default)"
        print(f"⚡ Using {flow_type} flow for content generation")

    if args.verbose:
        print("🚀 Starting unit creation process...")

    infra = infrastructure_provider()
    infra.initialize()

    # Read source material if provided via file
    source_material: str | None = None
    if args.source_file:
        if args.verbose:
            print(f"📖 Reading source material from: {args.source_file}")
        path = Path(args.source_file)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")
        source_material = path.read_text(encoding="utf-8")
        if args.verbose:
            print(f"✅ Loaded {len(source_material)} characters from source file")

    with infra.get_session_context() as s:
        content = content_provider(s)
        creator = content_creator_provider(content)

        if args.verbose:
            flow_type = "standard (slow)" if args.slow else "fast (default)"
            print("🏗️ Creating complete unit with lessons...")
            print(f"🤖 Using flow: {flow_type}")
            if args.topic:
                print(f"📚 Topic: {args.topic}")
            if args.target_lessons:
                print(f"🎯 Target lessons: {args.target_lessons}")
            print(f"👤 User level: {args.user_level}")
            if args.domain:
                print(f"🔬 Domain: {args.domain}")

        req: ContentCreatorService.CreateUnitFromTopicRequest | ContentCreatorService.CreateUnitFromSourceRequest
        if args.topic:
            req = ContentCreatorService.CreateUnitFromTopicRequest(
                topic=args.topic,
                target_lesson_count=args.target_lessons,
                user_level=args.user_level,
                domain=args.domain,
                use_fast_flow=use_fast_flow,
            )
            if args.verbose:
                print("⚡ Running complete unit creation flow (this may take several minutes)...")
            result = await creator.create_unit_from_topic(req)
        else:
            assert source_material is not None
            req = ContentCreatorService.CreateUnitFromSourceRequest(
                source_material=source_material,
                target_lesson_count=args.target_lessons,
                user_level=args.user_level,
                domain=args.domain,
                use_fast_flow=use_fast_flow,
            )
            if args.verbose:
                print("⚡ Running complete unit creation flow from source material (this may take several minutes)...")
            result = await creator.create_unit_from_source_material(req)

        lesson_ids = getattr(result, "lesson_ids", None)
        if args.verbose:
            print("\n🎉 Unit creation completed successfully!")

        print("✅ Created complete unit with lessons via UnitCreationFlow:")

        print(f"   • id: {result.unit_id}")
        print(f"   • title: {result.title}")
        print(f"   • lesson_count: {result.lesson_count}")
        if result.target_lesson_count is not None:
            print(f"   • target_lesson_count: {result.target_lesson_count}")
        print(f"   • generated_from_topic: {result.generated_from_topic}")

        if result.lesson_titles:
            print("   • lesson_titles:")
            for i, t in enumerate(result.lesson_titles, start=1):
                print(f"     {i:02d}. {t}")

        if lesson_ids:
            print("   • lesson_ids:")
            for i, lid in enumerate(lesson_ids, start=1):
                print(f"     {i:02d}. {lid}")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(_run_async())
    except KeyboardInterrupt:
        exit_code = 130
    raise SystemExit(exit_code)
