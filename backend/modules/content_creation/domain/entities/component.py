"""
Component domain entity for content creation.

This module contains the core business logic for educational content components.
"""

from datetime import UTC, datetime
from typing import Any
import uuid


class ComponentError(Exception):
    """Base exception for component-related errors"""

    pass


class InvalidComponentError(ComponentError):
    """Raised when component validation fails"""

    pass


class Component:
    """
    Domain entity representing an educational content component.

    Components are individual pieces of content within a topic (e.g., MCQs, explanations, exercises).
    """

    # Valid component types
    VALID_TYPES = {"mcq", "didactic_snippet", "glossary", "short_answer", "scenario_critique", "explanation", "exercise"}

    def __init__(
        self,
        topic_id: str,
        component_type: str,
        title: str,
        content: dict[str, Any],
        component_id: str | None = None,
        learning_objective: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        """
        Initialize a Component entity.

        Args:
            topic_id: ID of the parent topic
            component_type: Type of component (mcq, didactic_snippet, etc.)
            title: Component title
            content: Component content data
            component_id: Unique identifier (generated if not provided)
            learning_objective: Learning objective this component addresses
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = component_id or str(uuid.uuid4())
        self.topic_id = topic_id
        self.component_type = component_type
        self.title = title
        self.content = content
        self.learning_objective = learning_objective
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)

        # Validate on creation
        self.validate()

    def validate(self) -> None:
        """
        Validate component business rules.

        Raises:
            InvalidComponentError: If validation fails
        """
        if not self.topic_id or not self.topic_id.strip():
            raise InvalidComponentError("Component must have a topic_id")

        if not self.component_type or self.component_type not in self.VALID_TYPES:
            raise InvalidComponentError(f"Component type must be one of: {', '.join(self.VALID_TYPES)}")

        if not self.title or not self.title.strip():
            raise InvalidComponentError("Component title cannot be empty")

        if not isinstance(self.content, dict):
            raise InvalidComponentError("Component content must be a dictionary")

        if len(self.title) > 200:
            raise InvalidComponentError("Component title cannot exceed 200 characters")

        # Type-specific validation
        if self.component_type == "mcq":
            self._validate_mcq_content()
        elif self.component_type == "didactic_snippet":
            self._validate_didactic_content()
        elif self.component_type == "glossary":
            self._validate_glossary_content()

    def _validate_mcq_content(self) -> None:
        """Validate MCQ-specific content."""
        required_fields = ["question", "choices", "correct_answer"]
        for field in required_fields:
            if field not in self.content:
                raise InvalidComponentError(f"MCQ content must include '{field}'")

        if not isinstance(self.content["choices"], dict):
            raise InvalidComponentError("MCQ choices must be a dictionary")

        if len(self.content["choices"]) < 2:
            raise InvalidComponentError("MCQ must have at least 2 choices")

        correct_answer = self.content["correct_answer"]
        if correct_answer not in self.content["choices"]:
            raise InvalidComponentError("MCQ correct_answer must be a valid choice key")

    def _validate_didactic_content(self) -> None:
        """Validate didactic snippet content."""
        required_fields = ["explanation", "key_points"]
        for field in required_fields:
            if field not in self.content:
                raise InvalidComponentError(f"Didactic snippet content must include '{field}'")

        if not isinstance(self.content["key_points"], list):
            raise InvalidComponentError("Didactic snippet key_points must be a list")

    def _validate_glossary_content(self) -> None:
        """Validate glossary content."""
        required_fields = ["terms"]
        for field in required_fields:
            if field not in self.content:
                raise InvalidComponentError(f"Glossary content must include '{field}'")

        if not isinstance(self.content["terms"], list):
            raise InvalidComponentError("Glossary terms must be a list")

        for term in self.content["terms"]:
            if not isinstance(term, dict) or "term" not in term or "definition" not in term:
                raise InvalidComponentError("Each glossary term must have 'term' and 'definition'")

    def update_content(self, new_content: dict[str, Any]) -> None:
        """
        Update component content.

        Args:
            new_content: New content data

        Raises:
            InvalidComponentError: If new content is invalid
        """
        old_content = self.content
        self.content = new_content
        self.updated_at = datetime.now(UTC)

        try:
            self.validate()
        except InvalidComponentError:
            # Rollback on validation failure
            self.content = old_content
            raise

    def update_title(self, new_title: str) -> None:
        """
        Update component title.

        Args:
            new_title: New title

        Raises:
            InvalidComponentError: If new title is invalid
        """
        old_title = self.title
        self.title = new_title
        self.updated_at = datetime.now(UTC)

        try:
            self.validate()
        except InvalidComponentError:
            # Rollback on validation failure
            self.title = old_title
            raise

    def set_learning_objective(self, learning_objective: str | None) -> None:
        """
        Set the learning objective for this component.

        Args:
            learning_objective: Learning objective this component addresses
        """
        self.learning_objective = learning_objective
        self.updated_at = datetime.now(UTC)

    def is_mcq(self) -> bool:
        """Check if this is an MCQ component."""
        return self.component_type == "mcq"

    def is_didactic_snippet(self) -> bool:
        """Check if this is a didactic snippet component."""
        return self.component_type == "didactic_snippet"

    def is_glossary(self) -> bool:
        """Check if this is a glossary component."""
        return self.component_type == "glossary"

    def get_difficulty_level(self) -> str | None:
        """
        Get the difficulty level of this component.

        Returns:
            Difficulty level if available in content, None otherwise
        """
        return self.content.get("difficulty")

    def get_estimated_time_minutes(self) -> int | None:
        """
        Get estimated completion time in minutes.

        Returns:
            Estimated time in minutes if available, None otherwise
        """
        return self.content.get("estimated_time_minutes")

    def has_evaluation_data(self) -> bool:
        """
        Check if component has evaluation/assessment data.

        Returns:
            True if component has evaluation data
        """
        return "evaluation" in self.content or "assessment" in self.content

    def to_dict(self) -> dict[str, Any]:
        """Convert component to dictionary representation."""
        return {
            "id": self.id,
            "topic_id": self.topic_id,
            "component_type": self.component_type,
            "title": self.title,
            "content": self.content,
            "learning_objective": self.learning_objective,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Component":
        """
        Create Component from dictionary representation.

        Args:
            data: Dictionary containing component data

        Returns:
            Component instance
        """
        created_at = None
        updated_at = None

        if "created_at" in data:
            created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        if "updated_at" in data:
            updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))

        return cls(
            component_id=data["id"],
            topic_id=data["topic_id"],
            component_type=data["component_type"],
            title=data["title"],
            content=data["content"],
            learning_objective=data.get("learning_objective"),
            created_at=created_at,
            updated_at=updated_at,
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Component):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation."""
        return f"Component(id='{self.id}', type='{self.component_type}', title='{self.title}')"
