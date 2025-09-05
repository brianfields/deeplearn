"""
Topic domain entity for content creation.

This module contains the core business logic for educational topics.
"""

from datetime import UTC, datetime
from typing import Any
import uuid

from .component import Component


class TopicError(Exception):
    """Base exception for topic-related errors"""

    pass


class InvalidTopicError(TopicError):
    """Raised when topic validation fails"""

    pass


class Topic:
    """
    Domain entity representing an educational topic.

    Contains business logic for topic management, validation, and component organization.
    """

    def __init__(
        self,
        title: str,
        core_concept: str,
        user_level: str,
        topic_id: str | None = None,
        learning_objectives: list[str] | None = None,
        key_concepts: list[str] | None = None,
        key_aspects: list[str] | None = None,
        target_insights: list[str] | None = None,
        common_misconceptions: list[str] | None = None,
        previous_topics: list[str] | None = None,
        source_material: str | None = None,
        source_domain: str | None = None,
        refined_material: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        version: int = 1,
    ):
        """
        Initialize a Topic entity.

        Args:
            title: The topic title
            core_concept: The main concept being taught
            user_level: Target user level (beginner, intermediate, advanced)
            topic_id: Unique identifier (generated if not provided)
            learning_objectives: List of learning objectives
            key_concepts: List of key concepts
            key_aspects: List of key aspects to cover
            target_insights: List of insights students should gain
            common_misconceptions: List of common misconceptions to address
            previous_topics: List of prerequisite topics
            source_material: Original source material
            source_domain: Domain of the source material
            refined_material: Structured extraction from source material
            created_at: Creation timestamp
            updated_at: Last update timestamp
            version: Version number for optimistic locking
        """
        self.id = topic_id or str(uuid.uuid4())
        self.title = title
        self.core_concept = core_concept
        self.user_level = user_level
        self.learning_objectives = learning_objectives or []
        self.key_concepts = key_concepts or []
        self.key_aspects = key_aspects or []
        self.target_insights = target_insights or []
        self.common_misconceptions = common_misconceptions or []
        self.previous_topics = previous_topics or []
        self.source_material = source_material
        self.source_domain = source_domain
        self.refined_material = refined_material or {}
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)
        self.version = version
        self._components: list[Component] = []

        # Validate on creation
        self.validate()

    def validate(self) -> None:
        """
        Validate topic business rules.

        Raises:
            InvalidTopicError: If validation fails
        """
        if not self.title or not self.title.strip():
            raise InvalidTopicError("Topic title cannot be empty")

        if not self.core_concept or not self.core_concept.strip():
            raise InvalidTopicError("Core concept cannot be empty")

        if self.user_level not in ["beginner", "intermediate", "advanced"]:
            raise InvalidTopicError("User level must be beginner, intermediate, or advanced")

        if len(self.title) > 200:
            raise InvalidTopicError("Topic title cannot exceed 200 characters")

        if len(self.core_concept) > 500:
            raise InvalidTopicError("Core concept cannot exceed 500 characters")

    def add_component(self, component: Component) -> None:
        """
        Add a component to this topic.

        Args:
            component: The component to add

        Raises:
            InvalidTopicError: If component is invalid for this topic
        """
        if component.topic_id != self.id:
            raise InvalidTopicError("Component topic_id must match this topic's id")

        # Check for duplicate component types with same learning objective
        for existing in self._components:
            if existing.component_type == component.component_type and existing.learning_objective == component.learning_objective:
                raise InvalidTopicError(f"Component of type {component.component_type} with learning objective '{component.learning_objective}' already exists")

        self._components.append(component)
        self.updated_at = datetime.now(UTC)

    def remove_component(self, component_id: str) -> bool:
        """
        Remove a component from this topic.

        Args:
            component_id: ID of the component to remove

        Returns:
            True if component was removed, False if not found
        """
        for i, component in enumerate(self._components):
            if component.id == component_id:
                self._components.pop(i)
                self.updated_at = datetime.now(UTC)
                return True
        return False

    def get_component(self, component_id: str) -> Component | None:
        """
        Get a component by ID.

        Args:
            component_id: ID of the component

        Returns:
            Component if found, None otherwise
        """
        for component in self._components:
            if component.id == component_id:
                return component
        return None

    def get_components(self) -> list[Component]:
        """Get all components for this topic."""
        return self._components.copy()

    def get_components_by_type(self, component_type: str) -> list[Component]:
        """
        Get all components of a specific type.

        Args:
            component_type: Type of components to retrieve

        Returns:
            List of components of the specified type
        """
        return [c for c in self._components if c.component_type == component_type]

    def set_refined_material(self, refined_material: dict[str, Any]) -> None:
        """
        Set the refined material for this topic.

        Args:
            refined_material: Structured material extracted from source
        """
        self.refined_material = refined_material
        self.updated_at = datetime.now(UTC)

        # Extract learning objectives and key concepts if available
        if "topics" in refined_material and isinstance(refined_material["topics"], list):
            all_objectives = []
            all_concepts = []

            for topic_data in refined_material["topics"]:
                if "learning_objectives" in topic_data:
                    all_objectives.extend(topic_data["learning_objectives"])
                if "key_facts" in topic_data:
                    all_concepts.extend(topic_data["key_facts"])

            if all_objectives and not self.learning_objectives:
                self.learning_objectives = all_objectives
            if all_concepts and not self.key_concepts:
                self.key_concepts = all_concepts

    def calculate_completion_percentage(self) -> float:
        """
        Calculate the completion percentage based on components.

        Returns:
            Percentage of completion (0.0 to 100.0)
        """
        if not self.learning_objectives:
            return 0.0

        # Count components that address learning objectives
        addressed_objectives = set()
        for component in self._components:
            if component.learning_objective:
                addressed_objectives.add(component.learning_objective)

        if not self.learning_objectives:
            return 100.0 if self._components else 0.0

        return (len(addressed_objectives) / len(self.learning_objectives)) * 100.0

    def is_ready_for_learning(self) -> bool:
        """
        Check if topic has enough content for learning.

        Returns:
            True if topic is ready for learning sessions
        """
        # Must have at least one component and some learning objectives
        return len(self._components) > 0 and len(self.learning_objectives) > 0

    def update_metadata(
        self,
        title: str | None = None,
        core_concept: str | None = None,
        user_level: str | None = None,
        learning_objectives: list[str] | None = None,
        key_concepts: list[str] | None = None,
    ) -> None:
        """
        Update topic metadata.

        Args:
            title: New title (optional)
            core_concept: New core concept (optional)
            user_level: New user level (optional)
            learning_objectives: New learning objectives (optional)
            key_concepts: New key concepts (optional)
        """
        if title is not None:
            self.title = title
        if core_concept is not None:
            self.core_concept = core_concept
        if user_level is not None:
            self.user_level = user_level
        if learning_objectives is not None:
            self.learning_objectives = learning_objectives
        if key_concepts is not None:
            self.key_concepts = key_concepts

        self.updated_at = datetime.now(UTC)
        self.validate()

    def to_dict(self) -> dict[str, Any]:
        """Convert topic to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "core_concept": self.core_concept,
            "user_level": self.user_level,
            "learning_objectives": self.learning_objectives,
            "key_concepts": self.key_concepts,
            "key_aspects": self.key_aspects,
            "target_insights": self.target_insights,
            "common_misconceptions": self.common_misconceptions,
            "previous_topics": self.previous_topics,
            "source_material": self.source_material,
            "source_domain": self.source_domain,
            "refined_material": self.refined_material,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "components": [c.to_dict() for c in self._components],
            "completion_percentage": self.calculate_completion_percentage(),
            "is_ready_for_learning": self.is_ready_for_learning(),
        }

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Topic):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation."""
        return f"Topic(id='{self.id}', title='{self.title}', core_concept='{self.core_concept}')"
