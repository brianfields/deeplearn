"""
Bite-sized Topics Prompts

This package contains all prompt templates for bite-sized topic content creation.
"""

from .didactic_snippet import DidacticSnippetPrompt
from .glossary import GlossaryPrompt
from .multiple_choice_questions import MultipleChoiceQuestionsPrompt

__all__ = [
    "DidacticSnippetPrompt",
    "GlossaryPrompt",
    "MultipleChoiceQuestionsPrompt",
]
