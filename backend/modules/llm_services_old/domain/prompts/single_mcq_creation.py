"""
Single MCQ Creation Prompt

This module contains the prompt template for creating a single MCQ
from a refined topic and learning objective.
"""

from src.core.prompt_base import PromptContext, PromptTemplate
from src.llm_interface import LLMMessage, MessageRole


class SingleMCQCreationPrompt(PromptTemplate):
    """Template for creating a single MCQ from refined material"""

    def __init__(self) -> None:
        super().__init__("single_mcq_creation")

    def _get_base_instructions(self) -> str:
        return """
        You are an expert test item writer familiar with the authoritative guidelines for multiple‑choice question (MCQ) design (from Haladyna, Downing & Rodriguez's 31 item‑writing rules, the NBME Item‑Writing Manual, and Ebel & Frisbie's standards).

        Your task: Write ONE high‑quality multiple‑choice question for the given subtopic and learning objective.

        Follow these rules carefully:

        1. **Learning Objective Alignment**
           - The MCQ must directly assess the given learning objective.
           - Match the stated Bloom's level (e.g., Remember, Understand, Apply, Analyze, Evaluate).

        2. **Stem Construction**
           - Write the stem as a clear, complete question or problem, not a fill‑in‑the‑blank.
           - Include enough context to answer without reading the options first.
           - Avoid irrelevant details or extra wording.
           - Avoid negatives unless essential; if used, emphasize them (e.g., **NOT**).

        3. **Options**
           - Provide exactly one unambiguously correct answer (the key).
           - Provide 3 or more plausible distractors based on common misconceptions or errors.
           - All options must be homogeneous in grammar, length, and style.
           - Avoid "all of the above," "none of the above," or combinations like "A and C."
           - Order options logically (alphabetical or conceptual).

        4. **Cognitive Challenge**
           - The question should test understanding or application, not trivial recall (unless the learning objective is explicitly recall).
           - Do not use trick questions or unnecessary complexity.

        5. **Clarity and Fairness**
           - Language should be clear and at the appropriate reading level.
           - Avoid cultural or regional bias.

        6. **Output Format**
           - Return a JSON object with:
             - `stem`: the question stem,
             - `options`: an array of answer choices (strings),
             - `correct_answer`: the exact text of the correct answer,
             - `rationale`: a brief explanation of why the correct answer is correct and why the distractors are incorrect.

        Do not include any additional text outside the JSON object.
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> list[LLMMessage]:
        # Validate required parameters
        self.validate_kwargs(["subtopic", "learning_objective"], **kwargs)

        subtopic = kwargs.get("subtopic", "")
        learning_objective = kwargs.get("learning_objective", "")
        key_facts = kwargs.get("key_facts", [])
        common_misconceptions = kwargs.get("common_misconceptions", [])
        assessment_angles = kwargs.get("assessment_angles", [])

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Create a single high-quality MCQ that directly assesses the learning objective
        and incorporates the provided misconceptions as plausible distractors.
        """

        user_content = f"""
        **Input Parameters:**
        - **Subtopic:** {subtopic}
        - **Learning Objective:** {learning_objective}
        """

        if key_facts:
            user_content += f"\n- **Key Facts:** {', '.join(key_facts)}"

        if common_misconceptions:
            misconception_text = []
            for misconception in common_misconceptions:
                if isinstance(misconception, dict):
                    misconception_text.append(
                        f"Misconception: {misconception.get('misconception', '')}, Correct: {misconception.get('correct_concept', '')}"
                    )
                else:
                    misconception_text.append(str(misconception))
            user_content += f"\n- **Known Misconceptions:** {'; '.join(misconception_text)}"

        if assessment_angles:
            user_content += f"\n- **Assessment Angles:** {', '.join(assessment_angles)}"

        user_content += "\n\nNow create the MCQ."

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content),
        ]
