"""
Prompt Registry for loading prompt templates from modules.

This module provides a centralized way to load and manage prompt templates
from different modules in the system.
"""

import logging
from typing import Any

from ..domain.entities.prompt import Prompt, PromptMetadata, PromptType

logger = logging.getLogger(__name__)


class PromptRegistry:
    """
    Registry for loading and managing prompt templates.

    This class provides a way to load prompt templates from different modules
    and convert them to the LLM service's internal Prompt format.
    """

    def __init__(self):
        """Initialize the prompt registry."""
        self._template_cache: dict[str, Prompt] = {}
        self._loaded_modules: set[str] = set()

    def get_prompt(self, prompt_name: str) -> Prompt | None:
        """
        Get a prompt template by name.

        Args:
            prompt_name: Name of the prompt template

        Returns:
            Prompt template or None if not found
        """
        # Check cache first
        if prompt_name in self._template_cache:
            return self._template_cache[prompt_name]

        # Try to load from content creation module
        prompt = self._load_content_creation_prompt(prompt_name)
        if prompt:
            self._template_cache[prompt_name] = prompt
            return prompt

        logger.warning(f"Prompt template not found: {prompt_name}")
        return None

    def _load_content_creation_prompt(self, prompt_name: str) -> Prompt | None:
        """
        Load a prompt template from the content creation module.

        Args:
            prompt_name: Name of the prompt template

        Returns:
            Prompt template or None if not found
        """
        try:
            # Map prompt names to their template classes
            prompt_mapping = {
                "single_mcq_creation": "SingleMCQCreationPrompt",
                "mcq_evaluation": "MCQEvaluationPrompt",
                "extract_material": "RefinedMaterialExtractionPrompt",
                "glossary": "GlossaryPrompt",
                "didactic_snippet": "DidacticSnippetPrompt",
            }

            if prompt_name not in prompt_mapping:
                return None

            # Import the prompt template class
            from modules.content_creation.domain.prompts import (
                DidacticSnippetPrompt,
                GlossaryPrompt,
                MCQEvaluationPrompt,
                RefinedMaterialExtractionPrompt,
                SingleMCQCreationPrompt,
            )

            template_classes = {
                "SingleMCQCreationPrompt": SingleMCQCreationPrompt,
                "MCQEvaluationPrompt": MCQEvaluationPrompt,
                "RefinedMaterialExtractionPrompt": RefinedMaterialExtractionPrompt,
                "GlossaryPrompt": GlossaryPrompt,
                "DidacticSnippetPrompt": DidacticSnippetPrompt,
            }

            template_class_name = prompt_mapping[prompt_name]
            template_class = template_classes[template_class_name]

            # Create an instance of the template
            template_instance = template_class()

            # Convert to our internal Prompt format
            return self._convert_template_to_prompt(template_instance, prompt_name)

        except Exception as e:
            logger.error(f"Failed to load content creation prompt {prompt_name}: {e}")
            return None

    def _convert_template_to_prompt(self, template_instance: Any, prompt_name: str) -> Prompt:
        """
        Convert a template instance to our internal Prompt format.

        Args:
            template_instance: Instance of a prompt template class
            prompt_name: Name of the prompt

        Returns:
            Internal Prompt object
        """
        # Get the base instructions from the template
        base_instructions = template_instance._get_base_instructions()

        # Create metadata
        metadata = PromptMetadata(
            name=prompt_name,
            description=f"Prompt template for {prompt_name}",
            version="1.0.0",
            prompt_type=PromptType.SYSTEM_USER,
            tags=[prompt_name, "content_creation"],
        )

        # Create a simple template that uses the original template's generate_prompt method
        # This is a bridge between the old and new prompt systems
        template_str = base_instructions + "\n\n{context}\n\n{additional_content}"

        return Prompt(
            template=template_str,
            metadata=metadata,
            variables={"context": "", "additional_content": ""},
            required_variables=[],
        )

    def clear_cache(self) -> None:
        """Clear the prompt template cache."""
        self._template_cache.clear()
        self._loaded_modules.clear()


# Global registry instance
_prompt_registry = PromptRegistry()


def get_prompt_registry() -> PromptRegistry:
    """Get the global prompt registry instance."""
    return _prompt_registry

