#!/usr/bin/env python3
"""
Export Seed Data Script

Exports current database data to JSON files that match the database structure exactly.
Exported files can be directly re-imported without any transformation.

Canonical format:
- Each unit JSON file contains the full unit record plus all related data
- Lessons include complete 'package' field (LessonPackage with exercise_bank, quiz, quiz_metadata)
- Flow runs, step runs, and LLM requests are included alongside lessons
- Resources and conversations are included at the unit level

Usage:
    python scripts/export_seed_data.py --all-units --output-dir backend/seed_data
    python scripts/export_seed_data.py --unit-id 9435f1bf-472d-47c5-a759-99beadd98076
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any

# Add the backend directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from modules.content.models import LessonModel, UnitModel, UnitResourceModel
from modules.conversation_engine.models import ConversationMessageModel, ConversationModel
from modules.flow_engine.models import FlowRunModel, FlowStepRunModel
from modules.infrastructure.public import infrastructure_provider
from modules.llm_services.models import LLMRequestModel
from modules.object_store.models import DocumentModel, ImageModel
from modules.resource.models import ResourceModel
from modules.user.models import UserModel


def _serialize_value(obj: Any) -> Any:
    """Convert a value to JSON-serializable form."""
    if obj is None:
        return None
    if isinstance(obj, str | int | float | bool | list | dict):
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    # Convert UUID, Enum, and other types to string
    return str(obj)


def _serialize_dict(obj: Any) -> dict[str, Any]:
    """Convert a dict-like object to a JSON-serializable dict, recursively."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return {key: _serialize_value(value) for key, value in obj.items()}

    # Handle SQLAlchemy model
    result = {}
    if hasattr(obj, "__table__"):
        for column in obj.__table__.columns:
            value = getattr(obj, column.name, None)
            result[column.name] = _serialize_value(value)
    return result


async def export_users(db_session: Any, output_dir: Path) -> list[dict[str, Any]]:
    """Export users to users.json.

    Returns the list of user data for reference.
    """
    stmt = select(UserModel).order_by(UserModel.email)
    result = await db_session.execute(stmt)
    users = result.scalars().all()

    users_data: list[dict[str, Any]] = []
    for user in users:
        # Include basic user info; password hashes are not exported for security
        user_dict: dict[str, Any] = {
            "key": "user_" + str(user.id),  # Default key; can be customized
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            # Note: password must be set when importing
        }
        users_data.append(user_dict)

    users_file = output_dir / "users.json"
    with users_file.open("w") as f:
        json.dump(users_data, f, indent=2)

    print(f"✅ Exported {len(users_data)} users to {users_file}")
    return users_data


async def export_unit(db_session: Any, unit_id: str, output_dir: Path) -> None:
    """Export a single unit with all related data in canonical format."""
    unit = await db_session.get(UnitModel, unit_id)
    if not unit:
        print(f"❌ Unit {unit_id} not found")
        return

    # Get owner key for reference
    owner = await db_session.get(UserModel, unit.user_id) if unit.user_id else None
    owner_email = owner.email if owner else "unknown@example.com"

    # Map email to key for common users
    email_to_key: dict[str, str] = {
        "thecriticalpath@gmail.com": "brian",
        "eylem.ozaslan@gmail.com": "eylem",
        "epsilon.cat@example.com": "epsilon",
        "nova.cat@example.com": "nova",
    }
    owner_key = email_to_key.get(owner_email, "brian")

    # Build unit record
    unit_data: dict[str, Any] = _serialize_dict(unit)
    unit_data["owner_key"] = owner_key

    # Get lessons
    stmt = select(LessonModel).where(LessonModel.unit_id == unit_id).order_by(LessonModel.id)
    result = await db_session.execute(stmt)
    lessons = result.scalars().all()

    lessons_data: list[dict[str, Any]] = []
    for lesson in lessons:
        lesson_dict = _serialize_dict(lesson)

        # Lesson includes full package (already serialized in database as JSON)
        if lesson.package:
            lesson_dict["package"] = lesson.package

        # Check if there's a flow run for this lesson
        if lesson.flow_run_id:
            flow_run = await db_session.get(FlowRunModel, lesson.flow_run_id)
            if flow_run:
                lesson_dict["flow_run"] = _serialize_dict(flow_run)

                # Get step runs for this flow
                stmt_steps = select(FlowStepRunModel).where(FlowStepRunModel.flow_run_id == lesson.flow_run_id).order_by(FlowStepRunModel.step_order)
                result_steps = await db_session.execute(stmt_steps)
                step_runs = result_steps.scalars().all()
                if step_runs:
                    lesson_dict["step_runs"] = [_serialize_dict(sr) for sr in step_runs]

                # Get LLM requests associated with this flow
                stmt_llm = select(LLMRequestModel).where(LLMRequestModel.id.in_([sr.llm_request_id for sr in step_runs if sr.llm_request_id]))
                result_llm = await db_session.execute(stmt_llm)
                llm_requests = result_llm.scalars().all()
                if llm_requests:
                    lesson_dict["llm_requests"] = [_serialize_dict(lr) for lr in llm_requests]

        lessons_data.append(lesson_dict)

    unit_data["lessons"] = lessons_data

    # Get resources
    stmt_resources = select(ResourceModel, UnitResourceModel).join(UnitResourceModel, ResourceModel.id == UnitResourceModel.resource_id).where(UnitResourceModel.unit_id == unit_id).order_by(ResourceModel.id)
    result_resources = await db_session.execute(stmt_resources)
    resources_data: list[dict[str, Any]] = []
    for resource, _ in result_resources:
        resource_dict = _serialize_dict(resource)

        # Include related object store models if they exist
        if resource.object_store_document_id:
            document = await db_session.get(DocumentModel, resource.object_store_document_id)
            if document:
                resource_dict["document"] = _serialize_dict(document)

        if resource.object_store_image_id:
            image = await db_session.get(ImageModel, resource.object_store_image_id)
            if image:
                resource_dict["image"] = _serialize_dict(image)

        resources_data.append(resource_dict)

    if resources_data:
        unit_data["resources"] = resources_data

    # Get art image if present
    if unit.art_image_id:
        art_image = await db_session.get(ImageModel, unit.art_image_id)
        if art_image:
            unit_data["art_image"] = _serialize_dict(art_image)

    # Get conversations (both learning_coach and teaching_assistant)
    stmt_convos = select(ConversationModel).where(ConversationModel.user_id == unit.user_id).order_by(ConversationModel.created_at)
    result_convos = await db_session.execute(stmt_convos)
    conversations = result_convos.scalars().all()

    if conversations:
        learning_conversations: dict[str, list[dict[str, Any]]] = {"coach": [], "assistant": []}

        for conversation in conversations:
            conv_dict = _serialize_dict(conversation)

            # Get messages for this conversation
            stmt_msgs = select(ConversationMessageModel).where(ConversationMessageModel.conversation_id == conversation.id).order_by(ConversationMessageModel.message_order)
            result_msgs = await db_session.execute(stmt_msgs)
            messages = result_msgs.scalars().all()

            if messages:
                conv_dict["messages"] = [_serialize_dict(msg) for msg in messages]

            # Categorize by conversation type
            if conversation.conversation_type == "learning_coach":
                learning_conversations["coach"].append(conv_dict)
            elif conversation.conversation_type == "teaching_assistant":
                learning_conversations["assistant"].append(conv_dict)

        if learning_conversations["coach"] or learning_conversations["assistant"]:
            unit_data["learning_conversations"] = learning_conversations

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
    parser = argparse.ArgumentParser(description="Export database data to seed JSON files (canonical format)")
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
