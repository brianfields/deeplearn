#!/usr/bin/env python3
"""
Create Unit Script

Simple script to create a learning unit and optionally attach existing lessons by ID.

Usage:
  python scripts/create_unit.py --title "Algebra I" --difficulty beginner --description "Linear equations" \
      --lessons l1 l2 l3

Note: This script does not generate lessons; it groups existing lessons into a unit.
"""

from __future__ import annotations

import argparse
import uuid

from modules.content.public import content_provider
from modules.content.service import ContentService
from modules.infrastructure.public import infrastructure_provider


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create a learning unit")
    p.add_argument("--title", required=True, help="Unit title")
    p.add_argument("--description", default=None, help="Unit description")
    p.add_argument("--difficulty", default="beginner", choices=["beginner", "intermediate", "advanced"], help="Unit difficulty")
    p.add_argument("--lessons", nargs="*", default=[], help="Lesson IDs to include (ordered)")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    infra = infrastructure_provider()
    infra.initialize()

    with infra.get_session_context() as s:
        content = content_provider(s)
        data = ContentService.UnitCreate(id=str(uuid.uuid4()), title=args.title, description=args.description, difficulty=args.difficulty, lesson_order=list(args.lessons))
        created = content.create_unit(data)
        print(f"✅ Created unit: {created.id} — {created.title} ({created.difficulty})")
        if created.lesson_order:
            print(f"   • Lessons: {', '.join(created.lesson_order)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
