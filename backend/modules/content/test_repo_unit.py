"""Unit tests for content module repo (unit detail with lessons)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.content.repo import ContentRepo


class TestContentRepoGetUnitDetail:
    """Test suite for ContentRepo.get_unit_detail method."""

    @pytest.mark.asyncio
    async def test_get_unit_detail_returns_unit_and_ordered_lessons(self) -> None:
        """Test get_unit_detail returns unit with ordered lessons."""
        # Arrange
        mock_session = AsyncMock()
        repo = ContentRepo(mock_session)

        unit_id = "test-unit-123"

        # Mock unit with lesson_order
        mock_unit = MagicMock()
        mock_unit.id = unit_id
        mock_unit.lesson_order = ["lesson-2", "lesson-1", "lesson-3"]

        # Mock get_unit_by_id
        repo.get_unit_by_id = AsyncMock(return_value=mock_unit)

        # Mock lessons
        mock_lesson_1 = MagicMock()
        mock_lesson_1.id = "lesson-1"
        mock_lesson_1.title = "Lesson 1"

        mock_lesson_2 = MagicMock()
        mock_lesson_2.id = "lesson-2"
        mock_lesson_2.title = "Lesson 2 (Intro)"
        mock_lesson_2.lesson_type = "intro"

        mock_lesson_3 = MagicMock()
        mock_lesson_3.id = "lesson-3"
        mock_lesson_3.title = "Lesson 3"

        # Mock get_lessons_by_unit (returns unordered)
        repo.get_lessons_by_unit = AsyncMock(return_value=[mock_lesson_1, mock_lesson_2, mock_lesson_3])

        # Act
        result = await repo.get_unit_detail(unit_id)

        # Assert
        assert result is not None
        unit, lessons = result
        assert unit.id == unit_id
        assert len(lessons) == 3

        # Verify ordering matches lesson_order
        assert lessons[0].id == "lesson-2"
        assert lessons[1].id == "lesson-1"
        assert lessons[2].id == "lesson-3"

        # Verify intro is present
        assert lessons[0].lesson_type == "intro"

    @pytest.mark.asyncio
    async def test_get_unit_detail_returns_none_if_unit_not_found(self) -> None:
        """Test get_unit_detail returns None if unit doesn't exist."""
        # Arrange
        mock_session = AsyncMock()
        repo = ContentRepo(mock_session)

        unit_id = "nonexistent-unit"
        repo.get_unit_by_id = AsyncMock(return_value=None)

        # Act
        result = await repo.get_unit_detail(unit_id)

        # Assert
        assert result is None
        repo.get_unit_by_id.assert_called_once_with(unit_id)

    @pytest.mark.asyncio
    async def test_get_unit_detail_handles_empty_lesson_order(self) -> None:
        """Test get_unit_detail handles unit with no lesson_order."""
        # Arrange
        mock_session = AsyncMock()
        repo = ContentRepo(mock_session)

        unit_id = "test-unit-empty"

        # Mock unit with no lesson_order
        mock_unit = MagicMock()
        mock_unit.id = unit_id
        mock_unit.lesson_order = None

        repo.get_unit_by_id = AsyncMock(return_value=mock_unit)

        # Mock lessons (unordered fallback)
        mock_lesson_1 = MagicMock()
        mock_lesson_1.id = "lesson-1"
        mock_lesson_1.title = "Lesson 1"

        repo.get_lessons_by_unit = AsyncMock(return_value=[mock_lesson_1])

        # Act
        result = await repo.get_unit_detail(unit_id)

        # Assert
        assert result is not None
        _, lessons = result
        assert len(lessons) == 1
        assert lessons[0].id == "lesson-1"

    @pytest.mark.asyncio
    async def test_get_unit_detail_skips_missing_lessons(self) -> None:
        """Test get_unit_detail skips lessons in order if not found in lessons list."""
        # Arrange
        mock_session = AsyncMock()
        repo = ContentRepo(mock_session)

        unit_id = "test-unit-123"

        # Mock unit with lesson_order referencing missing lesson
        mock_unit = MagicMock()
        mock_unit.id = unit_id
        mock_unit.lesson_order = ["lesson-1", "lesson-missing", "lesson-2"]

        repo.get_unit_by_id = AsyncMock(return_value=mock_unit)

        # Mock lessons (missing one)
        mock_lesson_1 = MagicMock()
        mock_lesson_1.id = "lesson-1"
        mock_lesson_1.title = "Lesson 1"

        mock_lesson_2 = MagicMock()
        mock_lesson_2.id = "lesson-2"
        mock_lesson_2.title = "Lesson 2"

        repo.get_lessons_by_unit = AsyncMock(return_value=[mock_lesson_1, mock_lesson_2])

        # Act
        result = await repo.get_unit_detail(unit_id)

        # Assert
        assert result is not None
        _, lessons = result
        assert len(lessons) == 2
        assert lessons[0].id == "lesson-1"
        assert lessons[1].id == "lesson-2"
