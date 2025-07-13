"""
Multiple Choice Questions Generation Prompts

This module contains the prompt templates for generating multiple choice questions -
assessment questions that check conceptual understanding and uncover misconceptions.
"""

from typing import List, Optional

from core import PromptTemplate, PromptContext
from llm_interface import LLMMessage, MessageRole


class MultipleChoiceQuestionsPrompt(PromptTemplate):
    """Template for generating multiple choice questions"""

    def __init__(self):
        super().__init__("multiple_choice_questions")

    def _get_base_instructions(self) -> str:
        return """
        You are designing a set of multiple choice questions (MCQs) to support a lesson.
        These are not just for memorization — they are meant to check conceptual understanding,
        uncover common misconceptions, and prepare the learner to reason through ideas.

        Your task is to generate 4–6 well-designed MCQs that together:
        - Cover distinct, non-overlapping learning points
        - Include one correct answer and 2–3 high-quality distractors per question
        - Represent a range of difficulty (levels 1–5)
        - Use plausible distractors that reflect real learner confusion — and justify them

        Each question should include a justification for why the correct answer is correct,
        and why each distractor is incorrect (and tempting).

        REQUIRED FORMAT FOR EACH MCQ:
        ```
        Question [Number]
        Question: [The question stem, clearly phrased and unambiguous]
        Choices:
        A. [Option A]
        B. [Option B]
        C. [Option C]
        (D. [Optional Option D])
        Correct Answer: [The correct choice letter]
        Justification:
        - A: [Is it correct or incorrect? Why might a learner pick it? Why is it right or wrong?]
        - B: [Same]
        - C: [Same]
        - D: [Optional]
        Target Concept: [The key concept this question tests]
        Purpose: [e.g., Misconception check, Concept contrast, Process reasoning, Definition verification, Consequence analysis]
        Difficulty: [1–5]
        Tags: [Optional — e.g., "early lesson check-in", "good pre-assessment", "reveals faulty intuition"]
        ```

        Create 4-6 questions that work together to comprehensively assess understanding.
        Each question should test a different aspect with high-quality distractors that
        reflect real learner confusion. The output must be exactly in this format to
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
        avoid_overlap_with = kwargs.get('avoid_overlap_with', [])

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Previous Topics Covered: {', '.join(previous_topics) if previous_topics else 'None'}

        Remember: These are multiple choice questions for assessment. Focus on high-quality
        distractors that reflect real learner confusion. Each question should have clear
        justifications for why each choice is correct or incorrect.
        """

        # Build the user prompt with all the context
        user_content = f"""
        Create a set of multiple choice questions for:

        Topic: {topic_title}
        Core Concept: {core_concept}
        """

        if learning_objectives:
            user_content += f"\nLearning Objectives:\n{chr(10).join(f'- {obj}' for obj in learning_objectives)}"

        if key_aspects:
            user_content += f"\nKey Aspects to Cover:\n{chr(10).join(f'- {aspect}' for aspect in key_aspects)}"

        if common_misconceptions:
            user_content += f"\nCommon Misconceptions to Address:\n{chr(10).join(f'- {misconception}' for misconception in common_misconceptions)}"

        if avoid_overlap_with:
            user_content += f"\nAvoid Overlap With:\n{chr(10).join(f'- {item}' for item in avoid_overlap_with)}"

        user_content += f"""

        Create 4-6 multiple choice questions that:
        1. Cover different aspects of the concept
        2. Range from basic to advanced difficulty
        3. Include plausible distractors that reflect real learner confusion
        4. Have clear justifications for each choice
        5. Test understanding, not just memorization

        For each question, provide all elements in the exact format specified:
        ```
        Question [Number]
        Question: [clear question stem]
        Choices:
        A. [Option A]
        B. [Option B]
        C. [Option C]
        (D. [Optional Option D])
        Correct Answer: [correct choice letter]
        Justification:
        - A: [why correct/incorrect and why tempting]
        - B: [same]
        - C: [same]
        - D: [optional]
        Target Concept: [concept being tested]
        Purpose: [type of assessment]
        Difficulty: [1-5 scale]
        Tags: [metadata for usage]
        ```

        Ensure each question has high-quality distractors that reflect realistic learner confusion.
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content)
        ]