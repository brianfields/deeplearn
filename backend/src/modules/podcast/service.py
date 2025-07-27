"""
Podcast Service

This module provides services for creating and managing podcast episodes.
"""

import uuid

from src.core.llm_client import LLMClient
from src.core.service_base import ModuleService, ServiceConfig
from src.data_structures import PodcastEpisode, TopicResult, PodcastStructure, PodcastScript
from src.database_service import get_database_service
from .structure_service import PodcastStructureService
from .script_service import PodcastScriptService


class PodcastServiceError(Exception):
    """Exception for podcast service errors"""

    pass


class PodcastService(ModuleService):
    """Service for creating and managing podcast episodes"""

    def __init__(self, config: ServiceConfig, llm_client: LLMClient) -> None:
        super().__init__(config, llm_client)
        self.db_service = get_database_service()
        self.structure_service = PodcastStructureService(config, llm_client)
        self.script_service = PodcastScriptService(config, llm_client)

    async def initialize(self) -> None:
        """Initialize the service."""
        pass

    async def get_learning_outcomes_from_topic(self, topic_id: str) -> list[str]:
        """
        Extract learning outcomes from existing topic's refined material.

        Args:
            topic_id: ID of the topic to extract learning outcomes from

        Returns:
            List of learning outcomes suitable for 4-5 minute podcast format
        """
        if not self.db_service:
            raise PodcastServiceError("Database service not available")

        # Get topic from database
        topic = self.db_service.get_bite_sized_topic(topic_id)
        if not topic:
            raise PodcastServiceError(f"Topic {topic_id} not found")

        # Extract learning outcomes from refined material
        learning_outcomes = await self._extract_learning_outcomes_from_refined_material(topic)

        # Filter for podcast format (2-3 most important outcomes)
        podcast_outcomes = self._filter_outcomes_for_podcast(learning_outcomes)

        return podcast_outcomes

    async def _extract_learning_outcomes_from_refined_material(self, topic: TopicResult) -> list[str]:
        """
        Extract learning outcomes from topic's refined material.

        Args:
            topic: Topic data containing refined material

        Returns:
            List of learning outcomes
        """
        if not topic.refined_material:
            # Fallback to topic's learning objectives if no refined material
            return topic.learning_objectives or []

        # Extract learning objectives from refined material
        learning_outcomes = []

        # The refined_material should contain topics with learning_objectives
        if isinstance(topic.refined_material, dict) and "topics" in topic.refined_material:
            for topic_data in topic.refined_material["topics"]:
                if "learning_objectives" in topic_data:
                    learning_outcomes.extend(topic_data["learning_objectives"])

        # If no learning outcomes found in refined material, use topic's learning objectives
        if not learning_outcomes:
            learning_outcomes = topic.learning_objectives or []

        return learning_outcomes

    def _filter_outcomes_for_podcast(self, learning_outcomes: list[str]) -> list[str]:
        """
        Filter learning outcomes for 4-5 minute podcast format.

        Args:
            learning_outcomes: List of all learning outcomes

        Returns:
            List of 2-3 most important outcomes for podcast
        """
        if not learning_outcomes:
            return []

        # For MVP, take the first 2-3 outcomes
        # In the future, we could implement more sophisticated filtering
        # based on Bloom's taxonomy levels, concept importance, etc.
        return learning_outcomes[:3]

    async def generate_podcast_script(self, topic_id: str) -> PodcastScript:
        """
        Generate complete podcast script for a topic.

        Args:
            topic_id: ID of the topic to generate script for

        Returns:
            PodcastScript object with complete script
        """
        # Get topic content
        topic = self.db_service.get_bite_sized_topic(topic_id) if self.db_service else None
        if not topic:
            raise PodcastServiceError(f"Topic {topic_id} not found")

        # Plan structure (Phase 3)
        structure = await self.plan_podcast_structure(topic_id)

        # Generate script (Phase 4)
        script = await self.script_service.generate_podcast_script(
            structure, topic.content, topic_id
        )

        self.logger.info(
            f"Generated podcast script for topic {topic_id}: "
            f"{len(script.segments)} segments, {script.total_duration_seconds}s total"
        )

        return script

    async def create_podcast_from_topic(self, topic_id: str) -> PodcastEpisode:
        """
        Create complete podcast episode from topic.

        Args:
            topic_id: ID of the topic to create podcast for

        Returns:
            PodcastEpisode object with complete episode data
        """
        # Generate script (Phase 4)
        script = await self.generate_podcast_script(topic_id)

        # Save to database
        episode_id = self.db_service.save_podcast_episode(script, topic_id)

        # Return episode data
        episode_data = self.db_service.get_podcast_episode(episode_id)
        if not episode_data:
            raise PodcastServiceError(f"Failed to retrieve created episode {episode_id}")

        # Convert to PodcastEpisode model
        episode = PodcastEpisode(
            id=episode_data.id,
            title=episode_data.title,
            description=episode_data.description,
            learning_outcomes=episode_data.learning_outcomes,
            total_duration_minutes=episode_data.total_duration_minutes,
            full_script=episode_data.full_script,
            created_at=episode_data.created_at,
            updated_at=episode_data.updated_at,
            version=1
        )

        self.logger.info(
            f"Created podcast episode {episode_id} for topic {topic_id}"
        )

        return episode

    async def get_podcast_episode(self, episode_id: str) -> PodcastEpisode | None:
        """
        Get podcast episode by ID.

        Args:
            episode_id: ID of the episode to retrieve

        Returns:
            PodcastEpisode object or None if not found
        """
        episode_data = self.db_service.get_podcast_episode(episode_id)
        if not episode_data:
            return None

        # Convert to PodcastEpisode model
        episode = PodcastEpisode(
            id=episode_data.id,
            title=episode_data.title,
            description=episode_data.description,
            learning_outcomes=episode_data.learning_outcomes,
            total_duration_minutes=episode_data.total_duration_minutes,
            full_script=episode_data.full_script,
            created_at=episode_data.created_at,
            updated_at=episode_data.updated_at,
            version=1
        )

        return episode

    async def get_topic_podcast(self, topic_id: str) -> PodcastEpisode | None:
        """
        Get podcast episode for a specific topic.

        Args:
            topic_id: ID of the topic to get podcast for

        Returns:
            PodcastEpisode object or None if not found
        """
        episode_data = self.db_service.get_topic_podcast(topic_id)
        if not episode_data:
            return None

        # Convert to PodcastEpisode model
        episode = PodcastEpisode(
            id=episode_data.id,
            title=episode_data.title,
            description=episode_data.description,
            learning_outcomes=episode_data.learning_outcomes,
            total_duration_minutes=episode_data.total_duration_minutes,
            full_script=episode_data.full_script,
            created_at=episode_data.created_at,
            updated_at=episode_data.updated_at,
            version=1
        )

        return episode

    async def plan_podcast_structure(self, topic_id: str) -> PodcastStructure:
        """
        Plan podcast structure for a topic.

        Args:
            topic_id: ID of the topic to plan structure for

        Returns:
            PodcastStructure object with complete segment plans
        """
        # Get learning outcomes (from Phase 2)
        learning_outcomes = await self.get_learning_outcomes_from_topic(topic_id)

        # Get topic for title
        topic = self.db_service.get_bite_sized_topic(topic_id) if self.db_service else None
        topic_title = topic.title if topic else "Educational Topic"

        # Plan structure using outcomes
        structure = await self.structure_service.plan_podcast_structure(
            learning_outcomes, topic_title
        )

        # Validate structure
        if not await self.structure_service.validate_structure(structure):
            raise PodcastServiceError("Invalid podcast structure generated")

        self.logger.info(
            f"Planned podcast structure for topic {topic_id}: {structure.total_duration_seconds}s total"
        )

        return structure

    def _create_episode_id(self) -> str:
        """Create a new episode ID"""
        return str(uuid.uuid4())

    def _create_segment_id(self) -> str:
        """Create a new segment ID"""
        return str(uuid.uuid4())

    def _create_link_id(self) -> str:
        """Create a new topic-podcast link ID"""
        return str(uuid.uuid4())
