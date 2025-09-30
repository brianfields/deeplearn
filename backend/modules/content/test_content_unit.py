"""
Content Module - Unit Tests

Tests for the content module service layer with package structure.
"""

from datetime import UTC, datetime
import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from modules.content.models import LessonModel, UnitModel
from modules.content.package_models import GlossaryTerm, LessonPackage, MCQAnswerKey, MCQExercise, MCQOption, Meta, Objective
from modules.content.repo import ContentRepo
from modules.content.service import ContentService, LessonCreate
from modules.object_store.public import FileUploadResult, ImageRead


class TestContentService:
    """Unit tests for ContentService."""

    def test_get_lesson_returns_none_when_not_found(self) -> None:
        """Test that get_lesson returns None when lesson doesn't exist."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        repo.get_lesson_by_id.return_value = None
        service = ContentService(repo)

        # Act
        result = service.get_lesson("nonexistent")

        # Assert
        assert result is None
        repo.get_lesson_by_id.assert_called_once_with("nonexistent")

    def test_get_lesson_returns_lesson_with_package(self) -> None:
        """Test that get_lesson returns lesson with package when found."""
        # Arrange
        repo = Mock(spec=ContentRepo)

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
        result = service.get_lesson("test-id")

        # Assert
        assert result is not None
        assert result.id == "test-id"
        assert result.title == "Test Lesson"
        assert result.package_version == 1
        assert len(result.package.objectives) == 1
        assert len(result.package.exercises) == 1
        assert result.package.objectives[0].text == "Learn X"

        repo.get_lesson_by_id.assert_called_once_with("test-id")

    def test_save_lesson_creates_new_lesson_with_package(self) -> None:
        """Test that save_lesson creates a new lesson with package."""
        # Arrange
        repo = Mock(spec=ContentRepo)
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
        result = service.save_lesson(lesson_data)

        # Assert
        assert result.id == "test-id"
        assert result.title == "Test Lesson"
        assert result.package_version == 1
        assert len(result.package.objectives) == 1
        repo.save_lesson.assert_called_once()

    def test_lesson_exists_returns_true_when_exists(self) -> None:
        """Test that lesson_exists returns True when lesson exists."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        repo.lesson_exists.return_value = True
        service = ContentService(repo)

        # Act
        result = service.lesson_exists("test-id")

        # Assert
        assert result is True
        repo.lesson_exists.assert_called_once_with("test-id")

    def test_delete_lesson_returns_true_when_deleted(self) -> None:
        """Test that delete_lesson returns True when lesson is deleted."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        repo.delete_lesson.return_value = True
        service = ContentService(repo)

        # Act
        result = service.delete_lesson("test-id")

        # Assert
        assert result is True
        repo.delete_lesson.assert_called_once_with("test-id")

    def test_delete_unit_returns_true_when_deleted(self) -> None:
        """Test deleting an existing unit returns True."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        service = ContentService(repo)
        repo.delete_unit.return_value = True

        # Act
        result = service.delete_unit("unit-1")

        # Assert
        assert result is True
        repo.delete_unit.assert_called_once_with("unit-1")

    def test_delete_unit_returns_false_when_not_found(self) -> None:
        """Test deleting a non-existent unit returns False."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        service = ContentService(repo)
        repo.delete_unit.return_value = False

        # Act
        result = service.delete_unit("nonexistent-unit")

        # Assert
        assert result is False
        repo.delete_unit.assert_called_once_with("nonexistent-unit")

    @pytest.mark.asyncio
    async def test_create_unit_assigns_owner_and_sharing_flags(self) -> None:
        """Unit creation should persist ownership and sharing metadata."""

        repo = Mock(spec=ContentRepo)
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
        repo.add_unit.assert_called_once()
        stored_model = repo.add_unit.call_args.args[0]
        assert stored_model.user_id == 7
        assert stored_model.is_global is True

    @pytest.mark.asyncio
    async def test_create_unit_generates_cover_image_when_available(self) -> None:
        """LLM-backed image generation should populate cover metadata."""

        repo = Mock(spec=ContentRepo)
        repo.add_unit.side_effect = lambda model: model

        image_response = Mock()
        image_response.image_url = "https://images.example/weimar-edge.png"
        image_response.revised_prompt = "Refined prompt"
        image_response.size = "1024x1024"
        image_response.cost_estimate = 0.25

        llm = Mock()
        llm.generate_image = AsyncMock(return_value=(image_response, uuid.uuid4()))

        stored_image = ImageRead(
            id=uuid.uuid4(),
            user_id=None,
            s3_key="images/unit-cover-test.png",
            s3_bucket="bucket",
            filename="unit-cover-test.png",
            content_type="image/png",
            file_size=1024,
            width=1024,
            height=1024,
            alt_text=None,
            description="desc",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        object_store = Mock()
        object_store.upload_image = AsyncMock(
            return_value=FileUploadResult(file=stored_image, presigned_url="https://cdn.example/unit-cover.png")
        )
        object_store.generate_presigned_url = AsyncMock()

        service = ContentService(repo, llm, object_store)
        service._download_image_content = AsyncMock(return_value=(b"fake-bytes", "image/png"))

        payload = service.UnitCreate(
            title="Quantum Harmonics",
            learner_level="advanced",
            description="Exploring vibrational modes in quantum systems",
            learning_objectives=["Interpret energy spectra", "Model harmonic oscillators"],
        )

        created = await service.create_unit(payload)

        llm.generate_image.assert_awaited_once()
        object_store.upload_image.assert_awaited_once()
        assert created.cover_image_url == "https://cdn.example/unit-cover.png"
        assert created.cover_image_prompt == image_response.revised_prompt
        assert created.cover_image_object_id == stored_image.id
        stored_model = repo.add_unit.call_args.args[0]
        assert stored_model.cover_image_url == "https://cdn.example/unit-cover.png"
        assert stored_model.cover_image_prompt == image_response.revised_prompt
        assert stored_model.cover_image_object_id == stored_image.id

    @pytest.mark.asyncio
    async def test_create_unit_uses_provider_url_when_object_store_missing(self) -> None:
        """If object store is unavailable, fallback to provider URL."""

        repo = Mock(spec=ContentRepo)
        repo.add_unit.side_effect = lambda model: model

        image_response = Mock()
        image_response.image_url = "https://images.example/weimar-edge.png"
        image_response.revised_prompt = None
        image_response.size = "1024x1024"
        image_response.cost_estimate = 0.1

        llm = Mock()
        llm.generate_image = AsyncMock(return_value=(image_response, uuid.uuid4()))

        service = ContentService(repo, llm, None)

        payload = service.UnitCreate(title="Fallback", learner_level="beginner")

        created = await service.create_unit(payload)

        assert created.cover_image_url == image_response.image_url
        assert created.cover_image_object_id is None

    def test_list_units_for_user_uses_repo(self) -> None:
        """Ensure user-specific listing delegates to repository."""

        repo = Mock(spec=ContentRepo)
        service = ContentService(repo)

        repo.list_units_for_user.return_value = []

        result = service.list_units_for_user(10)

        assert result == []
        repo.list_units_for_user.assert_called_once_with(user_id=10, limit=100, offset=0)

    def test_list_global_units_uses_repo(self) -> None:
        """Ensure global listing delegates to repository."""

        repo = Mock(spec=ContentRepo)
        service = ContentService(repo)

        repo.list_global_units.return_value = []

        assert service.list_global_units() == []
        repo.list_global_units.assert_called_once_with(limit=100, offset=0)

    def test_set_unit_sharing_requires_owner_match(self) -> None:
        """Only the unit owner can toggle sharing when acting user is provided."""

        repo = Mock(spec=ContentRepo)
        service = ContentService(repo)

        repo.is_unit_owned_by_user.return_value = False

        with pytest.raises(PermissionError, match="User does not own this unit"):
            service.set_unit_sharing("unit-1", is_global=True, acting_user_id=3)

    def test_set_unit_sharing_updates_when_authorized(self) -> None:
        """Authorized owner should toggle sharing successfully."""

        repo = Mock(spec=ContentRepo)
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
        )

        result = service.set_unit_sharing("unit-1", is_global=True, acting_user_id=3)

        assert result.is_global is True
        repo.set_unit_sharing.assert_called_once_with("unit-1", True)

    def test_assign_unit_owner_updates_repo(self) -> None:
        """Assign unit owner should call repository and return DTO."""

        repo = Mock(spec=ContentRepo)
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

        result = service.assign_unit_owner("unit-1", owner_user_id=42)

        assert result.user_id == 42
        repo.set_unit_owner.assert_called_once_with("unit-1", 42)
