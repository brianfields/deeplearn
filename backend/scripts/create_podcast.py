#!/usr/bin/env python3
"""
Podcast Generation Script

Generates a podcast episode from an existing topic using the PodcastService:
1. Load existing topic from database
2. Generate podcast script with structure and content
3. Save podcast episode to database
4. Display results

Usage:
    python scripts/create_podcast.py \
        --topic-id "your-topic-id-here" \
        --verbose

    python scripts/create_podcast.py \
        --topic-id "123e4567-e89b-12d3-a456-426614174000" \
        --output podcast_output.json \
        --verbose

"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
import sys
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.llm_client import LLMClient
from src.core.service_base import ServiceConfig
from src.database_service import get_database_service
from src.llm_interface import LLMConfig, LLMProviderType
from src.modules.podcast.service import PodcastService


async def generate_podcast_from_topic(
    topic_id: str,
    verbose: bool = False,
    output_file: str | None = None,
) -> str | None:
    """Generate a podcast episode from an existing topic."""

    if verbose:
        print(f"🎤 Generating podcast for topic: {topic_id}")
        print("🔧 Initializing services...")

    try:
        # Initialize services
        llm_config = LLMConfig(provider=LLMProviderType.OPENAI, model="gpt-4o", temperature=0.7)
        llm_client = LLMClient(llm_config)
        config = ServiceConfig(llm_config=llm_config)

        podcast_service = PodcastService(config, llm_client)
        db_service = get_database_service()

        if verbose:
            print("✅ Services initialized successfully!")

        # Check if topic exists
        topic = db_service.get_bite_sized_topic(topic_id)
        if not topic:
            print(f"❌ Error: Topic {topic_id} not found in database")
            return None

        if verbose:
            print(f"📖 Found topic: {topic.title}")
            print(f"   • Core concept: {topic.core_concept}")
            print(f"   • Learning objectives: {len(topic.learning_objectives)}")
            print(f"   • User level: {topic.user_level}")

        # Generate podcast script
        if verbose:
            print("🔄 Generating podcast script...")

        script = await podcast_service.generate_podcast_script(topic_id)

        if verbose:
            print("✅ Generated podcast script!")
            print(f"   • Title: {script.title}")
            print(f"   • Duration: {script.total_duration_seconds} seconds ({script.total_duration_seconds // 60} minutes)")
            print(f"   • Segments: {len(script.segments)}")
            print(f"   • Learning outcomes: {len(script.learning_outcomes)}")

        # Save podcast episode to database
        if verbose:
            print("💾 Saving podcast episode to database...")

        episode_id = db_service.save_podcast_episode(script, topic_id)

        if verbose:
            print(f"✅ Saved podcast episode: {episode_id}")

        # Retrieve the episode to verify
        episode = await podcast_service.get_podcast_episode(episode_id)
        if episode:
            if verbose:
                print("✅ Retrieved episode successfully!")
                print(f"   • Episode ID: {episode.id}")
                print(f"   • Title: {episode.title}")
                print(f"   • Duration: {episode.total_duration_minutes} minutes")
                print(f"   • Script length: {len(episode.full_script)} characters")

        # Save to JSON file if requested
        if output_file:
            output_data = {
                "episode_id": episode_id,
                "topic_id": topic_id,
                "topic_title": topic.title,
                "podcast_title": script.title,
                "description": script.description,
                "total_duration_seconds": script.total_duration_seconds,
                "total_duration_minutes": script.total_duration_seconds // 60,
                "learning_outcomes": script.learning_outcomes,
                "segments": [segment.model_dump() for segment in script.segments],
                "full_script": script.full_script,
                "metadata": script.metadata.model_dump(),
                "generated_at": datetime.now().isoformat(),
            }

            with Path.open(output_file, "w") as f:
                json.dump(output_data, f, indent=2, default=str)

            if verbose:
                print(f"📁 Podcast content saved to: {output_file}")

        return episode_id

    except Exception as e:
        print(f"❌ Error generating podcast: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return None


async def list_available_topics(verbose: bool = False) -> None:
    """List all available topics in the database."""

    if verbose:
        print("📋 Listing available topics...")

    try:
        db_service = get_database_service()

        # Get all topics (this would need to be implemented in DatabaseService)
        # For now, we'll just show a message
        print("ℹ️  To see available topics, you can:")
        print("   1. Check your database directly")
        print("   2. Use the existing topic creation script first")
        print("   3. Create topics via the API endpoint")

        if verbose:
            print("💡 Tip: Use the create_topic.py script to create topics first")

    except Exception as e:
        print(f"❌ Error listing topics: {e}")


async def main() -> None:
    # Parse arguments
    parser = argparse.ArgumentParser(description="Generate podcast episode from existing topic")
    parser.add_argument("--topic-id", help="ID of the topic to generate podcast from")
    parser.add_argument("--list-topics", action="store_true", help="List available topics")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress and service logs")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--output", help="Save podcast content to JSON file for inspection")

    args = parser.parse_args()

    # Configure logging based on verbose/debug settings
    if args.debug:
        log_level = logging.DEBUG
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        print("🔧 Debug mode: All service logs including OpenAI API calls enabled")
    elif args.verbose:
        log_level = logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        print("🔧 Verbose mode: Detailed service logs enabled")
    else:
        # Only show warnings and errors from services
        logging.basicConfig(level=logging.WARNING)

    # Handle list topics request
    if args.list_topics:
        await list_available_topics(args.verbose)
        return

    # Validate required arguments
    if not args.topic_id:
        print("❌ Error: --topic-id is required")
        print("\nUsage examples:")
        print("  python scripts/create_podcast.py --topic-id your-topic-id --verbose")
        print("  python scripts/create_podcast.py --list-topics")
        print("\nTo create topics first, use:")
        print("  python scripts/create_topic.py --topic 'Your Topic' --concept 'Core Concept' --material path/to/material.txt")
        sys.exit(1)

    if args.verbose:
        print("🎤 Podcast Generation Script")
        print("=" * 40)
        print(f"📋 Topic ID: {args.topic_id}")
        if args.output:
            print(f"📁 Output file: {args.output}")
        print()

    try:
        # Generate podcast
        episode_id = await generate_podcast_from_topic(
            topic_id=args.topic_id,
            verbose=args.verbose,
            output_file=args.output,
        )

        if episode_id:
            print("🎉 Podcast generated successfully!")
            print(f"   • Episode ID: {episode_id}")
            print(f"   • Topic ID: {args.topic_id}")
            print(f"   • API URL: http://localhost:8000/api/content-creation/podcasts/{episode_id}")
            print(f"   • Topic URL: http://localhost:8000/api/content-creation/podcasts/topic/{args.topic_id}")

            if args.output:
                print(f"   • Content saved to: {args.output}")
        else:
            print("❌ Failed to generate podcast")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
