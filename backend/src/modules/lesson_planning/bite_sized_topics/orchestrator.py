"""
Bite-Sized Topic Orchestrator

This module provides high-level orchestration for creating complete bite-sized topics
with all components working together.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio

from core import ModuleService, ServiceConfig, LLMClient
from .service import BiteSizedTopicService
from .mcq_service import MCQService


class CreationStrategy(Enum):
    """Strategy for creating topic components"""
    COMPLETE = "complete"  # Create all components
    CORE_ONLY = "core_only"  # Only didactic snippet + glossary
    ASSESSMENT_FOCUSED = "assessment_focused"  # Heavy on questions
    INTERACTIVE_FOCUSED = "interactive_focused"  # Heavy on dialogues
    CUSTOM = "custom"  # User-specified components


@dataclass
class TopicSpec:
    """Specification for creating a bite-sized topic"""
    topic_title: str
    core_concept: str
    user_level: str = "beginner"
    learning_objectives: List[str] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    key_aspects: List[str] = field(default_factory=list)
    target_insights: List[str] = field(default_factory=list)
    common_misconceptions: List[str] = field(default_factory=list)
    previous_topics: List[str] = field(default_factory=list)
    creation_strategy: CreationStrategy = CreationStrategy.COMPLETE
    custom_components: Optional[List[str]] = None
    auto_identify_concepts: bool = False  # If True, don't auto-add core_concept

    def __post_init__(self):
        """Ensure key_concepts includes core_concept unless auto-identification is enabled"""
        if not self.auto_identify_concepts and self.core_concept not in self.key_concepts:
            self.key_concepts.insert(0, self.core_concept)


@dataclass
class TopicContent:
    """Complete content package for a bite-sized topic"""
    topic_spec: TopicSpec
    didactic_snippet: Optional[Dict[str, Any]] = None
    glossary: Optional[List[Dict[str, Any]]] = None
    socratic_dialogues: Optional[List[Dict[str, Any]]] = None
    short_answer_questions: Optional[List[Dict[str, Any]]] = None
    multiple_choice_questions: Optional[List[Dict[str, Any]]] = None
    post_topic_quiz: Optional[List[Dict[str, Any]]] = None
    creation_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def component_count(self) -> int:
        """Count of non-None components"""
        components = [
            self.didactic_snippet, self.glossary, self.socratic_dialogues,
            self.short_answer_questions, self.multiple_choice_questions, self.post_topic_quiz
        ]
        return sum(1 for comp in components if comp is not None)

    @property
    def total_items(self) -> int:
        """Total number of items across all components"""
        count = 0
        if self.didactic_snippet: count += 1
        if self.glossary: count += len(self.glossary)
        if self.socratic_dialogues: count += len(self.socratic_dialogues)
        if self.short_answer_questions: count += len(self.short_answer_questions)
        if self.multiple_choice_questions: count += len(self.multiple_choice_questions)
        if self.post_topic_quiz: count += len(self.post_topic_quiz)
        return count


class TopicOrchestrator(ModuleService):
    """High-level orchestrator for creating bite-sized topics"""

    def __init__(self, config: ServiceConfig, llm_client: LLMClient):
        super().__init__(config, llm_client)
        self.topic_service = BiteSizedTopicService(config, llm_client)
        self.mcq_service = MCQService(llm_client)

        # Strategy definitions
        self.strategies = {
            CreationStrategy.COMPLETE: [
                'didactic_snippet', 'glossary', 'socratic_dialogues',
                'short_answer_questions', 'multiple_choice_questions', 'post_topic_quiz'
            ],
            CreationStrategy.CORE_ONLY: [
                'didactic_snippet', 'glossary'
            ],
            CreationStrategy.ASSESSMENT_FOCUSED: [
                'didactic_snippet', 'glossary', 'short_answer_questions',
                'multiple_choice_questions', 'post_topic_quiz'
            ],
            CreationStrategy.INTERACTIVE_FOCUSED: [
                'didactic_snippet', 'glossary', 'socratic_dialogues', 'post_topic_quiz'
            ]
        }

    async def create_topic(self, topic_spec: TopicSpec) -> TopicContent:
        """
        Create a complete bite-sized topic with all specified components.

        Args:
            topic_spec: Specification for the topic to create

        Returns:
            TopicContent with all requested components

        Raises:
            Exception: If topic creation fails
        """
        self.logger.info(f"Starting creation of topic: {topic_spec.topic_title}")

        # Determine which components to create
        components_to_create = self._get_components_for_strategy(topic_spec)

        # Create topic content container
        topic_content = TopicContent(
            topic_spec=topic_spec,
            creation_metadata={
                'strategy': topic_spec.creation_strategy.value,
                'components_requested': components_to_create,
                'created_at': None,  # Will be set after creation
                'creation_time_seconds': None
            }
        )

        # Create components concurrently where possible
        start_time = asyncio.get_event_loop().time()

        try:
            # Create all components
            await self._create_components(topic_content, components_to_create)

            # Record creation metadata
            end_time = asyncio.get_event_loop().time()
            topic_content.creation_metadata.update({
                'created_at': end_time,
                'creation_time_seconds': end_time - start_time,
                'components_created': topic_content.component_count,
                'total_items': topic_content.total_items
            })

            self.logger.info(
                f"Successfully created topic '{topic_spec.topic_title}' with "
                f"{topic_content.component_count} components and {topic_content.total_items} items "
                f"in {topic_content.creation_metadata['creation_time_seconds']:.2f} seconds"
            )

            return topic_content

        except Exception as e:
            self.logger.error(f"Failed to create topic '{topic_spec.topic_title}': {e}")
            raise

    def _get_components_for_strategy(self, topic_spec: TopicSpec) -> List[str]:
        """Get list of components to create based on strategy"""
        if topic_spec.creation_strategy == CreationStrategy.CUSTOM:
            return topic_spec.custom_components or []
        return self.strategies.get(topic_spec.creation_strategy, [])

    async def _create_components(self, topic_content: TopicContent, components: List[str]):
        """Create all specified components for the topic"""
        spec = topic_content.topic_spec

        # Group components by dependency order
        # Phase 1: Foundation components (can be created in parallel)
        foundation_tasks = []

        if 'didactic_snippet' in components:
            foundation_tasks.append(self._create_didactic_snippet(topic_content))

        if 'glossary' in components:
            foundation_tasks.append(self._create_glossary(topic_content))

        # Execute foundation components in parallel
        if foundation_tasks:
            await asyncio.gather(*foundation_tasks)

        # Phase 2: Interactive and assessment components (can reference foundation)
        assessment_tasks = []

        if 'socratic_dialogues' in components:
            assessment_tasks.append(self._create_socratic_dialogues(topic_content))

        if 'short_answer_questions' in components:
            assessment_tasks.append(self._create_short_answer_questions(topic_content))

        if 'multiple_choice_questions' in components:
            assessment_tasks.append(self._create_multiple_choice_questions(topic_content))

        # Execute assessment components in parallel
        if assessment_tasks:
            await asyncio.gather(*assessment_tasks)

        # Phase 3: Comprehensive assessment (references other components)
        if 'post_topic_quiz' in components:
            await self._create_post_topic_quiz(topic_content)

    async def _create_didactic_snippet(self, topic_content: TopicContent):
        """Create didactic snippet component"""
        spec = topic_content.topic_spec

        snippet = await self.topic_service.create_didactic_snippet(
            topic_title=spec.topic_title,
            key_concept=spec.core_concept,
            user_level=spec.user_level,
            learning_objectives=spec.learning_objectives,
            previous_topics=spec.previous_topics
        )

        topic_content.didactic_snippet = snippet
        self.logger.debug(f"Created didactic snippet: {snippet['title']}")

    async def _create_glossary(self, topic_content: TopicContent):
        """Create glossary component"""
        spec = topic_content.topic_spec

        glossary_entries = await self.topic_service.create_glossary(
            topic_title=spec.topic_title,
            concepts=spec.key_concepts,
            user_level=spec.user_level,
            learning_objectives=spec.learning_objectives,
            previous_topics=spec.previous_topics
        )

        # Store as list of entries instead of dictionary
        topic_content.glossary = glossary_entries
        self.logger.debug(f"Created glossary with {len(glossary_entries)} entries")

    async def _create_socratic_dialogues(self, topic_content: TopicContent):
        """Create Socratic dialogues component"""
        spec = topic_content.topic_spec

        dialogues = await self.topic_service.create_socratic_dialogue(
            topic_title=spec.topic_title,
            core_concept=spec.core_concept,
            user_level=spec.user_level,
            learning_objectives=spec.learning_objectives,
            previous_topics=spec.previous_topics,
            target_insights=spec.target_insights,
            common_misconceptions=spec.common_misconceptions
        )

        topic_content.socratic_dialogues = dialogues
        self.logger.debug(f"Created {len(dialogues)} Socratic dialogues")

    async def _create_short_answer_questions(self, topic_content: TopicContent):
        """Create short answer questions component"""
        spec = topic_content.topic_spec

        questions = await self.topic_service.create_short_answer_questions(
            topic_title=spec.topic_title,
            core_concept=spec.core_concept,
            user_level=spec.user_level,
            learning_objectives=spec.learning_objectives,
            previous_topics=spec.previous_topics,
            key_aspects=spec.key_aspects
        )

        topic_content.short_answer_questions = questions
        self.logger.debug(f"Created {len(questions)} short answer questions")

    async def _create_multiple_choice_questions(self, topic_content: TopicContent):
        """Create multiple choice questions component"""
        spec = topic_content.topic_spec

        questions = await self.topic_service.create_multiple_choice_questions(
            topic_title=spec.topic_title,
            core_concept=spec.core_concept,
            user_level=spec.user_level,
            learning_objectives=spec.learning_objectives,
            previous_topics=spec.previous_topics,
            key_aspects=spec.key_aspects,
            common_misconceptions=spec.common_misconceptions
        )

        topic_content.multiple_choice_questions = questions
        self.logger.debug(f"Created {len(questions)} multiple choice questions")

    async def _create_post_topic_quiz(self, topic_content: TopicContent):
        """Create post-topic quiz component"""
        spec = topic_content.topic_spec

        # Avoid overlap with existing components
        avoid_overlap = []
        if topic_content.socratic_dialogues:
            avoid_overlap.extend([d.get('concept', '') for d in topic_content.socratic_dialogues])
        if topic_content.short_answer_questions:
            avoid_overlap.extend([q.get('target_concept', '') for q in topic_content.short_answer_questions])
        if topic_content.multiple_choice_questions:
            avoid_overlap.extend([q.get('target_concept', '') for q in topic_content.multiple_choice_questions])

        quiz = await self.topic_service.create_post_topic_quiz(
            topic_title=spec.topic_title,
            core_concept=spec.core_concept,
            user_level=spec.user_level,
            learning_objectives=spec.learning_objectives,
            previous_topics=spec.previous_topics,
            key_aspects=spec.key_aspects,
            common_misconceptions=spec.common_misconceptions
        )

        topic_content.post_topic_quiz = quiz
        self.logger.debug(f"Created post-topic quiz with {len(quiz)} items")

    async def create_topic_batch(self, topic_specs: List[TopicSpec]) -> List[TopicContent]:
        """
        Create multiple topics in parallel.

        Args:
            topic_specs: List of topic specifications

        Returns:
            List of created TopicContent objects
        """
        self.logger.info(f"Creating batch of {len(topic_specs)} topics")

        # Create topics in parallel
        tasks = [self.create_topic(spec) for spec in topic_specs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate successful results from exceptions
        successful_topics = []
        failed_topics = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_topics.append((topic_specs[i].topic_title, result))
            else:
                successful_topics.append(result)

        # Log results
        self.logger.info(f"Batch creation complete: {len(successful_topics)} successful, {len(failed_topics)} failed")

        if failed_topics:
            for topic_title, error in failed_topics:
                self.logger.error(f"Failed to create topic '{topic_title}': {error}")

        return successful_topics

    async def create_mcqs_from_unstructured_material(
        self,
        source_material: str,
        topic_title: str,
        domain: str = "",
        user_level: str = "intermediate"
    ) -> TopicContent:
        """
        Create MCQs from unstructured material using the two-pass approach.
        
        This method creates a TopicContent object with:
        1. A refined_material component (from first pass)
        2. Individual MCQ components (from second pass)
        3. Each MCQ includes quality evaluation
        
        Args:
            source_material: Unstructured text to process
            topic_title: Title for the topic
            domain: Subject domain (optional)
            user_level: Target user level
            
        Returns:
            TopicContent with refined material and MCQs
        """
        self.logger.info(f"Creating MCQs from unstructured material for topic: {topic_title}")
        
        # Create basic topic spec
        topic_spec = TopicSpec(
            topic_title=topic_title,
            core_concept=topic_title,  # Will be refined from material
            user_level=user_level,
            creation_strategy=CreationStrategy.CUSTOM,
            custom_components=["refined_material", "multiple_choice_questions"]
        )
        
        # Create topic content container
        topic_content = TopicContent(
            topic_spec=topic_spec,
            creation_metadata={
                'strategy': 'two_pass_mcq',
                'source_material_length': len(source_material),
                'domain': domain,
                'created_at': None,
                'creation_time_seconds': None
            }
        )
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Use MCQ service for two-pass creation
            refined_material, mcqs_with_evaluations = await self.mcq_service.create_mcqs_from_text(
                source_material=source_material,
                topic_title=topic_title,
                domain=domain,
                user_level=user_level
            )
            
            # Convert to MCQ format expected by TopicContent
            mcq_questions = []
            for mcq_data in mcqs_with_evaluations:
                mcq = mcq_data['mcq']
                evaluation = mcq_data['evaluation']
                
                # Create MCQ in the format expected by the system
                mcq_question = {
                    'title': mcq.get('stem', '')[:50] + '...' if len(mcq.get('stem', '')) > 50 else mcq.get('stem', ''),
                    'question': mcq.get('stem', ''),
                    'options': mcq.get('options', []),
                    'correct_answer': mcq.get('correct_answer', ''),
                    'rationale': mcq.get('rationale', ''),
                    'target_concept': mcq_data.get('topic', ''),
                    'learning_objective': mcq_data.get('learning_objective', ''),
                    'evaluation': evaluation,
                    'type': 'multiple_choice_question'
                }
                mcq_questions.append(mcq_question)
            
            # Store results in topic content
            topic_content.multiple_choice_questions = mcq_questions
            
            # Add refined material as metadata
            topic_content.creation_metadata['refined_material'] = refined_material
            
            # Record creation metadata
            end_time = asyncio.get_event_loop().time()
            topic_content.creation_metadata.update({
                'created_at': end_time,
                'creation_time_seconds': end_time - start_time,
                'total_topics_extracted': len(refined_material.get('topics', [])),
                'total_mcqs_created': len(mcq_questions)
            })
            
            self.logger.info(
                f"Successfully created {len(mcq_questions)} MCQs from unstructured material for "
                f"'{topic_title}' in {topic_content.creation_metadata['creation_time_seconds']:.2f} seconds"
            )
            
            return topic_content
            
        except Exception as e:
            self.logger.error(f"Failed to create MCQs from unstructured material for '{topic_title}': {e}")
            raise