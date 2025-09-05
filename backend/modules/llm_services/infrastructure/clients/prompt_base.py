"""
Base classes for prompt templates.

This module provides the foundation for all prompt templates used across
the learning system modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
from typing import Any

from .llm_interface import LLMMessage


@dataclass
class PromptContext:
    """Context information for prompt generation"""

    user_level: str = "beginner"  # beginner, intermediate, advanced
    learning_style: str = "balanced"  # visual, auditory, kinesthetic, balanced
    time_constraint: int = 15  # minutes
    previous_performance: dict[str, Any] = field(default_factory=dict)
    prerequisites_met: list[str] = field(default_factory=list)
    custom_instructions: str | None = None


class PromptTemplate(ABC):
    """
    Abstract base class for prompt templates.

    Each template defines how to generate prompts for specific learning tasks.
    All module-specific prompt templates should inherit from this class.
    """

    def __init__(self, template_name: str) -> None:
        self.template_name = template_name
        self.name = template_name  # Add name property for compatibility
        self.base_instructions = self._get_base_instructions()

    @abstractmethod
    def _get_base_instructions(self) -> str:
        """Get base instructions for this prompt type"""
        pass

    @abstractmethod
    def generate_prompt(self, context: PromptContext, **kwargs: Any) -> list[LLMMessage]:  # noqa: ANN401
        """Generate prompt messages for the given context"""
        pass

    def _format_context(self, context: PromptContext) -> str:
        """Format context information for inclusion in prompts"""
        context_str = f"""
        User Level: {context.user_level}
        Learning Style: {context.learning_style}
        Time Constraint: {context.time_constraint} minutes
        Prerequisites Met: {", ".join(context.prerequisites_met) if context.prerequisites_met else "None"}
        """

        if context.previous_performance:
            context_str += f"\nPrevious Performance: {json.dumps(context.previous_performance, indent=2)}"

        if context.custom_instructions:
            context_str += f"\nCustom Instructions: {context.custom_instructions}"

        return context_str.strip()

    def validate_kwargs(self, required_kwargs: list[str], **kwargs: Any) -> None:  # noqa: ANN401
        """Validate that required kwargs are present"""
        missing = [k for k in required_kwargs if k not in kwargs]
        if missing:
            raise ValueError(f"Missing required parameters for {self.template_name}: {missing}")


def create_default_context(
    user_level: str = "beginner",
    time_constraint: int = 15,
    **kwargs: Any,  # noqa: ANN401
) -> PromptContext:
    """
    Create a default prompt context with common settings.

    Args:
        user_level: User's skill level
        time_constraint: Time available in minutes
        **kwargs: Additional context parameters

    Returns:
        PromptContext object
    """
    return PromptContext(user_level=user_level, time_constraint=time_constraint, **kwargs)
