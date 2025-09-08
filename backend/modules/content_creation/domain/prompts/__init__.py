"""
Content Creation Prompts.

This package contains all prompt templates for content creation operations.
"""

from .didactic_snippet import DidacticSnippetPrompt
from .glossary import GlossaryPrompt
from .mcq_evaluation import MCQEvaluationPrompt
from .prompt_base import PromptContext, PromptTemplate, create_default_context
from .refined_material_extraction import RefinedMaterialExtractionPrompt
from .single_mcq_creation import SingleMCQCreationPrompt

__all__ = [
    "DidacticSnippetPrompt",
    "GlossaryPrompt",
    "MCQEvaluationPrompt",
    "PromptContext",
    "PromptTemplate",
    "RefinedMaterialExtractionPrompt",
    "SingleMCQCreationPrompt",
    "create_default_context",
]
