"""Unit tests for flow_engine module."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from pydantic import BaseModel, Field
import pytest

from .base_flow import BaseFlow
from .base_step import StepResult, StepType, StructuredStep, UnstructuredStep
from .models import FlowRunModel, FlowStepRunModel
from .repo import FlowRunRepo, FlowStepRunRepo
from .service import FlowEngineService


class TestModels:
    """Test SQLAlchemy models."""

    def test_flow_run_model_creation(self) -> None:
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

    def test_flow_run_model_arq_execution(self) -> None:
        """Test FlowRunModel with ARQ execution mode."""
        flow_run = FlowRunModel(
            flow_name="test_arq_flow",
            inputs={"test": "data"},
            status="pending",
            execution_mode="arq",  # Test new ARQ execution mode
            progress_percentage=0.0,
        )

        assert flow_run.flow_name == "test_arq_flow"
        assert flow_run.inputs == {"test": "data"}
        assert flow_run.status == "pending"
        assert flow_run.execution_mode == "arq"  # ARQ mode
        assert flow_run.progress_percentage == 0.0

    def test_flow_step_run_model_creation(self) -> None:
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

    def test_flow_run_repo_initialization(self) -> None:
        """Test FlowRunRepo initialization."""
        mock_session = MagicMock()
        repo = FlowRunRepo(mock_session)

        assert repo.s == mock_session

    def test_flow_step_run_repo_initialization(self) -> None:
        """Test FlowStepRunRepo initialization."""
        mock_session = MagicMock()
        repo = FlowStepRunRepo(mock_session)

        assert repo.s == mock_session


class TestService:
    """Test service layer."""

    def test_flow_engine_service_initialization(self) -> None:
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

    def test_step_type_enum(self) -> None:
        """Test StepType enum values."""
        assert StepType.UNSTRUCTURED_LLM.value == "unstructured_llm"
        assert StepType.STRUCTURED_LLM.value == "structured_llm"
        assert StepType.IMAGE_GENERATION.value == "image_generation"
        assert StepType.NEWS_GATHERING.value == "news_gathering"

    def test_step_result_creation(self) -> None:
        """Test StepResult creation."""
        result = StepResult(step_name="test_step", output_content="test output", metadata={"tokens": 100, "cost": 0.01})

        assert result.step_name == "test_step"
        assert result.output_content == "test output"
        assert result.metadata["tokens"] == 100
        assert result.metadata["cost"] == 0.01

    def test_unstructured_step_properties(self) -> None:
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

    def test_structured_step_properties(self) -> None:
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

    def test_base_flow_properties(self) -> None:
        """Test BaseFlow properties."""

        class TestFlow(BaseFlow):
            flow_name = "test_flow"

            class Inputs(BaseModel):
                data: str = Field(..., description="Input data")

            async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
                return {"result": inputs["data"]}

        flow = TestFlow()
        assert flow.flow_name == "test_flow"
        assert flow.inputs_model == TestFlow.Inputs

    @pytest.mark.asyncio
    async def test_execute_arq_integration(self) -> None:
        """Test BaseFlow ARQ integration."""

        class TestFlow(BaseFlow):
            flow_name = "test_arq_flow"

            class Inputs(BaseModel):
                data: str = Field(..., description="Input data")

            async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
                return {"result": inputs["data"]}

        flow = TestFlow()

        # Mock infrastructure and task queue services
        with (
            patch("modules.flow_engine.base_flow.infrastructure_provider") as mock_infra_provider,
            patch("modules.flow_engine.base_flow.llm_services_provider") as mock_llm_provider,
            patch("modules.task_queue.public.task_queue_provider") as mock_task_queue_provider,
        ):
            # Setup mocks
            mock_infra = MagicMock()
            mock_db_session = MagicMock()
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__ = MagicMock(return_value=mock_db_session)
            mock_context_manager.__exit__ = MagicMock(return_value=False)
            mock_infra.get_session_context.return_value = mock_context_manager
            mock_infra_provider.return_value = mock_infra

            mock_llm = MagicMock()
            mock_llm_provider.return_value = mock_llm

            mock_task_queue = AsyncMock()
            mock_task_result = MagicMock()
            mock_task_result.task_id = "test-task-123"
            mock_task_queue.submit_flow_task.return_value = mock_task_result
            mock_task_queue_provider.return_value = mock_task_queue

            # Mock flow engine service
            mock_service = MagicMock()
            mock_flow_run_id = uuid.uuid4()
            mock_service.create_flow_run_record = AsyncMock(return_value=mock_flow_run_id)
            mock_flow_repo = MagicMock()
            mock_flow_run = MagicMock()
            mock_flow_repo.by_id.return_value = mock_flow_run
            mock_service.flow_run_repo = mock_flow_repo

            with patch("modules.flow_engine.base_flow.FlowEngineService", return_value=mock_service):
                # Execute ARQ flow
                result_flow_run_id = await flow.execute_arq({"data": "test input"})

                # Verify behavior
                assert result_flow_run_id == mock_flow_run_id

                # Verify infrastructure was initialized
                mock_infra.initialize.assert_called_once()

                # Verify flow run was created with ARQ execution mode
                mock_service.create_flow_run_record.assert_called_once()
                call_args = mock_service.create_flow_run_record.call_args
                assert call_args[1]["execution_mode"] == "arq"
                assert call_args[1]["flow_name"] == "test_arq_flow"

                # Verify task was submitted to queue
                mock_task_queue.submit_flow_task.assert_called_once()
                task_call_args = mock_task_queue.submit_flow_task.call_args
                assert task_call_args[1]["flow_name"] == "test_arq_flow"
                assert task_call_args[1]["flow_run_id"] == mock_flow_run_id
                assert task_call_args[1]["inputs"] == {"data": "test input"}

                # Verify arq_task_id persisted on flow run
                mock_flow_repo.by_id.assert_called_once_with(mock_flow_run_id)
                assert mock_flow_run.arq_task_id == mock_task_result.task_id
                mock_flow_repo.save.assert_called_once_with(mock_flow_run)

    @pytest.mark.asyncio
    async def test_execute_arq_with_input_validation(self) -> None:
        """Test ARQ execution with input validation."""

        class TestFlow(BaseFlow):
            flow_name = "test_validation_flow"

            class Inputs(BaseModel):
                required_field: str = Field(..., description="Required field")
                optional_field: int = Field(default=42, description="Optional field")

            async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
                return {"result": f"processed {inputs['required_field']}"}

        flow = TestFlow()

        with (
            patch("modules.flow_engine.base_flow.infrastructure_provider") as mock_infra_provider,
            patch("modules.flow_engine.base_flow.llm_services_provider") as mock_llm_provider,
            patch("modules.task_queue.public.task_queue_provider") as mock_task_queue_provider,
        ):
            # Setup mocks
            mock_infra = MagicMock()
            mock_db_session = MagicMock()
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__ = MagicMock(return_value=mock_db_session)
            mock_context_manager.__exit__ = MagicMock(return_value=False)
            mock_infra.get_session_context.return_value = mock_context_manager
            mock_infra_provider.return_value = mock_infra

            mock_llm_provider.return_value = MagicMock()

            mock_task_queue = AsyncMock()
            mock_task_result = MagicMock()
            mock_task_result.task_id = "validation-task-123"
            mock_task_queue.submit_flow_task.return_value = mock_task_result
            mock_task_queue_provider.return_value = mock_task_queue

            mock_service = MagicMock()
            mock_service.create_flow_run_record = AsyncMock(return_value=uuid.uuid4())
            mock_flow_repo = MagicMock()
            mock_flow_run = MagicMock()
            mock_flow_repo.by_id.return_value = mock_flow_run
            mock_service.flow_run_repo = mock_flow_repo

            with patch("modules.flow_engine.base_flow.FlowEngineService", return_value=mock_service):
                # Execute with valid inputs
                await flow.execute_arq({"required_field": "test"})

                # Verify task was submitted with validated inputs
                task_call_args = mock_task_queue.submit_flow_task.call_args
                submitted_inputs = task_call_args[1]["inputs"]

                # Should have default value filled in
                assert submitted_inputs["required_field"] == "test"
                assert submitted_inputs["optional_field"] == 42
                mock_flow_repo.save.assert_called_once_with(mock_flow_run)
