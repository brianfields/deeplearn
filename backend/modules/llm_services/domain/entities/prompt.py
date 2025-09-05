"""
Domain entities for prompt management.

This module contains the business logic for prompt templates, context,
and prompt generation rules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from typing import Any

from .llm_provider import LLMMessage, MessageRole


class PromptType(str, Enum):
    """Types of prompts supported by the system"""

    CONTENT_CREATION = "content_creation"
    MCQ_GENERATION = "mcq_generation"
    MATERIAL_EXTRACTION = "material_extraction"
    SOCRATIC_DIALOGUE = "socratic_dialogue"
    EVALUATION = "evaluation"
    GLOSSARY = "glossary"


class UserLevel(str, Enum):
    """User skill levels for prompt customization"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningStyle(str, Enum):
    """Learning styles for prompt customization"""

    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    BALANCED = "balanced"


@dataclass
class PromptContext:
    """Context information for prompt generation"""

    user_level: UserLevel = UserLevel.BEGINNER
    learning_style: LearningStyle = LearningStyle.BALANCED
    time_constraint: int = 15  # minutes
    previous_performance: dict[str, Any] = field(default_factory=dict)
    prerequisites_met: list[str] = field(default_factory=list)
    custom_instructions: str | None = None
    session_id: str | None = None
    created_at: datetime | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            "user_level": self.user_level.value,
            "learning_style": self.learning_style.value,
            "time_constraint": self.time_constraint,
            "previous_performance": self.previous_performance,
            "prerequisites_met": self.prerequisites_met,
            "custom_instructions": self.custom_instructions,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromptContext":
        """Create context from dictionary"""
        context = cls(
            user_level=UserLevel(data.get("user_level", UserLevel.BEGINNER.value)),
            learning_style=LearningStyle(data.get("learning_style", LearningStyle.BALANCED.value)),
            time_constraint=data.get("time_constraint", 15),
            previous_performance=data.get("previous_performance", {}),
            prerequisites_met=data.get("prerequisites_met", []),
            custom_instructions=data.get("custom_instructions"),
            session_id=data.get("session_id"),
        )

        if data.get("created_at"):
            context.created_at = datetime.fromisoformat(data["created_at"])

        return context


@dataclass
class PromptMetadata:
    """Metadata for prompt templates"""

    name: str
    description: str
    prompt_type: PromptType
    version: str = "1.0"
    author: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at


class Prompt:
    """
    Domain entity representing a prompt template.

    This class encapsulates the business logic for prompt generation,
    validation, and customization.
    """

    def __init__(
        self,
        template: str,
        metadata: PromptMetadata,
        variables: dict[str, str] | None = None,
        required_variables: list[str] | None = None,
    ):
        self.template = template
        self.metadata = metadata
        self.variables = variables or {}
        self.required_variables = required_variables or []
        self._validate_template()

    def _validate_template(self) -> None:
        """Validate the prompt template"""
        if not self.template.strip():
            raise ValueError("Prompt template cannot be empty")

        # Check for required variables in template
        for var in self.required_variables:
            placeholder = f"{{{var}}}"
            if placeholder not in self.template:
                raise ValueError(f"Required variable '{var}' not found in template")

    def render(self, context: PromptContext, **kwargs: Any) -> list[LLMMessage]:
        """
        Render the prompt template with the given context.

        Args:
            context: Prompt context with user information
            **kwargs: Additional variables for template rendering

        Returns:
            List of LLM messages ready for sending
        """
        # Validate required variables
        all_variables = {**self.variables, **kwargs}
        missing_vars = [var for var in self.required_variables if var not in all_variables]
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")

        # Format context information
        context_str = self._format_context(context)

        # Combine all variables
        render_variables = {
            **all_variables,
            "context": context_str,
            "user_level": context.user_level.value,
            "learning_style": context.learning_style.value,
            "time_constraint": context.time_constraint,
        }

        # Render template
        try:
            rendered_content = self.template.format(**render_variables)
        except KeyError as e:
            raise ValueError(f"Template variable not provided: {e}")

        # Create messages based on prompt type
        return self._create_messages(rendered_content, context)

    def _format_context(self, context: PromptContext) -> str:
        """Format context information for inclusion in prompts"""
        context_parts = [
            f"User Level: {context.user_level.value}",
            f"Learning Style: {context.learning_style.value}",
            f"Time Constraint: {context.time_constraint} minutes",
        ]

        if context.prerequisites_met:
            context_parts.append(f"Prerequisites Met: {', '.join(context.prerequisites_met)}")

        if context.previous_performance:
            context_parts.append(f"Previous Performance: {json.dumps(context.previous_performance, indent=2)}")

        if context.custom_instructions:
            context_parts.append(f"Custom Instructions: {context.custom_instructions}")

        return "\n".join(context_parts)

    def _create_messages(self, content: str, context: PromptContext) -> list[LLMMessage]:
        """Create LLM messages from rendered content"""
        # For now, create a single system message
        # This can be extended to support multi-message prompts
        return [
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=content,
                metadata={
                    "prompt_name": self.metadata.name,
                    "prompt_type": self.metadata.prompt_type.value,
                    "context": context.to_dict(),
                },
            )
        ]

    def validate_context(self, context: PromptContext) -> bool:
        """Validate that the context is appropriate for this prompt"""
        # Basic validation - can be extended based on prompt type
        if context.time_constraint <= 0:
            return False

        # Add prompt-type specific validation
        if self.metadata.prompt_type == PromptType.MCQ_GENERATION:
            # MCQ generation needs sufficient time
            return context.time_constraint >= 5

        return True

    def estimate_tokens(self, context: PromptContext, **kwargs: Any) -> int:
        """Estimate token count for rendered prompt"""
        try:
            messages = self.render(context, **kwargs)
            total_content = " ".join(msg.content for msg in messages)
            # Rough approximation: ~1.3 tokens per word
            return int(len(total_content.split()) * 1.3)
        except Exception:
            # Fallback estimation
            return int(len(self.template.split()) * 1.5)

    def clone(self, new_name: str | None = None) -> "Prompt":
        """Create a copy of this prompt"""
        new_metadata = PromptMetadata(
            name=new_name or f"{self.metadata.name}_copy",
            description=f"Copy of {self.metadata.description}",
            prompt_type=self.metadata.prompt_type,
            version=self.metadata.version,
            author=self.metadata.author,
            tags=self.metadata.tags.copy(),
        )

        return Prompt(
            template=self.template,
            metadata=new_metadata,
            variables=self.variables.copy(),
            required_variables=self.required_variables.copy(),
        )


class PromptTemplate(ABC):
    """
    Abstract base class for prompt templates.

    This provides a standardized interface for all prompt templates
    used across different modules.
    """

    def __init__(self, name: str, prompt_type: PromptType):
        self.name = name
        self.prompt_type = prompt_type

    @abstractmethod
    def get_base_instructions(self) -> str:
        """Get base instructions for this prompt type"""
        pass

    @abstractmethod
    def generate_prompt(self, context: PromptContext, **kwargs: Any) -> Prompt:
        """Generate a prompt instance for the given context"""
        pass

    @abstractmethod
    def get_required_variables(self) -> list[str]:
        """Get list of required variables for this template"""
        pass

    def validate_variables(self, **kwargs: Any) -> None:
        """Validate that required variables are provided"""
        required = self.get_required_variables()
        missing = [var for var in required if var not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables for {self.name}: {missing}")


# Domain policies for prompts
class PromptPolicy:
    """Business rules for prompt management"""

    MAX_TEMPLATE_LENGTH = 50000  # characters
    MAX_VARIABLES = 50
    MAX_CONTEXT_SIZE = 10000  # characters

    @classmethod
    def validate_template(cls, template: str) -> None:
        """Validate prompt template according to business rules"""
        if len(template) > cls.MAX_TEMPLATE_LENGTH:
            raise ValueError(f"Template too long: {len(template)} > {cls.MAX_TEMPLATE_LENGTH}")

        if not template.strip():
            raise ValueError("Template cannot be empty")

    @classmethod
    def validate_variables(cls, variables: dict[str, Any]) -> None:
        """Validate prompt variables"""
        if len(variables) > cls.MAX_VARIABLES:
            raise ValueError(f"Too many variables: {len(variables)} > {cls.MAX_VARIABLES}")

        # Check for reserved variable names
        reserved = {"context", "user_level", "learning_style", "time_constraint"}
        conflicts = set(variables.keys()) & reserved
        if conflicts:
            raise ValueError(f"Variables use reserved names: {conflicts}")

    @classmethod
    def should_cache_prompt(cls, prompt: Prompt, context: PromptContext) -> bool:
        """Determine if a rendered prompt should be cached"""
        # Don't cache prompts with custom instructions (too specific)
        if context.custom_instructions:
            return False

        # Don't cache prompts with session-specific data
        if context.session_id:
            return False

        # Cache standard prompts for common contexts
        return True


# Factory function for creating default contexts
def create_default_context(
    user_level: UserLevel = UserLevel.BEGINNER,
    time_constraint: int = 15,
    **kwargs: Any,
) -> PromptContext:
    """Create a default prompt context with common settings"""
    return PromptContext(user_level=user_level, time_constraint=time_constraint, **kwargs)
