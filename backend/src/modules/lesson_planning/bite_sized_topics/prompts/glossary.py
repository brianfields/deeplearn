"""
Glossary Generation Prompts

This module contains the prompt templates for generating glossary entries -
teaching-style explanations of concepts that help learners understand ideas.
"""

from src.core.prompt_base import PromptContext, PromptTemplate
from src.llm_interface import LLMMessage, MessageRole


class GlossaryPrompt(PromptTemplate):
    """Template for generating glossary entries"""

    def __init__(self):
        super().__init__("glossary")

    def _get_base_instructions(self) -> str:
        return """
        You are writing glossary entries for a lesson. Each entry should help a motivated
        learner understand a concept, not just define it. These are teaching snippets —
        not dictionary definitions.

        Each glossary entry should:
        1. Start with the Concept name
        2. Provide a full, fluent Explanation that includes:
           - What the concept means in plain English
           - Why the concept exists or why it matters
           - How it connects to other ideas in the lesson
           - A simple example or metaphor if it helps reveal the intuition

        CRITICAL REQUIREMENTS:
        - Use natural, conversational tone — as if you're explaining to a smart peer who's never seen this idea before
        - Each entry should be 3 to 7 sentences and stand on its own
        - Focus on teaching and understanding, not just definition
        - Make connections to related concepts when relevant
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> list[LLMMessage]:
        # Validate required parameters
        self.validate_kwargs(["topic_title", "concepts"], **kwargs)

        topic_title = kwargs.get("topic_title", "")
        concepts = kwargs.get("concepts", [])
        lesson_context = kwargs.get("lesson_context", "")
        learning_objectives = kwargs.get("learning_objectives", [])
        previous_topics = kwargs.get("previous_topics", [])

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Previous Topics Covered: {", ".join(previous_topics) if previous_topics else "None"}

        Remember: These are teaching explanations, not dictionary definitions.
        Help the learner understand not just what each concept is, but why it matters
        and how it connects to the bigger picture.
        """

        # Build the user prompt with all the context
        # Check if we need to identify concepts from the topic
        needs_concept_identification = any(c.startswith("IDENTIFY_CONCEPTS_FROM:") for c in concepts)

        if needs_concept_identification:
            user_content = f"""
        You need to identify meaningful concepts within this topic and create glossary entries for them.

        Topic: {topic_title}

        TASK: First identify 3-5 key concepts, terms, or ideas that learners would encounter in this topic.
        These should be specific terms or concepts that would benefit from explanation, not just the topic title itself.

        Then create glossary entries for each identified concept.
        """
        else:
            user_content = f"""
        Create glossary entries for the following concepts in the context of:

        Topic: {topic_title}
        Concepts to explain: {", ".join(concepts)}
        """

        if lesson_context:
            user_content += f"\nLesson Context: {lesson_context}"

        if learning_objectives:
            user_content += f"\nLearning Objectives:\n{chr(10).join(f'- {obj}' for obj in learning_objectives)}"

        if needs_concept_identification:
            user_content += """

        For each concept you identify, provide a teaching-style explanation that helps learners understand:
        - What it means in plain English
        - Why it exists or matters
        - How it connects to other ideas
        - An example or metaphor if helpful

        Identify and provide entries for 3-5 meaningful concepts.
        """
        else:
            user_content += f"""

        For each concept, provide a teaching-style explanation that helps learners understand:
        - What it means in plain English
        - Why it exists or matters
        - How it connects to other ideas
        - An example or metaphor if helpful

        Provide entries for all {len(concepts)} concepts.
        """

        return [LLMMessage(role=MessageRole.SYSTEM, content=system_message), LLMMessage(role=MessageRole.USER, content=user_content)]
