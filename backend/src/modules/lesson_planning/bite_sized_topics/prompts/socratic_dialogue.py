"""
Socratic Dialogue Generation Prompts

This module contains the prompt templates for generating Socratic dialogue exercises -
guided discovery conversations that help learners construct understanding through questioning.
"""

from typing import List, Optional

from core import PromptTemplate, PromptContext
from llm_interface import LLMMessage, MessageRole


class SocraticDialoguePrompt(PromptTemplate):
    """Template for generating Socratic dialogue exercises"""

    def __init__(self):
        super().__init__("socratic_dialogue")

    def _get_base_instructions(self) -> str:
        return """
        You are a learning experience designer creating a set of Socratic dialogue exercises
        for a specific lesson topic. These are not quizzes — they are guided discovery
        conversations where a tutor helps a learner construct understanding through
        back-and-forth questioning and support.

        Your task is to propose a coordinated set of 3 to 5 non-redundant Socratic dialogues
        that together offer strong pedagogical coverage of the concept.

        Each dialogue should:
        - Target a different pedagogical function (e.g. analogical reasoning, correcting a
          misconception, contrasting cases, exploring consequences, step-by-step construction, etc.)
        - Span a range of difficulty levels (from intuitive entry points to deeper reasoning)
        - Lead to a distinct learner "aha" insight — a mental shift or realization
        - Include metadata so a tutor or adaptive system can choose which one to use

        REQUIRED FORMAT FOR EACH DIALOGUE:
        ```
        Dialogue [Number]
        Concept: [What idea this dialogue is about — this can be more specific than the overall lesson topic]
        Dialogue Objective: [The insight the learner should construct by the end. What shift in mental model or realization are we aiming for? Avoid mere fact recall.]
        Starting Prompt: [A tutor's natural-sounding first line to start the dialogue — open-ended and curiosity-provoking. Avoid trivia questions.]
        Dialogue Style: [e.g., Misconception correction, Analogy exploration, Thought experiment, Contrast of cases, Step-by-step reasoning, Consequence tracing]
        Hints and Scaffolding: [List 2–3 tutor strategies that could help if the learner gets stuck. These might be reframings, examples, analogies, simplifications.]
        Exit Criteria: [How does the tutor know to end the dialogue? Include both cognitive signals (e.g., learner articulates the core idea) and emotional/engagement signals (e.g., visible frustration, diminishing returns).]
        Difficulty: [1–5, where 1 = very introductory and 5 = advanced reasoning]
        Tags: [Optional metadata to support adaptive tutoring — e.g., "good for stuck learners", "reveals misconception", "builds intuition", "post-lesson reflection"]
        ```

        Create 3-5 dialogues that work together as a pedagogical set. Each should offer a different
        path to understanding the concept. The output must be exactly in this format to allow
        for easy parsing and extraction.
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> List[LLMMessage]:
        # Validate required parameters
        self.validate_kwargs(['topic_title', 'core_concept'], **kwargs)

        topic_title = kwargs.get('topic_title', '')
        core_concept = kwargs.get('core_concept', '')
        learning_objectives = kwargs.get('learning_objectives', [])
        previous_topics = kwargs.get('previous_topics', [])
        target_insights = kwargs.get('target_insights', [])
        common_misconceptions = kwargs.get('common_misconceptions', [])

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Previous Topics Covered: {', '.join(previous_topics) if previous_topics else 'None'}

        Remember: These are Socratic dialogues for guided discovery, not quiz questions.
        Each dialogue should lead to a distinct "aha" moment and use a different pedagogical approach.
        The set should work together to provide comprehensive coverage of the concept.
        """

        # Build the user prompt with all the context
        user_content = f"""
        Create a pedagogically useful set of Socratic dialogue exercises for:

        Topic: {topic_title}
        Core Concept: {core_concept}
        """

        if learning_objectives:
            user_content += f"\nLearning Objectives:\n{chr(10).join(f'- {obj}' for obj in learning_objectives)}"

        if target_insights:
            user_content += f"\nTarget Insights (learner should discover):\n{chr(10).join(f'- {insight}' for insight in target_insights)}"

        if common_misconceptions:
            user_content += f"\nCommon Misconceptions to Address:\n{chr(10).join(f'- {misconception}' for misconception in common_misconceptions)}"

        user_content += f"""

        Create 3-5 Socratic dialogues that:
        1. Use different pedagogical approaches (misconception correction, thought experiments, analogies, etc.)
        2. Range from introductory to advanced difficulty
        3. Lead to distinct "aha" insights
        4. Work together as a coordinated pedagogical set

        For each dialogue, provide all the metadata in the exact format specified:
        ```
        Dialogue [Number]
        Concept: [specific concept]
        Dialogue Objective: [target insight]
        Starting Prompt: [tutor's opening line]
        Dialogue Style: [pedagogical approach]
        Hints and Scaffolding: [2-3 tutor strategies]
        Exit Criteria: [when to end the dialogue]
        Difficulty: [1-5 scale]
        Tags: [metadata for adaptive tutoring]
        ```

        Ensure each dialogue targets a different aspect of understanding and uses a unique pedagogical function.
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content)
        ]