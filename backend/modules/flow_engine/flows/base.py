"""Base flow class with consistent execute() interface and automatic context management."""

from abc import ABC, abstractmethod
import functools
import logging
from typing import Any

from pydantic import BaseModel

from ..context import FlowContext
from ..service import FlowEngineService

logger = logging.getLogger(__name__)

__all__ = ["BaseFlow", "flow_execution"]


def flow_execution(func):
    """
    Decorator that provides flow context automatically.

    This decorator handles all the infrastructure setup and cleanup,
    so flow methods can focus on pure business logic.
    """

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Get infrastructure service
        from ...infrastructure.public import infrastructure_provider
        from ...llm_services.public import llm_services_provider
        from ..repo import FlowRunRepo, FlowStepRunRepo

        infra = infrastructure_provider()
        infra.initialize()
        llm_services = llm_services_provider()

        # Keep the entire flow execution within a managed DB session so writes commit
        with infra.get_session_context() as db_session:
            service = FlowEngineService(FlowRunRepo(db_session), FlowStepRunRepo(db_session), llm_services)

            # Create flow run record
            inputs = args[0] if args else {}
            user_id = kwargs.get("user_id")

            logger.info(f"🚀 Starting flow: {self.flow_name}")
            logger.debug(f"Flow inputs: {list(inputs.keys()) if isinstance(inputs, dict) else 'N/A'}")

            flow_run_id = await service.create_flow_run_record(flow_name=self.flow_name, inputs=inputs, user_id=user_id)

            # Set up flow context
            context = FlowContext.set(service=service, flow_run_id=flow_run_id, user_id=user_id, step_counter=0)

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
    async def execute(self, inputs: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
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
