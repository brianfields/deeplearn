"""
TopicSummary domain entity for topic catalog.

This module contains the lightweight topic representation used in catalog browsing.
"""

from datetime import UTC, datetime
from typing import Any


class TopicSummaryError(Exception):
    """Base exception for topic summary errors"""

    pass


class InvalidTopicSummaryError(TopicSummaryError):
    """Raised when topic summary validation fails"""

    pass


class TopicSummary:
    """
    Domain entity representing a lightweight topic summary for catalog browsing.

    This is a read-only representation optimized for discovery and browsing,
    containing only the essential information needed for topic selection.
    """

    def __init__(
        self,
        topic_id: str,
        title: str,
        core_concept: str,
        user_level: str,
        learning_objectives: list[str] | None = None,
        key_concepts: list[str] | None = None,
        estimated_duration: int = 15,
        component_count: int = 0,
        is_ready_for_learning: bool = False,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """
        Initialize a TopicSummary entity.

        Args:
            topic_id: Unique identifier of the topic
            title: Topic title
            core_concept: Core concept being taught
            user_level: Target user level
            learning_objectives: List of learning objectives
            key_concepts: List of key concepts
            estimated_duration: Estimated completion time in minutes
            component_count: Number of components in the topic
            is_ready_for_learning: Whether topic is ready for learning sessions
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.topic_id = topic_id
        self.title = title
        self.core_concept = core_concept
        self.user_level = user_level
        self.learning_objectives = learning_objectives or []
        self.key_concepts = key_concepts or []
        self.estimated_duration = estimated_duration
        self.component_count = component_count
        self.is_ready_for_learning = is_ready_for_learning
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)

        # Validate on creation
        self.validate()

    def validate(self) -> None:
        """
        Validate topic summary business rules.

        Raises:
            InvalidTopicSummaryError: If validation fails
        """
        if not self.topic_id or not self.topic_id.strip():
            raise InvalidTopicSummaryError("Topic ID cannot be empty")

        if not self.title or not self.title.strip():
            raise InvalidTopicSummaryError("Topic title cannot be empty")

        if not self.core_concept or not self.core_concept.strip():
            raise InvalidTopicSummaryError("Core concept cannot be empty")

        if self.user_level not in ["beginner", "intermediate", "advanced"]:
            raise InvalidTopicSummaryError("User level must be beginner, intermediate, or advanced")

        if len(self.title) > 200:
            raise InvalidTopicSummaryError("Topic title cannot exceed 200 characters")

        if len(self.core_concept) > 500:
            raise InvalidTopicSummaryError("Core concept cannot exceed 500 characters")

        if self.estimated_duration < 0:
            raise InvalidTopicSummaryError("Estimated duration cannot be negative")

        if self.component_count < 0:
            raise InvalidTopicSummaryError("Component count cannot be negative")

    def get_difficulty_level(self) -> str:
        """
        Get a human-readable difficulty level.

        Returns:
            Difficulty level string
        """
        level_map = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}
        return level_map.get(self.user_level, "Unknown")

    def get_duration_display(self) -> str:
        """
        Get a human-readable duration display.

        Returns:
            Duration string (e.g., "15 min", "1 hr 30 min")
        """
        if self.estimated_duration < 60:
            return f"{self.estimated_duration} min"
        else:
            hours = self.estimated_duration // 60
            minutes = self.estimated_duration % 60
            if minutes == 0:
                return f"{hours} hr"
            else:
                return f"{hours} hr {minutes} min"

    def get_readiness_status(self) -> str:
        """
        Get the readiness status for display.

        Returns:
            Status string
        """
        if self.is_ready_for_learning:
            return "Ready"
        elif self.component_count > 0:
            return "In Progress"
        else:
            return "Draft"

    def has_learning_objectives(self) -> bool:
        """Check if topic has learning objectives."""
        return len(self.learning_objectives) > 0

    def has_key_concepts(self) -> bool:
        """Check if topic has key concepts."""
        return len(self.key_concepts) > 0

    def matches_query(self, query: str) -> bool:
        """
        Check if topic matches a search query.

        Args:
            query: Search query string

        Returns:
            True if topic matches the query
        """
        if not query or not query.strip():
            return True

        query_lower = query.lower().strip()
        return query_lower in self.title.lower() or query_lower in self.core_concept.lower() or any(query_lower in concept.lower() for concept in self.key_concepts) or any(query_lower in obj.lower() for obj in self.learning_objectives)

    def is_suitable_for_user_level(self, user_level: str) -> bool:
        """
        Check if topic is suitable for a user level.

        Args:
            user_level: User's skill level

        Returns:
            True if topic is suitable
        """
        level_hierarchy = {"beginner": 1, "intermediate": 2, "advanced": 3}
        topic_level = level_hierarchy.get(self.user_level, 2)
        user_level_num = level_hierarchy.get(user_level, 2)

        # Allow topics at or below user's level
        return topic_level <= user_level_num

    def get_tags(self) -> list[str]:
        """
        Get display tags for the topic.

        Returns:
            List of tags for UI display
        """
        tags = []

        # Add user level tag
        tags.append(self.get_difficulty_level())

        # Add duration tag
        tags.append(self.get_duration_display())

        # Add readiness tag
        tags.append(self.get_readiness_status())

        # Add component count if available
        if self.component_count > 0:
            tags.append(f"{self.component_count} components")

        return tags

    def to_dict(self) -> dict[str, Any]:
        """Convert topic summary to dictionary representation."""
        return {
            "id": self.topic_id,
            "title": self.title,
            "core_concept": self.core_concept,
            "user_level": self.user_level,
            "learning_objectives": self.learning_objectives,
            "key_concepts": self.key_concepts,
            "estimated_duration": self.estimated_duration,
            "component_count": self.component_count,
            "is_ready_for_learning": self.is_ready_for_learning,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "difficulty_level": self.get_difficulty_level(),
            "duration_display": self.get_duration_display(),
            "readiness_status": self.get_readiness_status(),
            "tags": self.get_tags(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TopicSummary":
        """
        Create TopicSummary from dictionary representation.

        Args:
            data: Dictionary containing topic summary data

        Returns:
            TopicSummary instance
        """
        created_at = None
        updated_at = None

        if "created_at" in data:
            created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        if "updated_at" in data:
            updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))

        return cls(
            topic_id=data["id"],
            title=data["title"],
            core_concept=data["core_concept"],
            user_level=data["user_level"],
            learning_objectives=data.get("learning_objectives", []),
            key_concepts=data.get("key_concepts", []),
            estimated_duration=data.get("estimated_duration", 15),
            component_count=data.get("component_count", 0),
            is_ready_for_learning=data.get("is_ready_for_learning", False),
            created_at=created_at,
            updated_at=updated_at,
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, TopicSummary):
            return False
        return self.topic_id == other.topic_id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.topic_id)

    def __repr__(self) -> str:
        """String representation."""
        return f"TopicSummary(id='{self.topic_id}', title='{self.title}', level='{self.user_level}')"
