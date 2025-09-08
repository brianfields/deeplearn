"""
MCQ Evaluation Prompt

This module contains the prompt template for evaluating the quality
of a single MCQ.
"""

from .prompt_base import PromptContext, PromptTemplate
from modules.llm_services.module_api import LLMMessage, MessageRole


class MCQEvaluationPrompt(PromptTemplate):
    """Template for evaluating MCQ quality"""

    def __init__(self) -> None:
        super().__init__("mcq_evaluation")

    def _get_base_instructions(self) -> str:
        return """
        You are an expert in assessment design and item writing, familiar with authoritative guidelines:
        - Haladyna, Downing & Rodriguez's 31 item-writing rules,
        - NBME Item-Writing Manual,
        - Ebel & Frisbie's Essentials of Educational Measurement,
        - Bloom's Taxonomy.

        Your task: Evaluate the quality of ONE multiple-choice question (MCQ) according to the checklist below.

        ### Evaluation Checklist:

        1. **Alignment**
           - Does the MCQ directly assess the stated learning objective?
           - Does it match the intended Bloom's level (e.g., Remember, Understand, Apply)?

        2. **Stem Quality**
           - Is the stem a clear, complete question or problem (not a fill-in-the-blank)?
           - Can the stem be understood without reading the options?
           - Is wording concise and free of irrelevant detail?
           - Are negatives avoided or clearly emphasized if necessary?

        3. **Options**
           - Is there exactly one unambiguously correct answer?
           - Are distractors plausible and based on likely misconceptions or errors?
           - Are all options homogeneous in grammar, length, and complexity?
           - Are options free of clues (grammatical mismatches, longest answer, etc.)?
           - Are "all of the above," "none of the above," or combination options avoided?
           - Are options logically ordered (alphabetical, numeric, conceptual)?

        4. **Cognitive Challenge**
           - Does the MCQ test meaningful understanding or application (not trivial recall, unless that's the goal)?
           - Is difficulty appropriate (not too easy, not trickery)?

        5. **Clarity and Fairness**
           - Is the language clear and at an appropriate reading level?
           - Is the item free of cultural, regional, or gender bias?

        6. **Overall Quality**
           - Does the MCQ adhere to best-practice item-writing guidelines?
           - Would this item validly discriminate between students who have and have not attained the learning objective?

        ### Output Format:
        Return a JSON object with:

        ```json
        {
          "alignment": "your comments",
          "stem_quality": "your comments",
          "options_quality": "your comments",
          "cognitive_challenge": "your comments",
          "clarity_fairness": "your comments",
          "overall": "summary judgment and reasoning"
        }
        ```

        Do not include any additional text outside the JSON object.
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> list[LLMMessage]:
        # Validate required parameters
        self.validate_kwargs(["stem", "options", "correct_answer"], **kwargs)

        stem = kwargs.get("stem", "")
        options = kwargs.get("options", [])
        correct_answer = kwargs.get("correct_answer", "")
        learning_objective = kwargs.get("learning_objective", "")
        rationale = kwargs.get("rationale", "")

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Evaluate the MCQ based on authoritative item-writing guidelines and
        provide constructive feedback for improvement.
        """

        # Format options for display
        options_text = ""
        if isinstance(options, list):
            for i, option in enumerate(options):
                letter = chr(65 + i)  # A, B, C, D...
                options_text += f"{letter}) {option}\n"
        elif isinstance(options, dict):
            for letter, option in options.items():
                options_text += f"{letter}) {option}\n"
        else:
            options_text = str(options)

        user_content = f"""
        ### MCQ to Evaluate:
        - **STEM:** {stem}
        - **OPTIONS:**
        {options_text}
        - **CORRECT ANSWER:** {correct_answer}
        """

        if learning_objective:
            user_content += f"- **LEARNING OBJECTIVE:** {learning_objective}\n"

        if rationale:
            user_content += f"- **RATIONALE:** {rationale}\n"

        user_content += "\nNow perform the evaluation."

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content),
        ]
