"""Base step classes for flow execution with consistent execute() interface."""

from abc import ABC, abstractmethod
from enum import Enum
import logging
from pathlib import Path
import time
from typing import TYPE_CHECKING, Any, TypeVar
import uuid

from pydantic import BaseModel

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..context import FlowContext

# Type variable for input models
InputT = TypeVar("InputT", bound=BaseModel)

__all__ = [
    "BaseStep",
    "ImageStep",
    "StepResult",
    "StepType",
    "StructuredStep",
    "UnstructuredStep",
]


class StepType(Enum):
    """Types of steps supported by the framework."""

    UNSTRUCTURED_LLM = "unstructured_llm"  # Returns raw text content
    STRUCTURED_LLM = "structured_llm"  # Returns typed Pydantic object
    IMAGE_GENERATION = "image_generation"  # Generates images
    NEWS_GATHERING = "news_gathering"  # Fetches web data


class StepResult(BaseModel):
    """Result of step execution with output and metadata."""

    step_name: str
    output_content: Any
    metadata: dict[str, Any]


class BaseStep(ABC):
    """
    Abstract base class for all processing steps.

    This class provides the consistent execute() interface and handles
    infrastructure concerns automatically.
    """

    # Required class attributes (must be set by subclasses)
    step_name: str
    prompt_file: str | None = None  # Optional for non-LLM steps

    @property
    @abstractmethod
    def step_type(self) -> StepType:
        """Return the type of step for executor selection."""
        pass

    @property
    def inputs_model(self) -> type[BaseModel]:
        """Return the input validation model."""
        # Convention: looks for self.Inputs class
        inputs_class = getattr(self, "Inputs", None)
        if inputs_class is not None:
            return inputs_class
        raise NotImplementedError(f"Step {self.__class__.__name__} must define an Inputs class")

    @property
    def outputs_model(self) -> type[BaseModel] | None:
        """Return the output validation model (for structured steps)."""
        return getattr(self, "Outputs", None)

    async def execute(self, inputs: dict[str, Any]) -> StepResult:
        """
        Execute the step with the given inputs.

        This is the main entry point that provides consistent interface
        and handles infrastructure concerns.
        """
        start_time = time.time()

        # Validate inputs
        validated_inputs = self.inputs_model(**inputs)

        try:
            # Get infrastructure from context (will be implemented in flows/base.py)
            from ..context import FlowContext

            context = FlowContext.current()

            logger.info(f"🔧 Starting step: {self.step_name}")
            logger.debug(f"Step inputs: {list(validated_inputs.model_dump().keys())}")

            # Create step run record
            step_run_id = await context.service.create_step_run_record(flow_run_id=context.flow_run_id, step_name=self.step_name, step_order=context.get_next_step_order(), inputs=validated_inputs.model_dump())

            # Execute step-specific logic
            logger.debug(f"Executing step logic: {self.step_name}")
            logger.debug(f"Step inputs: {validated_inputs.model_dump()}")
            output_content, llm_request_id = await self._execute_step_logic(validated_inputs, context)
            logger.debug(f"Step output type: {type(output_content)}, content: {output_content}")

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Prepare outputs for database
            if hasattr(output_content, "model_dump"):
                outputs = output_content.model_dump()
            elif isinstance(output_content, dict):
                outputs = output_content
            else:
                outputs = {"content": str(output_content)}

            # Update step run with success
            await context.service.update_step_run_success(step_run_id=step_run_id, outputs=outputs, tokens_used=context.last_tokens_used, cost_estimate=context.last_cost_estimate, execution_time_ms=execution_time_ms, llm_request_id=llm_request_id)

            # Update flow progress
            await context.service.update_flow_progress(flow_run_id=context.flow_run_id, current_step=self.step_name, step_progress=context.step_counter)

            logger.info(f"✅ Step completed: {self.step_name} - Time: {execution_time_ms}ms, Tokens: {context.last_tokens_used or 0}")

            # Create result
            return StepResult(
                step_name=self.step_name,
                output_content=output_content,
                metadata={
                    "step_run_id": str(step_run_id),
                    "tokens_used": context.last_tokens_used,
                    "cost_estimate": context.last_cost_estimate,
                    "execution_time_ms": execution_time_ms,
                    "llm_request_id": str(llm_request_id) if llm_request_id else None,
                    "step_type": self.step_type.value,
                    "prompt_file": self.prompt_file,
                },
            )

        except Exception as e:
            # Calculate execution time for error case
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Update step run with error if we have step_run_id
            if "step_run_id" in locals():
                await context.service.update_step_run_error(step_run_id=step_run_id, error_message=str(e), execution_time_ms=execution_time_ms)

            # Re-raise the exception
            raise

    def _load_prompt_from_file(self, filename: str, context: "FlowContext") -> str:
        """
        Load a prompt from a markdown file.

        This method looks for the prompt file in the following locations:
        1. In the same module's prompts/ directory as the step class
        2. In a global prompts/ directory (future enhancement)

        Args:
            filename: Name of the prompt file (e.g., "extract_content.md")
            context: Flow execution context

        Returns:
            Content of the prompt file as a string

        Raises:
            FileNotFoundError: If the prompt file cannot be found
        """
        # Get the module path where the step class is defined
        step_module = self.__class__.__module__

        # Convert module path to file system path
        # e.g., "modules.content_creator.steps" -> "modules/content_creator"
        module_parts = step_module.split(".")
        if module_parts[-1] in ["steps", "flows"]:  # Remove the steps/flows part
            module_parts = module_parts[:-1]

        # Build path to prompts directory
        module_path = Path(*module_parts)
        prompts_dir = module_path / "prompts"
        prompt_file_path = prompts_dir / filename

        # Try to read the file
        try:
            with open(prompt_file_path, encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            # Fallback: try relative to current working directory
            try:
                with open(f"prompts/{filename}", encoding="utf-8") as f:
                    return f.read().strip()
            except FileNotFoundError:
                raise FileNotFoundError(f"Prompt file '{filename}' not found. Looked in: {prompt_file_path} and prompts/{filename}")

    @abstractmethod
    async def _execute_step_logic(self, inputs: BaseModel, context: "FlowContext") -> tuple[Any, uuid.UUID | None]:
        """
        Execute the step-specific logic.

        Args:
            inputs: Validated input model
            context: Flow execution context

        Returns:
            Tuple of (output_content, llm_request_id)
        """
        pass


class UnstructuredStep(BaseStep):
    """Base class for steps that generate unstructured text content."""

    @property
    def step_type(self) -> StepType:
        return StepType.UNSTRUCTURED_LLM

    async def _execute_step_logic(self, inputs: BaseModel, context: "FlowContext") -> tuple[str, uuid.UUID | None]:
        """Execute unstructured LLM generation."""
        if not self.prompt_file:
            raise ValueError(f"UnstructuredStep {self.step_name} must define prompt_file")

        # Load prompt template
        prompt_content = self._load_prompt(self.prompt_file, context)

        # Format prompt with inputs
        formatted_prompt = self._format_prompt(prompt_content, inputs.model_dump())

        # Generate response using LLM services
        from ...llm_services.public import LLMMessage

        messages = [LLMMessage(role="user", content=formatted_prompt)]

        llm_services = context.service.get_llm_services()
        response, request_id = await llm_services.generate_response(messages)

        # Update context with usage info
        context.last_tokens_used = response.metadata.get("tokens_used", 0)
        context.last_cost_estimate = response.metadata.get("cost_estimate", 0.0)

        return response.content, request_id

    def _load_prompt(self, filename: str, context: "FlowContext") -> str:
        """Load a prompt from a markdown file."""
        return self._load_prompt_from_file(filename, context)

    def _format_prompt(self, prompt: str, inputs: dict[str, Any]) -> str:
        """Format prompt template with input values."""
        # Simple string formatting - can be enhanced with Jinja2 later
        try:
            return prompt.format(**inputs)
        except KeyError as e:
            raise ValueError(f"Prompt template missing required input: {e}")


class StructuredStep(BaseStep):
    """Base class for steps that generate structured data."""

    @property
    def step_type(self) -> StepType:
        return StepType.STRUCTURED_LLM

    async def _execute_step_logic(self, inputs: BaseModel, context: "FlowContext") -> tuple[BaseModel, uuid.UUID | None]:
        """Execute structured LLM generation."""
        if not self.prompt_file:
            raise ValueError(f"StructuredStep {self.step_name} must define prompt_file")

        if not self.outputs_model:
            raise ValueError(f"StructuredStep {self.step_name} must define Outputs class")

        # Load and format prompt
        prompt_content = self._load_prompt(self.prompt_file, context)
        formatted_prompt = self._format_prompt(prompt_content, inputs.model_dump())

        # Generate structured response
        from ...llm_services.public import LLMMessage

        messages = [LLMMessage(role="user", content=formatted_prompt)]

        llm_services = context.service.get_llm_services()
        structured_response, request_id = await llm_services.generate_structured_response(messages, self.outputs_model)

        # Update context with usage info
        context.last_tokens_used = getattr(structured_response, "tokens_used", 0)
        context.last_cost_estimate = getattr(structured_response, "cost_estimate", 0.0)

        return structured_response, request_id

    def _load_prompt(self, filename: str, context: "FlowContext") -> str:
        """Load a prompt from a markdown file."""
        return self._load_prompt_from_file(filename, context)

    def _format_prompt(self, prompt: str, inputs: dict[str, Any]) -> str:
        """Format prompt template with input values."""
        try:
            return prompt.format(**inputs)
        except KeyError as e:
            raise ValueError(f"Prompt template missing required input: {e}")


class ImageStep(BaseStep):
    """Base class for steps that generate images."""

    @property
    def step_type(self) -> StepType:
        return StepType.IMAGE_GENERATION

    async def _execute_step_logic(self, inputs: BaseModel, context: "FlowContext") -> tuple[dict[str, Any], uuid.UUID | None]:
        """Execute image generation."""
        # Extract image generation parameters from inputs
        inputs_dict = inputs.model_dump()
        prompt = inputs_dict.get("prompt", "")
        size = inputs_dict.get("size", "1024x1024")
        quality = inputs_dict.get("quality", "standard")
        style = inputs_dict.get("style")

        if not prompt:
            raise ValueError("ImageStep requires 'prompt' in inputs")

        # Generate image using LLM services
        llm_services = context.service.get_llm_services()
        image_response, request_id = await llm_services.generate_image(prompt=prompt, size=size, quality=quality, style=style)

        # Update context with usage info
        context.last_tokens_used = 0  # Images don't use tokens
        context.last_cost_estimate = image_response.metadata.get("cost_estimate", 0.0)

        return image_response.model_dump(), request_id
