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
    """Create a single topic using direct service calls"""
    print(f"🎯 Creating: {topic_title} (level: {user_level})")

    try:
        # Setup services
        llm_config = get_llm_config()
        config = ServiceFactory.create_service_config(llm_config)
        llm_client = LLMClient(llm_config)
        service = BiteSizedTopicService(config, llm_client)

        # Create didactic snippet
        print("📝 Creating didactic snippet...")
        didactic_snippet = await service.create_didactic_snippet(
            topic_title=topic_title,
            key_concept=topic_title,
            user_level=user_level,
            learning_objectives=[f"Understand {topic_title}"]
        )

        # Create glossary
        print("📚 Creating glossary...")
        glossary = await service.create_glossary(
            topic_title=topic_title,
            concepts=[topic_title],
            user_level=user_level,
            learning_objectives=[f"Define key terms in {topic_title}"]
        )

        # Store directly to database using SQLAlchemy models
        print("💾 Storing to PostgreSQL...")
        db_service = get_database_service()

        # Create topic record
        topic_id = str(uuid.uuid4())
        with db_service.get_session() as session:
            # Create main topic
            topic_record = BiteSizedTopic(
                id=topic_id,
                title=topic_title,
                core_concept=topic_title,
                user_level=user_level,
                learning_objectives=[f"Understand {topic_title}"],
                key_concepts=[topic_title],
                key_aspects=[topic_title],
                target_insights=[f"Key insights about {topic_title}"],
                common_misconceptions=[],
                previous_topics=[],
                creation_strategy="core_only",
                creation_metadata={"created_by": "create_single_topic.py"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(topic_record)

            # Create didactic snippet component
            snippet_id = str(uuid.uuid4())
            snippet_component = BiteSizedComponent(
                id=snippet_id,
                topic_id=topic_id,
                component_type="didactic_snippet",
                content=str(didactic_snippet),
                component_metadata={"title": didactic_snippet.get("title", topic_title)},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(snippet_component)

            # Create glossary component
            glossary_id = str(uuid.uuid4())
            glossary_component = BiteSizedComponent(
                id=glossary_id,
                topic_id=topic_id,
                component_type="glossary",
                content=str(glossary),
                component_metadata={"term_count": len(glossary) if isinstance(glossary, list) else 1},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(glossary_component)

            session.commit()

        print(f"✅ Success! Topic ID: {topic_id}")
        print(f"   • Didactic snippet: {didactic_snippet.get('title', 'Created')}")
        print(f"   • Glossary: {len(glossary) if isinstance(glossary, list) else 1} terms")
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