"""
Integration test for complete lesson creation flow.

This test uses the real PostgreSQL database and makes actual LLM API calls
to test the complete lesson creation workflow from source material to stored content.

The test uses gpt-5 model to test the new GPT-5 Responses API functionality.
"""

import logging
import os

import pytest
from sqlalchemy import desc

from modules.content.repo import ContentRepo
from modules.content.service import ContentService
from modules.content_creator.service import ContentCreatorService, CreateLessonRequest
from modules.flow_engine.models import FlowRunModel, FlowStepRunModel
from modules.infrastructure.public import infrastructure_provider


class TestLessonCreationIntegration:
    """Integration test for complete lesson creation workflow."""

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
    async def test_complete_lesson_creation_workflow(self, infrastructure_service, sample_source_material):
        """
        Test the complete lesson creation workflow with real database and LLM calls.

        This test:
        1. Creates a lesson from source material using real LLM calls
        2. Verifies the lesson is saved to the database
        3. Checks that components (didactic snippet, glossary, MCQs) are created
        4. Validates the structure and content of created components
        """
        print("🚀 Starting lesson creation workflow test...")

        # Arrange: Ensure model is set before creating LLM service
        # The LLM service reads environment variables at initialization time
        print("🔧 Setting up test environment and services...")
        os.environ["OPENAI_MODEL"] = "gpt-5-nano"
        print(f"📝 Using model: {os.environ['OPENAI_MODEL']}")

        # Create services using the initialized infrastructure service
        print("🗄️ Getting database session...")
        db_session = infrastructure_service.get_database_session()
        print("📚 Creating content service...")
        content_service = ContentService(ContentRepo(db_session.session))
        print("🤖 Creating content creator service...")
        # llm_service no longer needed - flows handle LLM interactions internally
        creator_service = ContentCreatorService(content_service)
        print("✅ Services created successfully")

        request = CreateLessonRequest(title="Cross-Entropy Loss in Deep Learning", core_concept="Cross-Entropy Loss Function", source_material=sample_source_material, user_level="intermediate", domain="Machine Learning")

        # Act: Create the lesson
        result = await creator_service.create_lesson_from_source_material(request)

        # Assert: Verify the result structure
        assert result is not None
        assert result.lesson_id is not None
        assert len(result.lesson_id) > 0
        assert result.title == "Cross-Entropy Loss in Deep Learning"
        assert result.components_created > 0

        # Verify lesson was saved to database
        saved_lesson = content_service.get_lesson(result.lesson_id)
        assert saved_lesson is not None
        assert saved_lesson.title == request.title
        assert saved_lesson.core_concept == request.core_concept
        assert saved_lesson.user_level == request.user_level
        assert saved_lesson.source_domain == request.domain

        # Verify lesson has expected structure
        assert saved_lesson.package is not None
        assert saved_lesson.package.objectives is not None
        assert len(saved_lesson.package.objectives) > 0

        # Verify package components were created
        assert saved_lesson.package.glossary is not None
        assert len(saved_lesson.package.glossary.get("terms", [])) > 0
        assert saved_lesson.package.mcqs is not None
        assert len(saved_lesson.package.mcqs) > 0

        # Verify component counts match result
        assert len(saved_lesson.package.objectives) == result.objectives_count
        assert len(saved_lesson.package.glossary.get("terms", [])) == result.glossary_terms_count
        assert len(saved_lesson.package.mcqs) == result.mcqs_count

        # Verify didactic snippet structure (should be in package.didactic)
        # Note: didactic snippets may not always be created depending on flow implementation
        if saved_lesson.package.didactic and "by_lo" in saved_lesson.package.didactic:
            didactic_lo_keys = list(saved_lesson.package.didactic["by_lo"].keys())
            if len(didactic_lo_keys) > 0:
                first_didactic = saved_lesson.package.didactic["by_lo"][didactic_lo_keys[0]]
                assert first_didactic.plain_explanation is not None
                assert len(first_didactic.key_takeaways) > 0

        # Verify glossary structure (already checked counts above)
        for term in saved_lesson.package.glossary["terms"]:
            assert term.term is not None
            assert term.definition is not None

        # Verify MCQ structure
        for mcq in saved_lesson.package.mcqs:
            assert mcq.stem is not None
            assert len(mcq.options) >= 2  # Should have at least 2 options
            assert mcq.answer_key is not None

        # Verify flow run and step run records
        # Fetch the most recent flow run for this flow
        flow_run = db_session.session.query(FlowRunModel).filter(FlowRunModel.flow_name == "lesson_creation").order_by(desc(FlowRunModel.created_at)).first()

        assert flow_run is not None
        assert flow_run.status == "completed"
        assert flow_run.outputs is not None
        assert isinstance(flow_run.outputs, dict)
        assert "learning_objectives" in flow_run.outputs

        # Verify expected steps exist and counts match
        step_runs = db_session.session.query(FlowStepRunModel).filter(FlowStepRunModel.flow_run_id == flow_run.id).order_by(FlowStepRunModel.step_order).all()
        assert len(step_runs) >= 3

        step_names = [s.step_name for s in step_runs]
        assert "extract_lesson_metadata" in step_names
        assert "generate_didactic_snippet" in step_names
        assert "generate_glossary" in step_names

        expected_mcq_count = len(flow_run.outputs.get("learning_objectives", []))
        actual_mcq_count = sum(1 for n in step_names if n == "generate_mcq")
        assert actual_mcq_count == expected_mcq_count

        # Ensure all steps completed successfully
        assert all(s.status == "completed" for s in step_runs)

        # Cleanup: Close the database session
        infrastructure_service.close_database_session(db_session)
        print("🧹 Database session cleanup complete")
