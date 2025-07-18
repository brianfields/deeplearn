"""
Bite-sized Topics Prompts

This package contains all prompt templates for bite-sized topic content creation.
"""

from .lesson_content import LessonContentPrompt
from .didactic_snippet import DidacticSnippetPrompt
from .glossary import GlossaryPrompt
from .socratic_dialogue import SocraticDialoguePrompt
from .short_answer_questions import ShortAnswerQuestionsPrompt
from .multiple_choice_questions import MultipleChoiceQuestionsPrompt
from .post_topic_quiz import PostTopicQuizPrompt

# Placeholders for future prompts

__all__ = [
    'LessonContentPrompt',
    'DidacticSnippetPrompt',
    'GlossaryPrompt',
    'SocraticDialoguePrompt',
    'ShortAnswerQuestionsPrompt',
    'MultipleChoiceQuestionsPrompt',
    'PostTopicQuizPrompt',
    # Future prompts will be added here
]