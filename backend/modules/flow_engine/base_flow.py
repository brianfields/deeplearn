"""Base flow class with consistent execute() interface and automatic context management."""

from abc import ABC, abstractmethod
import asyncio
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

    async def execute_background(self, inputs: dict[str, Any], **kwargs: FlowExecutionKwargs) -> uuid.UUID:
        """
        Execute the flow in the background and return the flow run ID for tracking.

        Args:
            inputs: Dictionary of input parameters
            **kwargs: Additional parameters (user_id, etc.)

        Returns:
            Flow run ID that can be used to track progress
        """
        # Get infrastructure service
        infra = infrastructure_provider()
        infra.initialize()
        llm_services = llm_services_provider()

        # Create flow run record first in a separate session
        with infra.get_session_context() as db_session:
            service = FlowEngineService(FlowRunRepo(db_session), FlowStepRunRepo(db_session), llm_services)

            # Validate inputs if model is defined
            if self.inputs_model:
                validated_inputs = self.inputs_model(**inputs)
                inputs = validated_inputs.model_dump()

            user_id = cast(uuid.UUID | None, kwargs.get("user_id"))

            logger.info(f"🚀 Starting background flow: {self.flow_name}")
            logger.debug(f"Flow inputs: {list(inputs.keys()) if isinstance(inputs, dict) else 'N/A'}")

            # Create flow run record with background execution mode
            flow_run_id = await service.create_flow_run_record(flow_name=self.flow_name, inputs=inputs, user_id=user_id)

            # Update execution mode to background
            flow_run = service.flow_run_repo.by_id(flow_run_id)
            if flow_run:
                flow_run.execution_mode = "background"
                service.flow_run_repo.save(flow_run)

        # Start background task without waiting
        self._tsk = asyncio.create_task(self._execute_background_task(flow_run_id, inputs, **kwargs))

        return flow_run_id

    async def _execute_background_task(self, flow_run_id: uuid.UUID, inputs: dict[str, Any], **kwargs: FlowExecutionKwargs) -> None:
        """Execute the flow logic in a background task with proper session management."""
        try:
            # Get fresh infrastructure for background execution
            infra = infrastructure_provider()
            infra.initialize()
            llm_services = llm_services_provider()

            # Execute in a separate session to avoid conflicts
            with infra.get_session_context() as db_session:
                service = FlowEngineService(FlowRunRepo(db_session), FlowStepRunRepo(db_session), llm_services)

                user_id = cast(uuid.UUID | None, kwargs.get("user_id"))

                # Set up flow context for background execution
                FlowContext.set(service=service, flow_run_id=flow_run_id, user_id=user_id, step_counter=0)

                try:
                    # Execute the flow logic
                    logger.info(f"⚙️ Executing background flow logic: {self.flow_name}")
                    result = await self._execute_flow_logic(inputs)

                    # Complete the flow run
                    await service.complete_flow_run(flow_run_id, result)
                    logger.info(f"✅ Background flow completed successfully: {self.flow_name}")

                except Exception as e:
                    # Mark flow as failed
                    logger.error(f"❌ Background flow failed: {self.flow_name} - {e!s}")
                    await service.fail_flow_run(flow_run_id, str(e))
                    raise

                finally:
                    # Clean up context
                    FlowContext.clear()

        except Exception as e:
            logger.error(f"❌ Background flow task failed completely: {self.flow_name} - {e!s}")
            # Try to mark as failed even if session context failed
            try:
                infra = infrastructure_provider()
                infra.initialize()
                llm_services = llm_services_provider()
                with infra.get_session_context() as db_session:
                    service = FlowEngineService(FlowRunRepo(db_session), FlowStepRunRepo(db_session), llm_services)
                    await service.fail_flow_run(flow_run_id, f"Background task failed: {e!s}")
            except Exception as cleanup_error:
                logger.error(f"❌ Failed to mark background flow as failed: {cleanup_error!s}")

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
