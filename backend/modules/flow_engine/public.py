"""
Flow Engine Public Interface

This module provides everything needed to create and execute AI-powered workflows.
Both flows and steps use consistent execute() methods with type-safe Pydantic inputs.

## Quick Start

### Creating a Flow
```python
class ArticleProcessingFlow(BaseFlow):
    flow_name = "article_processing"

    # Optional: Input validation
    class Inputs(BaseModel):
        article_text: str = Field(..., description="The article to process")
        style: str = Field(default="professional", description="Writing style")

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        # Step 1: Extract content
        extract_result = await ExtractContentStep().execute({
            "article_text": inputs["article_text"]
        })

        # Step 2: Summarize
        summary_result = await SummarizeStep().execute({
            "content": extract_result.output_content,
            "style": inputs["style"]
        })

        return {
            "summary": summary_result.output_content,
        }

# Execute the flow - same pattern as steps!
result = await ArticleProcessingFlow().execute({
    "article_text": "Long article content...",
    "style": "technical"
})
```

### Creating Steps
```python
# Unstructured text generation
class ExtractContentStep(UnstructuredStep):
    step_name = "extract_content"
    prompt_file = "extract_content.md"

    class Inputs(BaseModel):
        article_text: str = Field(..., description="Article to extract from")
        max_length: int = Field(default=500, description="Maximum extraction length")

# Structured output generation
class SummarizeStep(StructuredStep):
    step_name = "summarize"
    prompt_file = "summarize.md"

    class Inputs(BaseModel):
        content: str = Field(..., description="Content to summarize")
        style: str = Field(default="professional", description="Writing style")

    class Outputs(BaseModel):
        title: str = Field(..., description="Generated title")
        summary: str = Field(..., description="Content summary")
        key_points: list[str] = Field(..., description="Key points extracted")

# Image generation
class CreateThumbnailStep(ImageStep):
    step_name = "create_thumbnail"

    class Inputs(BaseModel):
        prompt: str = Field(..., description="Image generation prompt")
        size: str = Field(default="1024x1024", description="Image size")

# Execute any step - consistent interface
result = await ExtractContentStep().execute({
    "article_text": "Article content...",
    "max_length": 300
})
```

## Available Base Classes

### BaseFlow
- **Purpose**: Base class for creating multi-step AI workflows
- **Required Attributes**:
  - `flow_name: str` - Unique identifier for the flow
- **Optional Attributes**:
  - `Inputs: BaseModel` - Pydantic model for input validation
- **Required Methods**:
  - `async def _execute_flow_logic(self, inputs: dict) -> dict` - Implement your flow logic
- **Available Methods**:
  - `async def execute(self, inputs: dict) -> dict` - Main execution entry point (handles context automatically)

### BaseStep
- **Purpose**: Base class for individual processing steps
- **Required Attributes**:
  - `step_name: str` - Human-readable step identifier
  - `prompt_file: str` - Filename of prompt template (in prompts/ directory) [for LLM steps]
  - `Inputs: BaseModel` - Pydantic model for input validation
- **Available Methods**:
  - `async def execute(self, inputs: dict) -> StepResult` - Execute the step

### UnstructuredStep(BaseStep)
- **Purpose**: Steps that generate unstructured text content
- **Required Attributes**: Same as BaseStep plus `prompt_file`
- **Output**: Raw text string in `result.output_content`

### StructuredStep(BaseStep)
- **Purpose**: Steps that generate structured data
- **Required Attributes**: Same as BaseStep plus `prompt_file`
- **Additional Attributes**:
  - `Outputs: BaseModel` - Pydantic model defining expected output structure
- **Output**: Pydantic model instance in `result.output_content`

### ImageStep(BaseStep)
- **Purpose**: Steps that generate images
- **Required Inputs**: Must include `prompt: str` in Inputs model
- **Optional Inputs**: `size: str`, `quality: str`, `style: str`
- **Output**: Image URL and metadata in `result.output_content`

## Result Types

### StepResult
- `step_name: str` - Name of the executed step
- `output_content: Any` - Step output (text, Pydantic model, or image data)
- `metadata: dict` - Execution metadata including:
  - `tokens_used: int` - LLM tokens consumed
  - `cost_estimate: float` - Estimated cost in USD
  - `execution_time_ms: int` - Execution time
  - `step_run_id: str` - Database record ID
  - `llm_request_id: str` - LLM request ID (if applicable)
  - `step_type: str` - Type of step executed
  - `prompt_file: str` - Prompt file used (if applicable)

## Step Types
- `StepType.UNSTRUCTURED_LLM` - Text generation
- `StepType.STRUCTURED_LLM` - Structured data extraction/generation
- `StepType.IMAGE_GENERATION` - Image creation
- `StepType.NEWS_GATHERING` - Web search (placeholder)

## Key Features
- **Consistent Interface**: Both flows and steps use `execute()` method
- **Type Safety**: Full Pydantic validation for inputs and outputs
- **Automatic Context**: No boilerplate - infrastructure handled automatically
- **Composable**: Flows can call other flows using the same interface
- **Database Tracking**: All executions automatically logged with performance metrics
- **LLM Integration**: Seamless integration with llm_services module
- **Self-Documenting**: All usage patterns documented in this file

## Complete Example
```python
from pydantic import BaseModel, Field

# Define reusable steps
class ExtractKeyPointsStep(UnstructuredStep):
    step_name = "extract_key_points"
    prompt_file = "extract_key_points.md"

    class Inputs(BaseModel):
        text: str = Field(..., description="Text to extract key points from")
        max_points: int = Field(default=5, description="Maximum number of points")

class CreateSummaryStep(StructuredStep):
    step_name = "create_summary"
    prompt_file = "create_summary.md"

    class Inputs(BaseModel):
        text: str = Field(..., description="Text to summarize")
        key_points: str = Field(..., description="Key points to include")
        style: str = Field(default="professional", description="Writing style")

    class Outputs(BaseModel):
        title: str = Field(..., description="Generated title")
        summary: str = Field(..., description="Main summary")
        conclusion: str = Field(..., description="Key conclusion")

# Define a complete workflow
class DocumentProcessingFlow(BaseFlow):
    flow_name = "document_processing"

    class Inputs(BaseModel):
        document_text: str = Field(..., description="Document to process")
        output_style: str = Field(default="professional", description="Output style")

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        # Step 1: Extract key points
        points_result = await ExtractKeyPointsStep().execute({
            "text": inputs["document_text"],
            "max_points": 7
        })

        # Step 2: Create structured summary
        summary_result = await CreateSummaryStep().execute({
            "text": inputs["document_text"],
            "key_points": points_result.output_content,
            "style": inputs["output_style"]
        })

        return {
            "key_points": points_result.output_content,
            "summary": summary_result.output_content.model_dump(),
        }

# Usage
async def process_document():
    flow = DocumentProcessingFlow()
    result = await flow.execute({
        "document_text": "Long document content here...",
        "output_style": "academic"
    })

    print(f"Title: {result['summary']['title']}")
    print(f"Summary: {result['summary']['summary']}")
```
"""

# Import base classes

# Admin query interface (minimal, selective exposure)
from typing import Any, Protocol
import uuid

from sqlalchemy.orm import Session

from ..llm_services.public import LLMServicesProvider

# For public interface
from .base_flow import BaseFlow
from .base_step import AudioStep, BaseStep, ImageStep, StepResult, StepType, StructuredStep, UnstructuredStep
from .context import FlowContext
from .repo import FlowRunRepo, FlowStepRunRepo
from .service import FlowRunDetailsDTO, FlowRunQueryService, FlowRunSummaryDTO, FlowStepDetailsDTO


class FlowEngineAdminProvider(Protocol):
    """
    Minimal protocol for admin module access to flow execution data.

    WARNING: This interface provides access to sensitive flow execution data
    and should only be used by the admin module for monitoring purposes.

    Only exposes the specific methods needed for admin dashboard functionality.
    """

    def get_recent_flow_runs(self, limit: int = 50, offset: int = 0) -> list[FlowRunSummaryDTO]:
        """Get recent flow runs with pagination. FOR ADMIN USE ONLY."""
        ...

    def count_flow_runs(self) -> int:
        """Get total count of flow runs. FOR ADMIN USE ONLY."""
        ...

    def get_flow_run_by_id(self, flow_run_id: uuid.UUID) -> FlowRunDetailsDTO | None:
        """Get flow run by ID. FOR ADMIN USE ONLY."""
        ...

    def get_flow_steps_by_run_id(self, flow_run_id: uuid.UUID) -> list[FlowStepDetailsDTO]:
        """Get all steps for a flow run. FOR ADMIN USE ONLY."""
        ...

    def get_flow_step_by_id(self, step_run_id: uuid.UUID) -> FlowStepDetailsDTO | None:
        """Get flow step by ID. FOR ADMIN USE ONLY."""
        ...


def flow_engine_admin_provider(session: Session) -> FlowEngineAdminProvider:
    """
    Create minimal admin provider for flow engine data.

    WARNING: This service provides access to sensitive flow execution data
    and should only be used by the admin module for monitoring purposes.

    Only exposes specific methods needed for admin functionality.
    """
    if not isinstance(session, Session):
        raise ValueError("Session must be a SQLAlchemy Session instance")

    flow_run_repo = FlowRunRepo(session)
    step_run_repo = FlowStepRunRepo(session)

    # Return the service directly - it already implements the protocol methods
    return FlowRunQueryService(flow_run_repo, step_run_repo)


# Minimal provider for worker processes (used by task_queue)
class FlowEngineWorkerProvider(Protocol):
    """
    Minimal protocol for worker-side flow engine operations.

    Exposes only the methods required by background workers to update
    flow and step run records.
    """

    async def create_step_run_record(self, flow_run_id: uuid.UUID, step_name: str, step_order: int, inputs: dict[str, Any]) -> uuid.UUID: ...
    async def update_step_run_success(self, step_run_id: uuid.UUID, outputs: dict[str, Any], tokens_used: int, cost_estimate: float, execution_time_ms: int, llm_request_id: uuid.UUID | None = None) -> None: ...
    async def update_step_run_error(self, step_run_id: uuid.UUID, error_message: str, execution_time_ms: int) -> None: ...
    async def update_flow_progress(self, flow_run_id: uuid.UUID, current_step: str, step_progress: int, progress_percentage: float | None = None) -> None: ...
    async def complete_flow_run(self, flow_run_id: uuid.UUID, outputs: dict[str, Any]) -> None: ...
    async def fail_flow_run(self, flow_run_id: uuid.UUID, error_message: str) -> None: ...


def flow_engine_worker_provider(session: Session, llm_services: LLMServicesProvider) -> FlowEngineWorkerProvider:
    """
    Build a minimal worker-facing provider backed by the internal service.

    Notes:
    - Returns the concrete FlowEngineService instance which implements the protocol
    - Kept internal construction here to preserve module boundaries
    """
    if not isinstance(session, Session):
        raise ValueError("Session must be a SQLAlchemy Session instance")

    flow_run_repo = FlowRunRepo(session)
    step_run_repo = FlowStepRunRepo(session)

    # Lazy import to avoid widening the public surface with internal types
    from .service import FlowEngineService  # local import  # noqa: PLC0415

    return FlowEngineService(flow_run_repo, step_run_repo, llm_services)


__all__ = [
    "AudioStep",
    "BaseFlow",
    "BaseStep",
    "FlowContext",
    "FlowEngineAdminProvider",  # For admin module only
    "FlowEngineWorkerProvider",  # For task_queue worker only
    "ImageStep",
    "StepResult",
    "StepType",
    "StructuredStep",
    "UnstructuredStep",
    "flow_engine_admin_provider",  # For admin module only
    "flow_engine_worker_provider",  # For task_queue worker only
]
