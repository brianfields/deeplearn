"""
Podcast Script Service

This module handles generating podcast scripts from structure plans.
"""

import re
from datetime import datetime
from typing import Any

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext, PromptTemplate
from src.core.service_base import ModuleService, ServiceConfig
from src.data_structures import (
    PodcastScript,
    PodcastStructure,
    SegmentPlan,
    SegmentScript,
    ScriptMetadata,
)
from src.llm_interface import LLMMessage, MessageRole


class PodcastScriptServiceError(Exception):
    """Exception for podcast script service errors"""

    pass


class PodcastScriptPrompt(PromptTemplate):
    """Template for generating podcast scripts"""

    def __init__(self) -> None:
        super().__init__("podcast_script_generation")

    def _get_base_instructions(self) -> str:
        return """
        You are creating engaging educational podcast scripts for 4-5 minute episodes.

        Your task is to generate script content that:
        1. Fits within exact timing constraints
        2. Addresses specific learning outcomes
        3. Maintains listener engagement
        4. Uses conversational, educational tone
        5. Includes natural transitions and flow

        SCRIPT REQUIREMENTS:
        - Use conversational, engaging language
        - Include questions and reflection points
        - Provide concrete examples and real-world connections
        - Use clear, accessible explanations
        - Include natural pauses and transitions
        - Target ~150 words per minute for timing

        SEGMENT APPROACHES:
        - Intro Hook: Start with engaging question or surprising fact
        - Overview: Preview learning outcomes clearly
        - Main Content: Detailed explanations with examples
        - Summary: Reinforce key concepts and takeaways

        TONE GUIDELINES:
        - Conversational and friendly
        - Educational but not academic
        - Engaging and accessible
        - Include listener interaction
        """

    def generate_prompt(self, context: PromptContext, **kwargs: Any) -> list[LLMMessage]:  # noqa: ANN401
        # Validate required parameters
        self.validate_kwargs(["segment_plan", "topic_content"], **kwargs)

        segment_plan = kwargs.get("segment_plan")
        topic_content = kwargs.get("topic_content", "")
        learning_outcomes = kwargs.get("learning_outcomes", [])

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Generate script for segment: {segment_plan.segment_type}
        Target duration: {segment_plan.target_duration_seconds} seconds
        """

        user_content = f"""
        SEGMENT DETAILS:
        - Type: {segment_plan.segment_type}
        - Title: {segment_plan.title}
        - Purpose: {segment_plan.purpose}
        - Target Duration: {segment_plan.target_duration_seconds} seconds
        - Learning Outcomes: {', '.join(segment_plan.learning_outcomes)}
        - Content Focus: {segment_plan.content_focus}

        TOPIC CONTENT:
        {topic_content[:1000]}...

        LEARNING OUTCOMES TO ADDRESS:
        {chr(10).join(f"- {outcome}" for outcome in learning_outcomes)}

        Create a {segment_plan.target_duration_seconds}-second script that:
        1. Addresses the specified learning outcomes
        2. Fits the segment purpose and content focus
        3. Uses engaging, conversational language
        4. Includes natural transitions
        5. Provides educational value while maintaining engagement

        Return only the script content, no additional formatting.
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content),
        ]


class PodcastScriptService(ModuleService):
    """Service for generating podcast scripts from structure plans"""

    def __init__(self, config: ServiceConfig, llm_client: LLMClient) -> None:
        super().__init__(config, llm_client)
        self.script_prompt = PodcastScriptPrompt()

    async def initialize(self) -> None:
        """Initialize the service."""
        pass

    async def generate_podcast_script(
        self, structure: PodcastStructure, topic_content: str, topic_id: str = ""
    ) -> PodcastScript:
        """
        Generate complete podcast script from structure plan.

        Args:
            structure: Podcast structure plan
            topic_content: Content from the topic
            topic_id: ID of the topic for metadata

        Returns:
            PodcastScript object with complete script
        """
        if not structure:
            raise PodcastScriptServiceError("No structure provided")

        # Generate scripts for each segment
        segments = [
            structure.intro_hook,
            structure.overview,
            structure.main_content,
            structure.summary,
        ]

        segment_scripts = []
        for segment_plan in segments:
            script = await self.generate_segment_script(segment_plan, topic_content)
            segment_scripts.append(script)

        # Create full script by combining segments
        full_script = self._combine_segments(segment_scripts)

        # Create metadata
        metadata = ScriptMetadata(
            generation_timestamp=datetime.now(),
            topic_id=topic_id,
            structure_id="",  # Could be structure ID if we store it
            total_segments=len(segment_scripts),
            target_duration_seconds=structure.total_duration_seconds,
            actual_duration_seconds=sum(s.estimated_duration_seconds for s in segment_scripts),
            tone_style="conversational_educational",
            educational_level="beginner_intermediate",
        )

        # Create podcast script
        podcast_script = PodcastScript(
            title=f"Educational Podcast on {structure.intro_hook.title.split(' to ')[-1] if ' to ' in structure.intro_hook.title else 'Topic'}",
            description=f"Educational podcast covering {len(structure.learning_outcomes)} key concepts",
            segments=segment_scripts,
            total_duration_seconds=metadata.actual_duration_seconds,
            learning_outcomes=structure.learning_outcomes,
            metadata=metadata,
            full_script=full_script,
        )

        # Validate script timing
        if not await self.validate_script_timing(podcast_script):
            self.logger.warning("Script timing validation failed")

        self.logger.info(
            f"Generated podcast script: {len(segment_scripts)} segments, "
            f"{podcast_script.total_duration_seconds}s total"
        )

        return podcast_script

    async def generate_segment_script(self, segment_plan: SegmentPlan, topic_content: str) -> SegmentScript:
        """
        Generate script for a single segment.

        Args:
            segment_plan: Plan for the segment
            topic_content: Content from the topic

        Returns:
            SegmentScript object with script content
        """
        # For MVP, create default scripts based on segment type
        # In the future, this could use LLM to generate more sophisticated content
        content = self._create_default_segment_script(segment_plan, topic_content)

        # Calculate word count and estimated duration
        word_count = len(content.split())
        estimated_duration = self._estimate_duration(word_count)

        return SegmentScript(
            segment_type=segment_plan.segment_type,
            title=segment_plan.title,
            content=content,
            estimated_duration_seconds=estimated_duration,
            learning_outcomes=segment_plan.learning_outcomes,
            tone="conversational_educational",
            word_count=word_count,
        )

    def _create_default_segment_script(self, segment_plan: SegmentPlan, topic_content: str) -> str:
        """
        Create default script content for a segment.

        Args:
            segment_plan: Plan for the segment
            topic_content: Content from the topic

        Returns:
            Script content as string
        """
        segment_type = segment_plan.segment_type
        learning_outcomes = segment_plan.learning_outcomes

        if segment_type == "intro_hook":
            return self._create_intro_hook_script(segment_plan, topic_content)
        elif segment_type == "overview":
            return self._create_overview_script(segment_plan, topic_content)
        elif segment_type == "main_content":
            return self._create_main_content_script(segment_plan, topic_content)
        elif segment_type == "summary":
            return self._create_summary_script(segment_plan, topic_content)
        else:
            return f"Welcome to our lesson on {segment_plan.title}."

    def _create_intro_hook_script(self, segment_plan: SegmentPlan, topic_content: str) -> str:
        """Create engaging intro hook script."""
        topic_title = segment_plan.title.split(" to ")[-1] if " to " in segment_plan.title else "this topic"

        return f"""Welcome to our educational journey! Have you ever wondered about {topic_title}?

Today, we're going to explore some fascinating concepts that will help you understand this topic better. Whether you're just starting out or looking to deepen your knowledge, this episode has something for you.

Let's dive in and discover what makes {topic_title} so interesting and important. We'll cover everything from the basics to practical applications, so you can walk away with a solid understanding of these concepts.

Are you ready to learn something new? Let's get started!"""

    def _create_overview_script(self, segment_plan: SegmentPlan, topic_content: str) -> str:
        """Create overview script that previews learning outcomes."""
        outcomes_text = ""
        if segment_plan.learning_outcomes:
            outcomes_list = [f"'{outcome.split('(')[0].strip()}'" for outcome in segment_plan.learning_outcomes]
            if len(outcomes_list) == 1:
                outcomes_text = f"we'll focus on {outcomes_list[0]}"
            elif len(outcomes_list) == 2:
                outcomes_text = f"we'll explore {outcomes_list[0]} and {outcomes_list[1]}"
            else:
                outcomes_text = f"we'll cover several key concepts including {', '.join(outcomes_list[:-1])}, and {outcomes_list[-1]}"

        return f"""In this episode, {outcomes_text}.

We'll start with the fundamentals and build up to more advanced concepts. Each section will include practical examples and real-world applications to help you understand these ideas better.

By the end of this episode, you'll have a solid foundation in these concepts and be ready to apply them in your own learning journey. We'll also provide some practical tips and common pitfalls to avoid.

So, let's break this down into manageable pieces and make sure you understand each concept thoroughly before moving on to the next one."""

    def _create_main_content_script(self, segment_plan: SegmentPlan, topic_content: str) -> str:
        """Create detailed main content script."""
        outcomes = segment_plan.learning_outcomes
        if not outcomes:
            return "Let's explore the key concepts in detail. We'll start with the fundamental principles and then build up to more complex applications. Throughout this section, we'll use real-world examples to illustrate these concepts and help you understand how they work in practice."

        content_parts = []
        for i, outcome in enumerate(outcomes, 1):
            # Extract the main concept from the learning outcome
            concept = outcome.split('(')[0].strip()
            content_parts.append(f"First, let's look at {concept}. This is fundamental to understanding our topic. We'll explore what this means and why it's important. We'll also look at some practical examples to help you grasp this concept better.")

        # Add practical application
        content_parts.append("Now, let's see how these concepts work together in practice. Understanding these relationships will help you apply this knowledge effectively. We'll also discuss some common misconceptions and how to avoid them.")

        # Add engagement elements
        content_parts.append("As we explore these concepts, think about how they might apply to your own learning or work. What questions do you have? What aspects would you like to explore further?")

        return " ".join(content_parts)

    def _create_summary_script(self, segment_plan: SegmentPlan, topic_content: str) -> str:
        """Create summary script with key takeaways."""
        outcomes = segment_plan.learning_outcomes
        if not outcomes:
            return "Thank you for joining us in this exploration. We hope you found this episode helpful and informative. Remember to keep practicing and applying these concepts in your daily learning."

        # Create summary of key points
        key_points = []
        for outcome in outcomes:
            concept = outcome.split('(')[0].strip()
            key_points.append(concept)

        summary_text = f"Let's recap what we've learned today. We covered {', '.join(key_points)}. These concepts form the foundation of our topic and will serve you well in your continued learning."

        return f"""{summary_text}

Remember, learning is a journey, and every step forward counts. Keep exploring, keep asking questions, and keep growing your knowledge.

Thank you for joining us today. We hope this episode has been helpful and inspiring for your learning journey! Don't forget to practice these concepts regularly to reinforce your understanding."""

    def _estimate_duration(self, word_count: int) -> int:
        """
        Estimate speaking duration based on word count.

        Args:
            word_count: Number of words in script

        Returns:
            Estimated duration in seconds
        """
        # Average speaking rate: ~150 words per minute
        words_per_minute = 150
        minutes = word_count / words_per_minute
        return int(minutes * 60)

    def _combine_segments(self, segment_scripts: list[SegmentScript]) -> str:
        """
        Combine segment scripts into full script.

        Args:
            segment_scripts: List of segment scripts

        Returns:
            Combined full script
        """
        full_script_parts = []

        for i, segment in enumerate(segment_scripts):
            # Add segment header
            full_script_parts.append(f"\n--- {segment.title.upper()} ---\n")

            # Add segment content
            full_script_parts.append(segment.content)

            # Add transition (except for last segment)
            if i < len(segment_scripts) - 1:
                full_script_parts.append("\n[Transition]\n")

        return "\n".join(full_script_parts)

    async def validate_script_timing(self, script: PodcastScript) -> bool:
        """
        Validate that script timing meets requirements.

        Args:
            script: Podcast script to validate

        Returns:
            True if timing is valid, False otherwise
        """
        # Check total duration (4-5 minutes = 240-300 seconds)
        if not (240 <= script.total_duration_seconds <= 300):
            self.logger.warning(
                f"Script duration {script.total_duration_seconds}s outside 4-5 minute range"
            )
            return False

        # Check individual segment timing
        for segment in script.segments:
            if segment.segment_type == "intro_hook" and not (30 <= segment.estimated_duration_seconds <= 45):
                self.logger.warning(
                    f"Intro hook duration {segment.estimated_duration_seconds}s outside 30-45s range"
                )
                return False
            elif segment.segment_type == "overview" and not (30 <= segment.estimated_duration_seconds <= 45):
                self.logger.warning(
                    f"Overview duration {segment.estimated_duration_seconds}s outside 30-45s range"
                )
                return False
            elif segment.segment_type == "main_content" and not (120 <= segment.estimated_duration_seconds <= 180):
                self.logger.warning(
                    f"Main content duration {segment.estimated_duration_seconds}s outside 2-3 minute range"
                )
                return False
            elif segment.segment_type == "summary" and not (30 <= segment.estimated_duration_seconds <= 45):
                self.logger.warning(
                    f"Summary duration {segment.estimated_duration_seconds}s outside 30-45s range"
                )
                return False

        return True

    async def create_transitions(self, segments: list[SegmentScript]) -> dict[str, str]:
        """
        Create natural transitions between segments.

        Args:
            segments: List of segment scripts

        Returns:
            Dictionary mapping segment types to transition text
        """
        transitions = {}

        for i, segment in enumerate(segments):
            if i < len(segments) - 1:
                next_segment = segments[i + 1]

                if segment.segment_type == "intro_hook" and next_segment.segment_type == "overview":
                    transitions[segment.segment_type] = "Now let's explore what we'll cover today."
                elif segment.segment_type == "overview" and next_segment.segment_type == "main_content":
                    transitions[segment.segment_type] = "Let's dive deeper into these concepts."
                elif segment.segment_type == "main_content" and next_segment.segment_type == "summary":
                    transitions[segment.segment_type] = "Now let's summarize what we've learned."

        return transitions
