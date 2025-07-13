"""
Assessment Prompts

This module contains the prompt templates for assessment operations.
"""

from typing import List

from core import PromptTemplate, PromptContext
from llm_interface import LLMMessage, MessageRole
from data_structures import QuizType


class QuizGenerationPrompt(PromptTemplate):
    """Template for generating quiz questions"""

    def __init__(self):
        super().__init__("quiz_generation")

    def _get_base_instructions(self) -> str:
        return """
        You are an expert in educational assessment and quiz design. Your task is to create
        effective quiz questions that accurately measure learning outcomes.

        Key principles:
        1. Align questions with learning objectives
        2. Use appropriate difficulty level
        3. Include variety in question types
        4. Provide clear, unambiguous questions
        5. Include distractors that reveal common misconceptions
        6. Focus on application and understanding, not just memorization
        7. Provide educational explanations for correct answers
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> List[LLMMessage]:
        # Validate required parameters
        self.validate_kwargs(['topic_title', 'learning_objectives', 'lesson_content'], **kwargs)

        topic_title = kwargs.get('topic_title', '')
        learning_objectives = kwargs.get('learning_objectives', [])
        lesson_content = kwargs.get('lesson_content', '')
        question_count = kwargs.get('question_count', 5)
        question_types = kwargs.get('question_types', [QuizType.MULTIPLE_CHOICE])

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Question Types Available:
        - multiple_choice: 4 options, 1 correct answer
        - short_answer: Brief written response
        - scenario_critique: Analyze and critique a scenario

        Response Format:
        Generate a JSON response with the following structure:
        {{
            "questions": [
                {{
                    "id": "unique_id",
                    "type": "multiple_choice|short_answer|scenario_critique",
                    "question": "string",
                    "options": ["option1", "option2", "option3", "option4"],  // for multiple_choice only
                    "correct_answer": "string",
                    "explanation": "string",
                    "difficulty": 1-5,
                    "learning_objective": "string"
                }}
            ]
        }}
        """

        user_content = f"""
        Create {question_count} quiz questions for:

        Topic: {topic_title}
        Learning Objectives:
        {chr(10).join(f"- {obj}" for obj in learning_objectives)}

        Question Types: {', '.join(qt.value for qt in question_types)}

        Lesson Content Summary:
        {lesson_content[:1000]}...  # First 1000 characters

        Ensure questions test understanding and application, not just memorization.
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content)
        ]


class AssessmentGradingPrompt(PromptTemplate):
    """Template for grading student responses"""

    def __init__(self):
        super().__init__("assessment_grading")

    def _get_base_instructions(self) -> str:
        return """
        You are an expert educator and assessment specialist. Your task is to fairly
        and consistently grade student responses to quiz questions.

        Key principles:
        1. Be fair and consistent in grading
        2. Provide constructive feedback
        3. Recognize partial understanding
        4. Give specific suggestions for improvement
        5. Highlight what the student did well
        6. Use clear grading criteria
        7. Consider the learning level and context
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> List[LLMMessage]:
        # Validate required parameters
        self.validate_kwargs(['question', 'correct_answer', 'student_answer'], **kwargs)

        question = kwargs.get('question', '')
        correct_answer = kwargs.get('correct_answer', '')
        student_answer = kwargs.get('student_answer', '')
        question_type = kwargs.get('question_type', QuizType.SHORT_ANSWER)

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Grading Scale:
        - 1.0: Excellent (90-100%) - Demonstrates mastery
        - 0.8: Good (80-89%) - Shows solid understanding
        - 0.6: Satisfactory (60-79%) - Basic understanding with gaps
        - 0.4: Needs Improvement (40-59%) - Limited understanding
        - 0.2: Poor (20-39%) - Minimal understanding
        - 0.0: Incorrect (0-19%) - No understanding demonstrated

        Response Format:
        Generate a JSON response with the following structure:
        {{
            "score": 0.0-1.0,
            "feedback": "string",
            "strengths": ["string"],
            "areas_for_improvement": ["string"],
            "suggestions": ["string"]
        }}
        """

        user_content = f"""
        Please grade this student response:

        Question: {question}
        Question Type: {question_type.value}
        Correct Answer: {correct_answer}
        Student Answer: {student_answer}

        Provide a fair grade, constructive feedback, and specific suggestions for improvement.
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content)
        ]