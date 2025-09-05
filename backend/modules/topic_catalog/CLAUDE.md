# Topic Catalog Module

## Purpose
This module handles topic discovery, browsing, search, and selection. It provides learners with the ability to find and choose topics for learning without managing the actual learning experience or progress tracking.

## Domain Responsibility
**"Discovering and browsing available learning topics"**

The Topic Catalog module owns all aspects of topic discovery:
- Topic listing and browsing interfaces
- Search functionality across topics
- Filtering and sorting topics by various criteria
- Topic metadata management and display
- Content recommendations and suggestions
- Topic categorization and tagging

## Architecture

### Module API (Public Interface)
```python
# module_api/topic_catalog_service.py
class TopicCatalogService:
    @staticmethod
    def browse_topics(filters: TopicFilters = None) -> List[TopicSummary]:
        """Get list of topics for browsing with optional filters"""

    @staticmethod
    def search_topics(query: str, filters: TopicFilters = None) -> SearchResults:
        """Search topics by query with optional filters"""

    @staticmethod
    def get_topic_metadata(topic_id: str) -> TopicMetadata:
        """Get topic metadata for preview/selection"""

    @staticmethod
    def get_recommended_topics(user_preferences: UserPreferences) -> List[TopicSummary]:
        """Get recommended topics based on user preferences"""

# module_api/types.py
@dataclass
class TopicSummary:
    id: str
    title: str
    description: str
    difficulty: int
    estimated_duration: int
    component_count: int
    tags: List[str]

@dataclass
class TopicFilters:
    difficulty_range: Optional[Tuple[int, int]]
    duration_range: Optional[Tuple[int, int]]
    tags: Optional[List[str]]
    search_query: Optional[str]

@dataclass
class SearchResults:
    topics: List[TopicSummary]
    total_count: int
    facets: Dict[str, List[str]]
```

### HTTP API (Frontend Interface)
```python
# http_api/routes.py
@router.get("/api/catalog/topics")
async def browse_topics(
    difficulty: Optional[str] = None,
    duration: Optional[str] = None,
    tags: Optional[str] = None
) -> TopicListResponse:
    """Browse topics with optional filters"""

@router.get("/api/catalog/search")
async def search_topics(
    q: str,
    difficulty: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> SearchResponse:
    """Search topics by query"""

@router.get("/api/catalog/topics/{topic_id}/metadata")
async def get_topic_metadata(topic_id: str) -> TopicMetadataResponse:
    """Get topic metadata for preview"""

@router.get("/api/catalog/recommendations")
async def get_recommendations(user_id: str) -> RecommendationResponse:
    """Get personalized topic recommendations"""
```

### Domain Layer (Business Logic)
```python
# domain/entities/catalog.py
class TopicCatalog:
    def __init__(self, topics: List[TopicSummary]):
        self.topics = topics

    def filter_by_difficulty(self, min_diff: int, max_diff: int) -> 'TopicCatalog':
        """Business logic for difficulty filtering"""
        filtered = [t for t in self.topics if min_diff <= t.difficulty <= max_diff]
        return TopicCatalog(filtered)

    def sort_by_relevance(self, query: str) -> 'TopicCatalog':
        """Business rules for relevance sorting"""
        # Implement relevance scoring algorithm

    def recommend_similar(self, topic_id: str, count: int = 5) -> List[TopicSummary]:
        """Business logic for finding similar topics"""

# domain/policies/search_policy.py
class SearchPolicy:
    @staticmethod
    def apply_filters(topics: List[TopicSummary], filters: TopicFilters) -> List[TopicSummary]:
        """Business rules for applying search filters"""

    @staticmethod
    def calculate_relevance_score(topic: TopicSummary, query: str) -> float:
        """Business rules for search relevance scoring"""

    @staticmethod
    def validate_search_query(query: str) -> bool:
        """Business rules for search query validation"""
```

### Infrastructure Layer (Technical Implementation)
```python
# infrastructure/repositories/catalog_repository.py
class CatalogRepository:
    @staticmethod
    def get_all_topics() -> List[TopicSummary]:
        """Retrieve all topics from database"""

    @staticmethod
    def search_by_text(query: str) -> List[TopicSummary]:
        """Full-text search in database"""

    @staticmethod
    def get_by_tags(tags: List[str]) -> List[TopicSummary]:
        """Get topics by tags"""

# infrastructure/search_adapters/search_engine.py
class SearchEngine:
    def index_topic(self, topic: TopicSummary) -> None:
        """Index topic for search"""

    def search(self, query: str, filters: Dict) -> SearchResults:
        """Execute search with filters"""
```

## Cross-Module Communication

### Provides to Other Modules
- **Learning Session Module**: Topic selection for starting learning sessions
- **Learning Analytics Module**: Topic metadata for progress visualization

### Dependencies
- **Content Creation Module**: Topic data and metadata
- **Infrastructure Module**: Database service, search service

### Communication Examples
```python
# Learning Session module selecting a topic
from modules.topic_catalog.module_api import TopicCatalogService

topic_metadata = TopicCatalogService.get_topic_metadata(topic_id)
# Then get full topic from Content Creation module for learning

# Learning Analytics showing progress on topics
topics = TopicCatalogService.browse_topics()
for topic in topics:
    progress = get_progress_for_topic(topic.id)  # From Analytics module
```

## Key Business Rules

1. **Search Relevance**: Search results ranked by title match > description match > tag match
2. **Filtering Logic**: Multiple filters applied with AND logic (all must match)
3. **Difficulty Scaling**: Difficulty levels 1-5 with clear progression criteria
4. **Duration Estimates**: Based on component count and type, with user skill level adjustments
5. **Recommendation Algorithm**: Based on completed topics, user preferences, and similarity scoring
6. **Content Freshness**: Recently created content gets slight boost in recommendations

## Data Flow

1. **Topic Discovery Workflow**:
   ```
   User Request → Apply Filters → Search/Browse → Rank Results → Return Summaries
   ```

2. **Topic Selection Workflow**:
   ```
   Topic Selection → Get Metadata → Validate Availability → Navigate to Learning
   ```

## Testing Strategy

### Domain Tests (Pure Business Logic)
```python
def test_difficulty_filtering():
    catalog = TopicCatalog([topic1, topic2, topic3])
    filtered = catalog.filter_by_difficulty(2, 4)
    assert all(2 <= t.difficulty <= 4 for t in filtered.topics)

def test_relevance_scoring():
    score = SearchPolicy.calculate_relevance_score(topic, "machine learning")
    assert 0 <= score <= 1
```

### Service Tests (Orchestration)
```python
@patch('infrastructure.repositories.CatalogRepository')
def test_browse_topics_with_filters(mock_repo):
    filters = TopicFilters(difficulty_range=(2, 4))
    result = TopicCatalogService.browse_topics(filters)
    mock_repo.get_all_topics.assert_called_once()
```

### HTTP Tests (API Endpoints)
```python
def test_search_topics_endpoint():
    response = client.get("/api/catalog/search?q=python&difficulty=beginner")
    assert response.status_code == 200
    assert "topics" in response.json()
```

## Integration Points

### With Content Creation Module
```python
# Get topic summaries from created content
from modules.content_creation.module_api import ContentCreationService

topics = ContentCreationService.get_all_topics()
summaries = [create_summary(topic) for topic in topics]
```

### With Learning Analytics Module
```python
# Provide topic metadata for progress display
topic_metadata = TopicCatalogService.get_topic_metadata(topic_id)
# Analytics module uses this for progress visualization
```

## Anti-Patterns to Avoid

❌ **Progress tracking logic in catalog**
❌ **Learning session management**
❌ **Content creation/editing functionality**
❌ **Business logic in HTTP routes**
❌ **Direct access to other modules' internals**

## Performance Considerations

- **Search Indexing**: Maintain search index for fast full-text search
- **Caching**: Cache popular search results and topic metadata
- **Pagination**: Support pagination for large topic lists
- **Lazy Loading**: Load topic details only when needed

## Module Evolution

This module can be extended with:
- **Advanced Search**: Semantic search, auto-complete, search suggestions
- **Personalization**: ML-based recommendations, user behavior tracking
- **Content Curation**: Editorial picks, trending topics, featured content
- **Social Features**: User ratings, reviews, bookmarking
- **Analytics**: Search analytics, popular topics, usage patterns

The modular architecture ensures these features can be added without affecting learning or content creation functionality.
