"""
Tutoring Integration API for Bite-Sized Topics

This module provides a high-level API for tutoring systems to access and combine
bite-sized topic components adaptively based on learner needs.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

from .storage import TopicRepository, ComponentType, StoredComponent
from .orchestrator import TopicContent, TopicSpec


class LearningPhase(Enum):
    """Phases of learning for adaptive content selection"""
    INTRODUCTION = "introduction"       # First exposure to concept
    EXPLORATION = "exploration"         # Active discovery and practice
    REINFORCEMENT = "reinforcement"     # Strengthening understanding
    ASSESSMENT = "assessment"           # Checking understanding
    REMEDIATION = "remediation"         # Addressing gaps/misconceptions
    MASTERY = "mastery"                # Advanced application


class LearnerState(Enum):
    """Current state of learner understanding"""
    NOVICE = "novice"                  # No prior knowledge
    LEARNING = "learning"              # Building understanding
    CONFUSED = "confused"              # Has misconceptions
    PROGRESSING = "progressing"        # Making good progress
    STUCK = "stuck"                    # Need help/scaffolding
    CONFIDENT = "confident"            # Ready for challenges


@dataclass
class TutoringContext:
    """Context information for adaptive content selection"""
    learner_id: str
    topic_id: str
    learning_phase: LearningPhase
    learner_state: LearnerState
    difficulty_preference: int = 3  # 1-5 scale
    time_available: int = 15        # minutes
    previous_attempts: List[str] = field(default_factory=list)
    misconceptions_detected: List[str] = field(default_factory=list)
    concepts_mastered: List[str] = field(default_factory=list)
    learning_style_tags: List[str] = field(default_factory=list)


@dataclass
class ContentRecommendation:
    """Recommended content for tutoring session"""
    component_id: str
    component_type: ComponentType
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    confidence_score: float = 0.0
    reasoning: str = ""
    estimated_time: int = 5  # minutes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'component_id': self.component_id,
            'component_type': self.component_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'confidence_score': self.confidence_score,
            'reasoning': self.reasoning,
            'estimated_time': self.estimated_time
        }


class ContentSelector:
    """Intelligent content selector for adaptive tutoring"""

    def __init__(self):
        self.phase_component_mapping = {
            LearningPhase.INTRODUCTION: [ComponentType.DIDACTIC_SNIPPET, ComponentType.GLOSSARY],
            LearningPhase.EXPLORATION: [ComponentType.SOCRATIC_DIALOGUE, ComponentType.GLOSSARY],
            LearningPhase.REINFORCEMENT: [ComponentType.SHORT_ANSWER_QUESTION, ComponentType.SOCRATIC_DIALOGUE],
            LearningPhase.ASSESSMENT: [ComponentType.MULTIPLE_CHOICE_QUESTION, ComponentType.POST_TOPIC_QUIZ],
            LearningPhase.REMEDIATION: [ComponentType.DIDACTIC_SNIPPET, ComponentType.SOCRATIC_DIALOGUE],
            LearningPhase.MASTERY: [ComponentType.POST_TOPIC_QUIZ, ComponentType.SHORT_ANSWER_QUESTION]
        }

        self.state_difficulty_mapping = {
            LearnerState.NOVICE: (1, 2),
            LearnerState.LEARNING: (2, 3),
            LearnerState.CONFUSED: (1, 2),
            LearnerState.PROGRESSING: (3, 4),
            LearnerState.STUCK: (1, 3),
            LearnerState.CONFIDENT: (4, 5)
        }

    def select_components(
        self,
        available_components: List[StoredComponent],
        context: TutoringContext
    ) -> List[ContentRecommendation]:
        """
        Select the most appropriate components for the current context.

        Args:
            available_components: All available components for the topic
            context: Current tutoring context

        Returns:
            List of recommended content items
        """
        recommendations = []

        # Filter by learning phase
        preferred_types = self.phase_component_mapping.get(context.learning_phase, [])
        phase_filtered = [c for c in available_components if c.component_type in preferred_types]

        # Filter by difficulty range
        difficulty_range = self.state_difficulty_mapping.get(context.learner_state, (1, 5))
        difficulty_filtered = [
            c for c in phase_filtered
            if difficulty_range[0] <= c.metadata.get('difficulty', 3) <= difficulty_range[1]
        ]

        # Score and rank components
        for component in difficulty_filtered:
            score = self._calculate_component_score(component, context)
            if score > 0.3:  # Threshold for inclusion
                reasoning = self._generate_reasoning(component, context, score)

                recommendation = ContentRecommendation(
                    component_id=component.id,
                    component_type=component.component_type,
                    content=component.content,
                    metadata=component.metadata,
                    confidence_score=score,
                    reasoning=reasoning,
                    estimated_time=self._estimate_time(component)
                )
                recommendations.append(recommendation)

        # Sort by confidence score and time constraints
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)

        # Filter by time constraints
        recommendations = self._filter_by_time(recommendations, context.time_available)

        return recommendations[:3]  # Return top 3 recommendations

    def _calculate_component_score(self, component: StoredComponent, context: TutoringContext) -> float:
        """Calculate relevance score for a component"""
        score = 0.5  # Base score

        # Difficulty alignment
        preferred_difficulty = context.difficulty_preference
        actual_difficulty = component.metadata.get('difficulty', 3)
        difficulty_diff = abs(preferred_difficulty - actual_difficulty)
        score += (3 - difficulty_diff) / 6  # Max +0.5 for perfect match

        # Learning state bonuses
        if context.learner_state == LearnerState.CONFUSED:
            if 'misconception' in component.metadata.get('tags', '').lower():
                score += 0.3
        elif context.learner_state == LearnerState.STUCK:
            if 'scaffolding' in component.metadata.get('tags', '').lower():
                score += 0.3
        elif context.learner_state == LearnerState.CONFIDENT:
            if component.metadata.get('difficulty', 3) >= 4:
                score += 0.2

        # Avoid recently used content
        if component.id in context.previous_attempts:
            score -= 0.4

        # Misconception targeting
        comp_tags = component.metadata.get('tags', '').lower()
        for misconception in context.misconceptions_detected:
            if misconception.lower() in comp_tags:
                score += 0.3

        # Learning style alignment
        for style_tag in context.learning_style_tags:
            if style_tag.lower() in comp_tags:
                score += 0.1

        return min(1.0, max(0.0, score))  # Clamp to [0, 1]

    def _generate_reasoning(self, component: StoredComponent, context: TutoringContext, score: float) -> str:
        """Generate human-readable reasoning for the recommendation"""
        reasons = []

        # Phase alignment
        if component.component_type in self.phase_component_mapping.get(context.learning_phase, []):
            reasons.append(f"Good fit for {context.learning_phase.value} phase")

        # Difficulty alignment
        if abs(context.difficulty_preference - component.metadata.get('difficulty', 3)) <= 1:
            reasons.append("Appropriate difficulty level")

        # State-specific reasons
        if context.learner_state == LearnerState.CONFUSED and 'misconception' in component.metadata.get('tags', ''):
            reasons.append("Addresses common misconceptions")
        elif context.learner_state == LearnerState.STUCK and 'scaffolding' in component.metadata.get('tags', ''):
            reasons.append("Provides helpful scaffolding")

        if not reasons:
            reasons.append("Matches current learning context")

        return "; ".join(reasons) + f" (confidence: {score:.2f})"

    def _estimate_time(self, component: StoredComponent) -> int:
        """Estimate time needed for a component (in minutes)"""
        time_estimates = {
            ComponentType.DIDACTIC_SNIPPET: 3,
            ComponentType.GLOSSARY: 2,
            ComponentType.SOCRATIC_DIALOGUE: 8,
            ComponentType.SHORT_ANSWER_QUESTION: 5,
            ComponentType.MULTIPLE_CHOICE_QUESTION: 3,
            ComponentType.POST_TOPIC_QUIZ: 10
        }

        base_time = time_estimates.get(component.component_type, 5)

        # Adjust for difficulty
        difficulty = component.metadata.get('difficulty', 3)
        time_multiplier = 0.7 + (difficulty * 0.15)  # 0.85x to 1.45x

        return int(base_time * time_multiplier)

    def _filter_by_time(self, recommendations: List[ContentRecommendation], time_available: int) -> List[ContentRecommendation]:
        """Filter recommendations to fit within time constraints"""
        if not recommendations:
            return []

        # Always include the top recommendation
        filtered = [recommendations[0]]
        total_time = recommendations[0].estimated_time

        # Add more if time permits
        for rec in recommendations[1:]:
            if total_time + rec.estimated_time <= time_available:
                filtered.append(rec)
                total_time += rec.estimated_time
            else:
                break

        return filtered


class TutoringAPI:
    """High-level API for tutoring system integration"""

    def __init__(self, repository: TopicRepository):
        self.repository = repository
        self.content_selector = ContentSelector()
        self.logger = logging.getLogger(__name__)

    async def get_recommended_content(self, context: TutoringContext) -> List[ContentRecommendation]:
        """
        Get recommended content for a tutoring session.

        Args:
            context: Current tutoring context

        Returns:
            List of recommended content items
        """
        # Get all components for the topic
        components = await self.repository.find_components_for_tutoring(
            topic_id=context.topic_id,
            component_types=None  # Get all types for intelligent selection
        )

        if not components:
            self.logger.warning(f"No components found for topic {context.topic_id}")
            return []

        # Select appropriate content
        recommendations = self.content_selector.select_components(components, context)

        self.logger.info(
            f"Generated {len(recommendations)} recommendations for learner {context.learner_id} "
            f"in {context.learning_phase.value} phase"
        )

        return recommendations

    async def get_specific_content(
        self,
        topic_id: str,
        component_types: List[ComponentType],
        difficulty_range: Optional[tuple] = None,
        tags: Optional[List[str]] = None
    ) -> List[StoredComponent]:
        """
        Get specific content types with filtering.

        Args:
            topic_id: Topic ID
            component_types: Specific component types to retrieve
            difficulty_range: Optional difficulty filtering
            tags: Optional tag filtering

        Returns:
            List of matching components
        """
        return await self.repository.find_components_for_tutoring(
            topic_id=topic_id,
            component_types=component_types,
            difficulty_range=difficulty_range,
            tags=tags
        )

    async def get_introduction_sequence(self, topic_id: str, user_level: str = "beginner") -> List[ContentRecommendation]:
        """
        Get a recommended sequence for introducing a topic.

        Args:
            topic_id: Topic ID
            user_level: User's skill level

        Returns:
            Ordered list of introduction content
        """
        context = TutoringContext(
            learner_id="system",
            topic_id=topic_id,
            learning_phase=LearningPhase.INTRODUCTION,
            learner_state=LearnerState.NOVICE if user_level == "beginner" else LearnerState.LEARNING,
            difficulty_preference=2 if user_level == "beginner" else 3
        )

        return await self.get_recommended_content(context)

    async def get_assessment_content(self, topic_id: str, difficulty_level: int = 3) -> List[ContentRecommendation]:
        """
        Get assessment content for a topic.

        Args:
            topic_id: Topic ID
            difficulty_level: Desired difficulty (1-5)

        Returns:
            Assessment content recommendations
        """
        context = TutoringContext(
            learner_id="system",
            topic_id=topic_id,
            learning_phase=LearningPhase.ASSESSMENT,
            learner_state=LearnerState.PROGRESSING,
            difficulty_preference=difficulty_level
        )

        return await self.get_recommended_content(context)

    async def get_remediation_content(
        self,
        topic_id: str,
        misconceptions: List[str],
        previous_attempts: List[str]
    ) -> List[ContentRecommendation]:
        """
        Get content for addressing misconceptions and learning gaps.

        Args:
            topic_id: Topic ID
            misconceptions: Detected misconceptions
            previous_attempts: Previously attempted content IDs

        Returns:
            Remediation content recommendations
        """
        context = TutoringContext(
            learner_id="system",
            topic_id=topic_id,
            learning_phase=LearningPhase.REMEDIATION,
            learner_state=LearnerState.CONFUSED,
            difficulty_preference=2,
            misconceptions_detected=misconceptions,
            previous_attempts=previous_attempts
        )

        return await self.get_recommended_content(context)

    async def create_custom_session(
        self,
        topic_id: str,
        session_goals: List[str],
        time_limit: int = 15,
        learner_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a custom tutoring session with multiple phases.

        Args:
            topic_id: Topic ID
            session_goals: List of session goals/objectives
            time_limit: Session time limit in minutes
            learner_profile: Optional learner profile data

        Returns:
            Complete session plan with phased content
        """
        session_plan = {
            'topic_id': topic_id,
            'session_goals': session_goals,
            'time_limit': time_limit,
            'phases': []
        }

        # Distribute time across phases
        introduction_time = max(3, time_limit // 4)
        exploration_time = max(5, time_limit // 2)
        assessment_time = time_limit - introduction_time - exploration_time

        # Phase 1: Introduction
        intro_context = TutoringContext(
            learner_id=learner_profile.get('id', 'system') if learner_profile else 'system',
            topic_id=topic_id,
            learning_phase=LearningPhase.INTRODUCTION,
            learner_state=LearnerState.NOVICE,
            time_available=introduction_time
        )
        intro_content = await self.get_recommended_content(intro_context)

        session_plan['phases'].append({
            'phase': 'introduction',
            'time_allocated': introduction_time,
            'content': [rec.to_dict() for rec in intro_content]
        })

        # Phase 2: Exploration
        exploration_context = TutoringContext(
            learner_id=learner_profile.get('id', 'system') if learner_profile else 'system',
            topic_id=topic_id,
            learning_phase=LearningPhase.EXPLORATION,
            learner_state=LearnerState.LEARNING,
            time_available=exploration_time
        )
        exploration_content = await self.get_recommended_content(exploration_context)

        session_plan['phases'].append({
            'phase': 'exploration',
            'time_allocated': exploration_time,
            'content': [rec.to_dict() for rec in exploration_content]
        })

        # Phase 3: Assessment
        assessment_context = TutoringContext(
            learner_id=learner_profile.get('id', 'system') if learner_profile else 'system',
            topic_id=topic_id,
            learning_phase=LearningPhase.ASSESSMENT,
            learner_state=LearnerState.PROGRESSING,
            time_available=assessment_time
        )
        assessment_content = await self.get_recommended_content(assessment_context)

        session_plan['phases'].append({
            'phase': 'assessment',
            'time_allocated': assessment_time,
            'content': [rec.to_dict() for rec in assessment_content]
        })

        return session_plan