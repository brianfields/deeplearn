"""
Lesson Catalog Module - Unit Tests

Tests for the lesson catalog service layer.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

from modules.lesson_catalog.service import LessonCatalogService


class TestLessonCatalogService:
    """Unit tests for LessonCatalogService."""

    def test_browse_lessons_returns_summaries(self):
        """Test that browse_lessons returns lesson summaries."""
        # Arrange
        content = Mock()

        # Mock lessons from content module
        from modules.content.service import LessonComponentRead, LessonRead

        mock_lessons = [
            LessonRead(
                id="lesson-1",
                title="Lesson 1",
                core_concept="Concept 1",
                user_level="beginner",
                learning_objectives=["Learn A"],
                key_concepts=["Key A"],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                components=[LessonComponentRead(id="comp-1", lesson_id="lesson-1", component_type="mcq", title="MCQ 1", content={"question": "What is A?"}, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))],
            ),
            LessonRead(id="lesson-2", title="Lesson 2", core_concept="Concept 2", user_level="intermediate", learning_objectives=["Learn B"], key_concepts=["Key B"], created_at=datetime.now(UTC), updated_at=datetime.now(UTC), components=[]),
        ]

        content.search_lessons.return_value = mock_lessons
        service = LessonCatalogService(content)

        # Act
        result = service.browse_lessons(user_level="beginner", limit=10)

        # Assert
        assert len(result.lessons) == 2
        assert result.total == 2
        assert result.lessons[0].id == "lesson-1"
        assert result.lessons[0].component_count == 1
        assert result.lessons[1].component_count == 0

        content.search_lessons.assert_called_once_with(user_level="beginner", limit=10)

    def test_get_lesson_details_returns_details(self):
        """Test that get_lesson_details returns lesson details."""
        # Arrange
        content = Mock()

        from modules.content.service import LessonComponentRead, LessonRead

        mock_lesson = LessonRead(
            id="lesson-1",
            title="Lesson 1",
            core_concept="Concept 1",
            user_level="beginner",
            learning_objectives=["Learn A"],
            key_concepts=["Key A"],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            components=[LessonComponentRead(id="comp-1", lesson_id="lesson-1", component_type="mcq", title="MCQ 1", content={"question": "What is A?"}, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))],
        )

        content.get_lesson.return_value = mock_lesson
        service = LessonCatalogService(content)

        # Act
        result = service.get_lesson_details("lesson-1")

        # Assert
        assert result is not None
        assert result.id == "lesson-1"
        assert result.title == "Lesson 1"
        assert result.component_count == 1
        assert len(result.components) == 1
        assert result.is_ready_for_learning() is True

        content.get_lesson.assert_called_once_with("lesson-1")

    def test_get_lesson_details_returns_none_when_not_found(self):
        """Test that get_lesson_details returns None when lesson doesn't exist."""
        # Arrange
        content = Mock()
        content.get_lesson.return_value = None
        service = LessonCatalogService(content)

        # Act
        result = service.get_lesson_details("nonexistent")

        # Assert
        assert result is None
        content.get_lesson.assert_called_once_with("nonexistent")

    def test_lesson_summary_matches_user_level(self):
        """Test LessonSummary.matches_user_level method."""
        # Arrange
        from modules.lesson_catalog.service import LessonSummary

        summary = LessonSummary(id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Key X"], component_count=1)

        # Act & Assert
        assert summary.matches_user_level("beginner") is True
        assert summary.matches_user_level("intermediate") is False

    def test_lesson_detail_is_ready_for_learning(self):
        """Test LessonDetail.is_ready_for_learning method."""
        # Arrange
        from modules.lesson_catalog.service import LessonDetail

        # Lesson with components
        detail_with_components = LessonDetail(
            id="test-id",
            title="Test Lesson",
            core_concept="Test Concept",
            user_level="beginner",
            learning_objectives=["Learn X"],
            key_concepts=["Key X"],
            components=[{"type": "mcq", "content": "test"}],
            created_at="2024-01-01T00:00:00",
            component_count=1,
        )

        # Lesson without components
        detail_without_components = LessonDetail(
            id="test-id-2", title="Test Lesson 2", core_concept="Test Concept 2", user_level="beginner", learning_objectives=["Learn Y"], key_concepts=["Key Y"], components=[], created_at="2024-01-01T00:00:00", component_count=0
        )

        # Act & Assert
        assert detail_with_components.is_ready_for_learning() is True
        assert detail_without_components.is_ready_for_learning() is False

    def test_search_lessons_with_query(self):
        """Test that search_lessons filters by query."""
        # Arrange
        content = Mock()

        from modules.content.service import LessonComponentRead, LessonRead

        mock_lessons = [
            LessonRead(
                id="lesson-1",
                title="React Basics",
                core_concept="Components",
                user_level="beginner",
                learning_objectives=["Learn React"],
                key_concepts=["JSX", "Props"],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                components=[LessonComponentRead(id="comp-1", lesson_id="lesson-1", component_type="mcq", title="MCQ 1", content={}, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))],
            ),
            LessonRead(
                id="lesson-2",
                title="Python Basics",
                core_concept="Variables",
                user_level="beginner",
                learning_objectives=["Learn Python"],
                key_concepts=["Variables", "Functions"],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                components=[],
            ),
        ]

        content.search_lessons.return_value = mock_lessons
        service = LessonCatalogService(content)

        # Act
        result = service.search_lessons(query="react", limit=10)

        # Assert
        assert len(result.lessons) == 1
        assert result.lessons[0].title == "React Basics"
        assert result.query == "react"

    def test_get_catalog_statistics(self):
        """Test that get_catalog_statistics returns statistics."""
        # Arrange
        content = Mock()

        from modules.content.service import LessonComponentRead, LessonRead

        mock_lessons = [
            LessonRead(
                id="lesson-1",
                title="Lesson 1",
                core_concept="Concept",
                user_level="beginner",
                learning_objectives=["Learn"],
                key_concepts=["Key"],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                components=[LessonComponentRead(id="comp-1", lesson_id="lesson-1", component_type="mcq", title="MCQ 1", content={}, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))],
            ),
            LessonRead(
                id="lesson-2",
                title="Lesson 2",
                core_concept="Concept",
                user_level="intermediate",
                learning_objectives=["Learn"],
                key_concepts=["Key"],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                components=[],
            ),
        ]

        content.search_lessons.return_value = mock_lessons
        service = LessonCatalogService(content)

        # Act
        result = service.get_catalog_statistics()

        # Assert
        assert result.total_lessons == 2
        assert result.lessons_by_user_level["beginner"] == 1
        assert result.lessons_by_user_level["intermediate"] == 1
        assert result.lessons_by_readiness["ready"] == 1
        assert result.lessons_by_readiness["draft"] == 1
