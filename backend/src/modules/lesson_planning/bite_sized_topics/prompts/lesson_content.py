"""
Lesson Content Generation Prompts

This module contains the prompt templates for generating lesson content.
"""

from src.core.prompt_base import PromptContext, PromptTemplate
from src.llm_interface import LLMMessage, MessageRole


class LessonContentPrompt(PromptTemplate):
    """Template for generating lesson content"""

    def __init__(self):
        super().__init__("lesson_content")

    def _get_base_instructions(self) -> str:
        return """
        You are an expert educator specializing in professional skills training. Your task is to
        create engaging, interactive lesson content that promotes active learning.

        Key principles:
        1. Use conversational, engaging tone
        2. Include real-world examples and scenarios
        3. Break content into digestible chunks
        4. Include interactive elements (questions, exercises)
        5. Use markdown formatting for clarity
        6. Follow progressive disclosure (simple to complex)
        7. Include practical applications
        8. Encourage reflection and critical thinking
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> list[LLMMessage]:
        # Validate required parameters
        self.validate_kwargs(["topic_title", "topic_description", "learning_objectives"], **kwargs)

        topic_title = kwargs.get("topic_title", "")
        topic_description = kwargs.get("topic_description", "")
        learning_objectives = kwargs.get("learning_objectives", [])
        previous_topics = kwargs.get("previous_topics", [])

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Previous Topics Covered: {", ".join(previous_topics) if previous_topics else "None"}

        Lesson Structure:
        1. Opening Hook (1 minute) - Engaging question or scenario
        2. Core Content (10-12 minutes) - Main teaching content with examples
        3. Interactive Elements (2-3 minutes) - Questions, exercises, or discussions
        4. Summary & Next Steps (1 minute) - Key takeaways and transition

        Use markdown formatting and create an engaging, conversational experience.
        """

        user_content = f"""
        Create a comprehensive lesson for:

        Topic: {topic_title}
        Description: {topic_description}
        Learning Objectives:
        {chr(10).join(f"- {obj}" for obj in learning_objectives)}

        The lesson should be interactive, engaging, and completable in 15 minutes.
        Include real-world examples and practical applications.
        """

        return [LLMMessage(role=MessageRole.SYSTEM, content=system_message), LLMMessage(role=MessageRole.USER, content=user_content)]
