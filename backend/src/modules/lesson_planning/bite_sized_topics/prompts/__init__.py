"""
Bite-sized Topics Prompts

This package contains all prompt templates for bite-sized topic content creation.
"""

from .didactic_snippet import DidacticSnippetPrompt
from .glossary import GlossaryPrompt
from .lesson_content import LessonContentPrompt
from .multiple_choice_questions import MultipleChoiceQuestionsPrompt
from .post_topic_quiz import PostTopicQuizPrompt
from .short_answer_questions import ShortAnswerQuestionsPrompt
from .socratic_dialogue import SocraticDialoguePrompt

# Placeholders for future prompts

__all__ = [
    "LessonContentPrompt",
    "DidacticSnippetPrompt",
    "GlossaryPrompt",
    "SocraticDialoguePrompt",
    "ShortAnswerQuestionsPrompt",
    "MultipleChoiceQuestionsPrompt",
    "PostTopicQuizPrompt",
    # Future prompts will be added here
]
