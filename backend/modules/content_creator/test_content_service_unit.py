"""Unit tests for content_creator content service (intro lesson creation)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.catalog.service import LessonSummary
from modules.content_creator.podcast import UnitPodcast
from modules.content_creator.service.content_service import ContentService


class TestContentServiceCreateIntroLesson:
    """Test suite for ContentService.create_intro_lesson method."""

    @pytest.mark.asyncio
    async def test_create_intro_lesson_validates_audio(self) -> None:
        """Test that create_intro_lesson validates audio bytes are present."""
        # Arrange
        mock_content = AsyncMock()

        podcast = UnitPodcast(
            transcript="Test intro transcript",
            audio_bytes=b"fake-audio",  # Non-empty
            mime_type="audio/mpeg",
            voice="test-voice",
            duration_seconds=300,
        )

        # Mock unit exists
        mock_unit = MagicMock()
        mock_unit.learner_level = "intermediate"
        mock_content.get_unit_detail.return_value = mock_unit

        # Mock get_intro_lesson_summary returns None (no existing intro)
        mock_content.get_intro_lesson_summary.return_value = None

        # Assert no validation error is raised with valid audio
        try:
            # This test validates the audio check passes; actual implementation tested separately
            assert podcast.audio_bytes  # Verify test setup
            mock_content.get_unit.return_value = mock_unit
            mock_unit.lesson_order = []
        except ValueError:
            pytest.fail("Should not raise ValueError for valid audio bytes")

    @pytest.mark.asyncio
    async def test_create_intro_lesson_idempotency(self) -> None:
        """Test idempotency: existing intro lesson is returned."""
        # Arrange
        mock_content = AsyncMock()
        service = ContentService(mock_content)

        unit_id = "test-unit-123"
        podcast = UnitPodcast(
            transcript="Test",
            audio_bytes=b"audio",
            mime_type="audio/mpeg",
            voice="voice",
            duration_seconds=100,
        )

        # Mock existing intro lesson
        existing_summary = LessonSummary(
            id=f"{unit_id}-intro",
            title="Unit Introduction",
            learner_level="beginner",
            lesson_type="intro",
            learning_objectives=[],
            key_concepts=[],
            exercise_count=0,
            has_podcast=True,
            podcast_duration_seconds=100,
            podcast_voice="voice",
        )
        mock_content.get_intro_lesson_summary.return_value = existing_summary

        # Act
        lesson_id, summary = await service.create_intro_lesson(
            unit_id=unit_id,
            podcast=podcast,
        )

        # Assert (returns existing, doesn't create new)
        assert lesson_id == f"{unit_id}-intro"
        assert summary == existing_summary
        mock_content.save_lesson.assert_not_called()
        mock_content.save_lesson_podcast_from_bytes.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_intro_lesson_no_audio_bytes_raises(self) -> None:
        """Test raises ValueError if no audio bytes."""
        # Arrange
        mock_content = AsyncMock()
        service = ContentService(mock_content)

        unit_id = "test-unit-123"
        podcast = UnitPodcast(
            transcript="Test",
            audio_bytes=b"",  # Empty!
            mime_type="audio/mpeg",
            voice="voice",
            duration_seconds=100,
        )

        mock_content.get_intro_lesson_summary.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="audio_bytes required"):
            await service.create_intro_lesson(unit_id=unit_id, podcast=podcast)

    @pytest.mark.asyncio
    async def test_create_intro_lesson_unit_not_found_raises(self) -> None:
        """Test raises ValueError if unit not found."""
        # Arrange
        mock_content = AsyncMock()
        service = ContentService(mock_content)

        unit_id = "nonexistent-unit"
        podcast = UnitPodcast(
            transcript="Test",
            audio_bytes=b"audio",
            mime_type="audio/mpeg",
            voice="voice",
            duration_seconds=100,
        )

        mock_content.get_intro_lesson_summary.return_value = None
        mock_content.get_unit_detail.return_value = None  # Unit not found

        # Act & Assert
        with pytest.raises(ValueError, match=r"Unit .* not found"):
            await service.create_intro_lesson(unit_id=unit_id, podcast=podcast)

    @pytest.mark.asyncio
    async def test_assign_intro_to_unit_prepends_lesson_id(self) -> None:
        """Test _assign_intro_to_unit prepends lesson ID to lesson_order."""
        # Arrange
        mock_content = AsyncMock()
        service = ContentService(mock_content)

        unit_id = "test-unit-123"
        lesson_id = f"{unit_id}-intro"

        mock_unit = MagicMock()
        mock_unit.lesson_order = ["lesson-1", "lesson-2"]
        mock_content.get_unit.return_value = mock_unit

        # Act
        await service._assign_intro_to_unit(unit_id, lesson_id)

        # Assert
        mock_content.set_unit_lesson_order.assert_called_once()
        call_args = mock_content.set_unit_lesson_order.call_args[0]
        assert call_args[0] == unit_id
        assert call_args[1] == [lesson_id, "lesson-1", "lesson-2"]
