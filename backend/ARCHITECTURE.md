# Learning System Architecture

## Overview

The learning system is built using a modular, domain-driven architecture that separates concerns into logical modules. This design promotes extensibility, maintainability, and testability while providing a clean API for learning operations.

## Architecture Principles

### 1. **Separation of Concerns**
- **Core**: Shared infrastructure and base classes
- **Modules**: Domain-specific business capabilities
- **Services**: Public APIs and orchestration

### 2. **Plugin-like Extensibility**
- Each prompt type is a separate file/class
- New functionality can be added without touching existing code
- Modules can be easily composed or replaced

### 3. **Hierarchical Service Design**
- Module-level services handle specific domains
- Feature-area services orchestrate multiple modules
- Main service provides unified public API

### 4. **Centralized Infrastructure**
- Single LLM client handles all AI interactions
- Shared base classes ensure consistency
- Common utilities reduce code duplication

## Directory Structure

```
backend/src/
├── core/                              # Shared infrastructure
│   ├── __init__.py                   # Core exports
│   ├── prompt_base.py                # Base classes for prompts
│   ├── service_base.py               # Base classes for services
│   └── llm_client.py                 # Centralized LLM client
├── modules/                           # Domain-specific modules
│   ├── __init__.py
│   ├── lesson_planning/              # Lesson planning domain
│   │   ├── __init__.py
│   │   ├── service.py                # Main lesson planning orchestrator
│   │   ├── syllabus_generation/      # Syllabus generation capability
│   │   │   ├── __init__.py
│   │   │   ├── service.py            # Syllabus-specific service
│   │   │   └── prompts.py            # Syllabus prompts
│   │   └── bite_sized_topics/        # Bite-sized content capability
│   │       ├── __init__.py
│   │       ├── service.py            # Bite-sized content service
│   │       └── prompts/              # Bite-sized content prompts
│   │           ├── __init__.py
│   │           ├── lesson_content.py
│   │           ├── didactic_snippet.py    # (Future)
│   │           ├── glossary.py            # (Future)
│   │           ├── socratic_dialogue.py   # (Future)
│   │           ├── short_answer_questions.py  # (Future)
│   │           ├── multiple_choice_questions.py  # (Future)
│   │           └── post_topic_quiz.py     # (Future)
│   ├── assessment/                   # Assessment domain
│   │   ├── __init__.py
│   │   ├── service.py                # Assessment service
│   │   └── prompts.py                # Assessment prompts
│   └── progress_tracking/            # (Future module)
│       ├── __init__.py
│       ├── service.py
│       └── prompts.py
└── services/                          # Public APIs
    └── learning_service.py           # Main unified API
```

## Core Components

### LLMClient (`core/llm_client.py`)
- **Purpose**: Centralized LLM communication with retry logic, caching, and error handling
- **Features**:
  - Automatic retries with exponential backoff
  - Response caching for performance
  - Health monitoring and statistics
  - Support for both text and structured responses

### PromptTemplate (`core/prompt_base.py`)
- **Purpose**: Base class for all prompt templates
- **Features**:
  - Context formatting utilities
  - Parameter validation
  - Consistent prompt structure
  - Easy extensibility

### ModuleService (`core/service_base.py`)
- **Purpose**: Base class for all module services
- **Features**:
  - Shared configuration management
  - Health check capabilities
  - Logging setup
  - Error handling patterns

## Module Design

### What Goes in a Module?

A module should be a **self-contained business capability** that:

1. **Solves a complete problem** within its domain
2. **Can operate independently** with minimal external dependencies
3. **Is pluggable/replaceable** - could be swapped for different implementations
4. **Is organized around business capabilities**, not technical concerns

### Module Structure

Each module follows this pattern:

```
module_name/
├── __init__.py           # Module exports
├── service.py            # Main module orchestrator
├── submodule/            # Specific capabilities
│   ├── __init__.py
│   ├── service.py        # Submodule service
│   └── prompts.py        # Submodule prompts
└── models.py             # (Optional) Module-specific data models
```

### Module Service Responsibilities

1. **Business Logic**: Implement domain-specific operations
2. **Orchestration**: Coordinate between prompts and external services
3. **Validation**: Ensure inputs and outputs meet business rules
4. **Error Handling**: Provide meaningful error messages and recovery
5. **Caching**: Optimize performance for repeated operations

## Service Hierarchy

### 1. Module Services
- Handle specific business domains
- Example: `LessonPlanningService`, `AssessmentService`
- Responsibilities: Domain logic, validation, error handling

### 2. Feature Services
- Orchestrate multiple capabilities within a domain
- Example: `BiteSizedTopicService`, `SyllabusGenerationService`
- Responsibilities: Feature coordination, business rules

### 3. Main Service
- Provides unified public API
- Example: `LearningService`
- Responsibilities: Cross-module orchestration, public interface

## Adding New Functionality

### Adding a New Prompt Type

1. **Create the prompt file**:
```python
# modules/lesson_planning/bite_sized_topics/prompts/didactic_snippet.py
from core import PromptTemplate, PromptContext
from llm_interface import LLMMessage, MessageRole

class DidacticSnippetPrompt(PromptTemplate):
    def __init__(self):
        super().__init__("didactic_snippet")

    def _get_base_instructions(self) -> str:
        return """You are an expert educator creating concise,
        focused explanations of key concepts..."""

    def generate_prompt(self, context: PromptContext, **kwargs) -> List[LLMMessage]:
        # Implementation here
        pass
```

2. **Add to service**:
```python
# modules/lesson_planning/bite_sized_topics/service.py
from .prompts import DidacticSnippetPrompt

class BiteSizedTopicService(ModuleService):
    def __init__(self, config: ServiceConfig, llm_client: LLMClient):
        super().__init__(config, llm_client)
        self.prompts = {
            'lesson_content': LessonContentPrompt(),
            'didactic_snippet': DidacticSnippetPrompt(),  # Add here
        }

    async def create_didactic_snippet(self, topic: str, concept: str):
        # Implementation here
        pass
```

3. **Export from module**:
```python
# modules/lesson_planning/bite_sized_topics/prompts/__init__.py
from .didactic_snippet import DidacticSnippetPrompt

__all__ = ['LessonContentPrompt', 'DidacticSnippetPrompt']
```

### Adding a New Module

1. **Create module structure**:
```
modules/new_module/
├── __init__.py
├── service.py
└── prompts.py
```

2. **Implement module service**:
```python
# modules/new_module/service.py
from core import ModuleService, ServiceConfig, LLMClient

class NewModuleService(ModuleService):
    def __init__(self, config: ServiceConfig, llm_client: LLMClient):
        super().__init__(config, llm_client)
        # Module-specific initialization

    async def module_specific_method(self):
        # Implementation
        pass
```

3. **Add to main service**:
```python
# services/learning_service.py
from modules.new_module import NewModuleService

class LearningService:
    def __init__(self, config: LearningServiceConfig):
        # ... existing initialization
        self.new_module = NewModuleService(service_config, self.llm_client)

    async def new_module_operation(self):
        return await self.new_module.module_specific_method()
```

## Best Practices

### Prompt Development
1. **Use descriptive template names** that clearly indicate purpose
2. **Validate required parameters** using `validate_kwargs()`
3. **Include comprehensive instructions** with examples and guidelines
4. **Structure responses** using JSON schemas when possible
5. **Test with various inputs** to ensure robustness

### Service Development
1. **Follow single responsibility principle** - each service has one clear purpose
2. **Use dependency injection** - accept dependencies via constructor
3. **Implement proper error handling** with meaningful error messages
4. **Add logging** for debugging and monitoring
5. **Include validation** for all inputs and outputs
6. **Write unit tests** for all public methods

### Module Organization
1. **Group related functionality** in the same module
2. **Keep modules independent** - minimize cross-module dependencies
3. **Use clear naming conventions** that reflect business domains
4. **Document module boundaries** and responsibilities
5. **Maintain consistent structure** across all modules

### Error Handling
1. **Use module-specific exceptions** that inherit from base exceptions
2. **Include context** in error messages (operation, inputs, etc.)
3. **Log errors** with appropriate levels (error, warning, info)
4. **Provide graceful degradation** when possible
5. **Don't expose internal errors** to end users

## Configuration Management

### Service Configuration
All services use a consistent configuration pattern:

```python
@dataclass
class ServiceConfig:
    llm_config: LLMConfig
    cache_enabled: bool = True
    retry_attempts: int = 3
    timeout_seconds: int = 30
    log_level: str = "INFO"
```

### Module-Specific Configuration
Modules can extend the base configuration:

```python
@dataclass
class ModuleSpecificConfig(ServiceConfig):
    module_specific_setting: str = "default_value"
    module_timeout: int = 60
```

## Testing Strategy

### Unit Tests
- Test each prompt template independently
- Test service methods with mocked dependencies
- Test error handling and edge cases
- Test configuration validation

### Integration Tests
- Test module interactions
- Test LLM client integration
- Test end-to-end workflows
- Test error propagation

### Example Test Structure
```python
# tests/modules/lesson_planning/test_service.py
import pytest
from unittest.mock import Mock, AsyncMock

from modules.lesson_planning import LessonPlanningService
from core import ServiceConfig, LLMClient

class TestLessonPlanningService:
    @pytest.fixture
    def mock_llm_client(self):
        return Mock(spec=LLMClient)

    @pytest.fixture
    def service_config(self):
        return ServiceConfig(llm_config=Mock())

    @pytest.fixture
    def service(self, service_config, mock_llm_client):
        return LessonPlanningService(service_config, mock_llm_client)

    async def test_generate_syllabus_success(self, service, mock_llm_client):
        # Test implementation
        pass
```

## Performance Considerations

### Caching Strategy
- **LLM Response Caching**: Automatic caching in LLMClient
- **Content Caching**: Module-specific caching for expensive operations
- **Cache Invalidation**: Time-based and content-based invalidation

### Optimization Patterns
1. **Parallel Requests**: Use asyncio for concurrent LLM calls
2. **Request Batching**: Combine multiple small requests when possible
3. **Prompt Optimization**: Minimize token usage while maintaining quality
4. **Connection Pooling**: Reuse HTTP connections for LLM providers

## Monitoring and Observability

### Health Checks
Each service provides health check endpoints:
- Service availability and configuration
- LLM client connectivity and performance
- Module-specific health indicators

### Metrics and Logging
- Request/response times for all operations
- Error rates and types by module
- Cache hit rates and performance
- LLM usage and costs

### Example Health Check Response
```json
{
  "learning_service": {
    "status": "healthy",
    "config": {
      "default_lesson_duration": 15,
      "max_quiz_questions": 10
    }
  },
  "llm_client": {
    "status": "healthy",
    "provider": "openai",
    "cache_hit_rate": 0.75
  },
  "modules": {
    "lesson_planning": {"status": "healthy"},
    "assessment": {"status": "healthy"}
  }
}
```

## Migration Guide

### From Monolithic to Modular
When migrating existing functionality:

1. **Identify domain boundaries** - group related functionality
2. **Extract prompts first** - move to appropriate modules
3. **Create module services** - implement business logic
4. **Update main service** - delegate to modules
5. **Test thoroughly** - ensure no functionality is lost
6. **Update documentation** - reflect new structure

### Backward Compatibility
The main `LearningService` API maintains backward compatibility:
- All existing method signatures remain the same
- Existing functionality continues to work
- New capabilities are additive

## Future Extensibility

The architecture is designed to easily accommodate:

### New Learning Modalities
- **Adaptive Learning**: Personalization based on performance
- **Collaborative Learning**: Group exercises and peer reviews
- **Gamification**: Points, badges, and leaderboards
- **Multimedia Content**: Video, audio, and interactive elements

### New Assessment Types
- **Peer Assessment**: Student-to-student evaluation
- **Portfolio Assessment**: Project-based evaluation
- **Continuous Assessment**: Real-time performance tracking
- **Competency Mapping**: Skills-based progression

### New Content Types
- **Interactive Simulations**: Hands-on practice environments
- **Case Studies**: Real-world scenario analysis
- **Microlearning**: Ultra-short, focused content
- **Just-in-Time Learning**: Context-aware content delivery

This architecture provides a solid foundation for building sophisticated learning experiences while maintaining code quality and developer productivity.