"""
Post-Topic Quiz Generation Prompts

This module contains the prompt templates for generating post-topic quizzes -
comprehensive assessments that use multiple question formats to evaluate understanding.
"""

from typing import List, Optional

from core import PromptTemplate, PromptContext
from llm_interface import LLMMessage, MessageRole


class PostTopicQuizPrompt(PromptTemplate):
    """Template for generating post-topic quizzes"""

    def __init__(self):
        super().__init__("post_topic_quiz")

    def _get_base_instructions(self) -> str:
        return """
        You are generating a post-topic quiz to assess how well a learner has understood
        a specific lesson. The quiz may include multiple choice, short answer, or even
        a brief assessment dialogue if the concept benefits from conversational evaluation.

        Your quiz should:
        - Contain 4 to 6 total items
        - Use a variety of question formats, chosen intentionally based on the concept
        - Span a range of difficulty levels (from basic recall to reasoning and application)
        - Help a tutor or system diagnose understanding — not just score a learner

        Each item should be clearly labeled by type, and include:
        - The question or dialogue setup
        - The target concept
        - A sample answer or justification
        - Difficulty (1–5)
        - Optional tags (e.g. "core idea", "misconception check", "synthesis")

        REQUIRED FORMAT FOR EACH ITEM:
        ```
        Item [Number]
        Title: [1-8 word title that captures what this item assesses]
        Type: [Multiple Choice, Short Answer, or Assessment Dialogue]
        Question or Prompt: [The question stem or tutor's first line for the dialogue]

        (For Multiple Choice:)
        Choices:
        A. [Option A]
        B. [Option B]
        C. [Option C]
        (D. [Optional Option D])
        Correct Answer: [Letter]
        Justification:
        - A: [Why someone might choose it and why it's wrong or right]
        - B: [Same]
        - C: [Same]
        - D: [Optional]

        (For Short Answer:)
        Expected Elements of a Good Answer: [Main points a strong answer should contain]

        (For Assessment Dialogue:)
        Dialogue Objective: [What insight or articulation the learner should reach]
        Scaffolding Prompts: [1–2 questions a tutor might use to push if learner stalls]
        Exit Criteria: [How the tutor knows the dialogue is complete]

        Target Concept: [What idea this item is testing]
        Difficulty: [1–5]
        Tags: [Optional metadata]
        ```

        Create a comprehensive quiz that uses the most appropriate question formats for
        assessing the specific concept. The output must be exactly in this format to
        allow for easy parsing and extraction.
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> List[LLMMessage]:
        # Validate required parameters
        self.validate_kwargs(['topic_title', 'core_concept'], **kwargs)

        topic_title = kwargs.get('topic_title', '')
        core_concept = kwargs.get('core_concept', '')
        learning_objectives = kwargs.get('learning_objectives', [])
        previous_topics = kwargs.get('previous_topics', [])
        key_aspects = kwargs.get('key_aspects', [])
        common_misconceptions = kwargs.get('common_misconceptions', [])
        preferred_formats = kwargs.get('preferred_formats', [])

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Previous Topics Covered: {', '.join(previous_topics) if previous_topics else 'None'}

        Remember: This is a comprehensive post-topic quiz that should diagnose understanding
        across multiple dimensions. Choose question formats strategically based on what
        best assesses each aspect of the concept.
        """

        # Build the user prompt with all the context
        user_content = f"""
        Create a post-topic quiz for:

        Topic: {topic_title}
        Core Concept: {core_concept}
        """

        if learning_objectives:
            user_content += f"\nLearning Objectives:\n{chr(10).join(f'- {obj}' for obj in learning_objectives)}"

        if key_aspects:
            user_content += f"\nKey Aspects to Assess:\n{chr(10).join(f'- {aspect}' for aspect in key_aspects)}"

        if common_misconceptions:
            user_content += f"\nCommon Misconceptions to Check:\n{chr(10).join(f'- {misconception}' for misconception in common_misconceptions)}"

        if preferred_formats:
            user_content += f"\nPreferred Question Formats:\n{chr(10).join(f'- {format_type}' for format_type in preferred_formats)}"

        user_content += f"""

        Create a 4-6 item quiz that:
        1. Uses multiple question formats (Multiple Choice, Short Answer, Assessment Dialogue)
        2. Spans difficulty levels from basic recall to advanced reasoning
        3. Focuses on diagnostic assessment, not just scoring
        4. Tests different aspects of the concept comprehensively
        5. Includes appropriate misconception checks

        For each item, provide all elements in the exact format specified:
        ```
        Item [Number]
        Type: [question format]
        Question or Prompt: [question or dialogue starter]
        [Format-specific fields as shown above]
        Target Concept: [concept being tested]
        Difficulty: [1-5 scale]
        Tags: [metadata for usage]
        ```

        Choose question formats strategically based on what best assesses each aspect of understanding.
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content)
        ]