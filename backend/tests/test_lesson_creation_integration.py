"""
Integration test for complete lesson creation flow.

This test uses the real PostgreSQL database and makes actual LLM API calls
to test the complete lesson creation workflow from source material to stored content.

The test uses gpt-5 model to test the new GPT-5 Responses API functionality.
"""

from collections.abc import Generator
import logging
import os
from typing import Any, cast

import pytest
from sqlalchemy import desc as _desc

from modules.content.repo import ContentRepo
from modules.content.service import ContentService
from modules.content_creator.service import ContentCreatorService
from modules.flow_engine.models import FlowRunModel
from modules.infrastructure.public import infrastructure_provider


class TestLessonCreationIntegration:
    """Integration test for complete lesson creation workflow."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_environment(self) -> Generator[None, None, None]:
        """Set up test environment and validate required variables."""
        print("🔧 Setting up test environment...")

        # Ensure we have required environment variables
        if not os.environ.get("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not set - skipping integration test")
            pytest.skip("OPENAI_API_KEY not set - skipping integration test")

        if not os.environ.get("DATABASE_URL"):
            print("❌ DATABASE_URL not set - skipping integration test")
            pytest.skip("DATABASE_URL not set - skipping integration test")

        print("✅ Environment variables validated")

        # Setup detailed logging if verbose mode is enabled
        if os.environ.get("INTEGRATION_TEST_VERBOSE_LOGGING") == "true":
            print("📝 Configuring detailed logging for verbose mode...")
            logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])

            # Set specific loggers to DEBUG for detailed flow tracking
            logging.getLogger("modules.llm_services.providers.openai").setLevel(logging.DEBUG)
            logging.getLogger("modules.flow_engine.flows.base").setLevel(logging.DEBUG)
            logging.getLogger("modules.flow_engine.steps.base").setLevel(logging.DEBUG)
            logging.getLogger("modules.content_creator.flows").setLevel(logging.INFO)
            logging.getLogger("modules.content_creator.service").setLevel(logging.INFO)
            print("✅ Detailed logging configured")
        else:
            logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])

        print("✅ Test environment setup complete")
        yield
        print("🧹 Test environment cleanup complete")

    @pytest.fixture(scope="class")
    def test_database_url(self) -> str:
        """Get test database URL - use existing database for integration tests."""
        # For integration tests, we use the existing database
        # This is acceptable since we're testing the real workflow
        # and we'll use unique IDs to avoid conflicts
        return os.environ["DATABASE_URL"]

    @pytest.fixture(scope="class")
    def infrastructure_service(self) -> Any:
        """Set up infrastructure service with database."""
        print("🏗️ Setting up infrastructure service...")

        # For integration tests, we use the existing database and schema
        # No need to override DATABASE_URL since test_database_url returns the same URL

        # Initialize infrastructure
        print("🔌 Initializing infrastructure provider...")
        infra = infrastructure_provider()
        print("⚡ Calling infra.initialize()...")
        infra.initialize()
        print("✅ Infrastructure initialized")

        # Verify the database connection works
        print("🔍 Validating database environment...")
        status = infra.validate_environment()
        if not status.is_valid:
            print(f"❌ Database environment not valid: {status.errors}")
            pytest.skip(f"Database environment not valid: {status.errors}")

        print("✅ Database environment validated")
        yield infra

        print("🧹 Infrastructure cleanup complete")

    @pytest.fixture
    def sample_source_material(self) -> str:
        """Provide sample source material for testing."""
        return """
        # Cross-Entropy Loss in Deep Learning

        Cross-entropy loss is a fundamental loss function used in classification tasks,
        particularly in neural networks. It measures the difference between the predicted
        probability distribution and the true distribution.

        ## Mathematical Definition

        For a single sample, cross-entropy loss is defined as:
        L = -∑(y_i * log(ŷ_i))

        Where:
        - y_i is the true label (one-hot encoded)
        - ŷ_i is the predicted probability for class i

        ## Key Properties

        1. **Non-negative**: Cross-entropy loss is always ≥ 0
        2. **Convex**: Has a single global minimum
        3. **Differentiable**: Enables gradient-based optimization
        4. **Probabilistic interpretation**: Based on maximum likelihood estimation

        ## Implementation in PyTorch

        ```python
        import torch
        import torch.nn as nn

        # Create loss function
        criterion = nn.CrossEntropyLoss()

        # Example usage
        outputs = torch.randn(3, 5)  # 3 samples, 5 classes
        targets = torch.tensor([1, 0, 4])  # True class indices
        loss = criterion(outputs, targets)
        ```

        ## Common Applications

        - Multi-class classification
        - Binary classification (with sigmoid activation)
        - Neural language models
        - Image classification tasks
        """

    # Removed lesson creation integration test to minimize costly runs

    # Removed additional fast-default lesson test to keep integration suite minimal


class TestUnitCreationIntegration:
    """Integration test for complete unit creation workflow from topic only."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_environment(self) -> Generator[None, None, None]:
        """Set up test environment and validate required variables."""
        print("🔧 Setting up test environment for unit creation...")

        # Ensure we have required environment variables
        if not os.environ.get("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not set - skipping integration test")
            pytest.skip("OPENAI_API_KEY not set - skipping integration test")

        if not os.environ.get("DATABASE_URL"):
            print("❌ DATABASE_URL not set - skipping integration test")
            pytest.skip("DATABASE_URL not set - skipping integration test")

        print("✅ Environment variables validated")

        # Setup detailed logging if verbose mode is enabled
        if os.environ.get("INTEGRATION_TEST_VERBOSE_LOGGING") == "true":
            print("📝 Configuring detailed logging for verbose mode...")
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[logging.StreamHandler()],
            )

            # Set specific loggers to DEBUG for detailed flow tracking
            logging.getLogger("modules.llm_services.providers.openai").setLevel(logging.DEBUG)
            logging.getLogger("modules.flow_engine.flows.base").setLevel(logging.DEBUG)
            logging.getLogger("modules.flow_engine.steps.base").setLevel(logging.DEBUG)
            logging.getLogger("modules.content_creator.flows").setLevel(logging.INFO)
            logging.getLogger("modules.content_creator.service").setLevel(logging.INFO)
            print("✅ Detailed logging configured")
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[logging.StreamHandler()],
            )

        print("✅ Test environment setup complete")
        yield
        print("🧹 Test environment cleanup complete")

    @pytest.fixture(scope="class")
    def infrastructure_service(self) -> Any:
        """Set up infrastructure service with database."""
        print("🏗️ Setting up infrastructure service...")

        # Initialize infrastructure
        print("🔌 Initializing infrastructure provider...")
        infra = infrastructure_provider()
        print("⚡ Calling infra.initialize()...")
        infra.initialize()
        print("✅ Infrastructure initialized")

        # Verify the database connection works
        print("🔍 Validating database environment...")
        status = infra.validate_environment()
        if not status.is_valid:
            print(f"❌ Database environment not valid: {status.errors}")
            pytest.skip(f"Database environment not valid: {status.errors}")

        print("✅ Database environment validated")
        yield infra

        print("🧹 Infrastructure cleanup complete")

    @pytest.mark.asyncio
    async def test_unit_creation_from_topic(self, infrastructure_service) -> None:
        """Create a unit from a topic (no source material) targeting 10 minutes."""
        print("🚀 Starting unit creation workflow test (topic-only)...")

        # Arrange: Ensure model is set before creating services
        print("🔧 Setting up test environment and services...")
        os.environ["OPENAI_MODEL"] = "gpt-5-nano"
        print(f"📝 Using model: {os.environ['OPENAI_MODEL']}")

        # Create services using the initialized infrastructure service
        print("🗄️ Getting database session...")
        db_session = infrastructure_service.get_database_session()
        print("📚 Creating content service...")
        content_service = ContentService(ContentRepo(db_session.session))
        print("🤖 Creating content creator service...")
        creator_service = ContentCreatorService(content_service)
        print("✅ Services created successfully")

        topic = "Introduction to Gradient Descent"

        # Act: Create the unit via unified API (foreground)
        result = await creator_service.create_unit(
            topic=topic,
            source_material=None,
            background=False,
            target_lesson_count=10,
            user_level="beginner",
            domain="Machine Learning",
        )

        # Assert: Verify result structure
        assert result is not None
        # Narrow type for static analysis
        unit_result = cast(ContentCreatorService.UnitCreationResult, result)
        assert isinstance(unit_result.unit_id, str) and len(unit_result.unit_id) > 0
        assert isinstance(unit_result.title, str) and len(unit_result.title) > 0
        assert unit_result.lesson_count >= 1
        assert isinstance(unit_result.lesson_titles, list) and len(unit_result.lesson_titles) >= 1
        assert unit_result.target_lesson_count == 10
        assert unit_result.generated_from_topic is True

        # Verify unit was saved to database
        saved_unit = content_service.get_unit(unit_result.unit_id)
        assert saved_unit is not None
        assert saved_unit.generated_from_topic is True
        assert saved_unit.target_lesson_count == 10
        assert saved_unit.learning_objectives is None or isinstance(saved_unit.learning_objectives, list)
        # flow_type should default to 'standard'
        assert getattr(saved_unit, "flow_type", "standard") == "standard"

        # Verify flow run record for unit_creation
        flow_run = db_session.session.query(FlowRunModel).filter(FlowRunModel.flow_name == "unit_creation").order_by(_desc(FlowRunModel.created_at)).first()

        assert flow_run is not None
        assert flow_run.status == "completed"
        assert flow_run.outputs is not None
        assert isinstance(flow_run.outputs, dict)
        assert "lesson_titles" in flow_run.outputs

        # Cleanup: Close the database session
        infrastructure_service.close_database_session(db_session)
        print("🧹 Database session cleanup complete")

    # Removed second unit creation test to keep integration suite minimal
