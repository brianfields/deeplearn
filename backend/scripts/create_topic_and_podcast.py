#!/usr/bin/env python3
"""
Topic and Podcast Creation Script

Creates a complete learning topic from source material and then generates a podcast episode:
1. Generate complete topic content from source material (didactic snippet, glossary, MCQs)
2. Save topic to database
3. Generate podcast script from the created topic
4. Save podcast episode to database
5. Display results

Usage:
    python scripts/create_topic_and_podcast.py \
        --topic "PyTorch Cross-Entropy Loss" \
        --concept "Cross-Entropy Loss Function" \
        --material scripts/examples/cross_entropy_material.txt \
        --verbose

    python scripts/create_topic_and_podcast.py \
        --topic "Neural Networks" \
        --concept "Neural Network Basics" \
        --material scripts/examples/cross_entropy_material.txt \
        --output combined_output.json \
        --verbose

"""

import argparse
import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
import uuid

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.llm_client import LLMClient
from src.core.service_base import ServiceConfig
from src.data_structures import BiteSizedComponent, BiteSizedTopic
from src.database_service import DatabaseService
from src.llm_interface import LLMConfig, LLMProviderType
from src.modules.content_creation.service import BiteSizedTopicContent, BiteSizedTopicService
from src.modules.podcast.service import PodcastService, PodcastEpisode


async def save_complete_topic_to_database(
    db_service: DatabaseService,
    topic_content: BiteSizedTopicContent,
    topic_title: str,
    core_concept: str,
    user_level: str,
    source_material: str,
    domain: str,
    verbose: bool = False,
) -> str:
    """Save the complete topic and all components to database."""
    topic_id = str(uuid.uuid4())

    if verbose:
        print(f"🔄 Saving complete topic to database with ID: {topic_id}")

    # Extract learning objectives from didactic snippet or use defaults
    learning_objectives = getattr(topic_content.didactic_snippet, "learning_objectives", [core_concept])
    if not learning_objectives:
        learning_objectives = [core_concept]

    # Create topic
    topic = BiteSizedTopic(
        id=topic_id,
        title=topic_title,
        core_concept=core_concept,
        user_level=user_level,
        learning_objectives=learning_objectives,
        key_concepts=[core_concept],
        source_material=source_material,
        source_domain=domain,
        source_level=user_level,
        refined_material={},  # Not directly accessible from the service result
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Create components
    components = []

    # Didactic snippet component
    didactic_component = BiteSizedComponent(
        id=str(uuid.uuid4()),
        topic_id=topic_id,
        component_type="didactic_snippet",
        title=topic_content.didactic_snippet.title,
        content=topic_content.didactic_snippet.model_dump(),
    )
    components.append(didactic_component)

    # Glossary component
    glossary_component = BiteSizedComponent(
        id=str(uuid.uuid4()),
        topic_id=topic_id,
        component_type="glossary",
        title=f"Glossary for {topic_title}",
        content=topic_content.glossary.model_dump(),
    )
    components.append(glossary_component)

    # MCQ components (one for each MCQ)
    for mcq_question in topic_content.multiple_choice_questions:
        mcq_component = BiteSizedComponent(
            id=str(uuid.uuid4()),
            topic_id=topic_id,
            component_type="mcq",
            title=f"MCQ: {mcq_question.title}",
            content=mcq_question.model_dump(),
        )
        components.append(mcq_component)

    # Attach components to topic
    topic.components = components

    # Save to database
    if db_service.save_bite_sized_topic(topic):
        if verbose:
            print(f"✅ Saved topic: {topic_title}")
            print("✅ Saved didactic snippet component")
            print(f"✅ Saved glossary component with {len(topic_content.glossary.glossary_entries)} entries")
            print(f"✅ Saved {len(topic_content.multiple_choice_questions)} MCQ components")
            print(f"🎉 Complete topic saved with {len(components)} components!")
        return topic_id
    else:
        raise Exception("Failed to save topic to database")


def display_podcast_script(episode: PodcastEpisode) -> None:
    """Display the podcast script content in a readable format."""
    print("\n" + "="*60)
    print("🎤 PODCAST SCRIPT")
    print("="*60)
    print(f"📻 Title: {episode.title}")
    print(f"⏱️  Duration: {episode.total_duration_minutes} minutes")
    print(f"📚 Learning Outcomes: {len(episode.learning_outcomes)}")
    print()

    if episode.learning_outcomes:
        print("🎯 Learning Outcomes:")
        for i, outcome in enumerate(episode.learning_outcomes, 1):
            print(f"   {i}. {outcome}")
        print()

    print("📝 FULL SCRIPT:")
    print("-" * 60)
    print(episode.full_script)
    print("-" * 60)
    print()


async def generate_podcast_from_topic(
    topic_id: str,
    verbose: bool = False,
) -> str | None:
    """Generate a podcast from an existing topic."""
    try:
        # Initialize services
        llm_config = LLMConfig(provider=LLMProviderType.OPENAI, model="gpt-4o", temperature=0.7)
        llm_client = LLMClient(llm_config)
        config = ServiceConfig(llm_config=llm_config)

        podcast_service = PodcastService(config, llm_client)
        db_service = DatabaseService()

        if verbose:
            print(f"🎤 Generating podcast for topic: {topic_id}")

        # Get topic info
        topic = db_service.get_bite_sized_topic(topic_id)
        if not topic:
            print(f"❌ Topic {topic_id} not found")
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
            print(f"   • Duration: {script.total_duration_seconds} seconds ({script.total_duration_seconds//60} minutes)")
            print(f"   • Segments: {len(script.segments)}")
            print(f"   • Learning outcomes: {len(script.learning_outcomes)}")

        # Save to database
        if verbose:
            print("💾 Saving podcast episode to database...")

        episode_id = db_service.save_podcast_episode(script, topic_id)

        if verbose:
            print(f"✅ Saved podcast episode: {episode_id}")

        # Retrieve the episode to verify and display
        episode = await podcast_service.get_podcast_episode(episode_id)
        if episode:
            if verbose:
                print("✅ Retrieved episode successfully!")
                print(f"   • Episode ID: {episode.id}")
                print(f"   • Title: {episode.title}")
                print(f"   • Duration: {episode.total_duration_minutes} minutes")
                print(f"   • Script length: {len(episode.full_script)} characters")

            # Display the podcast script content
            display_podcast_script(episode)

        return episode_id

    except Exception as e:
        print(f"❌ Error generating podcast: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return None


async def create_topic_and_podcast(
    topic_title: str,
    core_concept: str,
    source_material: str,
    user_level: str,
    domain: str,
    verbose: bool = False,
    output_file: str | None = None,
) -> tuple[str, str | None]:
    """Create a topic and generate a podcast from it."""

    if verbose:
        print("🎯 Creating topic and podcast workflow")
        print("=" * 50)
        print(f"📋 Topic: {topic_title}")
        print(f"🎯 Core Concept: {core_concept}")
        print(f"📚 User Level: {user_level}")
        print(f"🏷️  Domain: {domain}")
        print()

    try:
        # Initialize services
        llm_config = LLMConfig(provider=LLMProviderType.OPENAI, model="gpt-4o", temperature=0.7)
        llm_client = LLMClient(llm_config)
        config = ServiceConfig(llm_config=llm_config)

        topic_service = BiteSizedTopicService(config, llm_client)
        db_service = DatabaseService()

        # Step 1: Generate complete topic content
        if verbose:
            print("🔄 Step 1: Generating complete topic content...")

        topic_content = await topic_service.create_complete_bite_sized_topic(
            topic_title=topic_title,
            core_concept=core_concept,
            source_material=source_material,
            user_level=user_level,
            domain=domain,
        )

        if verbose:
            print("✅ Generated complete topic content!")
            print(f"   • Didactic snippet: {topic_content.didactic_snippet.title}")
            print(f"   • Glossary entries: {len(topic_content.glossary.glossary_entries)}")
            print(f"   • Multiple choice questions: {len(topic_content.multiple_choice_questions)}")

        # Step 2: Save topic to database
        if verbose:
            print("\n🔄 Step 2: Saving topic to database...")

        topic_id = await save_complete_topic_to_database(
            db_service=db_service,
            topic_content=topic_content,
            topic_title=topic_title,
            core_concept=core_concept,
            user_level=user_level,
            source_material=source_material,
            domain=domain,
            verbose=verbose,
        )

        if verbose:
            print(f"✅ Topic saved with ID: {topic_id}")

        # Step 3: Generate podcast from the created topic
        if verbose:
            print("\n🔄 Step 3: Generating podcast from topic...")

        episode_id = await generate_podcast_from_topic(
            topic_id=topic_id,
            verbose=verbose,
        )

        if verbose:
            if episode_id:
                print(f"✅ Podcast generated with episode ID: {episode_id}")
            else:
                print("❌ Failed to generate podcast")

        # Save combined output to JSON file if requested
        if output_file and episode_id:
            # Get the podcast script for JSON output
            podcast_service = PodcastService(config, llm_client)
            script = await podcast_service.generate_podcast_script(topic_id)

            output_data = {
                "topic_id": topic_id,
                "episode_id": episode_id,
                "topic_title": topic_title,
                "core_concept": core_concept,
                "user_level": user_level,
                "domain": domain,
                "topic_content": {
                    "didactic_snippet": topic_content.didactic_snippet.model_dump(),
                    "glossary": topic_content.glossary.model_dump(),
                    "mcqs": [mcq.model_dump() for mcq in topic_content.multiple_choice_questions],
                },
                "podcast_script": {
                    "title": script.title,
                    "description": script.description,
                    "total_duration_seconds": script.total_duration_seconds,
                    "learning_outcomes": script.learning_outcomes,
                    "segments": [segment.model_dump() for segment in script.segments],
                    "full_script": script.full_script,
                },
                "generated_at": datetime.now().isoformat(),
            }

            with Path.open(output_file, "w") as f:
                json.dump(output_data, f, indent=2, default=str)

            if verbose:
                print(f"📁 Combined content saved to: {output_file}")

        return topic_id, episode_id

    except Exception as e:
        print(f"❌ Error in topic and podcast creation: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return None, None


async def main() -> None:
    # Parse arguments
    parser = argparse.ArgumentParser(description="Create topic and generate podcast from source material")
    parser.add_argument("--topic", required=True, help="Topic title")
    parser.add_argument("--concept", required=True, help="Core concept to focus on")
    parser.add_argument("--material", required=True, help="Path to source material text file")
    parser.add_argument(
        "--level",
        default="intermediate",
        choices=["beginner", "intermediate", "advanced"],
        help="Target user level",
    )
    parser.add_argument("--domain", default="Machine Learning", help="Subject domain")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress and service logs")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--output", help="Save combined content to JSON file for inspection")

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

    # Validate inputs
    material_path = Path(args.material)
    if not material_path.exists():
        print(f"❌ Error: Material file not found: {args.material}")
        sys.exit(1)

    # Read source material
    try:
        source_material = material_path.read_text(encoding="utf-8")
        if args.verbose:
            print(f"📄 Loaded source material: {len(source_material)} characters")
    except Exception as e:
        print(f"❌ Error reading material file: {e}")
        sys.exit(1)

    try:
        # Create topic and generate podcast
        topic_id, episode_id = await create_topic_and_podcast(
            topic_title=args.topic,
            core_concept=args.concept,
            source_material=source_material,
            user_level=args.level,
            domain=args.domain,
            verbose=args.verbose,
            output_file=args.output,
        )

        if topic_id:
            print("\n🎉 Topic and podcast creation completed successfully!")
            print(f"   • Topic ID: {topic_id}")
            print(f"   • Episode ID: {episode_id if episode_id else 'Failed to generate'}")
            print(f"   • Topic URL: http://localhost:3000/learn/{topic_id}?mode=learning")

            if episode_id:
                print(f"   • Podcast API: http://localhost:8000/api/content-creation/podcasts/{episode_id}")
                print(f"   • Topic Podcast API: http://localhost:8000/api/content-creation/podcasts/topic/{topic_id}")

            if args.output:
                print(f"   • Combined content saved to: {args.output}")
        else:
            print("❌ Failed to create topic and podcast")
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
