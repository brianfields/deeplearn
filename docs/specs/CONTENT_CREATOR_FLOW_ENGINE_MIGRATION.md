# Content Creator to Flow Engine Migration Plan

## Overview

This document outlines the migration plan for the `content_creator` module to use the `flow_engine` instead of directly calling `llm_services`. This migration will improve maintainability, provide better observability, and create reusable AI workflows.

## Current State Analysis

### Current Dependencies
The `content_creator` module currently has direct dependencies on:
- `modules.llm_services.public.LLMMessage`
- `modules.llm_services.public.LLMServicesProvider`

### Current Architecture
```
content_creator/service.py
├── ContentCreatorService.__init__(content, llm)
├── create_topic_from_source_material()
│   └── _extract_topic_content() → llm.generate_response()
└── generate_component()
    ├── _generate_mcq() → llm.generate_response()
    ├── _generate_didactic_snippet() → llm.generate_response()
    └── _generate_glossary() → llm.generate_response()
```

### Current LLM Usage Patterns
1. **Topic Content Extraction**: Single unstructured LLM call with complex JSON response parsing that generates:
   - Learning objectives and key concepts
   - One didactic snippet
   - One glossary
   - Multiple MCQs (one per learning objective)

**Note**: The `generate_component()` method exists but is **unused** - no HTTP routes or other code calls it.

## Target Architecture

### New Flow-Based Architecture
```
content_creator/service.py
├── ContentCreatorService.__init__(content)  # No flow_engine dependency needed
└── create_topic_from_source_material()
    └── TopicCreationFlow.execute()  # Multi-step flow handles all components
```

**Note**: `generate_component()` method will be **removed entirely** since no code uses it.

### Flow Engine Integration Benefits
1. **Observability**: Automatic tracking of all LLM calls, costs, and performance
2. **Reusability**: Flows can be used by other modules
3. **Maintainability**: Centralized prompt management and error handling
4. **Composability**: Complex workflows can be built from simpler steps
5. **Testing**: Better unit testing with flow mocking capabilities

## Migration Plan

### Phase 1: Create Flow Engine Flows and Steps

#### 1.1 Create Content Creation Steps (in content_creator module)

**File: `backend/modules/content_creator/steps.py`**
```python
"""Content creation steps using flow engine infrastructure."""

from typing import Any
from pydantic import BaseModel, Field
from modules.flow_engine.public import StructuredStep

class ExtractTopicMetadataStep(StructuredStep):
    """Extract learning objectives and key concepts from source material."""
    step_name = "extract_topic_metadata"
    prompt_file = "extract_topic_metadata.md"

    class Inputs(BaseModel):
        title: str
        core_concept: str
        source_material: str
        user_level: str
        domain: str

    class Outputs(BaseModel):
        learning_objectives: list[str]
        key_concepts: list[str]
        refined_material: dict[str, Any]
```
class GenerateMCQStep(StructuredStep):
    step_name = "generate_mcq"
    prompt_file = "generate_mcq.md"

    class Inputs(BaseModel):
        topic_title: str
        core_concept: str
        learning_objective: str
        user_level: str

    class Outputs(BaseModel):
        question: str
        options: list[str]
        correct_answer: int
        explanation: str

class GenerateDidacticSnippetStep(StructuredStep):
    step_name = "generate_didactic_snippet"
    prompt_file = "generate_didactic_snippet.md"

    class Inputs(BaseModel):
        topic_title: str
        core_concept: str
        learning_objective: str
        user_level: str

    class Outputs(BaseModel):
        explanation: str
        key_points: list[str]

class GenerateGlossaryStep(StructuredStep):
    step_name = "generate_glossary"
    prompt_file = "generate_glossary.md"

    class Inputs(BaseModel):
        topic_title: str
        core_concept: str
        key_concepts: list[str]
        user_level: str

    class Outputs(BaseModel):
        terms: list[dict[str, str]]  # [{"term": "...", "definition": "..."}]
```

#### 1.2 Create Content Creation Flow (in content_creator module)

**File: `backend/modules/content_creator/flows.py`**
```python
"""Content creation flows using flow engine infrastructure."""

from typing import Any
from pydantic import BaseModel
from modules.flow_engine.public import BaseFlow
from .steps import ExtractTopicMetadataStep, GenerateMCQStep, GenerateDidacticSnippetStep, GenerateGlossaryStep

class TopicCreationFlow(BaseFlow):
    """Multi-step flow that creates a complete topic with all components."""
    flow_name = "topic_creation"

    class Inputs(BaseModel):
        title: str
        core_concept: str
        source_material: str
        user_level: str = "intermediate"
        domain: str = "General"

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        # Step 1: Extract topic metadata (learning objectives, key concepts)
        metadata_result = await ExtractTopicMetadataStep().execute(inputs)
        metadata = metadata_result.output_content

        # Prepare common inputs for component generation
        component_inputs = {
            "topic_title": inputs["title"],
            "core_concept": inputs["core_concept"],
            "user_level": inputs["user_level"],
            "key_concepts": metadata.key_concepts
        }

        # Step 2: Generate didactic snippet
        didactic_result = await GenerateDidacticSnippetStep().execute({
            **component_inputs,
            "learning_objective": "Understand the core concept and key principles"
        })

        # Step 3: Generate glossary
        glossary_result = await GenerateGlossaryStep().execute(component_inputs)

        # Step 4: Generate multiple MCQs (one for each learning objective)
        mcq_results = []
        for i, learning_objective in enumerate(metadata.learning_objectives):
            mcq_result = await GenerateMCQStep().execute({
                **component_inputs,
                "learning_objective": learning_objective
            })
            mcq_results.append(mcq_result)

        # Return dictionary (as required by BaseFlow.execute())
        # Flow engine automatically tracks all metadata in database
        return {
            "learning_objectives": metadata.learning_objectives,
            "key_concepts": metadata.key_concepts,
            "refined_material": metadata.refined_material,
            "didactic_snippet": didactic_result.output_content.model_dump(),
            "glossary": glossary_result.output_content.model_dump(),
            "mcqs": [mcq.output_content.model_dump() for mcq in mcq_results]
        }
```

#### 1.3 Create Prompt Templates (in content_creator module)

**File: `backend/modules/content_creator/prompts/extract_topic_metadata.md`**
```markdown
Analyze the following educational material and extract the core learning structure:

**Title**: {title}
**Core Concept**: {core_concept}
**User Level**: {user_level}
**Domain**: {domain}

**Source Material**:
{source_material}

Extract the following learning metadata:

1. **Learning Objectives**: 3-5 specific, measurable learning goals that students should achieve
2. **Key Concepts**: 5-10 important terms, principles, or ideas that students must understand
3. **Refined Material**: A structured overview object with clear explanations and organization

Focus on creating learning structure appropriate for {user_level} level learners in the {domain} domain.
The learning objectives should be specific and testable.
The key concepts should be the most essential terms students need to master.
```

**File: `backend/modules/content_creator/prompts/generate_mcq.md`**
```markdown
Create a multiple choice question for this educational topic:

**Topic**: {topic_title}
**Core Concept**: {core_concept}
**Learning Objective**: {learning_objective}
**User Level**: {user_level}

Generate a well-crafted MCQ that:
- Tests understanding of the core concept
- Is appropriate for {user_level} level learners
- Has 4 plausible answer options
- Includes a clear explanation of why the correct answer is right
- Avoids trick questions or ambiguous wording

The question should directly assess the learning objective: "{learning_objective}"
```

**File: `backend/modules/content_creator/prompts/generate_didactic_snippet.md`**
```markdown
Create an educational explanation for this topic:

**Topic**: {topic_title}
**Core Concept**: {core_concept}
**Learning Objective**: {learning_objective}
**User Level**: {user_level}

Generate a clear, engaging explanation that:
- Explains the core concept in accessible language
- Is appropriate for {user_level} level learners
- Includes 3-5 key takeaway points
- Uses examples or analogies when helpful
- Directly addresses the learning objective: "{learning_objective}"

Focus on clarity and educational value over length.
```

**File: `backend/modules/content_creator/prompts/generate_glossary.md`**
```markdown
Create a glossary for this educational topic:

**Topic**: {topic_title}
**Core Concept**: {core_concept}
**Key Concepts**: {key_concepts}
**User Level**: {user_level}

Generate clear, concise definitions for the key concepts that:
- Are appropriate for {user_level} level learners
- Use accessible language without oversimplifying
- Focus on the most important terms students need to understand
- Provide context for how terms relate to the core concept

Include 5-10 of the most essential terms from the key concepts list.
```

### Phase 2: Update Content Creator Service

#### 2.1 Modify ContentCreatorService Dependencies

**File: `backend/modules/content_creator/service.py`**
```python
# Replace LLM dependency with local flows
from .flows import TopicCreationFlow

class ContentCreatorService:
    def __init__(self, content: ContentProvider):
        """Initialize with content storage only - flows handle LLM interactions."""
        self.content = content
```

#### 2.2 Update Service Methods

```python
async def create_topic_from_source_material(self, request: CreateTopicRequest) -> TopicCreationResult:
    """Create a complete topic using flow engine for AI generation."""
    topic_id = str(uuid.uuid4())

    # Use flow engine for content extraction
    flow = TopicCreationFlow()
    flow_result = await flow.execute({
        "title": request.title,
        "core_concept": request.core_concept,
        "source_material": request.source_material,
        "user_level": request.user_level,
        "domain": request.domain
    })

    # flow_result is a dictionary with the extracted content

    # Rest of the method remains the same - save to content module
    # ...

# generate_component method REMOVED entirely - no code uses it
```

#### 2.3 Update Public Interface

The public interface will be simplified since `generate_component` is removed:

**File: `backend/modules/content_creator/public.py`**
```python
# Remove LLM services dependency - flows handle LLM interactions internally
from modules.content.public import ContentProvider, content_provider

class ContentCreatorProvider(Protocol):
    """Simplified protocol - generate_component method removed."""
    async def create_topic_from_source_material(self, request: CreateTopicRequest) -> TopicCreationResult: ...

def content_creator_provider(
    content: ContentProvider = Depends(content_provider)
) -> ContentCreatorProvider:
    """Dependency injection provider - no longer needs LLM services."""
    return ContentCreatorService(content)
```

### Phase 3: Update Tests

#### 3.1 Update Unit Tests

**File: `backend/modules/content_creator/test_content_creator_unit.py`**
```python
# Replace LLM mocking with flow mocking
from unittest.mock import AsyncMock, Mock, patch

class TestContentCreatorService:
    @pytest.mark.asyncio
    @patch('modules.content_creator.flows.TopicCreationFlow')
    async def test_create_topic_from_source_material(self, mock_flow_class):
        """Test creating a topic using flow engine."""
        # Arrange
        content = Mock()
        service = ContentCreatorService(content)

        # Mock flow execution
        mock_flow = AsyncMock()
        mock_flow_class.return_value = mock_flow
        mock_flow.execute.return_value = {
            "extracted_content": {
                "learning_objectives": ["Learn X", "Understand Y"],
                "key_concepts": ["Concept A", "Concept B"],
                # ... rest of mock data
            },
            "metadata": {"tokens_used": 100, "cost_estimate": 0.01}
        }

        # ... rest of test
```

### Phase 4: Migration Execution

#### 4.1 Implementation Order
1. Create flow engine steps and flows
2. Create prompt templates
3. Update content creator service (keeping old methods as fallback)
4. Update tests
5. Update public interface
6. Remove old LLM-direct methods
7. Update integration tests

#### 4.2 Rollback Strategy
- Keep old methods with `_legacy` suffix during transition
- Use feature flags to switch between implementations
- Gradual migration with A/B testing capability

## Benefits of Migration

### 1. Improved Observability
- All LLM calls tracked in flow_run and step_run tables
- Cost tracking per operation
- Performance metrics and debugging information
- Request/response logging for troubleshooting

### 2. Better Maintainability
- Centralized prompt management in markdown files
- Separation of concerns (business logic vs. AI orchestration)
- Reusable components across modules
- Type-safe inputs/outputs with Pydantic validation

### 3. Enhanced Testing
- Mock flows instead of individual LLM calls
- Integration tests can use real flows with test prompts
- Better unit test isolation
- Performance regression testing

### 4. Future Extensibility
- Easy to add new content generation types
- Flows can be composed into larger workflows
- Background execution support (future)
- Multi-step content generation pipelines

## Implementation Timeline

### Week 1: Foundation
- [ ] Create base steps for content generation
- [ ] Create prompt templates
- [ ] Create content creation flows
- [ ] Unit tests for new flows

### Week 2: Integration
- [ ] Update ContentCreatorService to use flows
- [ ] Update public interface
- [ ] Update unit tests
- [ ] Integration testing

### Week 3: Validation & Cleanup
- [ ] Performance testing and optimization
- [ ] Remove legacy code
- [ ] Documentation updates
- [ ] Production deployment

## Risk Mitigation

### 1. Prompt Quality
- **Risk**: New prompt templates may produce different results
- **Mitigation**: A/B testing with existing prompts, gradual rollout

### 2. Performance Impact
- **Risk**: Additional flow overhead may slow operations
- **Mitigation**: Performance benchmarking, optimization of flow engine

### 3. Breaking Changes
- **Risk**: Changes to service interface may break consumers
- **Mitigation**: Maintain backward compatibility during transition

### 4. Testing Coverage
- **Risk**: New architecture may have untested edge cases
- **Mitigation**: Comprehensive test suite, integration testing

## Success Metrics

1. **Functionality**: All existing content creation features work identically
2. **Performance**: No significant degradation in response times
3. **Observability**: 100% of LLM calls tracked in flow engine
4. **Maintainability**: Reduced code complexity in content_creator module
5. **Reusability**: Flows can be used by other modules (future validation)

## Conclusion

This migration will modernize the content_creator module to use the flow_engine architecture, providing better observability, maintainability, and extensibility while maintaining all existing functionality. The phased approach ensures minimal risk and allows for validation at each step.
