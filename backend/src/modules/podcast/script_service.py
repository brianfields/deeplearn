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
        """Create dynamic intro with Dan Carlin-style tone."""
        core_concept = segment_plan.title.split(" to ")[-1] if " to " in segment_plan.title else segment_plan.title

        # Extract key insights from topic content - clean it up
        content_sentences = topic_content.split('.')[:3]
        clean_sentences = []
        for sentence in content_sentences:
            # Remove markdown and clean up
            clean = sentence.replace('#', '').replace('*', '').replace('`', '').strip()
            if len(clean) > 20 and not clean.startswith('##'):
                clean_sentences.append(clean)

        content_context = ". ".join(clean_sentences) if clean_sentences else f"{core_concept} represents a fundamental shift in how we approach this problem."

        return f"""Imagine you're standing at the edge of something fundamental. {core_concept} isn't just another concept - it's a doorway to understanding how things actually work.

{content_context}

This isn't about memorizing facts. It's about seeing the patterns, understanding the why behind the what. When you grasp {core_concept}, you're not just learning - you're seeing the world differently.

The beauty of {core_concept} is that it connects everything. It's not isolated knowledge - it's a lens through which you can understand the entire field. And once you see it, you can't unsee it."""

    def _create_overview_script(self, segment_plan: SegmentPlan, topic_content: str) -> str:
        """Create dynamic overview with Dan Carlin-style tone."""
        outcomes = segment_plan.learning_outcomes
        if not outcomes:
            # Extract key concepts from topic content
            content_sentences = topic_content.split('.')[:5]
            key_concepts = []
            for sentence in content_sentences:
                clean = sentence.replace('#', '').replace('*', '').replace('`', '').strip()
                if len(clean) > 30 and not clean.startswith('##'):
                    key_concepts.append(clean)
            return f"We're going to dive into {', '.join(key_concepts[:3])}. Each piece connects to the next, building something larger than the sum of its parts. This isn't just theory - this is how the world actually works."

        concepts = [outcome.split('(')[0].strip() for outcome in outcomes]
        return f"""Here's what we're going to explore: {', '.join(concepts)}.

But here's the thing - these aren't separate topics. They're different angles of the same fundamental truth. Understanding one illuminates the others.

Each of these concepts builds on the others, creating a web of understanding that's stronger than any individual piece. This is how real learning happens - not in isolation, but in connection."""

    def _create_main_content_script(self, segment_plan: SegmentPlan, topic_content: str) -> str:
        """Create dynamic main content with Dan Carlin-style tone."""
        outcomes = segment_plan.learning_outcomes
        if not outcomes:
            # Extract insights from topic content
            content_sentences = topic_content.split('.')[:8]
            insights = []
            for sentence in content_sentences:
                clean = sentence.replace('#', '').replace('*', '').replace('`', '').strip()
                if len(clean) > 40 and not clean.startswith('##'):
                    insights.append(clean)
            return f"Let's look at what's actually happening here. {'. '.join(insights[:4])}. This isn't theory - this is how things work in practice. The patterns are everywhere once you know how to look."

        content_parts = []
        for outcome in outcomes:
            concept = outcome.split('(')[0].strip()
            # Extract specific details from the learning outcome
            if '(' in outcome:
                details = outcome.split('(')[1].split(')')[0]
                content_parts.append(f"{concept} - {details}. This isn't just academic knowledge. It's practical understanding that you can use immediately.")
            else:
                content_parts.append(f"{concept}. This is where theory meets reality, where abstract concepts become concrete tools.")

        # Add more depth to make it longer
        content_parts.append("The key insight here is that these aren't just rules to memorize. They're principles that emerge from deeper understanding. Once you see the pattern, you can apply it anywhere.")

        return " ".join(content_parts)

    def _create_summary_script(self, segment_plan: SegmentPlan, topic_content: str) -> str:
        """Create dynamic summary with Dan Carlin-style tone."""
        # Extract final insights from topic content
        content_sentences = topic_content.split('.')[-5:]
        final_insights = []
        for sentence in content_sentences:
            clean = sentence.replace('#', '').replace('*', '').replace('`', '').strip()
            if len(clean) > 30 and not clean.startswith('##'):
                final_insights.append(clean)

        return f"""So what have we learned? {'. '.join(final_insights[:3])}.

This isn't the end of the story - it's the beginning of seeing how these pieces fit together. Understanding {segment_plan.title} isn't about memorizing. It's about seeing the patterns that connect everything.

The real power comes when you start applying these principles to new problems. That's when you know you've truly understood - not when you can recite the facts, but when you can see the patterns in unfamiliar territory."""

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
