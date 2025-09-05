# Topic Catalog Module

## Purpose

The Topic Catalog module provides discovery and browsing capabilities for learning topics. It acts as a read-only interface to the content created by the Content Creation module, offering search, filtering, and statistical insights into available learning materials.

## Architecture

This module follows the layered architecture pattern with clear separation of concerns:

### Domain Layer (`domain/`)
- **Entities**: Core business objects representing catalog concepts
- **Policies**: Business rules for search, filtering, and topic organization
- **Repositories**: Abstract interfaces for data access

### Application Layer (`application/`)
- **Services**: Orchestrate domain logic and coordinate between layers
- **Use Cases**: Implement specific business workflows for topic discovery

### Infrastructure Layer (`infrastructure/`)
- **Persistence**: Concrete implementations of repository interfaces
- **External Services**: Integration with other modules (Content Creation)

### HTTP API Layer (`http_api/`)
- **Routes**: FastAPI endpoints for topic catalog operations
- **Request/Response Models**: HTTP-specific data structures

### Module API Layer (`module_api/`)
- **Service Interface**: Public API for other modules to consume
- **Types**: Shared data transfer objects and exceptions

## Key Components

### Domain Entities

#### TopicSummary
Represents a lightweight view of a topic optimized for browsing and discovery.

**Key Attributes:**
- `topic_id`: Unique identifier
- `title`: Human-readable topic name
- `core_concept`: Brief description of the main learning concept
- `user_level`: Target audience level (beginner, intermediate, advanced)
- `learning_objectives`: List of what learners will achieve
- `key_concepts`: Important terms and concepts covered
- `estimated_duration`: Expected time to complete (minutes)
- `component_count`: Number of learning components in the topic
- `is_ready_for_learning`: Whether the topic is complete and ready

**Business Logic:**
- Query matching across title, concept, and key terms
- Validation of required fields and constraints
- User level validation

#### Catalog
Represents the complete collection of available topics with metadata.

**Key Attributes:**
- `topics`: List of TopicSummary objects
- `last_updated`: Timestamp of last catalog refresh
- `total_count`: Total number of topics available

**Business Logic:**
- Filtering by user level, readiness, and search terms
- Statistical analysis of topic distribution
- Staleness detection for cache invalidation

### Domain Policies

#### SearchPolicy
Encapsulates business rules for topic discovery and organization.

**Capabilities:**
- **Filtering**: Apply multiple criteria (query, user level, readiness)
- **Sorting**: Multiple sort strategies (relevance, duration, user level)
- **Pagination**: Efficient result set management
- **Relevance Scoring**: Query-based ranking with component count weighting

**Business Rules:**
- Query matching is case-insensitive and searches across multiple fields
- User level filtering supports exact matches only
- Readiness filtering separates complete from incomplete topics
- Relevance scoring boosts query matches and considers topic complexity

### Application Services

#### TopicDiscoveryService
Orchestrates topic retrieval and filtering operations.

**Key Operations:**
- `discover_topics()`: Search and filter topics with pagination
- `get_topic_by_id()`: Retrieve specific topic details
- `get_popular_topics()`: Get most engaging topics (by component count)
- `get_catalog_statistics()`: Generate usage and distribution metrics
- `refresh_catalog()`: Trigger catalog data refresh

**Business Logic:**
- Applies search policies consistently across operations
- Handles error cases and data validation
- Coordinates between repository and domain layers

### Infrastructure

#### ContentCreationCatalogRepository
Integrates with the Content Creation module to retrieve topic data.

**Integration Points:**
- Uses `ContentCreationService.list_topics()` for data retrieval
- Converts `TopicSummaryResponse` to domain `TopicSummary` entities
- Handles service errors and data transformation

**Data Mapping:**
- Maps Content Creation DTOs to Catalog domain entities
- Preserves all relevant topic metadata
- Ensures data consistency and validation

## Public API

### Module API (`module_api/`)

The module exposes a clean service interface for other modules:

```python
class TopicCatalogService:
    async def search_topics(self, request: SearchTopicsRequest) -> SearchTopicsResponse
    async def get_topic_by_id(self, topic_id: str) -> TopicSummaryResponse
    async def get_popular_topics(self, limit: int = 10) -> List[TopicSummaryResponse]
    async def get_catalog_statistics(self) -> CatalogStatisticsResponse
    async def refresh_catalog(self) -> Dict[str, Any]
```

### HTTP API (`http_api/`)

RESTful endpoints for external clients:

- `GET /topics/search` - Search and filter topics
- `GET /topics/{topic_id}` - Get specific topic details
- `GET /topics/popular` - Get popular topics
- `GET /statistics` - Get catalog statistics
- `POST /refresh` - Trigger catalog refresh

## Data Flow

1. **Topic Discovery Request** → HTTP API → Module API → Application Service
2. **Application Service** → Domain Policy (filtering/sorting) → Repository
3. **Repository** → Content Creation Module → External Data
4. **Response Path**: Domain Entities → DTOs → HTTP Response

## Dependencies

### Internal Dependencies
- **Content Creation Module**: Source of topic data via `module_api`
- **Shared Infrastructure**: Database connections, logging, configuration

### External Dependencies
- **FastAPI**: HTTP framework for API endpoints
- **Pydantic**: Data validation and serialization
- **Python Standard Library**: datetime, typing, etc.

## Error Handling

### Domain Errors
- `TopicDiscoveryError`: Issues with topic retrieval or processing
- `ValidationError`: Invalid search parameters or data

### Integration Errors
- Service unavailable errors from Content Creation module
- Data transformation errors during DTO conversion

### HTTP Errors
- 400 Bad Request: Invalid search parameters
- 404 Not Found: Topic not found
- 500 Internal Server Error: Service failures

## Testing Strategy

### Unit Tests
- Domain entity validation and business logic
- Search policy filtering and sorting algorithms
- Service orchestration with mocked dependencies
- HTTP API request/response handling

### Integration Tests
- Repository integration with Content Creation module
- End-to-end API workflows
- Error handling across module boundaries

## Performance Considerations

### Caching Strategy
- Repository layer delegates caching to Content Creation module
- Application layer focuses on efficient filtering and sorting
- HTTP layer uses appropriate cache headers

### Scalability
- Pagination support for large topic collections
- Efficient filtering algorithms in domain policies
- Stateless service design for horizontal scaling

## Future Enhancements

### Planned Features
- Advanced search with faceted filtering
- Topic recommendation based on user preferences
- Analytics and usage tracking
- Real-time updates via WebSocket connections

### Architecture Evolution
- Event-driven updates from Content Creation module
- Dedicated search index for complex queries
- Microservice decomposition for specialized concerns