"""
Syllabus Generation Prompts

This module contains the prompt templates for generating learning syllabi.
"""

from typing import List

from core import PromptTemplate, PromptContext
from llm_interface import LLMMessage, MessageRole


class SyllabusGenerationPrompt(PromptTemplate):
    """Template for generating learning syllabi"""

    def __init__(self):
        super().__init__("syllabus_generation")

    def _get_base_instructions(self) -> str:
        return """
        You are an expert curriculum designer and learning specialist. Your task is to create
        comprehensive, well-structured learning syllabi for professional skills development.

        Key principles:
        1. Each topic should be completable in 15 minutes
        2. Build logical progression from basics to advanced concepts
        3. Include clear learning objectives for each topic
        4. Identify prerequisite relationships between topics
        5. Limit total topics to 20 maximum
        6. Focus on practical, applicable skills
        7. Include assessment opportunities
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> List[LLMMessage]:
        # Validate required parameters
        self.validate_kwargs(['topic'], **kwargs)

        topic = kwargs.get('topic', '')
        user_refinements = kwargs.get('user_refinements', [])

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Response Format:
        Generate a JSON response with the following structure:
        {{
            "topic_name": "string",
            "description": "string",
            "estimated_total_hours": "number",
            "topics": [
                {{
                    "title": "string",
                    "description": "string",
                    "learning_objectives": ["string"],
                    "estimated_duration": 15,
                    "difficulty_level": 1-5,
                    "prerequisite_topics": ["topic_title"],
                    "assessment_type": "quiz|project|discussion"
                }}
            ]
        }}
        """

        user_content = f"""
        Please create a comprehensive learning syllabus for: {topic}

        Requirements:
        - Maximum 20 topics
        - Each topic should take approximately 15 minutes
        - Include clear learning objectives
        - Build logical progression
        - Identify prerequisites
        """

        if user_refinements:
            user_content += f"\n\nUser Refinements:\n" + "\n".join(f"- {refinement}" for refinement in user_refinements)

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content)
        ]