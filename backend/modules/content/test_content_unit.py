"""
Content Module - Unit Tests

Tests for the content module service layer.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

from modules.content.models import LessonComponentModel, LessonModel
from modules.content.repo import ContentRepo
from modules.content.service import ContentService, LessonComponentCreate, LessonCreate


class TestContentService:
    """Unit tests for ContentService."""

    def test_get_lesson_returns_none_when_not_found(self):
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

    def test_get_lesson_returns_lesson_with_components(self):
        """Test that get_lesson returns lesson with components when found."""
        # Arrange
        repo = Mock(spec=ContentRepo)

        # Mock lesson
        mock_lesson = LessonModel(id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Concept A"], created_at=datetime.now(UTC), updated_at=datetime.now(UTC))

        # Mock components
        mock_component = LessonComponentModel(id="comp-id", lesson_id="test-id", component_type="mcq", title="Test MCQ", content={"question": "What is X?"}, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))

        repo.get_lesson_by_id.return_value = mock_lesson
        repo.get_components_by_lesson_id.return_value = [mock_component]

        service = ContentService(repo)

        # Act
        result = service.get_lesson("test-id")

        # Assert
        assert result is not None
        assert result.id == "test-id"
        assert result.title == "Test Lesson"
        assert len(result.components) == 1
        assert result.components[0].id == "comp-id"

        repo.get_lesson_by_id.assert_called_once_with("test-id")
        repo.get_components_by_lesson_id.assert_called_once_with("test-id")

    def test_save_lesson_creates_new_lesson(self):
        """Test that save_lesson creates a new lesson."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        service = ContentService(repo)

        lesson_data = LessonCreate(id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Concept A"])

        # Mock the saved lesson
        mock_saved_lesson = LessonModel(id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Concept A"], created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        repo.save_lesson.return_value = mock_saved_lesson

        # Act
        result = service.save_lesson(lesson_data)

        # Assert
        assert result.id == "test-id"
        assert result.title == "Test Lesson"
        assert len(result.components) == 0  # New lesson has no components
        repo.save_lesson.assert_called_once()

    def test_save_lesson_component_creates_new_component(self):
        """Test that save_lesson_component creates a new lesson component."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        service = ContentService(repo)

        component_data = LessonComponentCreate(id="comp-id", lesson_id="test-id", component_type="mcq", title="Test MCQ", content={"question": "What is X?"}, learning_objective="Learn X")

        # Mock the saved component
        mock_saved_component = LessonComponentModel(
            id="comp-id", lesson_id="test-id", component_type="mcq", title="Test MCQ", content={"question": "What is X?"}, learning_objective="Learn X", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)
        )
        repo.save_component.return_value = mock_saved_component

        # Act
        result = service.save_lesson_component(component_data)

        # Assert
        assert result.id == "comp-id"
        assert result.lesson_id == "test-id"
        assert result.component_type == "mcq"
        repo.save_component.assert_called_once()

    def test_lesson_exists_returns_true_when_exists(self):
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

    def test_delete_lesson_returns_true_when_deleted(self):
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
