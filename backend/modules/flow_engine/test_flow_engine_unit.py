"""Unit tests for flow_engine module."""

from unittest.mock import MagicMock
import uuid

from pydantic import BaseModel, Field

from .flows.base import BaseFlow
from .models import FlowRunModel, FlowStepRunModel
from .repo import FlowRunRepo, FlowStepRunRepo
from .service import FlowEngineService
from .steps.base import StepResult, StepType, StructuredStep, UnstructuredStep


class TestModels:
    """Test SQLAlchemy models."""

    def test_flow_run_model_creation(self):
        """Test FlowRunModel creation."""
        flow_run = FlowRunModel(
            flow_name="test_flow",
            inputs={"test": "data"},
            status="pending",
            execution_mode="sync",  # Explicitly set default value for testing
            progress_percentage=0.0,  # Explicitly set default value for testing
        )

        assert flow_run.flow_name == "test_flow"
        assert flow_run.inputs == {"test": "data"}
        assert flow_run.status == "pending"
        assert flow_run.execution_mode == "sync"  # default
        assert flow_run.progress_percentage == 0.0  # default

    def test_flow_step_run_model_creation(self):
        """Test FlowStepRunModel creation."""
        flow_run_id = uuid.uuid4()
        step_run = FlowStepRunModel(flow_run_id=flow_run_id, step_name="test_step", step_order=1, inputs={"input": "value"}, status="pending")

        assert step_run.flow_run_id == flow_run_id
        assert step_run.step_name == "test_step"
        assert step_run.step_order == 1
        assert step_run.inputs == {"input": "value"}
        assert step_run.status == "pending"


class TestRepositories:
    """Test repository classes."""

    def test_flow_run_repo_initialization(self):
        """Test FlowRunRepo initialization."""
        mock_session = MagicMock()
        repo = FlowRunRepo(mock_session)

        assert repo.s == mock_session

    def test_flow_step_run_repo_initialization(self):
        """Test FlowStepRunRepo initialization."""
        mock_session = MagicMock()
        repo = FlowStepRunRepo(mock_session)

        assert repo.s == mock_session


class TestService:
    """Test service layer."""

    def test_flow_engine_service_initialization(self):
        """Test FlowEngineService initialization."""
        mock_flow_repo = MagicMock()
        mock_step_repo = MagicMock()
        mock_llm_services = MagicMock()

        service = FlowEngineService(mock_flow_repo, mock_step_repo, mock_llm_services)

        assert service.flow_run_repo == mock_flow_repo
        assert service.step_run_repo == mock_step_repo
        assert service.llm_services == mock_llm_services


class TestSteps:
    """Test step base classes."""

    def test_step_type_enum(self):
        """Test StepType enum values."""
        assert StepType.UNSTRUCTURED_LLM.value == "unstructured_llm"
        assert StepType.STRUCTURED_LLM.value == "structured_llm"
        assert StepType.IMAGE_GENERATION.value == "image_generation"
        assert StepType.NEWS_GATHERING.value == "news_gathering"

    def test_step_result_creation(self):
        """Test StepResult creation."""
        result = StepResult(step_name="test_step", output_content="test output", metadata={"tokens": 100, "cost": 0.01})

        assert result.step_name == "test_step"
        assert result.output_content == "test output"
        assert result.metadata["tokens"] == 100
        assert result.metadata["cost"] == 0.01

    def test_unstructured_step_properties(self):
        """Test UnstructuredStep properties."""

        class TestStep(UnstructuredStep):
            step_name = "test_unstructured"
            prompt_file = "test.md"

            class Inputs(BaseModel):
                text: str = Field(..., description="Input text")

        step = TestStep()
        assert step.step_name == "test_unstructured"
        assert step.prompt_file == "test.md"
        assert step.step_type == StepType.UNSTRUCTURED_LLM
        assert step.inputs_model == TestStep.Inputs

    def test_structured_step_properties(self):
        """Test StructuredStep properties."""

        class TestStep(StructuredStep):
            step_name = "test_structured"
            prompt_file = "test.md"

            class Inputs(BaseModel):
                text: str = Field(..., description="Input text")

            class Outputs(BaseModel):
                result: str = Field(..., description="Output result")

        step = TestStep()
        assert step.step_name == "test_structured"
        assert step.prompt_file == "test.md"
        assert step.step_type == StepType.STRUCTURED_LLM
        assert step.inputs_model == TestStep.Inputs
        assert step.outputs_model == TestStep.Outputs


class TestFlows:
    """Test flow base classes."""

    def test_base_flow_properties(self):
        """Test BaseFlow properties."""

        class TestFlow(BaseFlow):
            flow_name = "test_flow"

            class Inputs(BaseModel):
                data: str = Field(..., description="Input data")

            async def _execute_flow_logic(self, inputs):
                return {"result": inputs["data"]}

        flow = TestFlow()
        assert flow.flow_name == "test_flow"
        assert flow.inputs_model == TestFlow.Inputs
