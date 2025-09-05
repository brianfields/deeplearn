"""
Topic validation policies for content creation.

This module contains business rules and policies for validating topics.
"""

from typing import Any

from ..entities.topic import InvalidTopicError, Topic


class TopicValidationPolicy:
    """
    Business rules and policies for topic validation.

    This class encapsulates the business logic for determining whether
    a topic meets the requirements for various operations.
    """

    # Minimum requirements for different operations
    MIN_LEARNING_OBJECTIVES = 1
    MAX_LEARNING_OBJECTIVES = 10
    MIN_KEY_CONCEPTS = 1
    MAX_KEY_CONCEPTS = 20
    MIN_TITLE_LENGTH = 5
    MAX_TITLE_LENGTH = 200
    MIN_CORE_CONCEPT_LENGTH = 10
    MAX_CORE_CONCEPT_LENGTH = 500

    # Valid user levels
    VALID_USER_LEVELS = {"beginner", "intermediate", "advanced"}

    @classmethod
    def is_valid_for_creation(cls, topic: Topic) -> bool:
        """
        Check if a topic is valid for initial creation.

        Args:
            topic: Topic to validate

        Returns:
            True if topic is valid for creation

        Raises:
            InvalidTopicError: If topic fails validation with details
        """
        errors = []

        # Basic field validation
        if not topic.title or len(topic.title.strip()) < cls.MIN_TITLE_LENGTH:
            errors.append(f"Title must be at least {cls.MIN_TITLE_LENGTH} characters")

        if len(topic.title) > cls.MAX_TITLE_LENGTH:
            errors.append(f"Title cannot exceed {cls.MAX_TITLE_LENGTH} characters")

        if not topic.core_concept or len(topic.core_concept.strip()) < cls.MIN_CORE_CONCEPT_LENGTH:
            errors.append(f"Core concept must be at least {cls.MIN_CORE_CONCEPT_LENGTH} characters")

        if len(topic.core_concept) > cls.MAX_CORE_CONCEPT_LENGTH:
            errors.append(f"Core concept cannot exceed {cls.MAX_CORE_CONCEPT_LENGTH} characters")

        if topic.user_level not in cls.VALID_USER_LEVELS:
            errors.append(f"User level must be one of: {', '.join(cls.VALID_USER_LEVELS)}")

        # Learning objectives validation
        if len(topic.learning_objectives) < cls.MIN_LEARNING_OBJECTIVES:
            errors.append(f"Topic must have at least {cls.MIN_LEARNING_OBJECTIVES} learning objective")

        if len(topic.learning_objectives) > cls.MAX_LEARNING_OBJECTIVES:
            errors.append(f"Topic cannot have more than {cls.MAX_LEARNING_OBJECTIVES} learning objectives")

        # Key concepts validation
        if len(topic.key_concepts) < cls.MIN_KEY_CONCEPTS:
            errors.append(f"Topic must have at least {cls.MIN_KEY_CONCEPTS} key concept")

        if len(topic.key_concepts) > cls.MAX_KEY_CONCEPTS:
            errors.append(f"Topic cannot have more than {cls.MAX_KEY_CONCEPTS} key concepts")

        if errors:
            raise InvalidTopicError("; ".join(errors))

        return True

    @classmethod
    def is_valid_for_publishing(cls, topic: Topic) -> bool:
        """
        Check if a topic is ready for publishing/learning sessions.

        Args:
            topic: Topic to validate

        Returns:
            True if topic is ready for publishing

        Raises:
            InvalidTopicError: If topic fails validation with details
        """
        errors = []

        # Must pass creation validation first
        try:
            cls.is_valid_for_creation(topic)
        except InvalidTopicError as e:
            errors.append(f"Basic validation failed: {e}")

        # Must have components
        components = topic.get_components()
        if not components:
            errors.append("Topic must have at least one component to be published")

        # Must have at least one MCQ or assessment component
        assessment_components = [c for c in components if c.component_type in ["mcq", "short_answer", "scenario_critique"]]
        if not assessment_components:
            errors.append("Topic must have at least one assessment component (MCQ, short answer, etc.)")

        # Check that learning objectives are addressed by components
        addressed_objectives = {c.learning_objective for c in components if c.learning_objective}
        unaddressed_objectives = set(topic.learning_objectives) - addressed_objectives
        if unaddressed_objectives:
            errors.append(f"Learning objectives not addressed by components: {', '.join(unaddressed_objectives)}")

        # Must have refined material if created from source material
        if topic.source_material and not topic.refined_material:
            errors.append("Topic created from source material must have refined material")

        if errors:
            raise InvalidTopicError("; ".join(errors))

        return True

    @classmethod
    def is_valid_source_material(cls, source_material: str) -> bool:
        """
        Check if source material is valid for topic creation.

        Args:
            source_material: Source material text

        Returns:
            True if source material is valid

        Raises:
            InvalidTopicError: If source material is invalid
        """
        errors = []

        if not source_material or not source_material.strip():
            errors.append("Source material cannot be empty")

        # Minimum length check (should have substantial content)
        if len(source_material.strip()) < 100:
            errors.append("Source material must be at least 100 characters")

        # Maximum length check (prevent abuse)
        if len(source_material) > 50000:  # ~50KB
            errors.append("Source material cannot exceed 50,000 characters")

        # Check for reasonable content (not just whitespace or repeated characters)
        unique_chars = len(set(source_material.strip()))
        if unique_chars < 10:
            errors.append("Source material must contain varied content")

        if errors:
            raise InvalidTopicError("; ".join(errors))

        return True

    @classmethod
    def is_valid_refined_material(cls, refined_material: dict[str, Any]) -> bool:
        """
        Check if refined material structure is valid.

        Args:
            refined_material: Refined material dictionary

        Returns:
            True if refined material is valid

        Raises:
            InvalidTopicError: If refined material is invalid
        """
        errors = []

        if not isinstance(refined_material, dict):
            errors.append("Refined material must be a dictionary")
            raise InvalidTopicError("; ".join(errors))

        # Check for required structure
        if "topics" not in refined_material:
            errors.append("Refined material must contain 'topics' field")

        if not isinstance(refined_material.get("topics"), list):
            errors.append("Refined material 'topics' must be a list")

        if not refined_material.get("topics"):
            errors.append("Refined material must contain at least one topic")

        # Validate each topic in refined material
        for i, topic_data in enumerate(refined_material.get("topics", [])):
            if not isinstance(topic_data, dict):
                errors.append(f"Topic {i} must be a dictionary")
                continue

            if "learning_objectives" not in topic_data:
                errors.append(f"Topic {i} must have learning_objectives")

            if "key_facts" not in topic_data:
                errors.append(f"Topic {i} must have key_facts")

            if not isinstance(topic_data.get("learning_objectives"), list):
                errors.append(f"Topic {i} learning_objectives must be a list")

            if not isinstance(topic_data.get("key_facts"), list):
                errors.append(f"Topic {i} key_facts must be a list")

        if errors:
            raise InvalidTopicError("; ".join(errors))

        return True

    @classmethod
    def calculate_topic_quality_score(cls, topic: Topic) -> float:
        """
        Calculate a quality score for a topic (0.0 to 1.0).

        Args:
            topic: Topic to evaluate

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 0.0

        # Basic completeness (0.3 weight)
        max_score += 0.3
        if topic.learning_objectives:
            score += 0.1
        if topic.key_concepts:
            score += 0.1
        if topic.refined_material:
            score += 0.1

        # Component coverage (0.4 weight)
        max_score += 0.4
        components = topic.get_components()
        if components:
            score += 0.2

            # Bonus for variety of component types
            component_types = {c.component_type for c in components}
            variety_bonus = min(len(component_types) * 0.05, 0.2)
            score += variety_bonus

        # Learning objective coverage (0.3 weight)
        max_score += 0.3
        if topic.learning_objectives:
            addressed_objectives = {c.learning_objective for c in components if c.learning_objective}
            coverage_ratio = len(addressed_objectives) / len(topic.learning_objectives)
            score += 0.3 * coverage_ratio

        return score / max_score if max_score > 0 else 0.0

    @classmethod
    def get_topic_readiness_status(cls, topic: Topic) -> str:
        """
        Get the readiness status of a topic.

        Args:
            topic: Topic to evaluate

        Returns:
            Status string: "draft", "needs_components", "needs_review", "ready"
        """
        try:
            cls.is_valid_for_creation(topic)
        except InvalidTopicError:
            return "draft"

        components = topic.get_components()
        if not components:
            return "needs_components"

        try:
            cls.is_valid_for_publishing(topic)
            return "ready"
        except InvalidTopicError:
            return "needs_review"
