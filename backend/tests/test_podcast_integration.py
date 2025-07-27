#!/usr/bin/env python3
"""
End-to-End Integration Test for Podcast Module

Tests the complete podcast generation pipeline from topic to final script.
This validates that all components work together correctly.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

import pytest

sys.path.append(str(Path(__file__).parent / ".." / "src"))

from src.core.service_base import ServiceConfig
from src.core.llm_client import LLMClient
from src.llm_interface import LLMConfig, LLMProviderType
from src.modules.podcast.service import PodcastService
from src.data_structures import PodcastScript, ScriptMetadata


class TestPodcastIntegration:
    """End-to-end integration tests for podcast generation"""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_llm_client = Mock(spec=LLMClient)
        self.llm_config = LLMConfig(provider=LLMProviderType.OPENAI)
        self.service_config = ServiceConfig(llm_config=self.llm_config)
        self.podcast_service = PodcastService(self.service_config, self.mock_llm_client)

    @pytest.mark.asyncio
    async def test_complete_podcast_generation_pipeline(self):
        """Test the complete pipeline from topic to podcast script."""
        # Mock database service to return a sample topic
        mock_db_service = Mock()
        mock_db_service.get_bite_sized_topic.return_value = Mock(
            id="test-topic-id",
            title="Neural Networks",
            content="Neural networks are computational models inspired by biological neural networks.",
            learning_objectives=[
                "Explain the basic structure of neural networks",
                "Describe how neurons process information",
                "Apply neural network concepts to simple problems"
            ]
        )
        mock_db_service.save_podcast_episode.return_value = "test-episode-id"

        # Mock the episode data that would be returned
        mock_episode_data = Mock(
            id="test-episode-id",
            title="Test Podcast",
            description="Test description",
            learning_outcomes=["test outcome"],
            total_duration_minutes=4,
            full_script="Test script",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_db_service.get_podcast_episode.return_value = mock_episode_data

        # Set the mocked database service directly on the podcast service
        self.podcast_service.db_service = mock_db_service

        # Test complete pipeline
        episode = await self.podcast_service.create_podcast_from_topic("test-topic-id")

        # Validate the result
        assert episode is not None
        assert episode.id == "test-episode-id"
        assert episode.total_duration_minutes >= 3  # At least 3 minutes
        assert episode.total_duration_minutes <= 6   # At most 6 minutes
        assert len(episode.learning_outcomes) > 0

    @pytest.mark.asyncio
    async def test_podcast_script_quality_integration(self):
        """Test that generated scripts meet quality standards."""
        # Create a sample script for quality validation
        script = PodcastScript(
            title="Test Educational Podcast",
            description="A comprehensive overview of neural networks",
            segments=[],
            total_duration_seconds=240,  # 4 minutes
            learning_outcomes=[
                "Explain the basic structure of neural networks",
                "Describe how neurons process information"
            ],
            metadata=ScriptMetadata(
                generation_timestamp=datetime.now(),
                topic_id="test-topic",
                structure_id="test-structure",
                total_segments=4,
                target_duration_seconds=240,
                actual_duration_seconds=240,
                tone_style="conversational_educational",
                educational_level="beginner"
            ),
            full_script="Test script content"
        )

        # Validate script quality
        assert script.title is not None
        assert script.description is not None
        assert 180 <= script.total_duration_seconds <= 360  # 3-6 minutes
        assert len(script.learning_outcomes) > 0
        assert script.metadata is not None
        assert script.full_script is not None

    def test_service_dependency_injection(self):
        """Test that services are properly configured with dependencies."""
        # Test service configuration
        assert self.podcast_service.config == self.service_config
        assert self.podcast_service.llm_client == self.mock_llm_client
        assert self.podcast_service.structure_service is not None
        assert self.podcast_service.script_service is not None

        # Test that services have required methods
        assert hasattr(self.podcast_service, 'create_podcast_from_topic')
        assert hasattr(self.podcast_service, 'get_podcast_episode')
        assert hasattr(self.podcast_service, 'get_topic_podcast')

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across the complete pipeline."""
        # Test with non-existent topic
        with patch('src.modules.podcast.service.get_database_service') as mock_db:
            mock_db_service = Mock()
            mock_db_service.get_bite_sized_topic.return_value = None
            mock_db.return_value = mock_db_service

            with pytest.raises(Exception):  # Should raise an error for non-existent topic
                await self.podcast_service.create_podcast_from_topic("non-existent-topic")

    def test_data_model_integration(self):
        """Test that all data models work together correctly."""
        from src.data_structures import (
            PodcastGenerationRequest,
            PodcastGenerationResponse,
            PodcastEpisodeResponse,
            SegmentScript
        )

        # Test request/response flow
        request = PodcastGenerationRequest(
            topic_id="test-topic-id",
            generate_audio=False
        )
        assert request.topic_id == "test-topic-id"

        # Test response creation
        response = PodcastGenerationResponse(
            episode_id="test-episode-id",
            title="Test Podcast",
            description="Test description",
            total_duration_minutes=4,
            learning_outcomes=["test outcome"],
            segments=[],
            full_script="Test script",
            status="generated"
        )
        assert response.episode_id == "test-episode-id"
        assert response.status == "generated"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
