#!/usr/bin/env python3
"""
Export Seed Data Script

Exports current database data to JSON files that can be used for seeding.
This allows you to capture the current state of the database and use it as seed data.

Usage:
    python scripts/export_seed_data.py --output-dir backend/seed_data
    python scripts/export_seed_data.py --unit-id 9435f1bf-472d-47c5-a759-99beadd98076
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any

# Add the backend directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from modules.content.models import LessonModel, UnitModel, UnitResourceModel
from modules.infrastructure.public import infrastructure_provider
from modules.object_store.models import AudioModel, DocumentModel, ImageModel
from modules.resource.models import ResourceModel
from modules.user.models import UserModel


def serialize_model(obj: Any) -> dict[str, Any]:
    """Convert a SQLAlchemy model to a JSON-serializable dict."""
    if obj is None:
        return {}

    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        # Convert UUIDs and datetimes to strings
        if value is not None:
            result[column.name] = str(value) if hasattr(value, "__str__") and not isinstance(value, str | int | float | bool | list | dict) else value
    return result


async def export_users(db_session: Any, output_dir: Path) -> None:
    """Export users to users.json."""
    stmt = select(UserModel).order_by(UserModel.email)
    result = await db_session.execute(stmt)
    users = result.scalars().all()

    users_data = []
    for user in users:
        # Don't export password hashes for security
        users_data.append(
            {
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "is_active": user.is_active,
                # Note: password will need to be set when importing
            }
        )

    users_file = output_dir / "users.json"
    with users_file.open("w") as f:
        json.dump(users_data, f, indent=2)

    print(f"✅ Exported {len(users_data)} users to {users_file}")


async def export_unit(db_session: Any, unit_id: str, output_dir: Path) -> None:
    """Export a single unit with all related data."""
    unit = await db_session.get(UnitModel, unit_id)
    if not unit:
        print(f"❌ Unit {unit_id} not found")
        return

    # Get owner key for reference (match with users.json)
    owner = await db_session.get(UserModel, unit.user_id)
    owner_email = owner.email if owner else "unknown@example.com"

    # Map email to key for common users
    email_to_key = {
        "thecriticalpath@gmail.com": "brian",
        "eylem.ozaslan@gmail.com": "eylem",
        "epsilon.cat@example.com": "epsilon",
        "nova.cat@example.com": "nova",
    }
    owner_key = email_to_key.get(owner_email, "brian")

    # Get lessons
    stmt = select(LessonModel).where(LessonModel.unit_id == unit_id).order_by(LessonModel.id)
    result = await db_session.execute(stmt)
    lessons = result.scalars().all()

    lessons_data = []
    for lesson in lessons:
        # Create lesson structure matching import expectations
        lesson_dict = {
            "id": str(lesson.id),
            "title": lesson.title,
            "learner_level": lesson.learner_level,
            "source_material": lesson.source_material,
            "podcast_transcript": lesson.podcast_transcript or "",
            "objectives": [],
            "mcqs": [],
            "misconceptions": [],
            "confusables": [],
        }

        # Extract structured data from package
        if lesson.package:
            package = lesson.package

            # Get objective IDs and match them with unit learning objectives
            objective_ids = package.get("unit_learning_objective_ids", [])
            for obj_id in objective_ids:
                # Find the matching objective from unit learning objectives
                matching_obj = next((obj for obj in unit.learning_objectives if obj.get("id") == obj_id), None)
                if matching_obj:
                    lesson_dict["objectives"].append(matching_obj)

            for exercise in package.get("exercises", []):
                mcq = {
                    "stem": exercise.get("stem"),
                    "options": [{"text": opt.get("text"), "rationale_wrong": opt.get("rationale_wrong")} for opt in exercise.get("options", [])],
                    "correct_index": 0,  # Default, should be calculated
                    "cognitive_level": exercise.get("cognitive_level"),
                    "difficulty": exercise.get("estimated_difficulty"),
                    "misconceptions": exercise.get("misconceptions_used", []),
                }
                # Find correct index
                answer_key = exercise.get("answer_key", {})
                if answer_key:
                    correct_label = answer_key.get("label", "A")
                    mcq["correct_index"] = ord(correct_label) - ord("A")
                    mcq["correct_rationale"] = answer_key.get("rationale_right")

                lesson_dict["mcqs"].append(mcq)

            lesson_dict["misconceptions"] = package.get("misconceptions", [])
            lesson_dict["confusables"] = package.get("confusables", [])

        lessons_data.append(lesson_dict)

    # Get resources
    stmt = select(ResourceModel, UnitResourceModel).join(UnitResourceModel, ResourceModel.id == UnitResourceModel.resource_id).where(UnitResourceModel.unit_id == unit_id)
    result = await db_session.execute(stmt)
    resources_data = []
    for resource, _ in result:
        resource_dict = serialize_model(resource)
        # Get document if exists
        if resource.object_store_document_id:
            document = await db_session.get(DocumentModel, resource.object_store_document_id)
            if document:
                resource_dict["document"] = serialize_model(document)
        resources_data.append(resource_dict)

    # Get images
    image_data = None
    if unit.art_image_id:
        image = await db_session.get(ImageModel, unit.art_image_id)
        if image:
            image_data = serialize_model(image)

    # Get audio
    audio_data = None
    if unit.podcast_audio_object_id:
        audio = await db_session.get(AudioModel, unit.podcast_audio_object_id)
        if audio:
            audio_data = serialize_model(audio)

    # Build complete unit data
    unit_data = {
        "id": str(unit.id),
        "title": unit.title,
        "description": unit.description,
        "learner_level": unit.learner_level,
        "learning_objectives": unit.learning_objectives,
        "target_lesson_count": unit.target_lesson_count,
        "source_material": unit.source_material,
        "generated_from_topic": unit.generated_from_topic,
        "is_global": unit.is_global,
        "owner_key": owner_key,
        "art_image_description": unit.art_image_description,
        "podcast_transcript": unit.podcast_transcript,
        "podcast_voice": unit.podcast_voice,
        "lessons": lessons_data,
        "resources": resources_data,
        "art_image": image_data,
        "podcast_audio": audio_data,
    }

    # Save to file
    safe_title = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in unit.title)
    safe_title = safe_title.replace(" ", "-").lower()[:50]
    unit_file = output_dir / "units" / f"{safe_title}.json"

    with unit_file.open("w") as f:
        json.dump(unit_data, f, indent=2)

    print(f"✅ Exported unit '{unit.title}' to {unit_file}")
    print(f"   • {len(lessons_data)} lessons")
    print(f"   • {len(resources_data)} resources")


async def export_all_units(db_session: Any, output_dir: Path) -> None:
    """Export all units."""
    stmt = select(UnitModel).order_by(UnitModel.title)
    result = await db_session.execute(stmt)
    units = result.scalars().all()

    for unit in units:
        await export_unit(db_session, str(unit.id), output_dir)


async def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Export database data to seed JSON files")
    parser.add_argument("--output-dir", default="backend/seed_data", help="Output directory for JSON files")
    parser.add_argument("--unit-id", help="Export a specific unit by ID")
    parser.add_argument("--all-units", action="store_true", help="Export all units")
    parser.add_argument("--users", action="store_true", help="Export users")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "units").mkdir(exist_ok=True)

    print(f"📦 Exporting seed data to {output_dir}")

    infra = infrastructure_provider()
    infra.initialize()

    async with infra.get_async_session_context() as db_session:
        if args.users:
            await export_users(db_session, output_dir)

        if args.unit_id:
            await export_unit(db_session, args.unit_id, output_dir)
        elif args.all_units:
            await export_all_units(db_session, output_dir)
        elif not args.users:
            print("⚠️  Please specify --users, --unit-id, or --all-units")
            print("   Example: python scripts/export_seed_data.py --all-units")

    print("\n✅ Export complete!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
