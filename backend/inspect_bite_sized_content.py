#!/usr/bin/env python3
"""
Interactive Bite-Sized Content Inspector for PostgreSQL

This script provides an interactive menu system for inspecting
bite-sized content stored in PostgreSQL database.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

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


class ContentInspector:
    """PostgreSQL-based content inspector"""

    def __init__(self):
        """Initialize the inspector"""
        try:
            self.db_service = get_database_service()
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            print("Make sure PostgreSQL is running and DATABASE_URL is configured")
            sys.exit(1)

    def get_learning_paths(self) -> Dict[str, Any]:
        """Get all learning paths"""
        try:
            return self.db_service.get_all_learning_paths()
        except Exception as e:
            print(f"⚠️  Error reading learning paths: {e}")
            return {}

    def get_bite_sized_topics(self) -> List[Dict[str, Any]]:
        """Get all bite-sized topics from database"""
        try:
            with self.db_service.get_session() as session:
                topics = session.execute(
                    select(BiteSizedTopic).order_by(BiteSizedTopic.created_at.desc())
                ).scalars().all()

                result = []
                for topic in topics:
                    topic_dict = {
                        'id': topic.id,
                        'title': topic.title,
                        'core_concept': topic.core_concept,
                        'user_level': topic.user_level,
                        'learning_objectives': topic.learning_objectives or [],
                        'key_concepts': topic.key_concepts or [],
                        'key_aspects': topic.key_aspects or [],
                        'target_insights': topic.target_insights or [],
                        'common_misconceptions': topic.common_misconceptions or [],
                        'previous_topics': topic.previous_topics or [],
                        'creation_strategy': topic.creation_strategy,
                        'creation_metadata': topic.creation_metadata or {},
                        'created_at': topic.created_at.isoformat() if topic.created_at else "",
                        'updated_at': topic.updated_at.isoformat() if topic.updated_at else "",
                        'version': topic.version
                    }
                    result.append(topic_dict)

                return result

        except Exception as e:
            print(f"⚠️  Error reading database: {e}")
            return []

    def get_topic_components(self, topic_id: str) -> List[Dict[str, Any]]:
        """Get components for a specific topic"""
        try:
            with self.db_service.get_session() as session:
                components = session.execute(
                    select(BiteSizedComponent)
                    .where(BiteSizedComponent.topic_id == topic_id)
                    .order_by(BiteSizedComponent.component_type)
                ).scalars().all()

                result = []
                for component in components:
                    comp_dict = {
                        'id': component.id,
                        'topic_id': component.topic_id,
                        'component_type': component.component_type,
                        'content': component.content,
                        'metadata': component.component_metadata or {},
                        'created_at': component.created_at.isoformat() if component.created_at else "",
                        'updated_at': component.updated_at.isoformat() if component.updated_at else "",
                        'version': component.version
                    }
                    result.append(comp_dict)

                return result

        except Exception as e:
            print(f"⚠️  Error reading topic components: {e}")
            return []

    def show_overview(self):
        """Show overview of all content"""
        learning_paths = self.get_learning_paths()
        topics = self.get_bite_sized_topics()

        print("🎓 DeepLearn Content Overview")
        print("=" * 50)

        # Learning paths summary
        print(f"📚 Learning Paths: {len(learning_paths)}")
        for path_id, path in learning_paths.items():
            topics_with_content = sum(1 for topic in path.topics if topic.get('has_bite_sized_content', False))
            print(f"  📖 {path.topic_name}")
            print(f"     📝 {len(path.topics)} topics, {topics_with_content} with content")

        print()

        # Bite-sized content summary
        print(f"🔍 Bite-Sized Topics: {len(topics)}")
        if topics:
            # Group by user level
            level_counts = {}
            strategy_counts = {}
            for topic in topics:
                level = topic['user_level']
                strategy = topic['creation_strategy']
                level_counts[level] = level_counts.get(level, 0) + 1
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

            print("  👤 By User Level:")
            for level, count in level_counts.items():
                print(f"     {level}: {count}")

            print("  ⚙️  By Creation Strategy:")
            for strategy, count in strategy_counts.items():
                print(f"     {strategy}: {count}")

        print()

    def show_learning_paths(self):
        """Show detailed learning paths"""
        learning_paths = self.get_learning_paths()

        if not learning_paths:
            print("📚 No learning paths found")
            return

        print("📚 Learning Paths")
        print("=" * 40)

        for i, (path_id, path) in enumerate(learning_paths.items(), 1):
            print(f"{i}. {path.topic_name}")
            print(f"   🆔 {path_id}")
            print(f"   📝 {len(path.topics)} topics")
            print(f"   🗓️  {path.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

            # Show topics with bite-sized content
            topics_with_content = [t for t in path.topics if t.get('has_bite_sized_content', False)]
            if topics_with_content:
                print(f"   📚 Topics with content:")
                for topic in topics_with_content[:3]:  # Show first 3
                    print(f"      • {topic['title']}")
                if len(topics_with_content) > 3:
                    print(f"      • ... and {len(topics_with_content) - 3} more")
            print()

    def show_bite_sized_content(self):
        """Show bite-sized content summary"""
        topics = self.get_bite_sized_topics()

        if not topics:
            print("🔍 No bite-sized content found")
            return

        print("🔍 Bite-Sized Content")
        print("=" * 40)

        for i, topic in enumerate(topics[:20], 1):  # Show first 20
            print(f"{i}. {topic['title']}")
            print(f"   🎯 {topic['core_concept']}")
            print(f"   👤 {topic['user_level']} • ⚙️ {topic['creation_strategy']}")
            print(f"   🗓️  {topic['created_at'][:19]}")
            print(f"   🆔 {topic['id']}")
            print()

        if len(topics) > 20:
            print(f"... and {len(topics) - 20} more topics")

    def show_topic_details(self, topic_id: str):
        """Show detailed information about a specific topic"""
        topics = self.get_bite_sized_topics()
        topic = next((t for t in topics if t['id'] == topic_id), None)

        if not topic:
            print(f"❌ Topic {topic_id} not found")
            return

        print(f"🎯 Topic Details: {topic['title']}")
        print("=" * 60)

        print(f"🆔 ID: {topic['id']}")
        print(f"🎯 Core Concept: {topic['core_concept']}")
        print(f"👤 User Level: {topic['user_level']}")
        print(f"⚙️  Creation Strategy: {topic['creation_strategy']}")
        print(f"🗓️  Created: {topic['created_at'][:19]}")
        print()

        # Learning objectives
        if topic['learning_objectives']:
            print("🎯 Learning Objectives:")
            for i, obj in enumerate(topic['learning_objectives'], 1):
                print(f"  {i}. {obj}")
            print()

        # Key concepts
        if topic['key_concepts']:
            print("🔑 Key Concepts:")
            for concept in topic['key_concepts']:
                print(f"  • {concept}")
            print()

        # Components
        components = self.get_topic_components(topic_id)
        if components:
            print(f"📚 Components ({len(components)}):")
            for component in components:
                print(f"  🔧 {component['component_type'].upper()}")
                if component['metadata']:
                    for key, value in component['metadata'].items():
                        if isinstance(value, (str, int, float)):
                            print(f"     {key}: {value}")
            print()

    def interactive_menu(self):
        """Show interactive menu"""
        while True:
            print("\n🎓 DeepLearn Content Inspector")
            print("=" * 40)
            print("1. 📊 Overview")
            print("2. 📚 Learning Paths")
            print("3. 🔍 Bite-Sized Content")
            print("4. 🎯 Topic Details")
            print("5. 🚪 Exit")
            print()

            try:
                choice = input("Choose an option (1-5): ").strip()

                if choice == '1':
                    print()
                    self.show_overview()
                elif choice == '2':
                    print()
                    self.show_learning_paths()
                elif choice == '3':
                    print()
                    self.show_bite_sized_content()
                elif choice == '4':
                    print()
                    topic_id = input("Enter topic ID: ").strip()
                    if topic_id:
                        print()
                        self.show_topic_details(topic_id)
                    else:
                        print("❌ Please provide a topic ID")
                elif choice == '5':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-5.")

                input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main function"""
    inspector = ContentInspector()

    # Check if database has content
    try:
        with inspector.db_service.get_session() as session:
            topic_count = session.execute(select(func.count(BiteSizedTopic.id))).scalar()

        db_exists = topic_count > 0

        if not db_exists:
            print("❌ No content found in database")
            print("\n💡 To generate content:")
            print("   1. Create learning paths using the API or web interface")
            print("   2. Generate bite-sized content for topics")
            print("   3. Run this inspector again")
            return

        print(f"✅ Found {topic_count} bite-sized topics in database")

    except Exception as e:
        print(f"❌ Database error: {e}")
        print("Make sure PostgreSQL is running and DATABASE_URL is configured")
        return

    # Run interactive menu
    inspector.interactive_menu()


if __name__ == "__main__":
    main()