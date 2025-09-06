"""
Topic Catalog Domain Entities.

Simple entities that represent topics for browsing and discovery.
These mirror the existing database structure without over-engineering.
"""

from datetime import datetime
from typing import Any


class TopicSummary:
    """
    A topic summary for browsing and discovery.

    This is a simple representation of a topic optimized for listing
    and basic filtering. Maps directly to the existing BiteSizedTopic structure.
    """

    def __init__(
        self,
        id: str,
        title: str,
        core_concept: str,
        user_level: str,
        learning_objectives: list[str],
        key_concepts: list[str],
        created_at: datetime,
        component_count: int = 0,
    ):
        """Initialize a topic summary."""
        self.id = id
        self.title = title
        self.core_concept = core_concept
        self.user_level = user_level
        self.learning_objectives = learning_objectives or []
        self.key_concepts = key_concepts or []
        self.created_at = created_at
        self.component_count = component_count

    def matches_user_level(self, user_level: str) -> bool:
        """Check if topic matches the specified user level."""
        return self.user_level == user_level


class TopicDetail:
    """
    Detailed topic information including components.

    Used when retrieving a specific topic for learning.
    """

    def __init__(
        self,
        id: str,
        title: str,
        core_concept: str,
        user_level: str,
        learning_objectives: list[str],
        key_concepts: list[str],
        key_aspects: list[str],
        target_insights: list[str],
        source_material: str | None,
        refined_material: dict[str, Any] | None,
        created_at: datetime,
        updated_at: datetime,
        components: list[dict[str, Any]] | None = None,
    ):
        """Initialize topic details."""
        self.id = id
        self.title = title
        self.core_concept = core_concept
        self.user_level = user_level
        self.learning_objectives = learning_objectives or []
        self.key_concepts = key_concepts or []
        self.key_aspects = key_aspects or []
        self.target_insights = target_insights or []
        self.source_material = source_material
        self.refined_material = refined_material
        self.created_at = created_at
        self.updated_at = updated_at
        self.components = components or []

    @property
    def component_count(self) -> int:
        """Get the number of components in this topic."""
        return len(self.components)

    def is_ready_for_learning(self) -> bool:
        """Check if topic has components and is ready for learning."""
        return self.component_count > 0
