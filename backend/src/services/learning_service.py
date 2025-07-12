"""
Learning Service - High-level API for Learning Operations

This module provides a high-level service layer that combines the LLM interface
with prompt engineering to deliver complete learning functionality. It serves as
the main API for the learning application.

Key Features:
- Syllabus generation and refinement
- Lesson content creation
- Quiz generation and grading
- Progress tracking and analysis
- Review content generation
- Adaptive difficulty adjustment
- Comprehensive error handling and logging
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from llm_interface import (
    LLMConfig,
    create_llm_provider, LLMError, LLMProviderType
)
from prompt_engineering import (PromptFactory, PromptType, create_default_context)
from data_structures import (
    QuizType, ProgressStatus, QuizQuestion, TopicProgressResponse
)

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class LearningServiceConfig:
    """Configuration for the learning service"""
    llm_config: LLMConfig
    default_lesson_duration: int = 15
    max_quiz_questions: int = 10
    min_quiz_questions: int = 3
    mastery_threshold: float = 0.9
    retry_attempts: int = 3
    cache_enabled: bool = True

class LearningServiceError(Exception):
    """Base exception for learning service errors"""
    pass

class ContentGenerationError(LearningServiceError):
    """Error in content generation"""
    pass

class AssessmentError(LearningServiceError):
    """Error in assessment operations"""
    pass

class LearningService:
    """
    High-level service for learning operations.

    This service provides a clean API for all learning-related operations,
    handling the complexity of LLM interactions and prompt engineering.
    """

    def __init__(self, config: LearningServiceConfig):
        self.config = config
        self.llm_provider = create_llm_provider(config.llm_config)
        self.prompt_factory = PromptFactory()
        self._content_cache = {} if config.cache_enabled else None

    async def generate_syllabus(
        self,
        topic: str,
        user_level: str = "beginner",
        user_refinements: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a learning syllabus for a given topic.

        Args:
            topic: The learning topic
            user_level: User's skill level (beginner, intermediate, advanced)
            user_refinements: User's refinement requests
            custom_instructions: Additional custom instructions

        Returns:
            Dictionary containing syllabus data

        Raises:
            ContentGenerationError: If syllabus generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=self.config.default_lesson_duration,
                custom_instructions=custom_instructions
            )

            messages = self.prompt_factory.create_prompt(
                PromptType.SYLLABUS_GENERATION,
                context,
                topic=topic,
                user_refinements=user_refinements or []
            )

            # Define expected schema
            schema = {
                "type": "object",
                "properties": {
                    "topic_name": {"type": "string"},
                    "description": {"type": "string"},
                    "estimated_total_hours": {"type": "number"},
                    "topics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "learning_objectives": {"type": "array", "items": {"type": "string"}},
                                "estimated_duration": {"type": "number"},
                                "difficulty_level": {"type": "number"},
                                "prerequisite_topics": {"type": "array", "items": {"type": "string"}},
                                "assessment_type": {"type": "string"}
                            },
                            "required": ["title", "description", "learning_objectives"]
                        }
                    }
                },
                "required": ["topic_name", "description", "topics"]
            }

            response = await self.llm_provider.generate_structured_response(
                messages, schema
            )

            # Validate response
            if not response.get("topics") or len(response["topics"]) > 20:
                raise ContentGenerationError("Invalid syllabus structure or too many topics")

            logger.info(f"Generated syllabus for '{topic}' with {len(response['topics'])} topics")
            return response

        except LLMError as e:
            raise ContentGenerationError(f"Failed to generate syllabus: {e}")
        except Exception as e:
            raise ContentGenerationError(f"Unexpected error generating syllabus: {e}")

    async def generate_lesson_content(
        self,
        topic_title: str,
        topic_description: str,
        learning_objectives: List[str],
        user_level: str = "beginner",
        previous_topics: Optional[List[str]] = None,
        user_performance: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate lesson content for a specific topic.

        Args:
            topic_title: Title of the topic
            topic_description: Description of the topic
            learning_objectives: List of learning objectives
            user_level: User's skill level
            previous_topics: Previously covered topics
            user_performance: User's previous performance data

        Returns:
            Generated lesson content in markdown format

        Raises:
            ContentGenerationError: If content generation fails
        """
        try:
            # Check cache first
            cache_key = f"lesson_{hash(topic_title + topic_description + user_level)}"
            if self._content_cache and cache_key in self._content_cache:
                logger.info(f"Using cached lesson content for '{topic_title}'")
                return self._content_cache[cache_key]

            context = create_default_context(
                user_level=user_level,
                time_constraint=self.config.default_lesson_duration,
                previous_performance=user_performance or {}
            )

            messages = self.prompt_factory.create_prompt(
                PromptType.LESSON_CONTENT,
                context,
                topic_title=topic_title,
                topic_description=topic_description,
                learning_objectives=learning_objectives,
                previous_topics=previous_topics or []
            )

            response = await self.llm_provider.generate_response(messages)
            content = response.content

            # Cache the content
            if self._content_cache:
                self._content_cache[cache_key] = content

            logger.info(f"Generated lesson content for '{topic_title}' ({len(content)} characters)")
            return content

        except LLMError as e:
            raise ContentGenerationError(f"Failed to generate lesson content: {e}")
        except Exception as e:
            raise ContentGenerationError(f"Unexpected error generating lesson content: {e}")

    async def generate_quiz(
        self,
        topic_title: str,
        learning_objectives: List[str],
        lesson_content: str,
        user_level: str = "beginner",
        question_count: int = 5,
        question_types: Optional[List[QuizType]] = None
    ) -> List[QuizQuestion]:
        """
        Generate quiz questions for a topic.

        Args:
            topic_title: Title of the topic
            learning_objectives: List of learning objectives
            lesson_content: The lesson content
            user_level: User's skill level
            question_count: Number of questions to generate
            question_types: Types of questions to generate

        Returns:
            List of QuizQuestion objects

        Raises:
            ContentGenerationError: If quiz generation fails
        """
        try:
            # Validate question count
            question_count = max(
                self.config.min_quiz_questions,
                min(question_count, self.config.max_quiz_questions)
            )

            if question_types is None:
                question_types = [QuizType.MULTIPLE_CHOICE, QuizType.SHORT_ANSWER]

            context = create_default_context(user_level=user_level)

            messages = self.prompt_factory.create_prompt(
                PromptType.QUIZ_GENERATION,
                context,
                topic_title=topic_title,
                learning_objectives=learning_objectives,
                lesson_content=lesson_content,
                question_count=question_count,
                question_types=question_types
            )

            schema = {
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "question": {"type": "string"},
                                "options": {"type": "array", "items": {"type": "string"}},
                                "correct_answer": {"type": "string"},
                                "explanation": {"type": "string"},
                                "difficulty": {"type": "number"},
                                "learning_objective": {"type": "string"}
                            },
                            "required": ["id", "type", "question", "correct_answer"]
                        }
                    }
                },
                "required": ["questions"]
            }

            response = await self.llm_provider.generate_structured_response(
                messages, schema
            )

            # Convert to QuizQuestion objects
            quiz_questions = []
            for q_data in response["questions"]:
                quiz_questions.append(QuizQuestion(
                    id=q_data["id"],
                    type=QuizType(q_data["type"]),
                    question=q_data["question"],
                    options=q_data.get("options"),
                    correct_answer=q_data["correct_answer"],
                    explanation=q_data.get("explanation")
                ))

            logger.info(f"Generated {len(quiz_questions)} quiz questions for '{topic_title}'")
            return quiz_questions

        except LLMError as e:
            raise ContentGenerationError(f"Failed to generate quiz: {e}")
        except Exception as e:
            raise ContentGenerationError(f"Unexpected error generating quiz: {e}")

    async def grade_quiz_response(
        self,
        question: QuizQuestion,
        student_answer: str,
        user_level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Grade a student's response to a quiz question.

        Args:
            question: The quiz question
            student_answer: Student's answer
            user_level: User's skill level

        Returns:
            Dictionary containing score and feedback

        Raises:
            AssessmentError: If grading fails
        """
        try:
            context = create_default_context(user_level=user_level)

            messages = self.prompt_factory.create_prompt(
                PromptType.ASSESSMENT_GRADING,
                context,
                question=question.question,
                correct_answer=question.correct_answer,
                student_answer=student_answer,
                question_type=question.type
            )

            schema = {
                "type": "object",
                "properties": {
                    "score": {"type": "number", "minimum": 0, "maximum": 1},
                    "feedback": {"type": "string"},
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "areas_for_improvement": {"type": "array", "items": {"type": "string"}},
                    "suggestions": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["score", "feedback"]
            }

            response = await self.llm_provider.generate_structured_response(
                messages, schema
            )

            logger.info(f"Graded response for question {question.id}: {response['score']}")
            return response

        except LLMError as e:
            raise AssessmentError(f"Failed to grade response: {e}")
        except Exception as e:
            raise AssessmentError(f"Unexpected error grading response: {e}")

    async def generate_review_content(
        self,
        topic_title: str,
        original_content: str,
        time_since_study: int,
        user_level: str = "beginner",
        previous_performance: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate review content for spaced repetition.

        Args:
            topic_title: Title of the topic to review
            original_content: Original lesson content
            time_since_study: Days since original study
            user_level: User's skill level
            previous_performance: Previous performance data

        Returns:
            Generated review content

        Raises:
            ContentGenerationError: If review generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=self.config.default_lesson_duration,
                previous_performance=previous_performance or {}
            )

            messages = self.prompt_factory.create_prompt(
                PromptType.REVIEW_CONTENT,
                context,
                topic_title=topic_title,
                original_content=original_content,
                time_since_study=time_since_study,
                previous_performance=previous_performance or {}
            )

            response = await self.llm_provider.generate_response(messages)
            content = response.content

            logger.info(f"Generated review content for '{topic_title}' ({time_since_study} days since study)")
            return content

        except LLMError as e:
            raise ContentGenerationError(f"Failed to generate review content: {e}")
        except Exception as e:
            raise ContentGenerationError(f"Unexpected error generating review content: {e}")

    async def adjust_content_difficulty(
        self,
        current_content: str,
        performance_data: Dict[str, Any],
        adjustment_direction: str = "maintain"
    ) -> str:
        """
        Adjust content difficulty based on performance.

        Args:
            current_content: Current content to adjust
            performance_data: Performance data for analysis
            adjustment_direction: Direction to adjust (easier, harder, maintain)

        Returns:
            Adjusted content

        Raises:
            ContentGenerationError: If adjustment fails
        """
        try:
            context = create_default_context(
                previous_performance=performance_data
            )

            messages = self.prompt_factory.create_prompt(
                PromptType.DIFFICULTY_ADJUSTMENT,
                context,
                current_content=current_content,
                performance_data=performance_data,
                adjustment_direction=adjustment_direction
            )

            response = await self.llm_provider.generate_response(messages)
            adjusted_content = response.content

            logger.info(f"Adjusted content difficulty: {adjustment_direction}")
            return adjusted_content

        except LLMError as e:
            raise ContentGenerationError(f"Failed to adjust content difficulty: {e}")
        except Exception as e:
            raise ContentGenerationError(f"Unexpected error adjusting content: {e}")

    async def analyze_learning_progress(
        self,
        topic_progress: List[TopicProgressResponse],
        recent_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze learning progress and provide recommendations.

        Args:
            topic_progress: List of topic progress data
            recent_performance: Recent performance data

        Returns:
            Analysis results and recommendations
        """
        try:
            # Calculate overall metrics
            total_topics = len(topic_progress)
            mastered_topics = sum(1 for tp in topic_progress if tp.status == ProgressStatus.MASTERY)
            average_mastery = sum(tp.mastery_level for tp in topic_progress) / total_topics if total_topics > 0 else 0

            # Identify topics needing review
            topics_needing_review = [
                tp for tp in topic_progress
                if tp.next_review_date and tp.next_review_date <= datetime.utcnow()
            ]

            # Calculate learning velocity
            recent_completions = [
                tp for tp in topic_progress
                if tp.last_studied and tp.last_studied >= datetime.utcnow() - timedelta(days=7)
            ]

            analysis = {
                "overall_progress": {
                    "total_topics": total_topics,
                    "mastered_topics": mastered_topics,
                    "completion_rate": mastered_topics / total_topics if total_topics > 0 else 0,
                    "average_mastery_level": average_mastery
                },
                "recent_activity": {
                    "topics_studied_last_week": len(recent_completions),
                    "average_time_per_topic": sum(tp.total_time_spent for tp in recent_completions) / len(recent_completions) if recent_completions else 0
                },
                "review_recommendations": {
                    "topics_due_for_review": len(topics_needing_review),
                    "priority_topics": [tp.topic_id for tp in topics_needing_review[:3]]  # Top 3
                },
                "performance_trends": recent_performance
            }

            logger.info(f"Analyzed progress for {total_topics} topics, {mastered_topics} mastered")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing learning progress: {e}")
            return {"error": str(e)}

    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get service statistics and health information.

        Returns:
            Dictionary containing service statistics
        """
        return {
            "provider": self.config.llm_config.provider.value,
            "model": self.config.llm_config.model,
            "cache_enabled": self.config.cache_enabled,
            "cache_size": len(self._content_cache) if self._content_cache else 0,
            "configuration": {
                "default_lesson_duration": self.config.default_lesson_duration,
                "max_quiz_questions": self.config.max_quiz_questions,
                "mastery_threshold": self.config.mastery_threshold
            }
        }

# Helper functions for service initialization
def create_learning_service(
    api_key: str,
    model: str = "gpt-3.5-turbo",
    provider: str = "openai"
) -> LearningService:
    """
    Create a learning service with common configuration.

    Args:
        api_key: API key for the LLM provider
        model: Model to use
        provider: Provider name

    Returns:
        Configured LearningService instance
    """
    llm_config = LLMConfig(
        provider=LLMProviderType(provider),
        model=model,
        api_key=api_key,
        temperature=0.7,
        max_tokens=1500
    )

    service_config = LearningServiceConfig(
        llm_config=llm_config,
        cache_enabled=True
    )

    return LearningService(service_config)

# Example usage
async def example_usage():
    """Example of how to use the learning service"""

    # Create service
    service = create_learning_service(
        api_key="your-api-key-here",
        model="gpt-3.5-turbo"
    )

    try:
        # Generate syllabus
        syllabus = await service.generate_syllabus(
            topic="Data Science Fundamentals",
            user_level="beginner"
        )
        print(f"Generated syllabus with {len(syllabus['topics'])} topics")

        # Generate lesson content
        if syllabus['topics']:
            first_topic = syllabus['topics'][0]
            lesson_content = await service.generate_lesson_content(
                topic_title=first_topic['title'],
                topic_description=first_topic['description'],
                learning_objectives=first_topic['learning_objectives']
            )
            print(f"Generated lesson content: {len(lesson_content)} characters")

            # Generate quiz
            quiz_questions = await service.generate_quiz(
                topic_title=first_topic['title'],
                learning_objectives=first_topic['learning_objectives'],
                lesson_content=lesson_content,
                question_count=3
            )
            print(f"Generated {len(quiz_questions)} quiz questions")

            # Grade a sample response
            if quiz_questions:
                sample_grade = await service.grade_quiz_response(
                    question=quiz_questions[0],
                    student_answer="Sample answer",
                    user_level="beginner"
                )
                print(f"Sample grade: {sample_grade['score']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(example_usage())