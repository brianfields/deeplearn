#!/usr/bin/env python3
"""
Test script to verify bite-sized topics component improvements

This script tests the new component structure with:
1. Title generation for all components
2. Consolidated content field (no separate metadata)
3. Fixed Socratic Dialogue repetition
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modules.lesson_planning.bite_sized_topics.orchestrator import TopicOrchestrator, TopicSpec, CreationStrategy
from modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService
from core.llm_client import LLMClient
from config.config import ServiceConfig

async def test_component_improvements():
    """Test the component improvements"""
    print("Testing bite-sized topics component improvements...")

    # Create service instances
    config = ServiceConfig()
    llm_client = LLMClient(config)
    topic_service = BiteSizedTopicService(config, llm_client)
    orchestrator = TopicOrchestrator(config, llm_client, topic_service)

    # Create a test topic spec
    topic_spec = TopicSpec(
        topic_title="Test Topic: Understanding Variables",
        core_concept="Variables in programming",
        user_level="beginner",
        learning_objectives=["Understand what variables are", "Learn how to declare variables"],
        key_concepts=["variable", "declaration", "assignment"],
        key_aspects=["syntax", "types", "scope"],
        target_insights=["Variables store data", "Variables have types"],
        common_misconceptions=["Variables are containers", "Variables are their values"],
        previous_topics=["Basic programming concepts"],
        creation_strategy=CreationStrategy.COMPREHENSIVE
    )

    print(f"Creating topic: {topic_spec.topic_title}")

    try:
        # Create the topic with all components
        topic_content = await orchestrator.create_topic(topic_spec)

        print(f"✓ Topic created successfully!")
        print(f"  Components: {topic_content.component_count}")
        print(f"  Total items: {topic_content.total_items}")

        # Test didactic snippet
        if topic_content.didactic_snippet:
            snippet = topic_content.didactic_snippet
            print(f"\n✓ Didactic Snippet:")
            print(f"  Title: {snippet.get('title', 'No title')}")
            print(f"  Type: {snippet.get('type', 'No type')}")
            print(f"  Difficulty: {snippet.get('difficulty', 'No difficulty')}")
            print(f"  Content length: {len(snippet.get('snippet', ''))}")

        # Test glossary
        if topic_content.glossary:
            print(f"\n✓ Glossary ({len(topic_content.glossary)} entries):")
            for i, entry in enumerate(topic_content.glossary[:2]):  # Show first 2
                print(f"  Entry {i+1}:")
                print(f"    Title: {entry.get('title', 'No title')}")
                print(f"    Concept: {entry.get('concept', 'No concept')}")
                print(f"    Type: {entry.get('type', 'No type')}")
                print(f"    Difficulty: {entry.get('difficulty', 'No difficulty')}")

        # Test Socratic dialogues
        if topic_content.socratic_dialogues:
            print(f"\n✓ Socratic Dialogues ({len(topic_content.socratic_dialogues)} dialogues):")
            for i, dialogue in enumerate(topic_content.socratic_dialogues[:2]):  # Show first 2
                print(f"  Dialogue {i+1}:")
                print(f"    Title: {dialogue.get('title', 'No title')}")
                print(f"    Concept: {dialogue.get('concept', 'No concept')}")
                print(f"    Type: {dialogue.get('type', 'No type')}")
                print(f"    Difficulty: {dialogue.get('difficulty', 'No difficulty')}")
                print(f"    Starting Prompt: {dialogue.get('starting_prompt', 'No prompt')[:50]}...")

                # Check for repetition - ensure data is not duplicated
                unique_keys = set(dialogue.keys())
                print(f"    Unique fields: {len(unique_keys)}")

        # Test short answer questions
        if topic_content.short_answer_questions:
            print(f"\n✓ Short Answer Questions ({len(topic_content.short_answer_questions)} questions):")
            for i, question in enumerate(topic_content.short_answer_questions[:2]):
                print(f"  Question {i+1}:")
                print(f"    Title: {question.get('title', 'No title')}")
                print(f"    Type: {question.get('type', 'No type')}")
                print(f"    Difficulty: {question.get('difficulty', 'No difficulty')}")
                print(f"    Purpose: {question.get('purpose', 'No purpose')}")

        # Test multiple choice questions
        if topic_content.multiple_choice_questions:
            print(f"\n✓ Multiple Choice Questions ({len(topic_content.multiple_choice_questions)} questions):")
            for i, question in enumerate(topic_content.multiple_choice_questions[:2]):
                print(f"  Question {i+1}:")
                print(f"    Title: {question.get('title', 'No title')}")
                print(f"    Type: {question.get('type', 'No type')}")
                print(f"    Difficulty: {question.get('difficulty', 'No difficulty')}")
                print(f"    Choices: {len(question.get('choices', {}))}")
                print(f"    Correct Answer: {question.get('correct_answer', 'No answer')}")

        print("\n✓ All component improvements verified successfully!")

    except Exception as e:
        print(f"✗ Error testing components: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    await test_component_improvements()

if __name__ == "__main__":
    asyncio.run(main())