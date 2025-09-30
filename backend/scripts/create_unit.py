#!/usr/bin/env python3
"""
Create Unit Script (UnitCreationFlow)

End-to-end unit generation from either a topic or provided source material,
using the unified content_creator service create_unit API.

Examples:
  # From a topic (creates unit + lessons)
  python scripts/create_unit.py --topic "Cross-Entropy Loss" --target-lessons 5 --learner-level beginner

  # From a source file (creates unit + lessons)
  python scripts/create_unit.py --source-file docs/samples/cross_entropy.md --target-lessons 10 --learner-level intermediate

  # Enable verbose logging to see detailed progress
  python scripts/create_unit.py --topic "Python Basics" --target-lessons 5 --verbose

Notes:
  - Creates complete units with all lessons generated and persisted.
  - Use --verbose (-v) to see detailed progress information during long-running operations.
  - Requires environment configuration for infrastructure and LLM provider.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from modules.content_creator.public import content_creator_provider
from modules.infrastructure.public import infrastructure_provider


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a learning unit using the new content creator API")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--topic", help="Topic to generate the unit from")
    src.add_argument("--source-file", help="Path to text/markdown file to use as source material")

    p.add_argument("--target-lessons", type=int, default=None, help="Target number of lessons for the unit (e.g., 5, 10, 20)")
    p.add_argument("--learner-level", default="beginner", choices=["beginner", "intermediate", "advanced"], help="Target learner level")
    p.add_argument("--background", action="store_true", help="Run creation in the background (ARQ)")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging to see detailed progress")
    return p.parse_args()


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
        logging.getLogger("modules.content_creator").setLevel(logging.DEBUG)
        logging.getLogger("modules.flow_engine").setLevel(logging.DEBUG)
        logging.getLogger("modules.llm_services").setLevel(logging.DEBUG)
        logging.getLogger("modules.content").setLevel(logging.DEBUG)
        print("🔍 Verbose logging enabled - you'll see detailed progress information")
    else:
        logging.basicConfig(level=logging.WARNING)


async def main() -> int:
    args = parse_args()

    setup_logging(args.verbose)

    if args.verbose:
        if args.background:
            print("⚙️  Using background mode (ARQ)")
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

    async with infra.get_async_session_context() as session:
        creator = content_creator_provider(session)

        if args.verbose:
            print("🏗️ Creating complete unit with lessons...")
            if args.topic:
                print(f"📚 Topic: {args.topic}")
            if args.target_lessons:
                print(f"🎯 Target lessons: {args.target_lessons}")
            print(f"👤 Learner level: {args.learner_level}")

        if args.verbose:
            print("⚡ Running unit creation (this may take several minutes)...")

        # Unified API
        result = await creator.create_unit(
            topic=args.topic or "",
            source_material=source_material,
            background=bool(args.background),
            target_lesson_count=args.target_lessons,
            learner_level=args.learner_level,
        )

        if args.background:
            # Background path returns MobileUnitCreationResult
            print("✅ Submitted unit creation to background queue:")
            print(f"   • id: {result.unit_id}")  # type: ignore[attr-defined]
            print(f"   • title: {result.title}")  # type: ignore[attr-defined]
            print(f"   • status: {result.status}")  # type: ignore[attr-defined]
            return 0

        # Foreground path returns UnitCreationResult
        if args.verbose:
            print("\n🎉 Unit creation completed successfully!")

        print("✅ Created complete unit with lessons:")
        print(f"   • id: {result.unit_id}")  # type: ignore[attr-defined]
        print(f"   • title: {result.title}")  # type: ignore[attr-defined]
        print(f"   • lesson_count: {result.lesson_count}")  # type: ignore[attr-defined]
        if getattr(result, "target_lesson_count", None) is not None:
            print(f"   • target_lesson_count: {result.target_lesson_count}")  # type: ignore[attr-defined]
        print(f"   • generated_from_topic: {getattr(result, 'generated_from_topic', source_material is None)}")

        lesson_titles = getattr(result, "lesson_titles", None)
        lesson_ids = getattr(result, "lesson_ids", None)
        if lesson_titles:
            print("   • lesson_titles:")
            for i, t in enumerate(lesson_titles, start=1):
                print(f"     {i:02d}. {t}")
        if lesson_ids:
            print("   • lesson_ids:")
            for i, lid in enumerate(lesson_ids, start=1):
                print(f"     {i:02d}. {lid}")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
    except KeyboardInterrupt:
        exit_code = 130
    raise SystemExit(exit_code)
