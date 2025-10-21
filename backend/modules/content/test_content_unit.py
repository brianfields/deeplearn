"""
Content Module - Unit Tests

Tests for the content module service layer with package structure.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import uuid

import pytest

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from modules.content.models import LessonModel, UnitModel
from modules.content.package_models import GlossaryTerm, LessonPackage, MCQAnswerKey, MCQExercise, MCQOption, Meta, Objective
from modules.content.repo import ContentRepo
from modules.content.routes import get_content_service, router as content_router
from modules.content.service import ContentService, LessonCreate

pytestmark = pytest.mark.asyncio


class TestContentService:
    """Unit tests for ContentService."""

    async def test_get_lesson_returns_none_when_not_found(self) -> None:
        """Test that get_lesson returns None when lesson doesn't exist."""
        # Arrange
        repo = AsyncMock(spec=ContentRepo)
        repo.get_lesson_by_id.return_value = None
        service = ContentService(repo)

        # Act
        result = await service.get_lesson("nonexistent")

        # Assert
        assert result is None
        repo.get_lesson_by_id.assert_awaited_once_with("nonexistent")

    async def test_get_lesson_returns_lesson_with_package(self) -> None:
        """Test that get_lesson returns lesson with package when found."""
        # Arrange
        repo = AsyncMock(spec=ContentRepo)

        # Create a sample package
        package = LessonPackage(
            meta=Meta(lesson_id="test-id", title="Test Lesson", learner_level="beginner"),
            objectives=[Objective(id="lo_1", text="Learn X")],
            glossary={"terms": [GlossaryTerm(id="term_1", term="Test Term", definition="Test Definition")]},
            mini_lesson="Test explanation",
            exercises=[
                MCQExercise(
                    id="mcq_1",
                    lo_id="lo_1",
                    stem="What is X?",
                    options=[MCQOption(id="opt_a", label="A", text="Option A"), MCQOption(id="opt_b", label="B", text="Option B"), MCQOption(id="opt_c", label="C", text="Option C")],
                    answer_key=MCQAnswerKey(label="A"),
                )
            ],
        )

        # Mock lesson with package
        mock_lesson = LessonModel(id="test-id", title="Test Lesson", learner_level="beginner", package=package.model_dump(), package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))

        repo.get_lesson_by_id.return_value = mock_lesson
        service = ContentService(repo)

        # Act
        result = await service.get_lesson("test-id")

        # Assert
        assert result is not None
        assert result.id == "test-id"
        assert result.title == "Test Lesson"
        assert result.package_version == 1
        assert len(result.package.objectives) == 1
        assert len(result.package.exercises) == 1
        assert result.package.objectives[0].text == "Learn X"

        repo.get_lesson_by_id.assert_awaited_once_with("test-id")

    async def test_save_lesson_creates_new_lesson_with_package(self) -> None:
        """Test that save_lesson creates a new lesson with package."""
        # Arrange
        repo = AsyncMock(spec=ContentRepo)
        service = ContentService(repo)

        # Create a sample package
        package = LessonPackage(
            meta=Meta(lesson_id="test-id", title="Test Lesson", learner_level="beginner"),
            objectives=[Objective(id="lo_1", text="Learn X")],
            glossary={"terms": []},
            mini_lesson="Test explanation",
            exercises=[],
        )

        lesson_data = LessonCreate(id="test-id", title="Test Lesson", learner_level="beginner", package=package, package_version=1)

        # Mock the saved lesson
        mock_saved_lesson = LessonModel(id="test-id", title="Test Lesson", learner_level="beginner", package=package.model_dump(), package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        repo.save_lesson.return_value = mock_saved_lesson

        # Act
        result = await service.save_lesson(lesson_data)

        # Assert
        assert result.id == "test-id"
        assert result.title == "Test Lesson"
        assert result.package_version == 1
        assert len(result.package.objectives) == 1
        repo.save_lesson.assert_awaited_once()

    async def test_lesson_exists_returns_true_when_exists(self) -> None:
        """Test that lesson_exists returns True when lesson exists."""
        # Arrange
        repo = AsyncMock(spec=ContentRepo)
        repo.lesson_exists.return_value = True
        service = ContentService(repo)

        # Act
        result = await service.lesson_exists("test-id")

        # Assert
        assert result is True
        repo.lesson_exists.assert_awaited_once_with("test-id")

    async def test_delete_lesson_returns_true_when_deleted(self) -> None:
        """Test that delete_lesson returns True when lesson is deleted."""
        # Arrange
        repo = AsyncMock(spec=ContentRepo)
        repo.delete_lesson.return_value = True
        service = ContentService(repo)

        # Act
        result = await service.delete_lesson("test-id")

        # Assert
        assert result is True
        repo.delete_lesson.assert_awaited_once_with("test-id")

    async def test_delete_unit_returns_true_when_deleted(self) -> None:
        """Test deleting an existing unit returns True."""
        # Arrange
        repo = AsyncMock(spec=ContentRepo)
        service = ContentService(repo)
        repo.delete_unit.return_value = True

        # Act
        result = await service.delete_unit("unit-1")

        # Assert
        assert result is True
        repo.delete_unit.assert_awaited_once_with("unit-1")

    async def test_delete_unit_returns_false_when_not_found(self) -> None:
        """Test deleting a non-existent unit returns False."""
        # Arrange
        repo = AsyncMock(spec=ContentRepo)
        service = ContentService(repo)
        repo.delete_unit.return_value = False

        # Act
        result = await service.delete_unit("nonexistent-unit")

        # Assert
        assert result is False
        repo.delete_unit.assert_awaited_once_with("nonexistent-unit")

    async def test_save_unit_art_from_bytes_uploads_and_sets_fields(self) -> None:
        """Persisting artwork should upload image and update unit metadata."""

        repo = AsyncMock(spec=ContentRepo)
        object_store = AsyncMock()
        service = ContentService(repo, object_store=object_store)

        unit_id = "unit-200"
        owner_id = 5
        now = datetime.now(UTC)
        repo.get_unit_by_id.return_value = UnitModel(
            id=unit_id,
            title="Artful Unit",
            learner_level="beginner",
            lesson_order=[],
            user_id=owner_id,
            is_global=False,
            status="completed",
            generated_from_topic=False,
            flow_type="standard",
            created_at=now,
            updated_at=now,
        )

        image_uuid = uuid.uuid4()
        repo.set_unit_art.return_value = UnitModel(
            id=unit_id,
            title="Artful Unit",
            learner_level="beginner",
            lesson_order=[],
            user_id=owner_id,
            is_global=False,
            status="completed",
            generated_from_topic=False,
            flow_type="standard",
            art_image_id=image_uuid,
            art_image_description="Petrol blue skyline",
            created_at=now,
            updated_at=now,
        )

        object_store.upload_image.return_value = Mock(file=Mock(id=image_uuid))
        object_store.get_image.return_value = Mock(presigned_url="https://cdn/unit-art.png")

        result = await service.save_unit_art_from_bytes(
            unit_id,
            image_bytes=b"binary",
            content_type="image/png",
            description="Petrol blue skyline",
            alt_text="Skyline alt",
        )

        object_store.upload_image.assert_awaited_once()
        repo.set_unit_art.assert_awaited_once_with(unit_id, image_object_id=image_uuid, description="Petrol blue skyline")
        object_store.get_image.assert_awaited_once_with(image_uuid, requesting_user_id=owner_id, include_presigned_url=True)

        assert result.art_image_id == image_uuid
        assert result.art_image_description == "Petrol blue skyline"
        assert result.art_image_url == "https://cdn/unit-art.png"

    async def test_create_unit_assigns_owner_and_sharing_flags(self) -> None:
        """Unit creation should persist ownership and sharing metadata."""

        repo = AsyncMock(spec=ContentRepo)
        service = ContentService(repo)

        now = datetime.now(UTC)

        unit_model = UnitModel(
            id="unit-1",
            title="Test Unit",
            description=None,
            learner_level="beginner",
            lesson_order=[],
            user_id=7,
            is_global=True,
            status="completed",
            generated_from_topic=False,
            flow_type="standard",
            created_at=now,
            updated_at=now,
        )

        repo.add_unit.return_value = unit_model

        payload = service.UnitCreate(
            id="unit-1",
            title="Test Unit",
            learner_level="beginner",
            user_id=7,
            is_global=True,
        )

        created = await service.create_unit(payload)

        assert created.user_id == 7
        assert created.is_global is True
        assert created.has_podcast is False
        assert created.podcast_voice is None
        repo.add_unit.assert_awaited_once()
        stored_model = repo.add_unit.await_args.args[0]
        assert stored_model.user_id == 7
        assert stored_model.is_global is True

    async def test_list_units_for_user_uses_repo(self) -> None:
        """Ensure user-specific listing delegates to repository."""

        repo = AsyncMock(spec=ContentRepo)
        service = ContentService(repo)

        repo.list_units_for_user.return_value = []

        result = await service.list_units_for_user(10)

        assert result == []
        repo.list_units_for_user.assert_awaited_once_with(user_id=10, limit=100, offset=0)

    async def test_list_global_units_uses_repo(self) -> None:
        """Ensure global listing delegates to repository."""

        repo = AsyncMock(spec=ContentRepo)
        service = ContentService(repo)

        repo.list_global_units.return_value = []

        assert await service.list_global_units() == []
        repo.list_global_units.assert_awaited_once_with(limit=100, offset=0)

    async def test_set_unit_sharing_requires_owner_match(self) -> None:
        """Only the unit owner can toggle sharing when acting user is provided."""

        repo = AsyncMock(spec=ContentRepo)
        service = ContentService(repo)

        repo.is_unit_owned_by_user.return_value = False

        with pytest.raises(PermissionError, match="User does not own this unit"):
            await service.set_unit_sharing("unit-1", is_global=True, acting_user_id=3)
        repo.is_unit_owned_by_user.assert_awaited_once_with("unit-1", 3)

    async def test_set_unit_sharing_updates_when_authorized(self) -> None:
        """Authorized owner should toggle sharing successfully."""

        repo = AsyncMock(spec=ContentRepo)
        service = ContentService(repo)

        repo.is_unit_owned_by_user.return_value = True
        repo.set_unit_sharing.return_value = UnitModel(
            id="unit-1",
            title="Unit",
            learner_level="beginner",
            lesson_order=[],
            user_id=3,
            is_global=True,
            status="completed",
            generated_from_topic=False,
            flow_type="standard",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            podcast_voice="Narrator",
        )

        result = await service.set_unit_sharing("unit-1", is_global=True, acting_user_id=3)

        assert result.is_global is True
        assert result.podcast_voice == "Narrator"
        assert result.podcast_duration_seconds is None
        repo.is_unit_owned_by_user.assert_awaited_once_with("unit-1", 3)
        repo.set_unit_sharing.assert_awaited_once_with("unit-1", True)

    async def test_assign_unit_owner_updates_repo(self) -> None:
        """Assign unit owner should call repository and return DTO."""

        repo = AsyncMock(spec=ContentRepo)
        service = ContentService(repo)

        repo.set_unit_owner.return_value = UnitModel(
            id="unit-1",
            title="Unit",
            learner_level="beginner",
            lesson_order=[],
            user_id=42,
            is_global=False,
            status="completed",
            generated_from_topic=False,
            flow_type="standard",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        result = await service.assign_unit_owner("unit-1", owner_user_id=42)

        assert result.user_id == 42
        repo.set_unit_owner.assert_awaited_once_with("unit-1", 42)

    async def test_set_unit_podcast_updates_metadata(self) -> None:
        """Persisting podcast metadata should surface on unit read models."""

        repo = AsyncMock(spec=ContentRepo)
        service = ContentService(repo)

        now = datetime.now(UTC)
        audio_id = uuid.uuid4()
        unit_model = UnitModel(
            id="unit-42",
            title="Podcast Unit",
            description=None,
            learner_level="intermediate",
            lesson_order=[],
            user_id=None,
            is_global=False,
            status="completed",
            generated_from_topic=False,
            flow_type="standard",
            podcast_transcript="Hello",
            podcast_voice="Storyteller",
            podcast_audio_object_id=audio_id,
            podcast_generated_at=now,
            created_at=now,
            updated_at=now,
        )

        repo.set_unit_podcast.return_value = unit_model

        result = await service.set_unit_podcast(
            "unit-42",
            transcript="Hello",
            audio_object_id=audio_id,
            voice="Storyteller",
        )

        assert result is not None
        assert result.has_podcast is True
        assert result.podcast_voice == "Storyteller"
        assert result.podcast_duration_seconds is None
        repo.set_unit_podcast.assert_awaited_once()
        _, kwargs = repo.set_unit_podcast.await_args
        assert kwargs.get("audio_object_id") == audio_id

    async def test_set_unit_podcast_uses_object_store_metadata_when_available(self) -> None:
        """Duration should be populated from object store metadata when available."""

        repo = AsyncMock(spec=ContentRepo)
        object_store = AsyncMock()
        object_store.get_audio = AsyncMock()
        object_store.get_audio.return_value = Mock(duration_seconds=181.6, content_type="audio/mpeg")

        service = ContentService(repo, object_store=object_store)

        now = datetime.now(UTC)
        audio_id = uuid.uuid4()
        unit_model = UnitModel(
            id="unit-50",
            title="Podcast Unit",
            description=None,
            learner_level="intermediate",
            lesson_order=[],
            user_id=12,
            is_global=False,
            status="completed",
            generated_from_topic=False,
            flow_type="standard",
            podcast_transcript="Hello",
            podcast_voice="Storyteller",
            podcast_audio_object_id=audio_id,
            podcast_generated_at=now,
            created_at=now,
            updated_at=now,
        )

        repo.set_unit_podcast.return_value = unit_model

        result = await service.set_unit_podcast(
            "unit-50",
            transcript="Hello",
            audio_object_id=audio_id,
            voice="Storyteller",
        )

        assert result is not None
        assert result.podcast_duration_seconds == 182
        object_store.get_audio.assert_awaited_once()

    async def test_get_unit_podcast_audio_returns_none_without_object_store(self) -> None:
        """Audio retrieval should return None when no object store client is configured."""

        repo = AsyncMock(spec=ContentRepo)
        service = ContentService(repo)

        now = datetime.now(UTC)
        audio_id = uuid.uuid4()
        unit_model = UnitModel(
            id="unit-99",
            title="Audio Unit",
            description=None,
            learner_level="beginner",
            lesson_order=[],
            user_id=None,
            is_global=False,
            status="completed",
            generated_from_topic=False,
            flow_type="standard",
            podcast_audio_object_id=audio_id,
            created_at=now,
            updated_at=now,
        )

        repo.get_unit_by_id.return_value = unit_model

        audio = await service.get_unit_podcast_audio("unit-99")

        assert audio is None
        repo.get_unit_by_id.assert_awaited_once_with("unit-99")

    async def test_get_unit_podcast_audio_uses_object_store_when_available(self) -> None:
        """When an object store reference exists it should be resolved via presigned URL."""

        repo = AsyncMock(spec=ContentRepo)
        object_store = AsyncMock()
        object_store.get_audio = AsyncMock()
        object_store.get_audio.return_value = Mock(
            content_type="audio/mpeg",
            presigned_url="https://example.com/audio.mp3",
        )

        service = ContentService(repo, object_store=object_store)

        now = datetime.now(UTC)
        audio_id = uuid.uuid4()
        unit_model = UnitModel(
            id="unit-100",
            title="Audio Unit",
            description=None,
            learner_level="beginner",
            lesson_order=[],
            user_id=None,
            is_global=False,
            status="completed",
            generated_from_topic=False,
            flow_type="standard",
            podcast_audio_object_id=audio_id,
            created_at=now,
            updated_at=now,
        )

        repo.get_unit_by_id.return_value = unit_model

        audio = await service.get_unit_podcast_audio("unit-100")

        assert audio is not None
        assert audio.presigned_url == "https://example.com/audio.mp3"
        assert audio.audio_bytes is None
        assert audio.mime_type == "audio/mpeg"

    async def test_get_units_since_returns_unit_and_assets(self) -> None:
        """Unit sync should include lessons, assets, and a cursor."""

        repo = AsyncMock(spec=ContentRepo)
        object_store = AsyncMock()
        service = ContentService(repo, object_store=object_store)

        now = datetime.now(UTC)
        since = now - timedelta(minutes=30)
        unit_id = "unit-sync"
        lesson_id = "lesson-sync"
        audio_uuid = uuid.uuid4()
        art_uuid = uuid.uuid4()

        unit_model = UnitModel(
            id=unit_id,
            title="Offline Unit",
            description="",
            learner_level="beginner",
            lesson_order=[lesson_id],
            user_id=5,
            is_global=False,
            learning_objectives=None,
            target_lesson_count=None,
            source_material=None,
            generated_from_topic=False,
            flow_type="standard",
            status="completed",
            creation_progress=None,
            error_message=None,
            podcast_transcript="Transcript",
            podcast_voice="alloy",
            podcast_audio_object_id=audio_uuid,
            podcast_generated_at=now,
            art_image_id=art_uuid,
            art_image_description="cover",
            created_at=now,
            updated_at=now,
        )

        package = LessonPackage(
            meta=Meta(lesson_id=lesson_id, title="Lesson", learner_level="beginner"),
            objectives=[Objective(id="obj-1", text="Objective")],
            glossary={"terms": []},
            mini_lesson="Mini lesson",
            exercises=[],
        )

        lesson_model = LessonModel(
            id=lesson_id,
            title="Lesson",
            learner_level="beginner",
            unit_id=unit_id,
            source_material=None,
            package=package.model_dump(),
            package_version=1,
            flow_run_id=None,
            created_at=now,
            updated_at=now,
        )

        repo.get_units_updated_since.return_value = [unit_model]
        repo.get_lessons_for_unit_ids.return_value = [lesson_model]
        repo.get_lessons_updated_since.return_value = []

        object_store.get_audio.return_value = SimpleNamespace(presigned_url="https://cdn/audio.mp3")
        object_store.get_image.return_value = SimpleNamespace(presigned_url="https://cdn/image.png")

        response = await service.get_units_since(since=since, limit=20)

        repo.get_units_updated_since.assert_awaited_once_with(since, limit=20)
        repo.get_lessons_for_unit_ids.assert_awaited_once()
        repo.get_lessons_updated_since.assert_awaited_once_with(since, limit=20)

        assert len(response.units) == 1
        entry = response.units[0]
        assert entry.unit.id == unit_id
        assert entry.unit.schema_version == 1
        assert entry.lessons and entry.lessons[0].id == lesson_id
        assert entry.lessons[0].schema_version == 1
        assert {asset.type for asset in entry.assets} == {"audio", "image"}
        assert response.cursor == now

    async def test_get_units_since_minimal_payload_skips_lessons_and_audio(self) -> None:
        """Minimal payload requests should avoid lesson hydration and audio fetches."""

        repo = AsyncMock(spec=ContentRepo)
        object_store = AsyncMock()
        object_store.get_audio = AsyncMock()
        object_store.get_image = AsyncMock(return_value=SimpleNamespace(presigned_url="https://cdn/image.png"))

        service = ContentService(repo, object_store=object_store)

        now = datetime.now(UTC)
        unit_id = "unit-minimal"
        audio_uuid = uuid.uuid4()
        art_uuid = uuid.uuid4()

        unit_model = UnitModel(
            id=unit_id,
            title="Offline Unit",
            description="",
            learner_level="beginner",
            lesson_order=[],
            user_id=None,
            is_global=False,
            learning_objectives=None,
            target_lesson_count=None,
            source_material=None,
            generated_from_topic=False,
            flow_type="standard",
            status="completed",
            creation_progress=None,
            error_message=None,
            podcast_transcript=None,
            podcast_voice=None,
            podcast_audio_object_id=audio_uuid,
            podcast_generated_at=now,
            art_image_id=art_uuid,
            art_image_description="cover",
            created_at=now,
            updated_at=now,
        )

        repo.get_units_updated_since.return_value = [unit_model]

        response = await service.get_units_since(since=None, limit=5, payload="minimal")

        repo.get_lessons_for_unit_ids.assert_not_called()
        repo.get_lessons_updated_since.assert_not_called()
        object_store.get_audio.assert_not_awaited()

        assert len(response.units) == 1
        entry = response.units[0]
        assert entry.lessons == []
        assert {asset.type for asset in entry.assets} == {"image"}
        assert response.cursor == now


class _StubSyncService:
    """Minimal stub to capture sync calls from the FastAPI route."""

    def __init__(self) -> None:
        self.args: tuple[
            datetime | None,
            int,
            bool,
            ContentService.UnitSyncPayload,
        ] | None = None

    async def get_units_since(
        self,
        *,
        since: datetime | None,
        limit: int,
        include_deleted: bool,
        payload: ContentService.UnitSyncPayload,
    ) -> ContentService.UnitSyncResponse:
        self.args = (since, limit, include_deleted, payload)
        return ContentService.UnitSyncResponse(
            units=[],
            deleted_unit_ids=[],
            deleted_lesson_ids=[],
            cursor=datetime.now(UTC),
        )


async def _build_test_app(stub: _StubSyncService) -> FastAPI:
    app = FastAPI()
    app.include_router(content_router)

    async def _override() -> _StubSyncService:
        return stub

    app.dependency_overrides[get_content_service] = _override
    return app


async def test_sync_units_route_parses_query_parameters() -> None:
    """The sync route should parse timestamps and limits before delegating to the service."""

    stub = _StubSyncService()
    app = await _build_test_app(stub)

    since_value = datetime.now(UTC).isoformat()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/content/units/sync",
            params={"since": since_value, "limit": 7, "include_deleted": "true"},
        )

    assert response.status_code == status.HTTP_200_OK
    assert stub.args is not None
    parsed_since, captured_limit, captured_deleted, payload = stub.args
    assert parsed_since == datetime.fromisoformat(since_value)
    assert captured_limit == 7
    assert captured_deleted is True
    assert payload == "full"


async def test_sync_units_route_validates_since_format() -> None:
    """Invalid timestamps should be rejected with a 400 response."""

    stub = _StubSyncService()
    app = await _build_test_app(stub)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/content/units/sync",
            params={"since": "not-a-timestamp"},
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # Dependency override means service was never invoked
    assert stub.args is None


async def test_sync_units_route_accepts_minimal_payload() -> None:
    """Clients may request the lightweight payload variant."""

    stub = _StubSyncService()
    app = await _build_test_app(stub)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/content/units/sync",
            params={"payload": "minimal"},
        )

    assert response.status_code == status.HTTP_200_OK
    assert stub.args is not None
    _, _, _, payload = stub.args
    assert payload == "minimal"


async def test_sync_units_route_rejects_unknown_payload() -> None:
    """Unsupported payload values should raise a validation error."""

    stub = _StubSyncService()
    app = await _build_test_app(stub)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/content/units/sync",
            params={"payload": "everything"},
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert stub.args is None
