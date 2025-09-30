"""Base flow class with consistent execute() interface and automatic context management."""

from abc import ABC, abstractmethod
from collections.abc import Callable
import functools
import logging
from typing import Any, cast
import uuid

from pydantic import BaseModel

from ..infrastructure.public import infrastructure_provider
from ..llm_services.public import llm_services_provider
from .context import FlowContext
from .repo import FlowRunRepo, FlowStepRunRepo
from .service import FlowEngineService
from .types import FlowExecutionKwargs

logger = logging.getLogger(__name__)

__all__ = ["BaseFlow", "FlowExecutionKwargs", "flow_execution"]


def flow_execution(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that provides flow context automatically.

    This decorator handles all the infrastructure setup and cleanup,
    so flow methods can focus on pure business logic.
    """

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: FlowExecutionKwargs) -> Any:
        # Get infrastructure service
        infra = infrastructure_provider()
        infra.initialize()
        llm_services = llm_services_provider()

        # Keep the entire flow execution within a managed DB session so writes commit
        with infra.get_session_context() as db_session:
            service = FlowEngineService(FlowRunRepo(db_session), FlowStepRunRepo(db_session), llm_services)

            # Create flow run record
            inputs = args[0] if args else {}
            # Strict validation (match step behavior): validate then dump, or log and raise
            inputs_model = getattr(self, "inputs_model", None)
            if inputs_model and isinstance(inputs, dict):
                try:
                    validated_inputs = inputs_model(**inputs)  # type: ignore[misc]
                    inputs = validated_inputs.model_dump()
                except Exception as e:
                    errors_detail = None
                    errors_attr = getattr(e, "errors", None)
                    if callable(errors_attr):
                        try:
                            errors_detail = errors_attr()
                        except Exception:
                            errors_detail = None
                    logger.error(
                        "Flow input validation failed; refusing to create run",
                        extra={
                            "flow_name": self.flow_name,
                            "error": repr(e),
                            "input_keys": list(inputs.keys()) if isinstance(inputs, dict) else None,
                            "errors": errors_detail,
                        },
                    )
                    raise
            user_id = cast(uuid.UUID | None, kwargs.get("user_id"))

            logger.info(f"🚀 Starting flow: {self.flow_name}")
            logger.debug(f"Flow inputs: {list(inputs.keys()) if isinstance(inputs, dict) else 'N/A'}")

            flow_run_id = await service.create_flow_run_record(flow_name=self.flow_name, inputs=inputs, user_id=user_id)

            # Set up flow context
            FlowContext.set(service=service, flow_run_id=flow_run_id, user_id=user_id, step_counter=0)

            try:
                # Execute the flow method
                logger.info(f"⚙️ Executing flow logic: {self.flow_name}")
                result = await func(self, *args, **kwargs)

                # Complete the flow run
                await service.complete_flow_run(flow_run_id, result)
                logger.info(f"✅ Flow completed successfully: {self.flow_name}")

                return result

            except Exception as e:
                # Mark flow as failed
                logger.error(f"❌ Flow failed: {self.flow_name} - {e!s}")
                await service.fail_flow_run(flow_run_id, str(e))
                raise

            finally:
                # Clean up context
                FlowContext.clear()

    return wrapper


class BaseFlow(ABC):
    """
    Base class for all flows providing consistent execute() interface.

    This class provides:
    - Consistent execute() method for all flows
    - Automatic context management through decorators
    - Input validation with Pydantic models
    - Infrastructure setup and cleanup
    """

    # Required class attribute (must be set by subclasses)
    flow_name: str

    @property
    def inputs_model(self) -> type[BaseModel] | None:
        """Return the input validation model if defined."""
        return getattr(self, "Inputs", None)

    @flow_execution
    async def execute(self, inputs: dict[str, Any], **kwargs: FlowExecutionKwargs) -> dict[str, Any]:  # noqa: ARG002
        """
        Execute the flow with automatic context management and input validation.

        Args:
            inputs: Dictionary of input parameters
            **kwargs: Additional parameters (user_id, etc.)

        Returns:
            Dictionary containing flow results
        """
        # Validate inputs if model is defined
        if self.inputs_model:
            validated_inputs = self.inputs_model(**inputs)
            inputs = validated_inputs.model_dump()

        # Execute the flow logic
        return await self._execute_flow_logic(inputs)

    async def execute_arq(self, inputs: dict[str, Any], **kwargs: FlowExecutionKwargs) -> uuid.UUID:
        """
        Execute the flow using ARQ background task queue and return the flow run ID for tracking.

        Args:
            inputs: Dictionary of input parameters
            **kwargs: Additional parameters (user_id, etc.)

        Returns:
            Flow run ID that can be used to track progress
        """
        # Get infrastructure and task queue services
        infra = infrastructure_provider()
        infra.initialize()
        llm_services = llm_services_provider()

        # Import here to avoid circular imports
        from ..task_queue.public import task_queue_provider  # noqa: PLC0415

        task_queue = task_queue_provider()

        # Validate inputs if model is defined
        if self.inputs_model:
            validated_inputs = self.inputs_model(**inputs)
            inputs = validated_inputs.model_dump()

        user_id = cast(uuid.UUID | None, kwargs.get("user_id"))

        logger.info(f"🚀 Starting ARQ flow: {self.flow_name}")
        logger.debug(f"Flow inputs: {list(inputs.keys()) if isinstance(inputs, dict) else 'N/A'}")

        # Create flow run record first in a separate session
        flow_run_id: uuid.UUID
        with infra.get_session_context() as db_session:
            service = FlowEngineService(FlowRunRepo(db_session), FlowStepRunRepo(db_session), llm_services)

            # Create flow run record with ARQ execution mode
            flow_run_id = await service.create_flow_run_record(flow_name=self.flow_name, inputs=inputs, user_id=user_id, execution_mode="arq")

        # Submit task to ARQ queue
        task_result = await task_queue.submit_flow_task(
            flow_name=self.flow_name,
            flow_run_id=flow_run_id,
            inputs=inputs,
            user_id=user_id,
        )

        logger.info(f"✅ Flow task submitted to ARQ: {self.flow_name} (task_id={task_result.task_id})")

        return flow_run_id

    @abstractmethod
    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Implement the actual flow logic here.

        This method is called by execute() after input validation and context setup.
        No need to handle infrastructure - just implement your business logic.

        Args:
            inputs: Validated input dictionary

        Returns:
            Dictionary containing flow results
        """
        pass
