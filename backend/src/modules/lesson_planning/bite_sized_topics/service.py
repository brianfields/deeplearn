"""
Bite-sized Topics Service

This module provides services for creating bite-sized topic content.
"""

from typing import Dict, List, Optional, Any
import logging

from core import ModuleService, ServiceConfig, LLMClient
from core.prompt_base import create_default_context
from .prompts import LessonContentPrompt


class BiteSizedTopicError(Exception):
    """Exception for bite-sized topic errors"""
    pass


class BiteSizedTopicService(ModuleService):
    """Service for creating bite-sized topic content"""

    def __init__(self, config: ServiceConfig, llm_client: LLMClient):
        super().__init__(config, llm_client)
        self.prompts = {
            'lesson_content': LessonContentPrompt(),
            # Future prompts will be added here
        }

    async def create_lesson_content(
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
            BiteSizedTopicError: If content generation fails
        """
        try:
            # Check cache first
            cache_key = f"lesson_{hash(topic_title + topic_description + user_level)}"

            context = create_default_context(
                user_level=user_level,
                time_constraint=15,
                previous_performance=user_performance or {}
            )

            messages = self.prompts['lesson_content'].generate_prompt(
                context,
                topic_title=topic_title,
                topic_description=topic_description,
                learning_objectives=learning_objectives,
                previous_topics=previous_topics or []
            )

            response = await self.llm_client.generate_response(messages)
            content = response.content

            self.logger.info(f"Generated lesson content for '{topic_title}' ({len(content)} characters)")
            return content

        except Exception as e:
            self.logger.error(f"Failed to generate lesson content: {e}")
            raise BiteSizedTopicError(f"Failed to generate lesson content: {e}")

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
            BiteSizedTopicError: If generation fails
        """
        # Placeholder implementation - will be replaced with proper prompt
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=5  # Shorter for snippets
            )

            # Using lesson content prompt as a temporary solution
            messages = self.prompts['lesson_content'].generate_prompt(
                context,
                topic_title=topic_title,
                topic_description=f"Brief explanation of {key_concept}",
                learning_objectives=[f"Understand {key_concept}"],
                previous_topics=[]
            )

            response = await self.llm_client.generate_response(messages)

            # Extract just the first section for a snippet
            content = response.content
            if '\n\n' in content:
                content = content.split('\n\n')[0]

            self.logger.info(f"Generated didactic snippet for '{key_concept}'")
            return content

        except Exception as e:
            self.logger.error(f"Failed to generate didactic snippet: {e}")
            raise BiteSizedTopicError(f"Failed to generate didactic snippet: {e}")

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
            BiteSizedTopicError: If generation fails
        """
        # Placeholder implementation - will be replaced with proper prompt
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=10
            )

            # Using lesson content prompt as a temporary solution
            messages = self.prompts['lesson_content'].generate_prompt(
                context,
                topic_title=topic_title,
                topic_description=f"Definitions for key terms in {topic_title}",
                learning_objectives=[f"Define and understand: {', '.join(terms)}"],
                previous_topics=[]
            )

            response = await self.llm_client.generate_response(messages)

            # For now, return a simple structure
            # This will be improved with a proper glossary prompt
            glossary = {}
            for term in terms:
                glossary[term] = f"Definition for {term} (placeholder)"

            self.logger.info(f"Generated glossary for '{topic_title}' with {len(terms)} terms")
            return glossary

        except Exception as e:
            self.logger.error(f"Failed to generate glossary: {e}")
            raise BiteSizedTopicError(f"Failed to generate glossary: {e}")

    async def validate_content(self, content: str) -> Dict[str, Any]:
        """
        Validate generated content for quality and structure.

        Args:
            content: Content to validate

        Returns:
            Validation results

        Raises:
            BiteSizedTopicError: If validation fails
        """
        try:
            issues = []

            # Basic content checks
            if not content or len(content.strip()) < 100:
                issues.append("Content too short")

            if len(content) > 5000:
                issues.append("Content too long for 15-minute lesson")

            # Check for markdown formatting
            if not any(marker in content for marker in ['#', '**', '*', '-', '1.']):
                issues.append("Content lacks proper formatting")

            # Check for interactive elements
            if not any(marker in content for marker in ['?', 'exercise', 'question', 'think', 'consider']):
                issues.append("Content lacks interactive elements")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "word_count": len(content.split()),
                "estimated_reading_time": len(content.split()) / 200  # Words per minute
            }

        except Exception as e:
            self.logger.error(f"Failed to validate content: {e}")
            raise BiteSizedTopicError(f"Failed to validate content: {e}")