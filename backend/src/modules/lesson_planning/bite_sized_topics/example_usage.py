"""
Complete Usage Example for Bite-Sized Topics System

This example demonstrates the full workflow from topic creation to tutoring integration.
"""

import asyncio
from typing import List

from core import ServiceConfig, LLMClient
from .orchestrator import TopicOrchestrator, TopicSpec, CreationStrategy
from .storage import TopicRepository
from .tutoring_api import TutoringAPI, TutoringContext, LearningPhase, LearnerState


async def main():
    """Complete workflow example"""

    print("🎯 Bite-Sized Topics System - Conceptual Workflow Demo")
    print("Note: This demonstrates the workflow with mock data")
    print("In a real implementation, you would integrate with actual LLM services")

    # For demonstration, we'll use mock data to show the complete workflow
    # In production, you would initialize:
    # - TopicOrchestrator(config, llm_client)
    # - TopicRepository(db_path)
    # - TutoringAPI(repository)

    # Initialize storage only (works without LLM)
    repository = TopicRepository("example_topics.db")
    tutoring_api = TutoringAPI(repository)

    print("🎯 Bite-Sized Topics System Demo")
    print("=" * 50)

    # Step 1: Create a complete topic
    print("\n📚 Step 1: Creating a complete topic")
    topic_spec = TopicSpec(
        topic_title="Large Language Models",
        core_concept="Next-token Prediction",
        user_level="intermediate",
        learning_objectives=[
            "Understand autoregressive generation",
            "Explain token-by-token prediction",
            "Recognize sampling effects"
        ],
        key_concepts=["Next-token Prediction", "Autoregressive", "Tokens", "Sampling"],
        key_aspects=["Sequential generation", "Probability distributions", "Context dependence"],
        target_insights=[
            "GPT generates one token at a time",
            "Randomness enables creativity",
            "Context determines next token probabilities"
        ],
        common_misconceptions=[
            "GPT plans entire sentences ahead",
            "Output variation means the model is broken",
            "GPT uses grammatical rules"
        ],
        previous_topics=["Neural Networks", "Transformers"],
        creation_strategy=CreationStrategy.COMPLETE
    )

    # Create the topic (this would normally use TopicOrchestrator with LLM)
    print(f"Creating topic: {topic_spec.topic_title}")
    print("📝 For demo purposes, using mock content (in production, this would call LLM)")
    topic_content = create_mock_topic_content(topic_spec)
    print(f"✅ Created topic with {topic_content.component_count} components")
    print(f"   Total items: {topic_content.total_items}")

    # Step 2: Store the topic
    print("\n💾 Step 2: Storing the topic")
    topic_id = await repository.store_topic(topic_content)
    print(f"✅ Stored topic with ID: {topic_id}")

    # Step 3: Retrieve and verify storage
    print("\n🔍 Step 3: Retrieving stored topic")
    retrieved_topic = await repository.get_topic(topic_id)
    if retrieved_topic:
        print(f"✅ Retrieved topic: {retrieved_topic.topic_spec.topic_title}")
        print(f"   Components: {retrieved_topic.component_count}")
    else:
        print("❌ Failed to retrieve topic")
        return

    # Step 4: Tutoring scenarios
    print("\n🎓 Step 4: Tutoring Integration Examples")

    # Scenario A: Introduction for a beginner
    print("\n📖 Scenario A: Introduction for a beginner")
    intro_content = await tutoring_api.get_introduction_sequence(topic_id, "beginner")
    print(f"   Recommended {len(intro_content)} introduction items:")
    for i, rec in enumerate(intro_content, 1):
        print(f"   {i}. {rec.component_type.value} (confidence: {rec.confidence_score:.2f})")
        print(f"      Reasoning: {rec.reasoning}")
        print(f"      Time: {rec.estimated_time} minutes")

    # Scenario B: Assessment for intermediate learner
    print("\n📝 Scenario B: Assessment for intermediate learner")
    assessment_content = await tutoring_api.get_assessment_content(topic_id, difficulty_level=3)
    print(f"   Recommended {len(assessment_content)} assessment items:")
    for i, rec in enumerate(assessment_content, 1):
        print(f"   {i}. {rec.component_type.value} (confidence: {rec.confidence_score:.2f})")
        print(f"      Time: {rec.estimated_time} minutes")

    # Scenario C: Remediation for confused learner
    print("\n🔧 Scenario C: Remediation for confused learner")
    misconceptions = ["GPT plans sentences ahead", "Randomness means broken"]
    remediation_content = await tutoring_api.get_remediation_content(
        topic_id, misconceptions, []
    )
    print(f"   Recommended {len(remediation_content)} remediation items:")
    for i, rec in enumerate(remediation_content, 1):
        print(f"   {i}. {rec.component_type.value} (confidence: {rec.confidence_score:.2f})")
        print(f"      Reasoning: {rec.reasoning}")

    # Scenario D: Custom adaptive session
    print("\n🎪 Scenario D: Custom adaptive tutoring session")
    session_plan = await tutoring_api.create_custom_session(
        topic_id=topic_id,
        session_goals=["Understand autoregressive generation", "Apply knowledge"],
        time_limit=20,
        learner_profile={"id": "learner_123", "level": "intermediate"}
    )

    print(f"   Created session with {len(session_plan['phases'])} phases:")
    for phase in session_plan['phases']:
        print(f"   📅 {phase['phase'].title()} Phase ({phase['time_allocated']} min):")
        for item in phase['content']:
            print(f"      - {item['component_type']} (confidence: {item['confidence_score']:.2f})")

    # Step 5: Advanced querying
    print("\n🔎 Step 5: Advanced content querying")

    # Find specific content types
    from .storage import ComponentType
    dialogue_components = await tutoring_api.get_specific_content(
        topic_id=topic_id,
        component_types=[ComponentType.SOCRATIC_DIALOGUE],
        difficulty_range=(2, 4)
    )
    print(f"   Found {len(dialogue_components)} Socratic dialogues (difficulty 2-4)")

    # Find content by tags
    misconception_components = await tutoring_api.get_specific_content(
        topic_id=topic_id,
        component_types=[ComponentType.MULTIPLE_CHOICE_QUESTION, ComponentType.SOCRATIC_DIALOGUE],
        tags=["misconception"]
    )
    print(f"   Found {len(misconception_components)} misconception-focused components")

    print("\n🎉 Demo completed successfully!")
    print("=" * 50)


def create_mock_topic_content(topic_spec: TopicSpec):
    """Create mock topic content for demonstration"""
    from .orchestrator import TopicContent

    # Mock didactic snippet
    didactic_snippet = {
        'title': 'Next-token Prediction',
        'snippet': 'GPT generates text one token at a time, choosing each next token based on the previous context. This autoregressive process enables flexible text generation while maintaining coherence through learned patterns.'
    }

    # Mock glossary
    glossary = {
        'Next-token Prediction': 'The process of generating text by predicting one token at a time based on previous context.',
        'Autoregressive': 'A generation method where each output depends on previous outputs in the sequence.',
        'Token': 'A unit of text that the model processes, which might be a word, part of a word, or punctuation.',
        'Sampling': 'The process of selecting the next token from a probability distribution rather than always choosing the most likely option.'
    }

    # Mock Socratic dialogues
    socratic_dialogues = [
        {
            'concept': 'Autoregressive Generation',
            'dialogue_objective': 'Help learner understand that GPT generates one token at a time',
            'starting_prompt': 'If GPT is writing "The cat sat on the", what happens next?',
            'dialogue_style': 'Thought experiment',
            'difficulty': 2,
            'tags': 'concept discovery, good for beginners'
        },
        {
            'concept': 'Sampling vs Deterministic',
            'dialogue_objective': 'Learner discovers why randomness is useful in generation',
            'starting_prompt': 'What would happen if GPT always picked the most likely next word?',
            'dialogue_style': 'Consequence exploration',
            'difficulty': 3,
            'tags': 'misconception correction, creativity understanding'
        }
    ]

    # Mock short answer questions
    short_answer_questions = [
        {
            'question': 'Why does GPT generate text one token at a time instead of planning whole sentences?',
            'purpose': 'Conceptual understanding',
            'target_concept': 'Autoregressive generation',
            'expected_elements': 'Should mention that this is how the model was trained and that it enables flexible generation',
            'difficulty': 3,
            'tags': 'core concept, architecture understanding'
        }
    ]

    # Mock multiple choice questions
    multiple_choice_questions = [
        {
            'question': 'What does it mean that GPT is "autoregressive"?',
            'choices': {
                'A': 'It can correct its own mistakes',
                'B': 'It generates each token based on previous tokens',
                'C': 'It plans ahead before generating',
                'D': 'It uses recursive algorithms'
            },
            'correct_answer': 'B',
            'justifications': {
                'A': '❌ Incorrect - this is not what autoregressive means',
                'B': '✅ Correct - autoregressive means each output depends on previous outputs',
                'C': '❌ Incorrect - GPT does not plan ahead',
                'D': '❌ Incorrect - this refers to implementation, not generation pattern'
            },
            'target_concept': 'Autoregressive generation',
            'purpose': 'Definition verification',
            'difficulty': 2,
            'tags': 'core concept, terminology'
        }
    ]

    # Mock post-topic quiz
    post_topic_quiz = [
        {
            'type': 'Multiple Choice',
            'question': 'How does sampling temperature affect GPT output?',
            'choices': {
                'A': 'Higher temperature makes output more predictable',
                'B': 'Higher temperature makes output more random',
                'C': 'Temperature only affects speed',
                'D': 'Temperature controls the length of output'
            },
            'correct_answer': 'B',
            'target_concept': 'Sampling behavior',
            'difficulty': 3,
            'tags': 'parameter understanding, behavior prediction'
        }
    ]

    return TopicContent(
        topic_spec=topic_spec,
        didactic_snippet=didactic_snippet,
        glossary=glossary,
        socratic_dialogues=socratic_dialogues,
        short_answer_questions=short_answer_questions,
        multiple_choice_questions=multiple_choice_questions,
        post_topic_quiz=post_topic_quiz,
        creation_metadata={
            'strategy': 'complete',
            'created_at': 'mock',
            'components_created': 6,
            'total_items': 8
        }
    )


if __name__ == "__main__":
    asyncio.run(main())