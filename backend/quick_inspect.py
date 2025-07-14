#!/usr/bin/env python3
"""
Quick inspection of learning paths and bite-sized content.

This script provides a fast way to see what content has been generated
using PostgreSQL instead of SQLite.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from database_service import get_database_service
    from data_structures import BiteSizedTopic, BiteSizedComponent
    from sqlalchemy import select, func
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the backend directory and have installed dependencies")
    sys.exit(1)


def quick_paths_summary():
    """Show quick summary of learning paths"""
    try:
        db_service = get_database_service()
        learning_paths = db_service.get_all_learning_paths()

        if not learning_paths:
            print("📚 No learning paths found")
            return

        print("🎓 Learning Paths:")
        print("=" * 50)

        for path_id, path in learning_paths.items():
            # Count topics with bite-sized content
            topics_with_content = sum(1 for topic in path.topics if topic.get('has_bite_sized_content', False))

            print(f"📖 {path.topic_name}")
            print(f"   📝 {len(path.topics)} topics")
            print(f"   📚 {topics_with_content} with bite-sized content")
            print(f"   🗓️  {path.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

    except Exception as e:
        print(f"⚠️  Error reading learning paths: {e}")


def quick_content_summary():
    """Show quick summary of bite-sized content"""
    try:
        db_service = get_database_service()

        with db_service.get_session() as session:
            # Get topic count
            topic_count = session.execute(select(func.count(BiteSizedTopic.id))).scalar()

            # Get component count
            component_count = session.execute(select(func.count(BiteSizedComponent.id))).scalar()

            if topic_count == 0:
                print("❌ No bite-sized content found")
                return

            # Get recent topics
            recent_topics = session.execute(
                select(BiteSizedTopic.title, BiteSizedTopic.user_level,
                       BiteSizedTopic.creation_strategy, BiteSizedTopic.created_at)
                .order_by(BiteSizedTopic.created_at.desc())
                .limit(10)
            ).all()

            print("🔍 Bite-Sized Content:")
            print("=" * 50)
            print(f"📊 {topic_count} topics, {component_count} components")
            print("\nRecent Topics:")

            for i, topic in enumerate(recent_topics, 1):
                print(f"{i}. {topic.title}")
                print(f"   👤 {topic.user_level} • ⚙️ {topic.creation_strategy}")
                print(f"   🗓️  {topic.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print()

    except Exception as e:
        print(f"⚠️  Error reading database: {e}")


def show_topic_details(topic_title: str):
    """Show detailed information about a specific topic"""
    try:
        db_service = get_database_service()

        with db_service.get_session() as session:
            # Find topic by title (case-insensitive)
            topic = session.execute(
                select(BiteSizedTopic)
                .where(func.lower(BiteSizedTopic.title).like(f'%{topic_title.lower()}%'))
            ).scalars().first()

            if not topic:
                print(f"❌ No topic found matching '{topic_title}'")
                return

            print(f"🎯 Topic Details: {topic.title}")
            print("=" * 60)
            print(f"📝 Core Concept: {topic.core_concept}")
            print(f"👤 User Level: {topic.user_level}")
            print(f"⚙️  Creation Strategy: {topic.creation_strategy}")
            print(f"🗓️  Created: {topic.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            # Show learning objectives
            if topic.learning_objectives:
                print("🎯 Learning Objectives:")
                for i, obj in enumerate(topic.learning_objectives, 1):
                    print(f"  {i}. {obj}")
                print()

            # Show components
            components = session.execute(
                select(BiteSizedComponent.component_type, func.count(BiteSizedComponent.id))
                .where(BiteSizedComponent.topic_id == topic.id)
                .group_by(BiteSizedComponent.component_type)
            ).all()

            if components:
                print("📚 Components:")
                for component_type, count in components:
                    print(f"  • {component_type}: {count}")
                print()

            # Show key concepts
            if topic.key_concepts:
                print("🔑 Key Concepts:")
                for concept in topic.key_concepts:
                    print(f"  • {concept}")
                print()

    except Exception as e:
        print(f"⚠️  Error reading topic details: {e}")


def main():
    parser = argparse.ArgumentParser(description="Quick inspection of learning content")
    parser.add_argument("--paths", action="store_true", help="Show learning paths summary")
    parser.add_argument("--content", action="store_true", help="Show bite-sized content summary")
    parser.add_argument("--topic", type=str, help="Show details for specific topic")
    parser.add_argument("--all", action="store_true", help="Show everything")

    args = parser.parse_args()

    if not any([args.paths, args.content, args.topic, args.all]):
        parser.print_help()
        return

    print("🔍 DeepLearn Content Inspector")
    print("=" * 40)
    print()

    try:
        if args.all or args.paths:
            quick_paths_summary()
            if args.all:
                print()

        if args.all or args.content:
            quick_content_summary()
            if args.all and args.topic:
                print()

        if args.topic:
            show_topic_details(args.topic)

    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("Make sure PostgreSQL is running and DATABASE_URL is configured")
        print("See POSTGRES_MIGRATION_GUIDE.md for setup instructions")


if __name__ == "__main__":
    main()