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
            "metadata": {
                "total_tokens": extract_result.metadata["tokens_used"] + summary_result.metadata["tokens_used"]
            }
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
from modules.flow_engine.public import BaseFlow, UnstructuredStep, StructuredStep
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
            "processing_metadata": {
                "total_tokens": points_result.metadata["tokens_used"] + summary_result.metadata["tokens_used"],
                "total_cost": points_result.metadata["cost_estimate"] + summary_result.metadata["cost_estimate"],
                "steps_executed": 2
            }
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
    print(f"Total cost: ${result['processing_metadata']['total_cost']:.4f}")
```
"""

# Import base classes
from .flows.base import BaseFlow

# Import result types
from .steps.base import BaseStep, ImageStep, StepResult, StepType, StructuredStep, UnstructuredStep

__all__ = [
    "BaseFlow",
    "BaseStep",
    "ImageStep",
    "StepResult",
    "StepType",
    "StructuredStep",
    "UnstructuredStep",
]
