# Topic Catalog Module

## Purpose

The Topic Catalog module provides simple topic browsing and discovery functionality for learners. It acts as a read-only interface to topics created by the Content Creation module, offering basic listing and retrieval capabilities without complex search or filtering logic.

## Architecture

This module follows the standard layered architecture pattern:

### Domain Layer (`domain/`)
- **Entities**: Simple domain objects (`TopicSummary`, `TopicDetail`)
- **Repository Interface**: Abstract interface for data access

### Infrastructure Layer (`infrastructure/`)
- **Repository Implementation**: Delegates to Content Creation module

### Module API Layer (`module_api/`)
- **Service**: Simple orchestration service
- **Types**: Request/Response DTOs and exceptions

### HTTP API Layer (`http_api/`)
- **Routes**: REST endpoints for topic browsing

## Key Components

### Domain Entities

#### TopicSummary
Lightweight representation of a topic for browsing lists.

**Attributes:**
- `id`: Unique identifier
- `title`: Topic title
- `core_concept`: Brief description
- `user_level`: Target audience (beginner/intermediate/advanced)
- `learning_objectives`: List of learning goals
- `key_concepts`: Important concepts covered
- `created_at`: Creation timestamp
- `component_count`: Number of learning components

**Business Logic:**
- `matches_user_level()`: Check if topic matches specified level

#### TopicDetail
Complete topic information including components for learning.

**Attributes:**
- All TopicSummary attributes plus:
- `key_aspects`: Additional topic aspects
- `target_insights`: Expected insights
- `source_material`: Original source content
- `refined_material`: Processed content structure
- `updated_at`: Last update timestamp
- `components`: List of learning components

**Business Logic:**
- `component_count`: Property returning number of components
- `is_ready_for_learning()`: Check if topic has components

### Repository Interface

#### TopicCatalogRepository
Abstract interface for topic data access.

**Methods:**
- `list_topics(user_level, limit)`: Get topics for browsing
- `get_topic_by_id(topic_id)`: Get detailed topic information

### Infrastructure Implementation

#### ContentCreationTopicRepository
Concrete repository that delegates to the Content Creation module.

**Integration:**
- Uses `ContentCreationService` to retrieve topic data
- Converts Content Creation DTOs to domain entities
- Handles filtering and data transformation

## Public API

### Module API (`module_api/`)

```python
class TopicCatalogService:
    async def browse_topics(self, request: BrowseTopicsRequest) -> BrowseTopicsResponse
    async def get_topic_by_id(self, topic_id: str) -> TopicDetailResponse

def create_topic_catalog_service() -> TopicCatalogService
```

### HTTP API (`http_api/`)

- `GET /api/topics/` - Browse topics with optional user level filter
- `GET /api/topics/{topic_id}` - Get detailed topic information

## Data Flow

1. **Browse Request** → HTTP API → Service → Repository → Content Creation Module
2. **Topic Detail Request** → HTTP API → Service → Repository → Content Creation Module
3. **Response Path**: Content Creation DTOs → Domain Entities → Response DTOs → HTTP Response

## Dependencies

### Internal Dependencies
- **Content Creation Module**: Source of all topic data via `module_api`

### External Dependencies
- **FastAPI**: HTTP framework
- **Pydantic**: Data validation and serialization

## Error Handling

- `TopicCatalogError`: Base exception for all catalog operations
- HTTP 404 for topic not found
- HTTP 500 for service errors
- Proper logging for debugging

## Design Principles

### Simplicity
- Minimal business logic - mostly data transformation
- No complex search or filtering algorithms
- Direct delegation to Content Creation module

### Separation of Concerns
- Domain entities contain only basic business rules
- Service layer provides thin orchestration
- Repository abstracts data access
- HTTP layer handles only HTTP concerns

### Testability
- Repository interface allows easy mocking
- Domain entities are pure objects
- Service logic is straightforward to test

## Testing Strategy

### Unit Tests
- Domain entity behavior
- Service orchestration logic
- Error handling scenarios
- Mock repository for isolation

### Integration Tests
- Not needed - functionality is simple delegation
- Content Creation module integration tested there

## Usage Examples

### Browse Topics
```python
from modules.topic_catalog.module_api import create_topic_catalog_service, BrowseTopicsRequest

service = create_topic_catalog_service()
request = BrowseTopicsRequest(user_level="beginner", limit=10)
response = await service.browse_topics(request)
```

### Get Topic Details
```python
topic_detail = await service.get_topic_by_id("topic-123")
if topic_detail.is_ready_for_learning:
    # Topic has components and is ready
    pass
```

This module provides essential topic discovery functionality while maintaining simplicity and clear boundaries with other modules.
