"""
Topic repository interface for content creation domain.

This module defines the abstract interface for topic persistence.
"""

from abc import ABC, abstractmethod

from ..entities.component import Component
from ..entities.topic import Topic


class TopicRepositoryError(Exception):
    """Base exception for topic repository errors"""

    pass


class TopicNotFoundError(TopicRepositoryError):
    """Raised when a topic is not found"""

    pass


class TopicRepository(ABC):
    """
    Abstract repository interface for topic persistence.

    This interface defines the contract for topic storage and retrieval,
    allowing the domain layer to remain independent of specific storage implementations.
    """

    @abstractmethod
    async def save(self, topic: Topic) -> Topic:
        """
        Save a topic to persistent storage.

        Args:
            topic: Topic to save

        Returns:
            Saved topic with updated metadata

        Raises:
            TopicRepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, topic_id: str) -> Topic:
        """
        Retrieve a topic by its ID.

        Args:
            topic_id: Unique identifier of the topic

        Returns:
            Topic instance

        Raises:
            TopicNotFoundError: If topic is not found
            TopicRepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> list[Topic]:
        """
        Retrieve all topics with pagination.

        Args:
            limit: Maximum number of topics to return
            offset: Number of topics to skip

        Returns:
            List of topics

        Raises:
            TopicRepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
    async def search(self, query: str | None = None, user_level: str | None = None, has_components: bool | None = None, limit: int = 100, offset: int = 0) -> list[Topic]:
        """
        Search topics by criteria.

        Args:
            query: Text query to search in title/core_concept
            user_level: Filter by user level
            has_components: Filter by whether topic has components
            limit: Maximum number of topics to return
            offset: Number of topics to skip

        Returns:
            List of matching topics

        Raises:
            TopicRepositoryError: If search fails
        """
        pass

    @abstractmethod
    async def delete(self, topic_id: str) -> bool:
        """
        Delete a topic by its ID.

        Args:
            topic_id: Unique identifier of the topic

        Returns:
            True if topic was deleted, False if not found

        Raises:
            TopicRepositoryError: If deletion fails
        """
        pass

    @abstractmethod
    async def exists(self, topic_id: str) -> bool:
        """
        Check if a topic exists.

        Args:
            topic_id: Unique identifier of the topic

        Returns:
            True if topic exists, False otherwise

        Raises:
            TopicRepositoryError: If check fails
        """
        pass

    @abstractmethod
    async def save_component(self, component: Component) -> Component:
        """
        Save a component to persistent storage.

        Args:
            component: Component to save

        Returns:
            Saved component with updated metadata

        Raises:
            TopicRepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    async def get_component_by_id(self, component_id: str) -> Component:
        """
        Retrieve a component by its ID.

        Args:
            component_id: Unique identifier of the component

        Returns:
            Component instance

        Raises:
            TopicNotFoundError: If component is not found
            TopicRepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_components_by_topic_id(self, topic_id: str) -> list[Component]:
        """
        Retrieve all components for a topic.

        Args:
            topic_id: Unique identifier of the topic

        Returns:
            List of components for the topic

        Raises:
            TopicRepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
    async def delete_component(self, component_id: str) -> bool:
        """
        Delete a component by its ID.

        Args:
            component_id: Unique identifier of the component

        Returns:
            True if component was deleted, False if not found

        Raises:
            TopicRepositoryError: If deletion fails
        """
        pass

    @abstractmethod
    async def get_topics_by_user_level(self, user_level: str) -> list[Topic]:
        """
        Get all topics for a specific user level.

        Args:
            user_level: User level to filter by

        Returns:
            List of topics for the user level

        Raises:
            TopicRepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_topics_ready_for_learning(self) -> list[Topic]:
        """
        Get all topics that are ready for learning sessions.

        Returns:
            List of topics ready for learning

        Raises:
            TopicRepositoryError: If retrieval fails
        """
        pass
