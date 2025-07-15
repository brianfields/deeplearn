#!/usr/bin/env python3
"""
Create Single Bite-Sized Topic

Simple script to create one bite-sized topic.
"""

import argparse
import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core import LLMClient, ServiceConfig
    from core.service_base import ServiceFactory
    from config.config import get_llm_config
    from modules.lesson_planning.bite_sized_topics.service import BiteSizedTopicService
    from modules.lesson_planning.bite_sized_topics.postgresql_storage import PostgreSQLTopicRepository
    from data_structures import BiteSizedTopic, BiteSizedComponent
    from database_service import get_database_service
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the backend directory")
    sys.exit(1)


async def create_topic(topic_title: str, user_level: str = "beginner"):
    """Create a single topic using the orchestrator"""
    print(f"🎯 Creating: {topic_title} (level: {user_level})")

    try:
        # Setup services
        llm_config = get_llm_config()
        config = ServiceFactory.create_service_config(llm_config)
        llm_client = LLMClient(llm_config)

        # Use the orchestrator instead of direct service calls
        from modules.lesson_planning.bite_sized_topics.orchestrator import TopicOrchestrator, TopicSpec, CreationStrategy

        orchestrator = TopicOrchestrator(config, llm_client)

        # Create a proper topic specification
        topic_spec = TopicSpec(
            topic_title=topic_title,
            core_concept=topic_title,
            user_level=user_level,
            learning_objectives=[f"Understand {topic_title}"],
            key_concepts=[],  # Will be populated by LLM during generation
            key_aspects=[],   # Will be populated by LLM during generation
            target_insights=[f"Key insights about {topic_title}"],
            common_misconceptions=[],
            previous_topics=[],
            creation_strategy=CreationStrategy.COMPLETE,  # Generate all components
            auto_identify_concepts=True  # Let LLM identify meaningful concepts
        )

        # Generate all components using the orchestrator
        print("📝 Generating all components...")
        topic_content = await orchestrator.create_topic(topic_spec)

        # Store using the repository
        print("💾 Storing to PostgreSQL...")
        from modules.lesson_planning.bite_sized_topics.postgresql_storage import PostgreSQLTopicRepository

        repository = PostgreSQLTopicRepository()
        topic_id = await repository.store_topic(topic_content)

        # Report what was created
        print(f"✅ Success! Topic ID: {topic_id}")
        if topic_content.didactic_snippet:
            print(f"   • Didactic snippet: {topic_content.didactic_snippet.get('title', 'Created')}")
        if topic_content.glossary:
            print(f"   • Glossary: {len(topic_content.glossary)} terms")
        if topic_content.socratic_dialogues:
            print(f"   • Socratic dialogues: {len(topic_content.socratic_dialogues)} dialogues")
        if topic_content.short_answer_questions:
            print(f"   • Short answer questions: {len(topic_content.short_answer_questions)} questions")
        if topic_content.multiple_choice_questions:
            print(f"   • Multiple choice questions: {len(topic_content.multiple_choice_questions)} questions")
        if topic_content.post_topic_quiz:
            print(f"   • Post-topic quiz: {len(topic_content.post_topic_quiz)} items")

        print(f"   • Total components: {topic_content.component_count}")
        print(f"   • Total items: {topic_content.total_items}")

        return topic_id

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="Topic to create")
    parser.add_argument("--level", default="beginner", choices=["beginner", "intermediate", "advanced"])
    args = parser.parse_args()

    result = asyncio.run(create_topic(args.topic, args.level))
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()