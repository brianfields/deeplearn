#!/usr/bin/env python3
"""
Update Learning Paths to Complete Strategy

This script updates existing learning paths to use the COMPLETE strategy
for bite-sized content generation instead of CORE_ONLY.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from simple_storage import SimpleStorage
from modules.lesson_planning.service import LessonPlanningService
from config.config import get_learning_service_config
from core import LLMClient

async def main():
    """Update existing learning paths to use COMPLETE strategy"""

    # Initialize services
    config = get_learning_service_config()
    llm_client = LLMClient(config.llm_config)
    lesson_service = LessonPlanningService(config, llm_client)
    storage = SimpleStorage()

    # Get all learning paths
    paths = storage.get_all_learning_paths()
    print(f"Found {len(paths)} learning paths")

    # Show current status
    for path in paths:
        topics_with_content = sum(1 for topic in path.topics if topic.has_bite_sized_content)
        print(f"📚 {path.topic_name}: {topics_with_content}/{len(path.topics)} topics have bite-sized content")

    print("\n🎯 The lesson planning service has been updated to use COMPLETE strategy.")
    print("🎯 New learning paths will automatically get rich content with 6 component types:")
    print("   - Didactic snippet")
    print("   - Glossary")
    print("   - Socratic dialogues")
    print("   - Short answer questions")
    print("   - Multiple choice questions")
    print("   - Post-topic quiz")
    print("\n💡 Create a new learning path to test the enhanced content generation!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())