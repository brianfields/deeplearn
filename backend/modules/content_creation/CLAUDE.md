# Content Creation Module (Backend)

## Purpose

This backend module handles the creation, management, and generation of educational content. It provides services for extracting structured learning material from unstructured sources and generating various types of educational components like MCQs, didactic snippets, and glossaries.

## Domain Responsibility

**"Creating and managing educational content through AI-assisted content generation and structured material extraction"**

The Content Creation backend module owns:

- Topic creation and management with structured learning objectives
- Component generation (MCQs, didactic snippets, glossaries)
- Material extraction from unstructured source content
- Content validation and quality assessment
- Topic-component relationships and completion tracking

## Architecture

This module follows the layered architecture pattern:

```
content_creation/
├── module_api/           # Public interface (thin orchestration)
├── http_api/            # HTTP routes (HTTP concerns only)
├── application/         # Application services (orchestration)
├── domain/              # Business logic and entities
│   ├── entities/        # Core business entities
│   ├── policies/        # Business rules and validation
│   └── repositories/    # Repository interfaces
├── infrastructure/      # External concerns
│   └── persistence/     # Database implementations
└── tests/              # Unit and integration tests
```

## Key Components

### Domain Entities

#### Topic (`domain/entities/topic.py`)
- **Purpose**: Core educational topic with learning objectives and components
- **Business Logic**:
  - Topic validation and completion tracking
  - Component management and organization
  - Learning objective coverage calculation
  - Readiness assessment for learning sessions

#### Component (`domain/entities/component.py`)
- **Purpose**: Individual content pieces (MCQs, explanations, exercises)
- **Business Logic**:
  - Type-specific validation (MCQ structure, didactic content, etc.)
  - Content integrity checks
  - Learning objective mapping

### Application Services

#### MaterialExtractionService (`application/material_extraction.py`)
- **Purpose**: Extract structured content from unstructured source material
- **Responsibilities**:
  - Source material validation and quality analysis
  - LLM-powered content extraction and structuring
  - Refined material generation with learning objectives
  - Glossary and didactic snippet generation

#### MCQGenerationService (`application/mcq_generation.py`)
- **Purpose**: Generate multiple choice questions from topics
- **Responsibilities**:
  - MCQ generation for specific learning objectives
  - Batch MCQ creation for all topic objectives
  - MCQ quality evaluation and validation
  - Concurrent generation with rate limiting

### Module API

#### ContentCreationService (`module_api/content_creation_service.py`)
- **Purpose**: Main orchestration service for external modules
- **Public Methods**:
  - `create_topic_from_source_material()` - Create topics from raw text
  - `create_component()` - Generate individual components
  - `generate_all_components_for_topic()` - Batch component generation
  - `get_topic()`, `search_topics()` - Topic retrieval and search
  - `delete_topic()`, `delete_component()` - Content management

## Cross-Module Dependencies

### LLM Services Module
```python
from modules.llm_services.module_api import LLMService, create_llm_service

# Used for content generation and material extraction
llm_service = create_llm_service(api_key="...", model="gpt-4o")
```

### Infrastructure Module
```python
from modules.infrastructure.public import infrastructure_provider, InfrastructureProvider

# Use for database connections and configuration
infra = infrastructure_provider()
infra.initialize()
db_session = infra.get_database_session()
```

## API Contracts

### Input DTOs
```python
class CreateTopicRequest(BaseModel):
    title: str
    core_concept: str
    source_material: str  # Min 100 chars
    user_level: str       # beginner|intermediate|advanced
    domain: str | None

class CreateComponentRequest(BaseModel):
    component_type: str   # mcq|didactic_snippet|glossary
    learning_objective: str
```

### Output DTOs
```python
class TopicResponse(BaseModel):
    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    components: list[ComponentResponse]
    completion_percentage: float
    is_ready_for_learning: bool
    readiness_status: str  # draft|needs_components|needs_review|ready
    quality_score: float

class ComponentResponse(BaseModel):
    id: str
    topic_id: str
    component_type: str
    title: str
    content: dict[str, Any]  # Type-specific structure
    learning_objective: str | None
```

## Business Rules

### Topic Validation Policy
- Topics must have 1-10 learning objectives
- Topics must have 1-20 key concepts
- Source material must be 100-50,000 characters
- Title must be 5-200 characters
- Core concept must be 10-500 characters

### Component Validation
- MCQs must have question, choices (min 2), correct answer, explanation
- Didactic snippets must have explanation and key_points list
- Glossary must have terms list with term/definition pairs
- All components must reference valid learning objectives

### Quality Assessment
- Quality score based on completeness (30%), component coverage (40%), objective coverage (30%)
- Readiness status: draft → needs_components → needs_review → ready
- Topics ready for learning must have ≥1 assessment component and address all objectives

## Testing Strategy

### Unit Tests (`tests/test_content_creation_service.py`)
- **Scope**: Service orchestration logic with mocked dependencies
- **Coverage**: All public API methods, error handling, validation
- **Mocking**: Repository, LLM service, application services
- **Speed**: Fast (<1 second), no external dependencies

### Integration Tests (Future)
- **Scope**: Real LLM integration, database persistence
- **Coverage**: End-to-end content creation workflows
- **Dependencies**: Real LLM API, test database
- **Markers**: `@pytest.mark.integration`

## Usage Examples

### Creating a Topic
```python
from modules.content_creation.module_api import ContentCreationService, CreateTopicRequest

service = ContentCreationService(topic_repository, llm_service)

request = CreateTopicRequest(
    title="Python Variables",
    core_concept="Understanding variable declaration and usage",
    source_material="Variables in Python are used to store data values...",
    user_level="beginner",
    domain="Programming"
)

topic = await service.create_topic_from_source_material(request)
```

### Generating Components
```python
from modules.content_creation.module_api import CreateComponentRequest

# Generate MCQ for specific objective
mcq_request = CreateComponentRequest(
    component_type="mcq",
    learning_objective="Understand variable declaration syntax"
)

component = await service.create_component(topic.id, mcq_request)

# Generate all components for topic
all_components = await service.generate_all_components_for_topic(topic.id)
```

### Repository Implementation
```python
from modules.content_creation.infrastructure.persistence import SQLAlchemyTopicRepository

# Configure repository with database session
repository = SQLAlchemyTopicRepository(session_factory)
service = ContentCreationService(repository, llm_service)
```

## Performance Considerations

- **Concurrent MCQ Generation**: Limited to 5 concurrent operations to prevent API rate limits
- **Caching**: LLM responses cached at service level to reduce costs
- **Batch Operations**: Optimized for generating multiple components efficiently
- **Database**: Uses existing BiteSizedTopic/BiteSizedComponent schema for compatibility

## Error Handling

- **ContentCreationError**: Base exception for all module errors
- **InvalidTopicError**: Domain validation failures
- **InvalidComponentError**: Component validation failures
- **TopicNotFoundError**: Repository-level not found errors
- **MaterialExtractionError**: LLM extraction failures
- **MCQGenerationError**: MCQ generation failures

All errors are caught at service boundaries and converted to appropriate HTTP status codes in the API layer.

## Future Enhancements

1. **Advanced Component Types**: Short answer questions, scenario critiques, interactive exercises
2. **Content Versioning**: Track changes and maintain version history
3. **Collaborative Editing**: Multi-user content creation workflows
4. **Content Templates**: Predefined structures for common content types
5. **Analytics Integration**: Track content usage and effectiveness metrics
6. **Import/Export**: Support for various content formats (SCORM, xAPI, etc.)

This module provides a solid foundation for AI-assisted educational content creation while maintaining clean separation of concerns and extensibility for future requirements.