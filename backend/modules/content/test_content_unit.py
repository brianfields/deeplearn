"""
Content Module - Unit Tests

Tests for the content module service layer with package structure.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

from modules.content.models import LessonModel
from modules.content.package_models import GlossaryTerm, LessonPackage, MCQAnswerKey, MCQItem, MCQOption, Meta, Objective
from modules.content.repo import ContentRepo
from modules.content.service import ContentService, LessonCreate


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

    def test_get_lesson_returns_lesson_with_package(self):
        """Test that get_lesson returns lesson with package when found."""
        # Arrange
        repo = Mock(spec=ContentRepo)

        # Create a sample package
        package = LessonPackage(
            meta=Meta(lesson_id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", domain="General"),
            objectives=[Objective(id="lo_1", text="Learn X")],
            glossary={"terms": [GlossaryTerm(id="term_1", term="Test Term", definition="Test Definition")]},
            didactic={"by_lo": {}},
            mcqs=[
                MCQItem(
                    id="mcq_1",
                    lo_id="lo_1",
                    stem="What is X?",
                    options=[MCQOption(id="opt_a", label="A", text="Option A"), MCQOption(id="opt_b", label="B", text="Option B"), MCQOption(id="opt_c", label="C", text="Option C")],
                    answer_key=MCQAnswerKey(label="A"),
                )
            ],
        )

        # Mock lesson with package
        mock_lesson = LessonModel(id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", package=package.model_dump(), package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))

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
        assert len(result.package.mcqs) == 1
        assert result.package.objectives[0].text == "Learn X"

        repo.get_lesson_by_id.assert_called_once_with("test-id")

    def test_save_lesson_creates_new_lesson_with_package(self):
        """Test that save_lesson creates a new lesson with package."""
        # Arrange
        repo = Mock(spec=ContentRepo)
        service = ContentService(repo)

        # Create a sample package
        package = LessonPackage(
            meta=Meta(lesson_id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", domain="General"), objectives=[Objective(id="lo_1", text="Learn X")], glossary={"terms": []}, didactic={"by_lo": {}}, mcqs=[]
        )

        lesson_data = LessonCreate(id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", package=package, package_version=1)

        # Mock the saved lesson
        mock_saved_lesson = LessonModel(id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", package=package.model_dump(), package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        repo.save_lesson.return_value = mock_saved_lesson

        # Act
        result = service.save_lesson(lesson_data)

        # Assert
        assert result.id == "test-id"
        assert result.title == "Test Lesson"
        assert result.package_version == 1
        assert len(result.package.objectives) == 1
        repo.save_lesson.assert_called_once()

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
