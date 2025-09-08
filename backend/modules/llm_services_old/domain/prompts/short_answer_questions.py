"""
Short Answer Questions Generation Prompts

This module contains the prompt templates for generating short answer questions -
assessment questions that encourage learners to articulate understanding and reasoning.
"""

from src.core.prompt_base import PromptContext, PromptTemplate
from src.llm_interface import LLMMessage, MessageRole


class ShortAnswerQuestionsPrompt(PromptTemplate):
    """Template for generating short answer questions"""

    def __init__(self) -> None:
        super().__init__("short_answer_questions")

    def _get_base_instructions(self) -> str:
        return """
        You are designing a set of short answer questions to support learning for a specific
        lesson concept. These questions are intended to encourage learners to articulate
        understanding, reason through ideas, and make connections — not just recall definitions.

        Your task is to generate 4–6 non-redundant questions that together:
        - Cover a range of thinking levels (e.g., recall, explanation, application, analysis)
        - Test different aspects of the concept
        - Avoid overlapping with Socratic dialogues or each other
        - Are phrased clearly, with no ambiguity about what is being asked

        Each question should be followed by metadata to support tutor usage, grading, and sequencing.

        REQUIRED OUTPUT FORMAT:
        You must respond with valid JSON containing an array of short answer questions:
        {
            "questions": [
                {
                    "title": "1-8 word title that captures what this question assesses",
                    "question": "The question, stated clearly and concisely",
                    "purpose": "What kind of thinking this question is meant to evoke — e.g., definition recall, conceptual explanation, contrast, consequence reasoning, generalization, error detection",
                    "target_concept": "What idea this question is focused on",
                    "expected_elements": "What the learner should ideally say, in natural language — not a rigid rubric, but the core ideas they should touch on",
                    "difficulty": 3,
                    "tags": "Optional metadata to support adaptivity, e.g., mid-lesson check-in, good exit question, reveals partial understanding",
                    "type": "short_answer_question"
                }
            ]
        }

        Create 4-6 questions that work together to comprehensively assess understanding of the concept.
        Each question should target a different aspect or thinking level. Do not include any additional
        text outside the JSON object.
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> list[LLMMessage]:
        # Validate required parameters
        self.validate_kwargs(["topic_title", "core_concept"], **kwargs)

        topic_title = kwargs.get("topic_title", "")
        core_concept = kwargs.get("core_concept", "")
        learning_objectives = kwargs.get("learning_objectives", [])
        previous_topics = kwargs.get("previous_topics", [])
        key_aspects = kwargs.get("key_aspects", [])
        avoid_overlap_with = kwargs.get("avoid_overlap_with", [])

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Previous Topics Covered: {", ".join(previous_topics) if previous_topics else "None"}

        Remember: These are short answer questions for assessment, not interactive dialogues.
        Focus on clear, unambiguous questions that test understanding and reasoning.
        Each question should target a different aspect of the concept.
        """

        # Build the user prompt with all the context
        user_content = f"""
        Create a set of short answer questions for:

        Topic: {topic_title}
        Core Concept: {core_concept}
        """

        if learning_objectives:
            user_content += f"\nLearning Objectives:\n{chr(10).join(f'- {obj}' for obj in learning_objectives)}"

        if key_aspects:
            user_content += f"\nKey Aspects to Cover:\n{chr(10).join(f'- {aspect}' for aspect in key_aspects)}"

        if avoid_overlap_with:
            user_content += f"\nAvoid Overlap With:\n{chr(10).join(f'- {item}' for item in avoid_overlap_with)}"

        user_content += """

        Create 4-6 short answer questions that:
        1. Cover different thinking levels (recall, explanation, application, analysis)
        2. Test different aspects of the concept
        3. Are clearly phrased with no ambiguity
        4. Progress from basic to more advanced reasoning
        5. Avoid redundancy with each other

        For each question, provide all the metadata in the exact format specified:
        ```
        Question [Number]
        Question: [clear, concise question]
        Purpose: [type of thinking being assessed]
        Target Concept: [specific concept focus]
        Expected Elements of a Good Answer: [core ideas learner should include]
        Difficulty: [1-5 scale]
        Tags: [metadata for adaptive usage]
        ```

        Ensure each question targets a different aspect and thinking level for comprehensive assessment.
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content),
        ]
