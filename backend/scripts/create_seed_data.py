#!/usr/bin/env python3
"""
Seed Data Creation Script (JSON-based)

Loads seed data from JSON files in the seed_data directory and creates database records.
The JSON format matches the database structure exactly: exported seed data can be directly imported.

Canonical format:
- units.json: List of complete unit specs with lessons, resources, conversations
- Each lesson includes a full 'package' field (LessonPackage with exercise_bank, quiz, quiz_metadata)
- Flow runs, step runs, and LLM requests are stored alongside lessons if present

Usage:
    python scripts/create_seed_data.py --verbose
    python scripts/create_seed_data.py --unit-file seed_data/units/my-unit.json
"""

import argparse
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import sys
import traceback
from typing import Any, cast
import uuid

# Add the backend directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete

from modules.content.models import (
    LessonModel,
    LessonType,
    UnitModel,
    UnitResourceModel,
)
from modules.content.package_models import LessonPackage
from modules.conversation_engine.models import ConversationMessageModel, ConversationModel
from modules.flow_engine.models import FlowRunModel, FlowStepRunModel
from modules.infrastructure.public import infrastructure_provider
from modules.llm_services.models import LLMRequestModel
from modules.object_store.models import AudioModel, DocumentModel, ImageModel
from modules.resource.models import ResourceModel
from modules.user.repo import UserRepo
from modules.user.service import UserService


def load_json_file(file_path: Path) -> Any:
    """Load and parse a JSON file."""
    with file_path.open("r") as f:
        return json.load(f)


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime string to datetime object."""
    if not value:
        return None
    try:
        # Handle ISO format with timezone
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value
    except (ValueError, AttributeError):
        return None


def _serialize_value(value: Any) -> Any:
    """Convert non-JSON-serializable values to strings."""
    if value is None:
        return None
    if isinstance(value, str | int | float | bool | list | dict):
        return value
    # Convert UUID and datetime to string
    return str(value)


async def load_and_create_users(db_session: Any, users_file: Path, args: Any) -> tuple[dict[str, int], dict[str, dict[str, Any]]]:
    """Load users from JSON and create them in the database."""
    users_data = load_json_file(users_file)

    sample_user_ids: dict[str, int] = {}
    user_snapshots: dict[str, dict[str, Any]] = {}

    user_repo = UserRepo(db_session)
    user_service = UserService(user_repo)

    if args.verbose:
        print(f"👥 Creating {len(users_data)} users...")

    for user_spec in users_data:
        key = user_spec["key"]
        email = user_spec["email"]

        # Check if user already exists
        existing_user = user_repo.by_email(email)
        if existing_user:
            if args.verbose:
                print(f"   • User {email} already exists, reusing...")
            user = existing_user
        else:
            password_hash = user_service._hash_password(user_spec["password"])
            user = user_repo.create(
                email=email,
                password_hash=password_hash,
                name=user_spec["name"],
                role=user_spec.get("role", "learner"),
                is_active=user_spec.get("is_active", True),
            )
            if args.verbose:
                print(f"   • Created user {email}")

        user_id = cast(int, user.id)
        sample_user_ids[key] = user_id
        user_snapshots[key] = {
            "id": user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }

    return sample_user_ids, user_snapshots


async def process_unit_from_json(
    db_session: Any,
    unit_spec: dict[str, Any],
    user_ids: dict[str, int],
    args: Any,
) -> dict[str, Any]:
    """Process a single unit from JSON spec and create all related records.

    The JSON format matches the database structure exactly:
    - unit: Complete unit record with all metadata
    - lessons: Array of lesson records, each with full 'package' field
    - flow_runs: Optional flow run records (indexed by lesson id)
    - step_runs: Optional step run records
    - llm_requests: Optional LLM request records
    - resources: Optional resource records
    - learning_conversations: Optional conversations (both 'coach' and 'assistant')
    """

    if args.verbose:
        print(f"\n📦 Processing unit: {unit_spec['title']}")

    # Resolve owner
    owner_key = unit_spec.get("owner_key", "brian")
    owner_id = user_ids.get(owner_key)
    if not owner_id:
        raise ValueError(f"Unknown owner_key: {owner_key}")

    seed_timestamp = datetime.utcnow()
    bucket_name = os.getenv("OBJECT_STORE_BUCKET", "lantern-room")

    # Generate IDs if not provided
    unit_id = unit_spec.get("id") or str(uuid.uuid4())

    # Clean up existing unit if it exists
    existing_unit = await db_session.get(UnitModel, unit_id)
    if existing_unit:
        if args.verbose:
            print(f"   • Deleting existing unit: {existing_unit.title}")
        # Delete in correct order to avoid FK violations
        from modules.content.models import UserMyUnitModel
        from modules.learning_session.models import LearningSessionModel, UnitSessionModel

        await db_session.execute(delete(UserMyUnitModel).where(UserMyUnitModel.unit_id == unit_id))
        await db_session.execute(delete(LearningSessionModel).where(LearningSessionModel.unit_id == unit_id))
        await db_session.execute(delete(UnitSessionModel).where(UnitSessionModel.unit_id == unit_id))
        await db_session.execute(delete(LessonModel).where(LessonModel.unit_id == unit_id))
        await db_session.execute(delete(UnitResourceModel).where(UnitResourceModel.unit_id == unit_id))
        await db_session.delete(existing_unit)
        await db_session.flush()

    # Process art image if provided
    art_image_id = None
    if unit_spec.get("art_image"):
        img_spec = unit_spec["art_image"]
        art_image_id = uuid.UUID(img_spec["id"]) if "id" in img_spec else uuid.uuid4()

        # Delete existing image if it exists
        existing_image = await db_session.get(ImageModel, art_image_id)
        if existing_image:
            await db_session.delete(existing_image)
            await db_session.flush()

        image_model = ImageModel(
            id=art_image_id,
            user_id=owner_id,
            s3_key=img_spec["s3_key"],
            s3_bucket=img_spec.get("s3_bucket", bucket_name),
            filename=img_spec["filename"],
            content_type=img_spec["content_type"],
            file_size=img_spec["file_size"],
            width=img_spec.get("width"),
            height=img_spec.get("height"),
            alt_text=img_spec.get("alt_text"),
            description=img_spec.get("description"),
            created_at=seed_timestamp,
            updated_at=seed_timestamp,
        )
        db_session.add(image_model)
        await db_session.flush()

    # Process podcast audio if provided
    podcast_audio_id = None
    if unit_spec.get("podcast_audio"):
        audio_spec = unit_spec["podcast_audio"]
        podcast_audio_id = uuid.UUID(audio_spec["id"]) if "id" in audio_spec else uuid.uuid4()

        # Delete existing audio if it exists
        existing_audio = await db_session.get(AudioModel, podcast_audio_id)
        if existing_audio:
            await db_session.delete(existing_audio)
            await db_session.flush()

        audio_model = AudioModel(
            id=podcast_audio_id,
            user_id=owner_id,
            s3_key=audio_spec["s3_key"],
            s3_bucket=audio_spec.get("s3_bucket", bucket_name),
            filename=audio_spec["filename"],
            content_type=audio_spec["content_type"],
            file_size=audio_spec["file_size"],
            duration_seconds=audio_spec.get("duration_seconds"),
            bitrate_kbps=audio_spec.get("bitrate_kbps"),
            sample_rate_hz=audio_spec.get("sample_rate_hz"),
            transcript=unit_spec.get("podcast_transcript"),
            created_at=seed_timestamp,
            updated_at=seed_timestamp,
        )
        db_session.add(audio_model)
        await db_session.flush()

    # Create unit model
    lesson_ids = []
    for lesson_spec in unit_spec.get("lessons", []):
        lesson_id = lesson_spec.get("id") or str(uuid.uuid4())
        lesson_ids.append(lesson_id)

    unit_model = UnitModel(
        id=unit_id,
        title=unit_spec["title"],
        description=unit_spec["description"],
        learner_level=unit_spec["learner_level"],
        lesson_order=lesson_ids,
        learning_objectives=unit_spec.get("learning_objectives", []),
        target_lesson_count=unit_spec.get("target_lesson_count", len(lesson_ids)),
        source_material=unit_spec.get("source_material"),
        generated_from_topic=unit_spec.get("generated_from_topic", True),
        flow_type="standard",
        status="completed",
        creation_progress=None,
        error_message=None,
        user_id=owner_id,
        is_global=unit_spec.get("is_global", False),
        art_image_description=unit_spec.get("art_image_description"),
        # Note: Unit-level podcast fields are deprecated; intros are now lessons with lesson_type='intro'
        art_image_id=art_image_id,
    )
    db_session.add(unit_model)
    await db_session.flush()

    # Process lessons - JSON must include full 'package' (LessonPackage)
    for lesson_spec in unit_spec.get("lessons", []):
        lesson_id = lesson_spec.get("id") or str(uuid.uuid4())
        flow_run_id = lesson_spec.get("flow_run_id") or str(uuid.uuid4())

        # Validate and deserialize package - must be complete
        if not lesson_spec.get("package"):
            raise ValueError(f"Lesson {lesson_id} missing required 'package' field. Each lesson must include a complete LessonPackage.")

        # Validate package structure by deserializing (this will raise if invalid)
        try:
            LessonPackage.model_validate(lesson_spec["package"])
        except Exception as e:
            raise ValueError(f"Lesson {lesson_id} package validation failed: {e}") from e

        # Build lesson record from spec - use values directly from JSON
        lesson_db_dict: dict[str, Any] = {
            "id": lesson_id,
            "title": lesson_spec["title"],
            "learner_level": lesson_spec["learner_level"],
            "unit_id": unit_id,
            "source_material": lesson_spec.get("source_material"),
            "podcast_transcript": lesson_spec.get("podcast_transcript"),
            "package": lesson_spec["package"],
            "package_version": lesson_spec.get("package_version", 1),
            "flow_run_id": flow_run_id,
            "podcast_voice": lesson_spec.get("podcast_voice") or unit_spec.get("podcast_voice"),
            "podcast_audio_object_id": lesson_spec.get("podcast_audio_object_id") or podcast_audio_id,
            "podcast_generated_at": _parse_datetime(lesson_spec.get("podcast_generated_at")) or seed_timestamp,
            "podcast_duration_seconds": lesson_spec.get("podcast_duration_seconds", 180),
            "podcast_transcript_segments": lesson_spec.get("podcast_transcript_segments"),
            "lesson_type": LessonType.INTRO if lesson_spec.get("lesson_type") == "intro" else LessonType.STANDARD,
        }

        # Handle timestamps
        if lesson_spec.get("created_at"):
            lesson_db_dict["created_at"] = _parse_datetime(lesson_spec["created_at"])
        if lesson_spec.get("updated_at"):
            lesson_db_dict["updated_at"] = _parse_datetime(lesson_spec["updated_at"])

        # Create flow run if provided in the JSON
        if lesson_spec.get("flow_run"):
            flow_run_data = dict(lesson_spec["flow_run"])
            flow_run_data["id"] = flow_run_id
            # Parse datetime fields
            for dt_field in ["created_at", "updated_at", "started_at", "completed_at", "last_heartbeat"]:
                if dt_field in flow_run_data:
                    flow_run_data[dt_field] = _parse_datetime(flow_run_data[dt_field])
            db_session.add(FlowRunModel(**flow_run_data))
            await db_session.flush()

        # Create step runs if provided
        if lesson_spec.get("step_runs"):
            for step_data in lesson_spec["step_runs"]:
                step_dict = dict(step_data)
                step_dict["flow_run_id"] = flow_run_id
                # Parse datetime fields
                for dt_field in ["created_at", "updated_at", "completed_at"]:
                    if dt_field in step_dict:
                        step_dict[dt_field] = _parse_datetime(step_dict[dt_field])
                db_session.add(FlowStepRunModel(**step_dict))
            await db_session.flush()

        # Create LLM requests if provided
        if lesson_spec.get("llm_requests"):
            for llm_data in lesson_spec["llm_requests"]:
                llm_dict = dict(llm_data)
                # Parse datetime fields
                for dt_field in ["response_created_at", "created_at", "updated_at"]:
                    if dt_field in llm_dict:
                        llm_dict[dt_field] = _parse_datetime(llm_dict[dt_field])
                db_session.add(LLMRequestModel(**llm_dict))
            await db_session.flush()

        # Create lesson
        db_session.add(LessonModel(**lesson_db_dict))
        await db_session.flush()

        lesson_type_label = "intro" if lesson_spec.get("lesson_type") == "intro" else "standard"
        if args.verbose:
            print(f"   • Created lesson: {lesson_spec['title']} ({lesson_type_label})")

    # Process resources if provided
    photo_resource_ids: list[uuid.UUID] = []
    for resource_spec in unit_spec.get("resources", []):
        resource_id = uuid.UUID(resource_spec["resource_id"]) if "resource_id" in resource_spec else uuid.uuid4()

        # Clean up existing
        await db_session.execute(delete(UnitResourceModel).where(UnitResourceModel.resource_id == resource_id))
        existing_resource = await db_session.get(ResourceModel, resource_id)
        if existing_resource:
            await db_session.delete(existing_resource)
            await db_session.flush()

        # Create document if provided
        document_id = None
        if resource_spec.get("document"):
            doc_spec = resource_spec["document"]
            document_id = uuid.UUID(doc_spec["id"]) if "id" in doc_spec else uuid.uuid4()

            # Check if document already exists - if so, we'll reuse it
            existing_doc = await db_session.get(DocumentModel, document_id)
            if not existing_doc:
                document_model = DocumentModel(
                    id=document_id,
                    user_id=owner_id,
                    s3_key=doc_spec["s3_key"],
                    s3_bucket=doc_spec.get("s3_bucket", bucket_name),
                    filename=doc_spec["filename"],
                    content_type=doc_spec["content_type"],
                    file_size=doc_spec["file_size"],
                    created_at=seed_timestamp,
                    updated_at=seed_timestamp,
                )
                db_session.add(document_model)
                await db_session.flush()

        image_id: uuid.UUID | None = None
        if resource_spec.get("object_store_image_id"):
            image_id = uuid.UUID(str(resource_spec["object_store_image_id"]))

        if resource_spec.get("image"):
            img_spec = resource_spec["image"]
            image_id = image_id or (uuid.UUID(img_spec["id"]) if "id" in img_spec else uuid.uuid4())
            existing_image = await db_session.get(ImageModel, image_id)
            if not existing_image:
                image_model = ImageModel(
                    id=image_id,
                    user_id=img_spec.get("user_id", owner_id),
                    s3_key=img_spec["s3_key"],
                    s3_bucket=img_spec.get("s3_bucket", bucket_name),
                    filename=img_spec["filename"],
                    content_type=img_spec.get("content_type", "image/jpeg"),
                    file_size=img_spec.get("file_size", resource_spec.get("file_size", 0) or 0),
                    width=img_spec.get("width"),
                    height=img_spec.get("height"),
                    alt_text=img_spec.get("alt_text"),
                    description=img_spec.get("description"),
                    created_at=seed_timestamp,
                    updated_at=seed_timestamp,
                )
                db_session.add(image_model)
                await db_session.flush()

        if resource_spec.get("resource_type") == "photo" and image_id is not None:
            photo_resource_ids.append(resource_id)

        # Create resource
        resource_model = ResourceModel(
            id=resource_id,
            user_id=owner_id,
            resource_type=resource_spec["resource_type"],
            filename=resource_spec.get("filename"),
            source_url=resource_spec.get("source_url"),
            extracted_text=resource_spec.get("extracted_text", ""),
            extraction_metadata=resource_spec.get("metadata", {}),
            file_size=resource_spec.get("file_size"),
            object_store_document_id=document_id,
            object_store_image_id=image_id,
            created_at=seed_timestamp,
            updated_at=seed_timestamp,
        )
        db_session.add(resource_model)
        await db_session.flush()

        # Link to unit
        db_session.add(UnitResourceModel(unit_id=unit_id, resource_id=resource_id))
        await db_session.flush()

        if args.verbose:
            label = resource_spec.get("filename") or resource_spec.get("source_url") or str(resource_id)
            print(f"   • Created resource: {label} ({resource_spec['resource_type']})")

    # Seed optional learning conversations (both coach and assistant) tied to the new resources
    conversations_section = unit_spec.get("learning_conversations") or {}
    if isinstance(conversations_section, dict):
        coach_conversations = conversations_section.get("coach", [])
        assistant_conversations = conversations_section.get("assistant", [])
    else:
        coach_conversations = []
        assistant_conversations = []

    # Support legacy key until all seed files migrate
    if not coach_conversations:
        coach_conversations = unit_spec.get("learning_coach_conversations", [])

    # Process learning coach conversations
    for conversation_spec in coach_conversations:
        conversation_id = uuid.UUID(conversation_spec["id"]) if "id" in conversation_spec else uuid.uuid4()
        existing_conversation = await db_session.get(ConversationModel, conversation_id)
        if existing_conversation:
            await db_session.delete(existing_conversation)
            await db_session.flush()

        participant_key = conversation_spec.get("user_key", owner_key)
        participant_id = user_ids.get(participant_key)
        if not participant_id:
            raise ValueError(f"Unknown user_key for conversation: {participant_key}")

        metadata = dict(conversation_spec.get("metadata", {}))
        resource_ids = [uuid.UUID(str(value)) for value in conversation_spec.get("resource_ids", [])]
        if resource_ids:
            metadata.setdefault("resource_ids", [str(resource_id) for resource_id in resource_ids])

        messages = conversation_spec.get("messages", [])
        message_count = len(messages)
        conversation = ConversationModel(
            id=conversation_id,
            user_id=participant_id,
            conversation_type="learning_coach",
            title=conversation_spec.get("title"),
            status=conversation_spec.get("status", "active"),
            conversation_metadata=metadata,
            message_count=message_count,
            created_at=seed_timestamp,
            updated_at=seed_timestamp,
            last_message_at=seed_timestamp if message_count else None,
        )
        db_session.add(conversation)
        await db_session.flush()

        message_base_time = seed_timestamp
        for index, message_spec in enumerate(messages, start=1):
            offset_seconds = message_spec.get("offset_seconds")
            message_time = message_base_time if offset_seconds is None else message_base_time + timedelta(seconds=float(offset_seconds))
            conversation_message = ConversationMessageModel(
                conversation_id=conversation_id,
                role=message_spec["role"],
                content=message_spec["content"],
                message_order=index,
                llm_request_id=None,
                tokens_used=message_spec.get("tokens_used"),
                cost_estimate=message_spec.get("cost_estimate"),
                message_metadata=message_spec.get("metadata"),
                created_at=message_time,
                updated_at=message_time,
            )
            db_session.add(conversation_message)
            conversation.last_message_at = message_time
            conversation.updated_at = message_time

        if resource_ids:
            missing_photos = [resource_id for resource_id in resource_ids if resource_id not in photo_resource_ids]
            if missing_photos and args.verbose:
                print(
                    "   • Conversation references non-photo resources:",
                    ", ".join(str(value) for value in missing_photos),
                )
        if args.verbose:
            print(f"   • Seeded learning coach conversation: {conversation.title or conversation_id}")

    # Process teaching assistant conversations
    for conversation_spec in assistant_conversations:
        conversation_id = uuid.UUID(conversation_spec["id"]) if "id" in conversation_spec else uuid.uuid4()
        existing_conversation = await db_session.get(ConversationModel, conversation_id)
        if existing_conversation:
            await db_session.delete(existing_conversation)
            await db_session.flush()

        participant_key = conversation_spec.get("user_key", owner_key)
        participant_id = user_ids.get(participant_key)
        if not participant_id:
            raise ValueError(f"Unknown user_key for conversation: {participant_key}")

        metadata = dict(conversation_spec.get("metadata", {}))

        messages = conversation_spec.get("messages", [])
        message_count = len(messages)
        conversation = ConversationModel(
            id=conversation_id,
            user_id=participant_id,
            conversation_type="teaching_assistant",
            title=conversation_spec.get("title"),
            status=conversation_spec.get("status", "active"),
            conversation_metadata=metadata,
            message_count=message_count,
            created_at=seed_timestamp,
            updated_at=seed_timestamp,
            last_message_at=seed_timestamp if message_count else None,
        )
        db_session.add(conversation)
        await db_session.flush()

        message_base_time = seed_timestamp
        for index, message_spec in enumerate(messages, start=1):
            offset_seconds = message_spec.get("offset_seconds")
            message_time = message_base_time if offset_seconds is None else message_base_time + timedelta(seconds=float(offset_seconds))
            conversation_message = ConversationMessageModel(
                conversation_id=conversation_id,
                role=message_spec["role"],
                content=message_spec["content"],
                message_order=index,
                llm_request_id=None,
                tokens_used=message_spec.get("tokens_used"),
                cost_estimate=message_spec.get("cost_estimate"),
                message_metadata=message_spec.get("metadata"),
                created_at=message_time,
                updated_at=message_time,
            )
            db_session.add(conversation_message)
            conversation.last_message_at = message_time
            conversation.updated_at = message_time

        if args.verbose:
            print(f"   • Seeded teaching assistant conversation: {conversation.title or conversation_id}")

    await db_session.flush()

    return {
        "unit_id": unit_id,
        "title": unit_spec["title"],
        "lessons_count": len(unit_spec.get("lessons", [])),
        "resources_count": len(unit_spec.get("resources", [])),
    }


async def main() -> None:
    """Main function to create seed data from JSON files."""

    parser = argparse.ArgumentParser(description="Create seed data from JSON files")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress logs")
    parser.add_argument("--seed-data-dir", default="seed_data", help="Directory containing seed data JSON files")
    parser.add_argument("--unit-file", help="Process a specific unit JSON file")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        print("🔧 Verbose mode enabled")

    seed_data_dir = Path(args.seed_data_dir)
    if not seed_data_dir.is_absolute():
        seed_data_dir = Path(__file__).parent.parent / seed_data_dir

    print(f"🌱 Creating seed data from {seed_data_dir}")
    print()

    try:
        infra = infrastructure_provider()
        if args.verbose:
            print("🔄 Initializing infrastructure...")
        infra.initialize()

        # Load and create users
        with infra.get_session_context() as sync_session:
            users_file = seed_data_dir / "users.json"
            if not users_file.exists():
                print(f"❌ Users file not found: {users_file}")
                sys.exit(1)

            sample_user_ids, user_snapshots = await load_and_create_users(sync_session, users_file, args)

        # Process units
        async with infra.get_async_session_context() as db_session:
            units_processed = []

            if args.unit_file:
                # Process single unit file
                unit_file = Path(args.unit_file)
                if not unit_file.is_absolute():
                    unit_file = seed_data_dir / "units" / unit_file

                if not unit_file.exists():
                    print(f"❌ Unit file not found: {unit_file}")
                    sys.exit(1)

                unit_spec = load_json_file(unit_file)
                result = await process_unit_from_json(db_session, unit_spec, sample_user_ids, args)
                units_processed.append(result)
            else:
                # Process all unit files in the units directory
                units_dir = seed_data_dir / "units"
                if not units_dir.exists():
                    print(f"⚠️  Units directory not found: {units_dir}")
                else:
                    unit_files = sorted(units_dir.glob("*.json"))
                    # Skip template files
                    unit_files = [f for f in unit_files if not f.name.startswith("_")]

                    for unit_file in unit_files:
                        unit_spec = load_json_file(unit_file)
                        result = await process_unit_from_json(db_session, unit_spec, sample_user_ids, args)
                        units_processed.append(result)

            await db_session.commit()

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    # Print summary
    print("\n✅ Seed data created successfully!")
    print(f"   • Users: {len(user_snapshots)}")
    for snapshot in user_snapshots.values():
        role_label = "Admin" if snapshot["role"] == "admin" else "Learner"
        print(f"     - {role_label}: {snapshot['name']} <{snapshot['email']}>")

    print(f"\n   • Units: {len(units_processed)}")
    for unit_info in units_processed:
        print(f"     - {unit_info['title']} ({unit_info['lessons_count']} lessons, {unit_info['resources_count']} resources)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
