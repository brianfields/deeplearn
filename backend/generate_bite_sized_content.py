#!/usr/bin/env python3
"""
Bite-Sized Content Generation Script

This script generates bite-sized content for existing learning paths that don't have it yet.
It handles the long-running process outside of web requests and provides progress tracking.

Usage:
    python generate_bite_sized_content.py [options]

Options:
    --list              List learning paths that need bite-sized content
    --generate-all      Generate content for all paths that need it
    --generate-path ID  Generate content for a specific learning path
    --strategy STRATEGY Strategy to use (core_only, complete, assessment_focused, interactive_focused)
    --max-topics N      Maximum number of topics to process per path (default: 5)
    --check-status      Check generation status for all paths
    --resume            Resume interrupted generation
"""

import asyncio
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core import ServiceConfig, LLMClient, ServiceFactory
from config.config import get_llm_config
from modules.lesson_planning.bite_sized_topics.orchestrator import (
    TopicOrchestrator, TopicSpec, CreationStrategy
)
from modules.lesson_planning.bite_sized_topics.storage import TopicRepository
from simple_storage import SimpleStorage, SimpleLearningPath

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BatchContentGenerator:
    """Handles batch generation of bite-sized content"""

    def __init__(self, strategy: CreationStrategy = CreationStrategy.COMPLETE, max_topics: int = 5):
        self.strategy = strategy
        self.max_topics = max_topics
        llm_config = get_llm_config()
        self.config = ServiceFactory.create_service_config(llm_config)
        self.llm_client = LLMClient(llm_config)
        self.orchestrator = TopicOrchestrator(self.config, self.llm_client)
        self.repository = TopicRepository()
        self.storage = SimpleStorage()

    async def initialize(self):
        """Initialize the repository"""
        await self.repository.initialize()

    async def list_paths_needing_content(self) -> List[Dict[str, Any]]:
        """List learning paths that need bite-sized content"""
        paths = self.storage.get_all_learning_paths()
        needs_content = []

        for path in paths:
            topics_with_content = sum(1 for topic in path.topics if topic.has_bite_sized_content)
            total_topics = len(path.topics)

            if topics_with_content < min(self.max_topics, total_topics):
                needs_content.append({
                    'id': path.id,
                    'topic_name': path.topic_name,
                    'total_topics': total_topics,
                    'topics_with_content': topics_with_content,
                    'topics_needed': min(self.max_topics, total_topics) - topics_with_content,
                    'created_at': path.created_at
                })

        return needs_content

    async def generate_content_for_path(self, path_id: str, resume: bool = False) -> Dict[str, Any]:
        """Generate bite-sized content for a specific learning path"""
        try:
            path = self.storage.get_learning_path(path_id)
            if not path:
                raise ValueError(f"Learning path {path_id} not found")

            logger.info(f"🚀 Starting content generation for: {path.topic_name}")
            logger.info(f"📊 Strategy: {self.strategy.value}, Max topics: {self.max_topics}")

            topics_to_process = []
            for i, topic in enumerate(path.topics):
                if i >= self.max_topics:
                    break

                # Skip if already has content and not resuming
                if topic.has_bite_sized_content and not resume:
                    logger.info(f"⏭️  Skipping topic {i+1}: {topic.title} (already has content)")
                    continue

                topics_to_process.append((i, topic))

            if not topics_to_process:
                logger.info("✅ All topics already have bite-sized content")
                return {"status": "complete", "topics_processed": 0}

            results = []
            for i, (topic_index, topic) in enumerate(topics_to_process):
                logger.info(f"📝 Processing topic {topic_index + 1}/{len(path.topics)}: {topic.title}")

                try:
                    # Create topic specification
                    topic_spec = TopicSpec(
                        topic_title=topic.title,
                        core_concept=topic.description,
                        user_level="advanced",  # Could be made configurable
                        learning_objectives=topic.learning_objectives,
                        key_concepts=topic.learning_objectives[:3],
                        key_aspects=[topic.title],
                        target_insights=topic.learning_objectives[:2],
                        common_misconceptions=[],
                        previous_topics=[path.topics[j].title for j in range(topic_index)],
                        creation_strategy=self.strategy
                    )

                    # Generate content
                    start_time = datetime.now()
                    topic_content = await self.orchestrator.create_topic(topic_spec)
                    generation_time = (datetime.now() - start_time).total_seconds()

                    # Store in database
                    bite_sized_topic_id = await self.repository.store_topic(topic_content)

                    # Update the learning path
                    self.storage.update_topic_bite_sized_content(
                        path_id, topic_index, bite_sized_topic_id
                    )

                    results.append({
                        "topic_index": topic_index,
                        "topic_title": topic.title,
                        "topic_id": bite_sized_topic_id,
                        "generation_time": generation_time,
                        "components": topic_content.component_count,
                        "total_items": topic_content.total_items
                    })

                    logger.info(f"✅ Completed topic {topic_index + 1}: {topic.title}")
                    logger.info(f"   📊 {topic_content.component_count} components, {topic_content.total_items} items")
                    logger.info(f"   ⏱️  {generation_time:.1f}s")

                except Exception as e:
                    logger.error(f"❌ Failed to generate content for topic {topic_index + 1}: {e}")
                    results.append({
                        "topic_index": topic_index,
                        "topic_title": topic.title,
                        "error": str(e)
                    })

            success_count = sum(1 for r in results if "error" not in r)
            logger.info(f"🎉 Content generation complete for {path.topic_name}")
            logger.info(f"✅ {success_count}/{len(topics_to_process)} topics processed successfully")

            return {
                "status": "complete",
                "topics_processed": success_count,
                "topics_failed": len(topics_to_process) - success_count,
                "results": results
            }

        except Exception as e:
            logger.error(f"❌ Failed to generate content for path {path_id}: {e}")
            raise

    async def generate_content_for_all_paths(self) -> Dict[str, Any]:
        """Generate content for all paths that need it"""
        paths_needing_content = await self.list_paths_needing_content()

        if not paths_needing_content:
            logger.info("✅ All learning paths already have bite-sized content")
            return {"status": "complete", "paths_processed": 0}

        logger.info(f"🔄 Found {len(paths_needing_content)} paths needing content generation")

        overall_results = []
        for path_info in paths_needing_content:
            try:
                result = await self.generate_content_for_path(path_info['id'])
                overall_results.append({
                    "path_id": path_info['id'],
                    "path_name": path_info['topic_name'],
                    **result
                })

                # Small delay between paths to avoid overwhelming the system
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ Failed to process path {path_info['id']}: {e}")
                overall_results.append({
                    "path_id": path_info['id'],
                    "path_name": path_info['topic_name'],
                    "status": "failed",
                    "error": str(e)
                })

        success_count = sum(1 for r in overall_results if r.get("status") == "complete")
        logger.info(f"🎉 Batch generation complete: {success_count}/{len(paths_needing_content)} paths processed")

        return {
            "status": "complete",
            "paths_processed": success_count,
            "paths_failed": len(paths_needing_content) - success_count,
            "results": overall_results
        }

    async def check_generation_status(self) -> Dict[str, Any]:
        """Check the generation status of all learning paths"""
        paths = self.storage.get_all_learning_paths()
        status_info = []

        for path in paths:
            topics_with_content = sum(1 for topic in path.topics if topic.has_bite_sized_content)
            total_topics = len(path.topics)
            max_expected = min(self.max_topics, total_topics)

            status = "complete" if topics_with_content >= max_expected else "partial"
            if topics_with_content == 0:
                status = "none"

            status_info.append({
                'id': path.id,
                'topic_name': path.topic_name,
                'status': status,
                'topics_with_content': topics_with_content,
                'total_topics': total_topics,
                'max_expected': max_expected,
                'completion_percentage': (topics_with_content / max_expected) * 100 if max_expected > 0 else 0
            })

        return {
            "total_paths": len(paths),
            "complete": len([s for s in status_info if s['status'] == 'complete']),
            "partial": len([s for s in status_info if s['status'] == 'partial']),
            "none": len([s for s in status_info if s['status'] == 'none']),
            "paths": status_info
        }

async def main():
    parser = argparse.ArgumentParser(description='Generate bite-sized content for learning paths')
    parser.add_argument('--list', action='store_true', help='List paths needing content')
    parser.add_argument('--generate-all', action='store_true', help='Generate content for all paths')
    parser.add_argument('--generate-path', type=str, help='Generate content for specific path ID')
    parser.add_argument('--strategy', type=str, default='complete',
                       choices=['core_only', 'complete', 'assessment_focused', 'interactive_focused'],
                       help='Generation strategy')
    parser.add_argument('--max-topics', type=int, default=5, help='Maximum topics per path')
    parser.add_argument('--check-status', action='store_true', help='Check generation status')
    parser.add_argument('--resume', action='store_true', help='Resume interrupted generation')

    args = parser.parse_args()

    # Map strategy string to enum
    strategy_map = {
        'core_only': CreationStrategy.CORE_ONLY,
        'complete': CreationStrategy.COMPLETE,
        'assessment_focused': CreationStrategy.ASSESSMENT_FOCUSED,
        'interactive_focused': CreationStrategy.INTERACTIVE_FOCUSED
    }

    strategy = strategy_map[args.strategy]

    generator = BatchContentGenerator(strategy=strategy, max_topics=args.max_topics)
    await generator.initialize()

    try:
        if args.list:
            paths = await generator.list_paths_needing_content()
            print("\n📚 Learning Paths Needing Bite-Sized Content:")
            print("=" * 60)
            if not paths:
                print("✅ All learning paths already have bite-sized content")
            else:
                for path in paths:
                    print(f"📖 {path['topic_name']}")
                    print(f"   🆔 {path['id']}")
                    print(f"   📊 {path['topics_with_content']}/{path['total_topics']} topics have content")
                    print(f"   🎯 Need {path['topics_needed']} more topics")
                    print(f"   📅 Created: {path['created_at']}")
                    print()

        elif args.generate_all:
            result = await generator.generate_content_for_all_paths()
            print(f"\n🎉 Generation Complete!")
            print(f"✅ {result['paths_processed']} paths processed successfully")
            if result['paths_failed'] > 0:
                print(f"❌ {result['paths_failed']} paths failed")

        elif args.generate_path:
            result = await generator.generate_content_for_path(args.generate_path, resume=args.resume)
            print(f"\n🎉 Generation Complete!")
            print(f"✅ {result['topics_processed']} topics processed successfully")
            if result.get('topics_failed', 0) > 0:
                print(f"❌ {result['topics_failed']} topics failed")

        elif args.check_status:
            status = await generator.check_generation_status()
            print(f"\n📊 Generation Status Summary:")
            print("=" * 50)
            print(f"📚 Total paths: {status['total_paths']}")
            print(f"✅ Complete: {status['complete']}")
            print(f"🔄 Partial: {status['partial']}")
            print(f"❌ None: {status['none']}")
            print()

            for path in status['paths']:
                status_emoji = {"complete": "✅", "partial": "🔄", "none": "❌"}[path['status']]
                print(f"{status_emoji} {path['topic_name']}")
                print(f"   📊 {path['topics_with_content']}/{path['max_expected']} topics ({path['completion_percentage']:.0f}%)")
                print(f"   🆔 {path['id']}")
                print()

        else:
            parser.print_help()

    except KeyboardInterrupt:
        logger.info("🛑 Generation interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())