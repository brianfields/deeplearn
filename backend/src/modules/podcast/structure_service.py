"""
Podcast Structure Service

This module handles planning podcast structure and timing based on learning outcomes.
"""

from typing import Any

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext, PromptTemplate
from src.core.service_base import ModuleService, ServiceConfig
from src.data_structures import PodcastStructure, SegmentPlan, TimedStructure, FlowPlan
from src.llm_interface import LLMMessage, MessageRole


class PodcastStructureServiceError(Exception):
    """Exception for podcast structure service errors"""

    pass


class PodcastStructurePrompt(PromptTemplate):
    """Template for planning podcast structure"""

    def __init__(self) -> None:
        super().__init__("podcast_structure_planning")

    def _get_base_instructions(self) -> str:
        return """
        You are planning a 4-5 minute educational podcast structure.

        Your task is to create a structured plan for a podcast that:
        1. Distributes learning outcomes across 4 segments appropriately
        2. Maintains engagement throughout the podcast
        3. Provides clear educational progression
        4. Fits within 4-5 minute timing constraints

        SEGMENT TYPES:
        - intro_hook: 30-45 seconds - Engaging opening to hook listeners
        - overview: 30-45 seconds - Preview of what will be covered
        - main_content: 2-3 minutes - Detailed coverage of learning outcomes
        - summary: 30-45 seconds - Key takeaways and reinforcement

        TIMING CONSTRAINTS:
        - Total duration: 4-5 minutes (240-300 seconds)
        - Intro hook: 30-45 seconds
        - Overview: 30-45 seconds
        - Main content: 2-3 minutes (120-180 seconds)
        - Summary: 30-45 seconds

        LEARNING OUTCOME DISTRIBUTION:
        - Intro hook: 0-1 outcomes (focus on engagement)
        - Overview: 1-2 outcomes (preview what will be covered)
        - Main content: 2-3 outcomes (detailed coverage)
        - Summary: 1-2 outcomes (key takeaways)

        Each segment should have:
        - Clear purpose and focus
        - Appropriate learning outcomes assigned
        - Natural transitions in and out
        - Engaging content approach
        """

    def generate_prompt(self, context: PromptContext, **kwargs: Any) -> list[LLMMessage]:  # noqa: ANN401
        # Validate required parameters
        self.validate_kwargs(["learning_outcomes"], **kwargs)

        learning_outcomes = kwargs.get("learning_outcomes", [])
        topic_title = kwargs.get("topic_title", "Educational Topic")

        system_message = f"""
        {self.base_instructions}

        Context Information:
        {self._format_context(context)}

        Create a podcast structure plan for: {topic_title}
        """

        user_content = f"""
        Learning Outcomes to Structure:
        {chr(10).join(f"- {outcome}" for outcome in learning_outcomes)}

        Create a complete podcast structure plan that:
        1. Distributes these learning outcomes across 4 segments
        2. Maintains total duration of 4-5 minutes
        3. Creates engaging flow between segments
        4. Provides clear educational progression

        Return a structured plan with:
        - Segment plans for intro_hook, overview, main_content, summary
        - Timing allocation for each segment
        - Learning outcome distribution
        - Transition planning
        """

        return [
            LLMMessage(role=MessageRole.SYSTEM, content=system_message),
            LLMMessage(role=MessageRole.USER, content=user_content),
        ]


class PodcastStructureService(ModuleService):
    """Service for planning podcast structure and timing"""

    def __init__(self, config: ServiceConfig, llm_client: LLMClient) -> None:
        super().__init__(config, llm_client)
        self.structure_prompt = PodcastStructurePrompt()

    async def initialize(self) -> None:
        """Initialize the service."""
        pass

    async def plan_podcast_structure(
        self, learning_outcomes: list[str], topic_title: str = "Educational Topic"
    ) -> PodcastStructure:
        """
        Plan podcast structure based on learning outcomes.

        Args:
            learning_outcomes: List of learning outcomes to structure
            topic_title: Title of the topic for context

        Returns:
            PodcastStructure object with complete segment plans
        """
        if not learning_outcomes:
            raise PodcastStructureServiceError("No learning outcomes provided")

        # For MVP, create a default structure based on learning outcomes
        # In the future, this could use LLM to generate more sophisticated structures
        structure = self._create_default_structure(learning_outcomes, topic_title)

        return structure

    def _create_default_structure(self, learning_outcomes: list[str], topic_title: str) -> PodcastStructure:
        """
        Create a default podcast structure based on learning outcomes.

        Args:
            learning_outcomes: List of learning outcomes
            topic_title: Title of the topic

        Returns:
            PodcastStructure with default segment plans
        """
        # Default timing allocation
        timing = {
            "intro_hook": 35,
            "overview": 40,
            "main_content": 150,
            "summary": 35
        }

        # Distribute learning outcomes across segments
        outcomes_by_segment = self._distribute_learning_outcomes(learning_outcomes)

        # Create segment plans
        intro_hook = SegmentPlan(
            segment_type="intro_hook",
            title=f"Introduction to {topic_title}",
            purpose="Engage listeners and introduce the topic",
            target_duration_seconds=timing["intro_hook"],
            learning_outcomes=outcomes_by_segment["intro_hook"],
            content_focus="Hook with real-world example or interesting fact",
            transition_in="Welcome to our lesson on",
            transition_out="Now let's explore what we'll cover today"
        )

        overview = SegmentPlan(
            segment_type="overview",
            title="What We'll Learn",
            purpose="Preview the key concepts we'll cover",
            target_duration_seconds=timing["overview"],
            learning_outcomes=outcomes_by_segment["overview"],
            content_focus="Brief overview of all learning outcomes",
            transition_in="Today we'll cover several important concepts",
            transition_out="Let's dive deeper into the first concept"
        )

        main_content = SegmentPlan(
            segment_type="main_content",
            title="Deep Dive into Concepts",
            purpose="Detailed coverage of all learning outcomes",
            target_duration_seconds=timing["main_content"],
            learning_outcomes=outcomes_by_segment["main_content"],
            content_focus="Detailed explanation with examples and applications",
            transition_in="Let's start with the fundamental concepts",
            transition_out="Now let's summarize what we've learned"
        )

        summary = SegmentPlan(
            segment_type="summary",
            title="Key Takeaways",
            purpose="Reinforce main concepts and provide closure",
            target_duration_seconds=timing["summary"],
            learning_outcomes=outcomes_by_segment["summary"],
            content_focus="Key points and practical applications",
            transition_in="To summarize what we've learned today",
            transition_out="Thank you for joining us in this exploration"
        )

        total_duration = sum(timing.values())

        return PodcastStructure(
            intro_hook=intro_hook,
            overview=overview,
            main_content=main_content,
            summary=summary,
            total_duration_seconds=total_duration,
            learning_outcomes=learning_outcomes
        )

    def _distribute_learning_outcomes(self, learning_outcomes: list[str]) -> dict[str, list[str]]:
        """
        Distribute learning outcomes across podcast segments.

        Args:
            learning_outcomes: List of all learning outcomes

        Returns:
            Dictionary mapping segment types to learning outcomes
        """
        if not learning_outcomes:
            return {
                "intro_hook": [],
                "overview": [],
                "main_content": [],
                "summary": []
            }

        # Simple distribution strategy for MVP
        # In the future, this could be more sophisticated
        num_outcomes = len(learning_outcomes)

        if num_outcomes == 1:
            return {
                "intro_hook": [],
                "overview": [learning_outcomes[0]],
                "main_content": [learning_outcomes[0]],
                "summary": [learning_outcomes[0]]
            }
        elif num_outcomes == 2:
            return {
                "intro_hook": [],
                "overview": learning_outcomes,
                "main_content": learning_outcomes,
                "summary": learning_outcomes
            }
        else:  # 3 or more outcomes
            return {
                "intro_hook": [],
                "overview": learning_outcomes[:2],
                "main_content": learning_outcomes,
                "summary": learning_outcomes[-2:]  # Last 2 outcomes
            }

    async def allocate_timing(self, structure: PodcastStructure) -> TimedStructure:
        """
        Allocate precise timing for podcast structure.

        Args:
            structure: Podcast structure to time

        Returns:
            TimedStructure with precise timing breakdown
        """
        segment_timing = {
            "intro_hook": structure.intro_hook.target_duration_seconds,
            "overview": structure.overview.target_duration_seconds,
            "main_content": structure.main_content.target_duration_seconds,
            "summary": structure.summary.target_duration_seconds
        }

        total_duration = sum(segment_timing.values())

        timing_notes = f"Total duration: {total_duration} seconds ({total_duration/60:.1f} minutes)"

        return TimedStructure(
            structure=structure,
            segment_timing=segment_timing,
            total_duration_seconds=total_duration,
            timing_notes=timing_notes
        )

    async def create_segment_flow(self, structure: PodcastStructure) -> FlowPlan:
        """
        Create natural flow between segments.

        Args:
            structure: Podcast structure to create flow for

        Returns:
            FlowPlan with transition details
        """
        transitions = {
            "intro_hook": structure.intro_hook.transition_out,
            "overview": structure.overview.transition_out,
            "main_content": structure.main_content.transition_out,
            "summary": structure.summary.transition_out
        }

        flow_notes = "Natural progression from engagement to overview to detailed content to summary"

        return FlowPlan(
            structure=structure,
            transitions=transitions,
            flow_notes=flow_notes
        )

    async def validate_structure(self, structure: PodcastStructure) -> bool:
        """
        Validate podcast structure meets requirements.

        Args:
            structure: Podcast structure to validate

        Returns:
            True if structure is valid, False otherwise
        """
        # Check total duration (4-5 minutes = 240-300 seconds)
        if not (240 <= structure.total_duration_seconds <= 300):
            self.logger.warning(
                f"Total duration {structure.total_duration_seconds}s outside 4-5 minute range"
            )
            return False

        # Check individual segment timing
        segments = [structure.intro_hook, structure.overview, structure.main_content, structure.summary]

        for segment in segments:
            if segment.segment_type == "intro_hook" and not (30 <= segment.target_duration_seconds <= 45):
                self.logger.warning(f"Intro hook duration {segment.target_duration_seconds}s outside 30-45s range")
                return False
            elif segment.segment_type == "overview" and not (30 <= segment.target_duration_seconds <= 45):
                self.logger.warning(f"Overview duration {segment.target_duration_seconds}s outside 30-45s range")
                return False
            elif segment.segment_type == "main_content" and not (120 <= segment.target_duration_seconds <= 180):
                self.logger.warning(f"Main content duration {segment.target_duration_seconds}s outside 2-3 minute range")
                return False
            elif segment.segment_type == "summary" and not (30 <= segment.target_duration_seconds <= 45):
                self.logger.warning(f"Summary duration {segment.target_duration_seconds}s outside 30-45s range")
                return False

        # Check that all learning outcomes are addressed
        all_segment_outcomes = []
        for segment in segments:
            all_segment_outcomes.extend(segment.learning_outcomes)

        for outcome in structure.learning_outcomes:
            if outcome not in all_segment_outcomes:
                self.logger.warning(
                    f"Learning outcome '{outcome}' not addressed in any segment"
                )
                return False

        return True
