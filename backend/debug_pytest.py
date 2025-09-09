#!/usr/bin/env python3
"""
Debug script to isolate pytest fixture issues.
"""

import asyncio
import logging
import os
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def load_env_file(env_path: Path) -> None:
    """Load environment variables from .env file"""
    if not env_path.exists():
        return

    print(f"📄 Loading environment from: {env_path}")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Only set if not already in environment
                if key not in os.environ:
                    os.environ[key] = value


async def test_content_creator_flow():
    """Test the content creator flow directly without pytest."""
    print("🚀 Testing content creator flow directly...")

    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.getLogger("modules.llm_services.providers.openai").setLevel(logging.INFO)
    logging.getLogger("modules.flow_engine.flows.base").setLevel(logging.INFO)
    logging.getLogger("modules.flow_engine.steps.base").setLevel(logging.INFO)
    logging.getLogger("modules.content_creator.flows").setLevel(logging.INFO)
    logging.getLogger("modules.content_creator.service").setLevel(logging.INFO)

    # Set model
    os.environ["OPENAI_MODEL"] = "gpt-5"
    print(f"📝 Using model: {os.environ['OPENAI_MODEL']}")

    try:
        # Import and setup services
        print("📚 Importing services...")
        from modules.content.repo import ContentRepo
        from modules.content.service import ContentService
        from modules.content_creator.service import ContentCreatorService, CreateTopicRequest
        from modules.infrastructure.public import infrastructure_provider

        print("🏗️ Setting up infrastructure...")
        infra = infrastructure_provider()
        infra.initialize()

        print("🗄️ Getting database session...")
        db_session = infra.get_database_session()

        print("📚 Creating services...")
        content_service = ContentService(ContentRepo(db_session))
        creator_service = ContentCreatorService(content_service)

        print("📝 Creating test request...")
        sample_source_material = """
        # Cross-Entropy Loss in Deep Learning

        Cross-entropy loss is a fundamental loss function used in classification tasks.
        It measures the difference between predicted and true probability distributions.

        ## Mathematical Definition
        For a single sample: L = -∑(y_i * log(ŷ_i))

        ## Key Properties
        1. Non-negative: Always ≥ 0
        2. Convex: Single global minimum
        3. Differentiable: Enables gradient optimization
        """

        request = CreateTopicRequest(title="Cross-Entropy Loss in Deep Learning", core_concept="Cross-Entropy Loss Function", source_material=sample_source_material, user_level="intermediate", domain="Machine Learning")

        print("🎯 Starting topic creation...")
        result = await creator_service.create_topic_from_source_material(request)

        print("🎉 Topic creation completed!")
        print(f"Topic ID: {result.topic_id}")
        print(f"Title: {result.title}")
        print(f"Components created: {result.components_created}")

        # Cleanup
        infra.close_database_session(db_session)
        infra.shutdown()

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the debug test."""
    print("🧪 Debug testing content creator flow...")

    # Load environment
    backend_dir = Path(__file__).parent
    env_files = [backend_dir / ".env.local", backend_dir / ".env.test", backend_dir / ".env", backend_dir.parent / ".env"]

    for env_file in env_files:
        load_env_file(env_file)

    # Check environment
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        return 1

    if not os.environ.get("DATABASE_URL"):
        print("❌ DATABASE_URL not set")
        return 1

    print("✅ Environment variables validated")

    # Run the async test
    try:
        success = asyncio.run(test_content_creator_flow())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1


if __name__ == "__main__":
    sys.exit(main())
