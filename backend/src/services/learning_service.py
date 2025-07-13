"""
Learning Service - High-level API for Learning Operations

This module provides a high-level service layer that orchestrates the various
learning modules to deliver complete learning functionality. It serves as
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

from llm_interface import LLMConfig, LLMProviderType
from core import LLMClient, ServiceConfig
from core.service_base import ServiceFactory
from modules.lesson_planning import LessonPlanningService
from modules.assessment import AssessmentService
from data_structures import QuizType, ProgressStatus, QuizQuestion, TopicProgressResponse

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

    This service orchestrates the various learning modules to provide a unified
    API for all learning-related operations.
    """

    def __init__(self, config: LearningServiceConfig):
        self.config = config
        self.llm_client = LLMClient(config.llm_config, config.cache_enabled)

        # Create service configuration for modules
        service_config = ServiceFactory.create_service_config(
            llm_config=config.llm_config,
            cache_enabled=config.cache_enabled,
            retry_attempts=config.retry_attempts
        )

        # Initialize module services
        self.lesson_planning = LessonPlanningService(service_config, self.llm_client)
        self.assessment = AssessmentService(service_config, self.llm_client)

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
            return await self.lesson_planning.generate_syllabus(
                topic=topic,
                user_level=user_level,
                user_refinements=user_refinements,
                custom_instructions=custom_instructions
            )
        except Exception as e:
            logger.error(f"Failed to generate syllabus: {e}")
            raise ContentGenerationError(f"Failed to generate syllabus: {e}")

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
            return await self.lesson_planning.generate_lesson_content(
                topic_title=topic_title,
                topic_description=topic_description,
                learning_objectives=learning_objectives,
                user_level=user_level,
                previous_topics=previous_topics,
                user_performance=user_performance
            )
        except Exception as e:
            logger.error(f"Failed to generate lesson content: {e}")
            raise ContentGenerationError(f"Failed to generate lesson content: {e}")

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

            return await self.assessment.generate_quiz(
                topic_title=topic_title,
                learning_objectives=learning_objectives,
                lesson_content=lesson_content,
                user_level=user_level,
                question_count=question_count,
                question_types=question_types
            )
        except Exception as e:
            logger.error(f"Failed to generate quiz: {e}")
            raise ContentGenerationError(f"Failed to generate quiz: {e}")

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
            return await self.assessment.grade_quiz_response(
                question=question,
                student_answer=student_answer,
                user_level=user_level
            )
        except Exception as e:
            logger.error(f"Failed to grade quiz response: {e}")
            raise AssessmentError(f"Failed to grade quiz response: {e}")

    async def create_complete_lesson_plan(
        self,
        topic: str,
        user_level: str = "beginner",
        user_refinements: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a complete lesson plan including syllabus and initial content.

        Args:
            topic: The learning topic
            user_level: User's skill level
            user_refinements: User's refinement requests
            custom_instructions: Additional custom instructions

        Returns:
            Complete lesson plan with syllabus and content

        Raises:
            ContentGenerationError: If lesson plan creation fails
        """
        try:
            return await self.lesson_planning.create_complete_lesson_plan(
                topic=topic,
                user_level=user_level,
                user_refinements=user_refinements,
                custom_instructions=custom_instructions
            )
        except Exception as e:
            logger.error(f"Failed to create complete lesson plan: {e}")
            raise ContentGenerationError(f"Failed to create complete lesson plan: {e}")

    async def create_didactic_snippet(
        self,
        topic_title: str,
        key_concept: str,
        user_level: str = "beginner"
    ) -> str:
        """
        Create a didactic snippet for a specific concept.

        Args:
            topic_title: Title of the topic
            key_concept: Key concept to explain
            user_level: User's skill level

        Returns:
            Generated didactic snippet

        Raises:
            ContentGenerationError: If snippet generation fails
        """
        try:
            return await self.lesson_planning.create_didactic_snippet(
                topic_title=topic_title,
                key_concept=key_concept,
                user_level=user_level
            )
        except Exception as e:
            logger.error(f"Failed to create didactic snippet: {e}")
            raise ContentGenerationError(f"Failed to create didactic snippet: {e}")

    async def create_glossary(
        self,
        topic_title: str,
        terms: List[str],
        user_level: str = "beginner"
    ) -> Dict[str, str]:
        """
        Create a glossary of terms for a topic.

        Args:
            topic_title: Title of the topic
            terms: List of terms to define
            user_level: User's skill level

        Returns:
            Dictionary mapping terms to definitions

        Raises:
            ContentGenerationError: If glossary generation fails
        """
        try:
            return await self.lesson_planning.create_glossary(
                topic_title=topic_title,
                terms=terms,
                user_level=user_level
            )
        except Exception as e:
            logger.error(f"Failed to create glossary: {e}")
            raise ContentGenerationError(f"Failed to create glossary: {e}")

    async def grade_quiz(
        self,
        quiz_questions: List[QuizQuestion],
        student_answers: List[str],
        user_level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Grade a complete quiz with multiple questions.

        Args:
            quiz_questions: List of quiz questions
            student_answers: List of student answers
            user_level: User's skill level

        Returns:
            Dictionary containing overall results

        Raises:
            AssessmentError: If grading fails
        """
        try:
            return await self.assessment.grade_quiz(
                quiz_questions=quiz_questions,
                student_answers=student_answers,
                user_level=user_level
            )
        except Exception as e:
            logger.error(f"Failed to grade quiz: {e}")
            raise AssessmentError(f"Failed to grade quiz: {e}")

    async def analyze_quiz_results(self, quiz_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze quiz results to provide insights and recommendations.

        Args:
            quiz_results: Results from grade_quiz method

        Returns:
            Analysis and recommendations

        Raises:
            AssessmentError: If analysis fails
        """
        try:
            return await self.assessment.analyze_quiz_results(quiz_results)
        except Exception as e:
            logger.error(f"Failed to analyze quiz results: {e}")
            raise AssessmentError(f"Failed to analyze quiz results: {e}")

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

    async def get_service_health(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of all services.

        Returns:
            Dictionary containing health status of all services
        """
        try:
            return {
                "learning_service": {
                    "status": "healthy",
                    "config": {
                        "default_lesson_duration": self.config.default_lesson_duration,
                        "max_quiz_questions": self.config.max_quiz_questions,
                        "mastery_threshold": self.config.mastery_threshold
                    }
                },
                "llm_client": await self.llm_client.health_check(),
                "modules": await self.lesson_planning.get_service_status()
            }
        except Exception as e:
            logger.error(f"Failed to get service health: {e}")
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
            "llm_client_stats": self.llm_client.get_stats(),
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
    provider: str = "openai",
    cache_enabled: bool = True,
    **kwargs
) -> LearningService:
    """
    Create a learning service with common configuration.

    Args:
        api_key: API key for the LLM provider
        model: Model to use
        provider: Provider name
        cache_enabled: Whether to enable caching
        **kwargs: Additional configuration parameters

    Returns:
        Configured LearningService instance
    """
    llm_config = LLMConfig(
        provider=LLMProviderType(provider),
        model=model,
        api_key=api_key,
        temperature=kwargs.get('temperature', 0.7),
        max_tokens=kwargs.get('max_tokens', 1500)
    )

    service_config = LearningServiceConfig(
        llm_config=llm_config,
        cache_enabled=cache_enabled,
        default_lesson_duration=kwargs.get('default_lesson_duration', 15),
        max_quiz_questions=kwargs.get('max_quiz_questions', 10),
        min_quiz_questions=kwargs.get('min_quiz_questions', 3),
        mastery_threshold=kwargs.get('mastery_threshold', 0.9),
        retry_attempts=kwargs.get('retry_attempts', 3)
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

        # Create complete lesson plan
        lesson_plan = await service.create_complete_lesson_plan(
            topic="Data Science Fundamentals",
            user_level="beginner"
        )
        print(f"Created complete lesson plan with {len(lesson_plan['lesson_contents'])} content pieces")

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

        # Check service health
        health = await service.get_service_health()
        print(f"Service health: {health}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(example_usage())