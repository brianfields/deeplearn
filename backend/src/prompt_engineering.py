"""
Prompt Engineering Helpers for Proactive Learning App

This module provides structured prompt templates and helpers for generating
effective prompts for the learning application. It includes templates for
syllabus generation, lesson creation, quiz generation, and assessment.

Key Features:
- Template-based prompt generation
- Dynamic content injection
- Validation and error handling
- Consistent formatting across all prompts
- Easy customization and extensibility
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

from llm_interface import LLMMessage, MessageRole
from data_structures import QuizType

class PromptType(str, Enum):
    """Types of prompts used in the learning system"""
    SYLLABUS_GENERATION = "syllabus_generation"
    LESSON_CONTENT = "lesson_content"
    QUIZ_GENERATION = "quiz_generation"
    ASSESSMENT_GRADING = "assessment_grading"
    PROGRESS_ANALYSIS = "progress_analysis"
    REVIEW_CONTENT = "review_content"
    DIFFICULTY_ADJUSTMENT = "difficulty_adjustment"

@dataclass
class PromptContext:
    """Context information for prompt generation"""
    user_level: str = "beginner"  # beginner, intermediate, advanced
    learning_style: str = "balanced"  # visual, auditory, kinesthetic, balanced
    time_constraint: int = 15  # minutes
    previous_performance: Dict[str, Any] = field(default_factory=dict)
    prerequisites_met: List[str] = field(default_factory=list)
    custom_instructions: Optional[str] = None

class PromptTemplate(ABC):
    """
    Abstract base class for prompt templates.

    Each template defines how to generate prompts for specific learning tasks.
    """

    def __init__(self, prompt_type: PromptType):
        self.prompt_type = prompt_type
        self.base_instructions = self._get_base_instructions()

    @abstractmethod
    def _get_base_instructions(self) -> str:
        """Get base instructions for this prompt type"""
        pass

    @abstractmethod
    def generate_prompt(self, context: PromptContext, **kwargs) -> List[LLMMessage]:
        """Generate prompt messages for the given context"""
        pass

    def _format_context(self, context: PromptContext) -> str:
        """Format context information for inclusion in prompts"""
        context_str = f"""
        User Level: {context.user_level}
        Learning Style: {context.learning_style}
        Time Constraint: {context.time_constraint} minutes
        Prerequisites Met: {', '.join(context.prerequisites_met) if context.prerequisites_met else 'None'}
        """

        if context.previous_performance:
            context_str += f"\nPrevious Performance: {json.dumps(context.previous_performance, indent=2)}"

        if context.custom_instructions:
            context_str += f"\nCustom Instructions: {context.custom_instructions}"

        return context_str.strip()

class SyllabusGenerationTemplate(PromptTemplate):
    """Template for generating learning syllabi"""

    def __init__(self):
        super().__init__(PromptType.SYLLABUS_GENERATION)

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

class LessonContentTemplate(PromptTemplate):
    """Template for generating lesson content"""

    def __init__(self):
        super().__init__(PromptType.LESSON_CONTENT)

    def _get_base_instructions(self) -> str:
        return """
        You are an expert educator specializing in professional skills training. Your task is to
        create engaging, interactive lesson content that promotes active learning.

        Key principles:
        1. Use conversational, engaging tone
        2. Include real-world examples and scenarios
        3. Break content into digestible chunks
        4. Include interactive elements (questions, exercises)
        5. Use markdown formatting for clarity
        6. Follow progressive disclosure (simple to complex)
        7. Include practical applications
        8. Encourage reflection and critical thinking
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> List[LLMMessage]:
        topic_title = kwargs.get('topic_title', '')
        topic_description = kwargs.get('topic_description', '')
        learning_objectives = kwargs.get('learning_objectives', [])
        previous_topics = kwargs.get('previous_topics', [])

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Previous Topics Covered: {', '.join(previous_topics) if previous_topics else 'None'}

        Lesson Structure:
        1. Opening Hook (1 minute) - Engaging question or scenario
        2. Core Content (10-12 minutes) - Main teaching content with examples
        3. Interactive Elements (2-3 minutes) - Questions, exercises, or discussions
        4. Summary & Next Steps (1 minute) - Key takeaways and transition

        Use markdown formatting and create an engaging, conversational experience.
        """

        user_content = f"""
        Create a comprehensive lesson for:

        Topic: {topic_title}
        Description: {topic_description}
        Learning Objectives:
        {chr(10).join(f"- {obj}" for obj in learning_objectives)}

        The lesson should be interactive, engaging, and completable in 15 minutes.
        Include real-world examples and practical applications.
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content)
        ]

class QuizGenerationTemplate(PromptTemplate):
    """Template for generating quiz questions"""

    def __init__(self):
        super().__init__(PromptType.QUIZ_GENERATION)

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

class AssessmentGradingTemplate(PromptTemplate):
    """Template for grading student responses"""

    def __init__(self):
        super().__init__(PromptType.ASSESSMENT_GRADING)

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

class ReviewContentTemplate(PromptTemplate):
    """Template for generating review content"""

    def __init__(self):
        super().__init__(PromptType.REVIEW_CONTENT)

    def _get_base_instructions(self) -> str:
        return """
        You are an expert in spaced repetition and memory consolidation. Your task is to
        create effective review content that helps students retain and strengthen their
        understanding of previously learned material.

        Key principles:
        1. Focus on key concepts and connections
        2. Use varied approaches to reinforce learning
        3. Include practical application opportunities
        4. Build on previous knowledge
        5. Use active recall techniques
        6. Provide elaborative rehearsal
        7. Connect to broader context
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> List[LLMMessage]:
        topic_title = kwargs.get('topic_title', '')
        original_content = kwargs.get('original_content', '')
        time_since_study = kwargs.get('time_since_study', 0)  # days
        previous_performance = kwargs.get('previous_performance', {})

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Time Since Original Study: {time_since_study} days
        Previous Performance: {json.dumps(previous_performance, indent=2) if previous_performance else 'No previous data'}

        Review Session Structure:
        1. Activation (2-3 minutes) - Quick recall of key concepts
        2. Reinforcement (8-10 minutes) - Deeper exploration and connections
        3. Application (3-5 minutes) - Practical exercises or scenarios
        4. Reflection (1-2 minutes) - Self-assessment and next steps
        """

        user_content = f"""
        Create a review session for:

        Topic: {topic_title}
        Days Since Study: {time_since_study}

        Original Content Summary:
        {original_content[:1500]}...  # First 1500 characters

        Focus on reinforcing key concepts and helping the student reconnect with the material.
        Use active recall and varied approaches to strengthen understanding.
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content)
        ]

class DifficultyAdjustmentTemplate(PromptTemplate):
    """Template for adjusting content difficulty"""

    def __init__(self):
        super().__init__(PromptType.DIFFICULTY_ADJUSTMENT)

    def _get_base_instructions(self) -> str:
        return """
        You are an expert in adaptive learning and instructional design. Your task is to
        adjust the difficulty level of learning content based on student performance.

        Key principles:
        1. Maintain appropriate challenge level
        2. Provide scaffolding when needed
        3. Advance difficulty gradually
        4. Consider individual learning patterns
        5. Preserve core learning objectives
        6. Adjust examples and explanations
        7. Modify practice exercises appropriately
        """

    def generate_prompt(self, context: PromptContext, **kwargs) -> List[LLMMessage]:
        current_content = kwargs.get('current_content', '')
        performance_data = kwargs.get('performance_data', {})
        adjustment_direction = kwargs.get('adjustment_direction', 'maintain')  # easier, harder, maintain

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Performance Data: {json.dumps(performance_data, indent=2) if performance_data else 'No data'}
        Adjustment Direction: {adjustment_direction}

        Adjustment Guidelines:
        - Easier: Simplify language, add more examples, break into smaller steps
        - Harder: Increase complexity, add advanced examples, require deeper thinking
        - Maintain: Keep current level but vary presentation style
        """

        user_content = f"""
        Please adjust the difficulty of this content:

        Current Content:
        {current_content}

        Adjustment Direction: {adjustment_direction}

        Maintain the core learning objectives while making the content more appropriate
        for the student's current performance level.
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content)
        ]

# Prompt Factory
class PromptFactory:
    """
    Factory class for creating prompt templates and generating prompts.

    This class provides a centralized way to access all prompt templates
    and generate prompts for different learning scenarios.
    """

    _templates = {
        PromptType.SYLLABUS_GENERATION: SyllabusGenerationTemplate,
        PromptType.LESSON_CONTENT: LessonContentTemplate,
        PromptType.QUIZ_GENERATION: QuizGenerationTemplate,
        PromptType.ASSESSMENT_GRADING: AssessmentGradingTemplate,
        PromptType.REVIEW_CONTENT: ReviewContentTemplate,
        PromptType.DIFFICULTY_ADJUSTMENT: DifficultyAdjustmentTemplate,
    }

    @classmethod
    def create_prompt(
        cls,
        prompt_type: PromptType,
        context: PromptContext,
        **kwargs
    ) -> List[LLMMessage]:
        """
        Create a prompt for the specified type and context.

        Args:
            prompt_type: Type of prompt to generate
            context: Context information for the prompt
            **kwargs: Additional template-specific parameters

        Returns:
            List of LLMMessage objects forming the prompt

        Raises:
            ValueError: If prompt type is not supported
        """
        if prompt_type not in cls._templates:
            raise ValueError(f"Unsupported prompt type: {prompt_type}")

        template = cls._templates[prompt_type]()
        return template.generate_prompt(context, **kwargs)

    @classmethod
    def get_available_types(cls) -> List[PromptType]:
        """Get list of available prompt types"""
        return list(cls._templates.keys())

# Helper functions
def create_default_context(
    user_level: str = "beginner",
    time_constraint: int = 15,
    **kwargs
) -> PromptContext:
    """
    Create a default prompt context with common settings.

    Args:
        user_level: User's skill level
        time_constraint: Time available in minutes
        **kwargs: Additional context parameters

    Returns:
        PromptContext object
    """
    return PromptContext(
        user_level=user_level,
        time_constraint=time_constraint,
        **kwargs
    )

def validate_prompt_response(response: str, expected_format: str = "json") -> bool:
    """
    Validate that a prompt response matches expected format.

    Args:
        response: Response from LLM
        expected_format: Expected format (json, text, etc.)

    Returns:
        True if valid, False otherwise
    """
    if expected_format == "json":
        try:
            json.loads(response)
            return True
        except json.JSONDecodeError:
            return False

    # Add other format validations as needed
    return True

# Example usage
if __name__ == "__main__":
    # Example: Generate a syllabus prompt
    context = create_default_context(user_level="intermediate")

    syllabus_prompt = PromptFactory.create_prompt(
        PromptType.SYLLABUS_GENERATION,
        context,
        topic="Project Management Fundamentals",
        user_refinements=["Focus on agile methodologies", "Include team communication"]
    )

    print("Generated Syllabus Prompt:")
    for message in syllabus_prompt:
        print(f"{message.role}: {message.content[:200]}...")
        print("-" * 50)