"""Integration test for complete lesson creation flow.

This test uses the real PostgreSQL database and makes actual LLM API calls
to test the complete lesson creation workflow from source material to stored content.

The test uses gpt-5 model to test the new GPT-5 Responses API functionality.
"""

import base64
from collections.abc import Generator
import logging
import os
from typing import Any, cast
from unittest.mock import patch
import uuid

import pytest
from sqlalchemy import desc as _desc
from sqlalchemy import select

from modules.content.public import content_provider
from modules.content_creator.public import content_creator_provider
from modules.content_creator.service import ContentCreatorService
from modules.content_creator.steps import ExtractLessonMetadataStep, ExtractUnitMetadataStep, GenerateMCQStep, GenerateUnitArtDescriptionStep
from modules.flow_engine.models import FlowRunModel
from modules.infrastructure.public import infrastructure_provider
from modules.llm_services.public import AudioResponse, ImageResponse, LLMResponse


class TestLessonCreationIntegration:
    """Integration test for complete lesson creation workflow."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_environment(self) -> Generator[None, None, None]:
        """Set up test environment and validate required variables."""
        print("🔧 Setting up test environment...")

        # Allow running without OPENAI_API_KEY when using mocked LLMs
        use_real = os.environ.get("REAL_LLM", "false").lower() == "true"
        if use_real and not os.environ.get("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not set and REAL_LLM=true - skipping integration test")
            pytest.skip("OPENAI_API_KEY not set - skipping integration test with real LLMs")

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
        L = -sum(y_i * log(y_hat_i))

        Where:
        - y_i is the true label (one-hot encoded)
        - y_hat_i is the predicted probability for class i

        ## Key Properties

        1. **Non-negative**: Cross-entropy loss is always >= 0
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


# ------------------------------------------------------------
# LLM mocking: default to mocked responses unless REAL_LLM=true
# ------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def _maybe_mock_llm() -> Generator[None, None, None]:
    """Mock LLM services for all flows/steps by default.

    Set REAL_LLM=true to use real providers.
    """

    use_real = os.environ.get("REAL_LLM", "false").lower() == "true"
    if use_real:
        print("🤖 Using REAL LLM services for integration tests (REAL_LLM=true)")
        yield
        return

    print("🧪 Using MOCKED LLM services for integration tests (set REAL_LLM=true to use real)")

    class _FakeLLMService:
        async def generate_response(self, messages: list[Any], user_id: Any | None = None, model: str | None = None, temperature: float | None = None, max_output_tokens: int | None = None, **kwargs: Any) -> tuple[LLMResponse, uuid.UUID | None]:  # noqa: ARG002
            content = "This is mocked unstructured content."
            for m in messages:
                msg_content = str(getattr(m, "content", ""))
                low = msg_content.lower()
                if "podcast" in low:
                    content = "Mocked podcast transcript of the unit."
                    break
                if "source material" in low:
                    content = "Mocked unit source material with headings and examples."
            response = LLMResponse(
                content=content,
                provider="mock",
                model=model or "mock-model",
                tokens_used=0,
                input_tokens=0,
                output_tokens=0,
                cost_estimate=0.0,
                response_time_ms=5,
                cached=False,
                provider_response_id=None,
                system_fingerprint=None,
                response_output=None,
                response_created_at=None,
            )
            return response, None

        async def generate_structured_response(
            self, _messages: list[Any], response_model: type[Any], _user_id: Any | None = None, _model: str | None = None, _temperature: float | None = None, _max_output_tokens: int | None = None, **_kwargs: Any
        ) -> tuple[Any, uuid.UUID | None, dict[str, Any]]:
            usage = {"tokens_used": 0, "cost_estimate": 0.0}

            if response_model is ExtractUnitMetadataStep.Outputs:
                payload = {
                    "unit_title": "Mocked",
                    "learning_objectives": [
                        {"id": "lo_1", "title": "Understand Concept A", "description": "Understand concept A", "bloom_level": "Understand"},
                        {"id": "lo_2", "title": "Apply Concept B", "description": "Apply concept B", "bloom_level": "Apply"},
                    ],
                    "lessons": [
                        {"title": "Lesson 1", "lesson_objective": "Intro to A", "learning_objective_ids": ["lo_1"]},
                        {"title": "Lesson 2", "lesson_objective": "Intro to B", "learning_objective_ids": ["lo_2"]},
                    ],
                    "lesson_count": 2,
                }
                return response_model.model_validate(payload), None, usage

            if response_model is ExtractLessonMetadataStep.Outputs:
                payload = {
                    "topic": "Mocked Topic",
                    "learner_level": "beginner",
                    "voice": "Plain",
                    "learning_objectives": ["Understand concept A"],
                    "learning_objective_ids": ["lo_1"],
                    "misconceptions": [{"id": "m1", "misbelief": "A is always B", "why_plausible": "Overgeneralization", "correction": "A can be C too"}],
                    "confusables": [{"id": "c1", "a": "term1", "b": "term2", "contrast": "Different contexts"}],
                    "glossary": [{"term": "Entropy", "definition": "Measure of uncertainty", "micro_check": None}],
                    "mini_lesson": "This is a concise mocked mini-lesson.",
                }
                return response_model.model_validate(payload), None, usage

            if response_model is GenerateMCQStep.Outputs:
                payload = {
                    "metadata": {"lesson_title": "Mocked Lesson", "lesson_objective": "Learn A", "learner_level": "beginner", "voice": "Plain"},
                    "mcqs": [
                        {
                            "stem": "What is A?",
                            "options": [
                                {"label": "A", "text": "Option A"},
                                {"label": "B", "text": "Option B"},
                                {"label": "C", "text": "Option C"},
                                {"label": "D", "text": "Option D"},
                            ],
                            "answer_key": {"label": "A", "rationale_right": "Because it's correct"},
                            "learning_objectives_covered": ["lo_1"],
                            "misconceptions_used": [],
                            "confusables_used": [],
                            "glossary_terms_used": [],
                        }
                    ],
                }
                return response_model.model_validate(payload), None, usage

            if response_model is GenerateUnitArtDescriptionStep.Outputs:
                payload = {
                    "prompt": "A geometric abstract representation of learning concepts",
                    "alt_text": "Abstract geometric shapes representing learning",
                    "palette": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
                }
                return response_model.model_validate(payload), None, usage

            try:
                return response_model.model_validate({}), None, usage
            except Exception as exc:
                raise RuntimeError(f"Mock LLM cannot synthesize response for model: {response_model}: {exc}") from None

        async def generate_audio(self, text: str, voice: str, _user_id: Any | None = None, model: str | None = None, _audio_format: str = "mp3", _speed: float | None = None, **_kwargs: Any) -> tuple[AudioResponse, uuid.UUID | None]:  # noqa: ARG002
            audio_base64 = base64.b64encode(b"FAKEAUDIO").decode()
            dto = AudioResponse(audio_base64=audio_base64, mime_type="audio/mpeg", voice=voice, model=model or "mock-tts", cost_estimate=0.0, duration_seconds=8.5)
            return dto, None

        async def generate_image(self, prompt: str, _user_id: Any | None = None, _size: str = "1024x1024", _quality: str = "standard", _style: str | None = None, **_kwargs: Any) -> tuple[Any, uuid.UUID | None]:
            """Mock generate_image for testing."""
            # Return a minimal image response with a proper HTTP URL to avoid httpx protocol error
            dto = ImageResponse(
                image_url="https://example.com/fake-unit-art.png",
                revised_prompt=prompt,
                size=_size,
                cost_estimate=0.0,
            )
            return dto, None

    with patch("modules.flow_engine.base_flow.llm_services_provider", new=lambda: _FakeLLMService()):
        yield

    # Removed lesson creation integration test to minimize costly runs

    # Removed additional fast-default lesson test to keep integration suite minimal


class TestUnitCreationIntegration:
    """Integration test for complete unit creation workflow from topic only."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_environment(self) -> Generator[None, None, None]:
        """Set up test environment and validate required variables."""
        print("🔧 Setting up test environment for unit creation...")

        # Allow running without OPENAI_API_KEY when using mocked LLMs
        use_real = os.environ.get("REAL_LLM", "false").lower() == "true"
        if use_real and not os.environ.get("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not set and REAL_LLM=true - skipping integration test")
            pytest.skip("OPENAI_API_KEY not set - skipping integration test with real LLMs")

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
        """Create a unit from a topic (no source material) targeting 2 lessons."""
        print("🚀 Starting unit creation workflow test (topic-only)...")

        # Arrange: Ensure model is set before creating services
        print("🔧 Setting up test environment and services...")
        os.environ["OPENAI_MODEL"] = "gpt-5-nano"
        print(f"📝 Using model: {os.environ['OPENAI_MODEL']}")

        # Create services using the initialized infrastructure service
        print("🗄️ Getting async database session...")
        async with infrastructure_service.get_async_session_context() as session:
            print("📚 Creating content service...")
            content_service = content_provider(session)
            print("🤖 Creating content creator service...")
            creator_service = content_creator_provider(session)
            print("✅ Services created successfully")

            topic = "Introduction to Gradient Descent"

            # Act: Create the unit via unified API (foreground)
            result = await creator_service.create_unit(
                topic=topic,
                source_material=None,
                background=False,
                target_lesson_count=2,
                learner_level="beginner",
            )

            # Assert: Verify result structure
            assert result is not None
            # Narrow type for static analysis
            unit_result = cast(ContentCreatorService.UnitCreationResult, result)
            assert isinstance(unit_result.unit_id, str) and len(unit_result.unit_id) > 0
            assert isinstance(unit_result.title, str) and len(unit_result.title) > 0
            assert unit_result.lesson_count >= 1
            assert isinstance(unit_result.lesson_titles, list) and len(unit_result.lesson_titles) >= 1
            assert unit_result.target_lesson_count == 2
            assert unit_result.generated_from_topic is True

            # Verify unit was saved to database
            saved_unit = await content_service.get_unit(unit_result.unit_id)
            assert saved_unit is not None
            assert saved_unit.generated_from_topic is True
            assert saved_unit.target_lesson_count == 2
            assert saved_unit.learning_objectives is None or isinstance(saved_unit.learning_objectives, list)
            # flow_type should default to 'standard'
            assert getattr(saved_unit, "flow_type", "standard") == "standard"

            # Verify flow run record for unit_creation
            stmt = select(FlowRunModel).where(FlowRunModel.flow_name == "unit_creation").order_by(_desc(FlowRunModel.created_at))
            result_row = await session.execute(stmt)
            flow_run = result_row.scalars().first()

            assert flow_run is not None
            assert flow_run.status == "completed"
            assert flow_run.outputs is not None
            assert isinstance(flow_run.outputs, dict)
            assert "lessons" in flow_run.outputs

    # Removed second unit creation test to keep integration suite minimal
