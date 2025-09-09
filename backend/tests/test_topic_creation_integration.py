"""
Integration test for complete topic creation flow.

This test uses the real PostgreSQL database and makes actual LLM API calls
to test the complete topic creation workflow from source material to stored content.

The test uses gpt-5 model to test the new GPT-5 Responses API functionality.
"""

import logging
import os

import pytest

from modules.content.repo import ContentRepo
from modules.content.service import ContentService
from modules.content_creator.service import ContentCreatorService, CreateTopicRequest
from modules.infrastructure.public import infrastructure_provider


@pytest.mark.integration
@pytest.mark.llm
class TestTopicCreationIntegration:
    """Integration test for complete topic creation workflow."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_environment(self):
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

        # Configure logging for integration test
        print("📝 Configuring logging...")
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])

        # Set specific loggers to DEBUG for detailed flow tracking
        logging.getLogger("modules.llm_services.providers.openai").setLevel(logging.DEBUG)
        logging.getLogger("modules.flow_engine.flows.base").setLevel(logging.DEBUG)
        logging.getLogger("modules.flow_engine.steps.base").setLevel(logging.DEBUG)
        logging.getLogger("modules.content_creator.flows").setLevel(logging.INFO)
        logging.getLogger("modules.content_creator.service").setLevel(logging.INFO)

        print("✅ Test environment setup complete")
        yield
        print("🧹 Test environment cleanup complete")

    @pytest.fixture(scope="class")
    def test_database_url(self):
        """Get test database URL - use existing database for integration tests."""
        # For integration tests, we use the existing database
        # This is acceptable since we're testing the real workflow
        # and we'll use unique IDs to avoid conflicts
        return os.environ["DATABASE_URL"]

    @pytest.fixture(scope="class")
    def infrastructure_service(self):
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
    def sample_source_material(self):
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

    @pytest.mark.asyncio
    async def test_complete_topic_creation_workflow(self, infrastructure_service, sample_source_material):
        """
        Test the complete topic creation workflow with real database and LLM calls.

        This test:
        1. Creates a topic from source material using real LLM calls
        2. Verifies the topic is saved to the database
        3. Checks that components (didactic snippet, glossary, MCQs) are created
        4. Validates the structure and content of created components
        """
        print("🚀 Starting topic creation workflow test...")

        # Arrange: Ensure model is set before creating LLM service
        # The LLM service reads environment variables at initialization time
        print("🔧 Setting up test environment and services...")
        os.environ["OPENAI_MODEL"] = "gpt-4o-mini"
        print(f"📝 Using model: {os.environ['OPENAI_MODEL']}")

        # Create services using the initialized infrastructure service
        print("🗄️ Getting database session...")
        db_session = infrastructure_service.get_database_session()
        print("📚 Creating content service...")
        content_service = ContentService(ContentRepo(db_session))
        print("🤖 Creating content creator service...")
        # llm_service no longer needed - flows handle LLM interactions internally
        creator_service = ContentCreatorService(content_service)
        print("✅ Services created successfully")

        request = CreateTopicRequest(title="Cross-Entropy Loss in Deep Learning", core_concept="Cross-Entropy Loss Function", source_material=sample_source_material, user_level="intermediate", domain="Machine Learning")

        # Act: Create the topic
        result = await creator_service.create_topic_from_source_material(request)

        # Assert: Verify the result structure
        assert result is not None
        assert result.topic_id is not None
        assert len(result.topic_id) > 0
        assert result.title == "Cross-Entropy Loss in Deep Learning"
        assert result.components_created > 0

        # Verify topic was saved to database
        saved_topic = content_service.get_topic(result.topic_id)
        assert saved_topic is not None
        assert saved_topic.title == request.title
        assert saved_topic.core_concept == request.core_concept
        assert saved_topic.user_level == request.user_level
        assert saved_topic.source_domain == request.domain

        # Verify topic has expected structure
        assert saved_topic.learning_objectives is not None
        assert len(saved_topic.learning_objectives) > 0
        assert saved_topic.key_concepts is not None
        assert len(saved_topic.key_concepts) > 0

        # Verify components were created
        components = content_service.get_components_by_topic(result.topic_id)
        assert len(components) == result.components_created
        assert len(components) >= 2  # At minimum should have didactic snippet and glossary

        # Check component types
        component_types = {comp.component_type for comp in components}
        assert "didactic_snippet" in component_types
        assert "glossary" in component_types

        # Verify didactic snippet structure
        didactic_components = [c for c in components if c.component_type == "didactic_snippet"]
        assert len(didactic_components) == 1
        didactic = didactic_components[0]
        assert didactic.content is not None
        assert isinstance(didactic.content, dict)
        # Should contain explanation and key points
        assert "explanation" in didactic.content or "overview" in didactic.content

        # Verify glossary structure
        glossary_components = [c for c in components if c.component_type == "glossary"]
        assert len(glossary_components) == 1
        glossary = glossary_components[0]
        assert glossary.content is not None
        assert isinstance(glossary.content, dict)
        # Should contain terms
        assert "terms" in glossary.content
        assert isinstance(glossary.content["terms"], list)
        assert len(glossary.content["terms"]) > 0

        # If MCQs were created, verify their structure
        mcq_components = [c for c in components if c.component_type == "mcq"]
        for mcq in mcq_components:
            assert mcq.content is not None
            assert isinstance(mcq.content, dict)
            # Should have question, options, and correct answer
            assert "question" in mcq.content
            assert "options" in mcq.content
            assert "correct_answer" in mcq.content
            assert isinstance(mcq.content["options"], list)
            assert len(mcq.content["options"]) >= 2
            # correct_answer can be either an integer index or a string answer
            correct_answer = mcq.content["correct_answer"]
            if isinstance(correct_answer, int):
                assert 0 <= correct_answer < len(mcq.content["options"])
            else:
                # If it's a string, it should be one of the options
                assert isinstance(correct_answer, str)
                assert correct_answer in mcq.content["options"]
