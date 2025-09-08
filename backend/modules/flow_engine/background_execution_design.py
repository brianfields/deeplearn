"""
Design proposal for background execution support in flow_engine module.

This shows how background execution could be implemented with minimal changes
to the existing architecture.
"""

from abc import ABC, abstractmethod
import asyncio
from typing import Any
import uuid

from pydantic import BaseModel


# This would be added to flows/base.py
class BaseFlowWithBackground(ABC):
    """Enhanced BaseFlow with background execution support."""

    flow_name: str

    @property
    def inputs_model(self) -> type[BaseModel] | None:
        return getattr(self, "Inputs", None)

    async def execute(self, inputs: dict[str, Any], background: bool = False, **kwargs: Any) -> dict[str, Any] | uuid.UUID:
        """
        Execute the flow with optional background execution.

        Args:
            inputs: Dictionary of input parameters
            background: If True, execute in background and return flow_run_id
            **kwargs: Additional parameters (user_id, etc.)

        Returns:
            If background=False: Dictionary containing flow results
            If background=True: UUID of the flow_run for status tracking
        """
        if background:
            return await self._execute_background(inputs, **kwargs)
        else:
            return await self._execute_foreground(inputs, **kwargs)

    async def _execute_foreground(self, inputs: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Execute flow in foreground (current behavior)."""
        # This would use the existing @flow_execution decorator logic
        # ... existing implementation ...
        pass

    async def _execute_background(self, inputs: dict[str, Any], **kwargs: Any) -> uuid.UUID:
        """Execute flow in background and return flow_run_id."""
        # 1. Create flow run record with execution_mode="background"
        # 2. Submit to background task queue
        # 3. Return flow_run_id immediately

        from ...infrastructure.public import infrastructure_provider
        from ...llm_services.public import llm_services_provider
        from ..repo import FlowRunRepo, FlowStepRunRepo
        from ..service import FlowEngineService

        # Set up infrastructure (same as foreground)
        infra = infrastructure_provider()
        infra.initialize()
        db_session = infra.get_database_session()
        llm_services = llm_services_provider()
        service = FlowEngineService(FlowRunRepo(db_session.session), FlowStepRunRepo(db_session.session), llm_services)

        # Create flow run record with background mode
        user_id = kwargs.get("user_id")
        flow_run_id = await service.create_flow_run_record(
            flow_name=self.flow_name,
            inputs=inputs,
            user_id=user_id,
            execution_mode="background",  # Key difference!
        )

        # Submit to background task queue
        asyncio.create_task(self._background_execution_wrapper(flow_run_id, inputs, service, **kwargs))

        return flow_run_id

    async def _background_execution_wrapper(self, flow_run_id: uuid.UUID, inputs: dict[str, Any], service: "FlowEngineService", **kwargs: Any) -> None:
        """Wrapper that handles background execution with proper error handling."""
        try:
            # Set up flow context for background execution
            from ..context import FlowContext

            context = FlowContext.set(service=service, flow_run_id=flow_run_id, user_id=kwargs.get("user_id"), step_counter=0)

            # Validate inputs
            if self.inputs_model:
                validated_inputs = self.inputs_model(**inputs)
                inputs = validated_inputs.model_dump()

            # Execute the flow logic
            result = await self._execute_flow_logic(inputs)

            # Complete the flow run
            await service.complete_flow_run(flow_run_id, result)

        except Exception as e:
            # Mark flow as failed
            await service.fail_flow_run(flow_run_id, str(e))

        finally:
            # Clean up context
            FlowContext.clear()

    @abstractmethod
    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Implement the actual flow logic here."""
        pass


# This would be added to service.py
class FlowEngineServiceWithBackground:
    """Enhanced service with background execution support."""

    async def create_flow_run_record(
        self,
        flow_name: str,
        inputs: dict[str, Any],
        user_id: uuid.UUID | None = None,
        execution_mode: str = "sync",  # New parameter!
    ) -> uuid.UUID:
        """Create a new flow run record with specified execution mode."""
        from datetime import UTC, datetime

        from .models import FlowRunModel

        flow_run = FlowRunModel(
            user_id=user_id,
            flow_name=flow_name,
            inputs=inputs,
            status="running",
            execution_mode=execution_mode,  # Use the parameter
            started_at=datetime.now(UTC),
        )

        created_run = self.flow_run_repo.create(flow_run)
        return created_run.id

    async def get_flow_status(self, flow_run_id: uuid.UUID) -> dict[str, Any]:
        """Get current status of a flow run."""
        flow_run = self.flow_run_repo.by_id(flow_run_id)
        if not flow_run:
            raise ValueError(f"Flow run {flow_run_id} not found")

        return flow_run.progress_info

    async def get_flow_result(self, flow_run_id: uuid.UUID) -> dict[str, Any] | None:
        """Get result of completed flow, or None if still running."""
        flow_run = self.flow_run_repo.by_id(flow_run_id)
        if not flow_run:
            raise ValueError(f"Flow run {flow_run_id} not found")

        if flow_run.status == "completed":
            return flow_run.outputs
        elif flow_run.status == "failed":
            raise RuntimeError(f"Flow failed: {flow_run.error_message}")
        else:
            return None  # Still running

    async def cancel_flow(self, flow_run_id: uuid.UUID) -> bool:
        """Cancel a running background flow."""
        flow_run = self.flow_run_repo.by_id(flow_run_id)
        if not flow_run:
            return False

        if flow_run.status in ["pending", "running"]:
            flow_run.status = "cancelled"
            flow_run.completed_at = datetime.now(UTC)
            self.flow_run_repo.save(flow_run)
            return True

        return False


# Usage examples
async def example_background_usage():
    """Examples of how background execution would work."""

    # Example 1: Simple background flag
    flow = ArticleProcessingFlow()

    # Foreground execution (current behavior)
    result = await flow.execute({"article_text": "Long article...", "style": "professional"})
    print(f"Immediate result: {result}")

    # Background execution (new feature)
    flow_run_id = await flow.execute({"article_text": "Long article...", "style": "professional"}, background=True)
    print(f"Started background flow: {flow_run_id}")

    # Check status periodically
    service = get_flow_engine_service()  # Helper function

    while True:
        status = await service.get_flow_status(flow_run_id)
        print(f"Status: {status['status']}, Progress: {status['progress_percentage']}%")

        if status["status"] in ["completed", "failed", "cancelled"]:
            break

        await asyncio.sleep(1)  # Wait 1 second

    # Get final result
    if status["status"] == "completed":
        result = await service.get_flow_result(flow_run_id)
        print(f"Final result: {result}")


# Example 2: Batch background processing
async def example_batch_background():
    """Process multiple flows in background."""

    articles = ["Article 1...", "Article 2...", "Article 3..."]
    flow_run_ids = []

    # Submit all flows to background
    for article in articles:
        flow_run_id = await ArticleProcessingFlow().execute({"article_text": article, "style": "technical"}, background=True)
        flow_run_ids.append(flow_run_id)

    print(f"Started {len(flow_run_ids)} background flows")

    # Wait for all to complete
    service = get_flow_engine_service()
    results = []

    for flow_run_id in flow_run_ids:
        # Poll until complete
        while True:
            result = await service.get_flow_result(flow_run_id)
            if result is not None:
                results.append(result)
                break
            await asyncio.sleep(0.5)

    print(f"All {len(results)} flows completed!")


def get_flow_engine_service():
    """Helper to get flow engine service (would be in public.py)."""
    # Implementation would go here
    pass
