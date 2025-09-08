"""
Didactic Snippet Generation Prompts

This module contains the prompt templates for generating didactic snippets -
short, engaging explanations that introduce concepts in lessons.
"""

from typing import Any

from src.core.prompt_base import PromptContext, PromptTemplate
from src.llm_interface import LLMMessage, MessageRole


class DidacticSnippetPrompt(PromptTemplate):
    """Template for generating didactic snippets"""

    def __init__(self) -> None:
        super().__init__("didactic_snippet")

    def _get_base_instructions(self) -> str:
        return """
        You are writing a didactic snippet — a short, engaging explanation that introduces
        a concept in a lesson. This is the learner's first exposure to the idea, before
        any exercises or interaction.

        Your job is to help the learner build a clear, intuitive mental model of the concept.

        CRITICAL REQUIREMENTS:
        1. Create a short, descriptive title (1-8 words) that captures the essence of what this snippet teaches
        2. Write 3–10 fluent sentences in natural, plain English for the snippet content
        3. Imagine you're a great teacher talking to a smart but unfamiliar learner
        4. Start where the learner is — you don't need to define the term first if another framing works better
        5. Avoid bullet points or formal structure. This is a verbal explanation
        6. Don't ask the learner questions — this is for teaching, not interacting
        7. You may include a concrete example, contrast, or metaphor if it helps explain

        FRAMING OPTIONS (choose the most appropriate):
        - "What is X?" → good for introducing new objects or structures
        - "Why do we need X?" → good for justifying unfamiliar ideas
        - "You might expect X, but actually…" → good for surprising or unintuitive ideas
        - "To do Y, we need X…" → good for prerequisite ideas
        - "Let's walk through an example…" → good for process-oriented ideas
        """

    def generate_prompt(self, context: PromptContext, **kwargs: Any) -> list[LLMMessage]:  # noqa: ANN401
        # Validate required parameters
        self.validate_kwargs(["topic_title", "key_concept"], **kwargs)

        topic_title = kwargs.get("topic_title", "")
        key_concept = kwargs.get("key_concept", "")
        learning_objectives = kwargs.get("learning_objectives", [])
        previous_topics = kwargs.get("previous_topics", [])
        concept_context = kwargs.get("concept_context", "")

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Previous Topics Covered: {", ".join(previous_topics) if previous_topics else "None"}

        Remember: This is a didactic snippet, not a full lesson. Keep it concise but impactful.
        The learner should walk away with a clear mental model of the concept.
        """

        # Build the user prompt with all the context
        user_content = f"""
        Create a didactic snippet for:

        Topic: {topic_title}
        Key Concept: {key_concept}
        """

        if concept_context:
            user_content += f"\nConcept Context: {concept_context}"

        if learning_objectives:
            user_content += f"\nLearning Objectives:\n{chr(10).join(f'- {obj}' for obj in learning_objectives)}"

        user_content += """

        Choose the most appropriate framing from the options provided and create a snippet
        that will help the learner build an intuitive understanding of this concept.
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content),
        ]
