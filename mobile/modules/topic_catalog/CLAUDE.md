# Topic Catalog Module (Frontend)

## Purpose

The Topic Catalog frontend module provides a comprehensive topic discovery and browsing experience for learners. It offers search, filtering, and navigation capabilities to help users find and select learning topics that match their interests and skill level.

## Domain Responsibility

**"Discovering and browsing learning topics through intuitive search and filtering interfaces"**

The Topic Catalog frontend module owns:

- Topic discovery and search interfaces
- Advanced filtering and sorting capabilities
- Topic browsing and selection experience
- Integration with backend catalog services
- Offline-aware topic availability

## Architecture

This module follows the layered architecture pattern with React Native specific concerns:

```
topic_catalog/
├── module_api/          # Public interface (exports and configuration)
├── screens/            # Screen components (navigation targets)
├── components/         # Reusable UI components
├── application/        # React Query hooks and state management
├── http_client/        # Backend communication
├── domain/             # Business logic and entities
│   ├── entities/       # Core business entities
│   └── policies/       # Business rules and validation
├── adapters/           # External service integration
└── tests/             # Unit and integration tests
```

## Key Components

### Domain Entities

#### TopicSummary (`domain/entities/topic-summary.ts`)

- **Purpose**: Lightweight topic representation optimized for browsing
- **Business Logic**:
  - Query matching across multiple fields
  - User level suitability checking
  - Duration and difficulty formatting
  - Readiness status calculation

#### TopicFilters & TopicSortOptions

- **Purpose**: Search and filtering criteria
- **Business Logic**:
  - Filter validation and sanitization
  - Sort option combinations
  - Query parameter mapping

### Domain Policies

#### SearchPolicy (`domain/policies/search-policy.ts`)

- **Purpose**: Business rules for topic discovery and organization
- **Capabilities**:
  - Multi-criteria filtering (query, level, duration, readiness)
  - Multiple sorting strategies (relevance, duration, title, level)
  - Pagination and result limiting
  - Popular and recommended topic selection

### Application Layer

#### React Query Hooks (`application/queries.ts`)

- **Purpose**: Data fetching, caching, and state management
- **Key Hooks**:
  - `useTopicCatalog()` - Main hook for topic browsing with filters
  - `useSearchTopics()` - Raw search with backend integration
  - `usePopularTopics()` - Curated popular topics
  - `useCatalogStatistics()` - Analytics and metrics
  - `useRefreshCatalog()` - Cache invalidation and refresh

**Caching Strategy**:

- 5-minute stale time for search results
- 10-minute cache time for topic data
- 15-minute stale time for popular topics
- 30-minute stale time for statistics
- Automatic invalidation on catalog refresh

### HTTP Client Layer

#### TopicCatalogClient (`http_client/topic-catalog-client.ts`)

- **Purpose**: Backend API communication
- **Capabilities**:
  - RESTful API integration with backend Topic Catalog module
  - Request/response transformation
  - Error handling and retry logic
  - Authentication token management

**API Endpoints**:

- `GET /api/v1/catalog/topics/search` - Search topics with filters
- `GET /api/v1/catalog/topics/{id}` - Get specific topic
- `GET /api/v1/catalog/topics/popular` - Get popular topics
- `GET /api/v1/catalog/statistics` - Get catalog statistics
- `POST /api/v1/catalog/refresh` - Refresh catalog data

### Screen Components

#### TopicListScreen (`screens/TopicListScreen.tsx`)

- **Purpose**: Main topic browsing interface
- **Features**:
  - Search input with real-time filtering
  - Advanced filter modal
  - Pull-to-refresh functionality
  - Infinite scroll/pagination
  - Loading and error states
  - Empty state handling

**User Experience**:

- Touch-friendly topic cards with animations
- Responsive search with debouncing
- Visual filter indicators
- Smooth transitions and feedback
- Offline availability indicators

### Reusable Components

#### TopicCard (`components/TopicCard.tsx`)

- **Purpose**: Individual topic display component
- **Features**:
  - Topic metadata display (duration, difficulty, components)
  - Progress indicators for partially completed topics
  - Readiness status badges
  - Offline availability indicators
  - Touch animations and feedback

#### SearchFilters (`components/SearchFilters.tsx`)

- **Purpose**: Advanced filtering interface
- **Features**:
  - Difficulty level selection
  - Duration range filtering
  - Readiness status filtering
  - Clear and apply actions
  - Modal presentation

## Cross-Module Dependencies

### Backend Integration

```typescript
// Communicates with backend Topic Catalog module
const client = createTopicCatalogClient('http://localhost:8000', apiKey);
const { topics } = useTopicCatalog(filters, client);
```

### Navigation Integration

```typescript
// Integrates with app navigation system
interface TopicCatalogNavigation {
  navigateToTopic: (topicId: string) => void;
  navigateToLearningSession: (topic: TopicSummary) => void;
}
```

### UI System Integration (Future)

```typescript
// Will use shared UI components
import { Card, Button, Input } from '@/modules/ui_system/module_api';
```

## API Contracts

### Public Module Interface

```typescript
// Main screen component
export function TopicListScreen(props: {
  onTopicPress: (topic: TopicSummary) => void;
  baseUrl?: string;
  apiKey?: string;
});

// Data hooks
export function useTopicCatalog(
  filters: TopicFilters,
  client: TopicCatalogClient
): {
  topics: TopicSummary[];
  totalCount: number;
  isLoading: boolean;
  isError: boolean;
  refetch: () => Promise<void>;
};

// Factory function
export function createTopicCatalogScreen(config: {
  baseUrl?: string;
  apiKey?: string;
  onTopicPress: (topic: TopicSummary) => void;
}): React.ComponentType;
```

### Domain Types

```typescript
export interface TopicSummary {
  readonly id: string;
  readonly title: string;
  readonly coreConcept: string;
  readonly userLevel: 'beginner' | 'intermediate' | 'advanced';
  readonly learningObjectives: string[];
  readonly keyConcepts: string[];
  readonly estimatedDuration: number;
  readonly componentCount: number;
  readonly isReadyForLearning: boolean;
  readonly tags: string[];
}

export interface TopicFilters {
  readonly query?: string;
  readonly userLevel?: 'beginner' | 'intermediate' | 'advanced';
  readonly minDuration?: number;
  readonly maxDuration?: number;
  readonly readyOnly?: boolean;
}
```

## Performance Considerations

### Optimization Strategies

- **React Query Caching**: Aggressive caching with smart invalidation
- **Component Memoization**: Optimized re-renders for topic cards
- **Virtual Scrolling**: Efficient handling of large topic lists
- **Image Lazy Loading**: Deferred loading of topic thumbnails
- **Search Debouncing**: Reduced API calls during typing

### Memory Management

- **Query Garbage Collection**: Automatic cleanup of unused queries
- **Component Cleanup**: Proper cleanup of animations and timers
- **Cache Size Limits**: Bounded cache to prevent memory leaks

## Testing Strategy

### Unit Tests

- Domain entity business logic
- Search policy filtering and sorting
- HTTP client request/response handling
- Component rendering and interactions

### Integration Tests

- React Query hook behavior
- Backend API integration
- Navigation flow testing
- Error handling scenarios

### E2E Tests

- Complete topic discovery workflow
- Search and filter functionality
- Topic selection and navigation
- Offline behavior testing

## Usage Examples

### Basic Integration

```typescript
import { TopicListScreen } from '@/modules/topic_catalog/module_api';

function LearningHub() {
  const handleTopicPress = (topic: TopicSummary) => {
    navigation.navigate('LearningSession', { topicId: topic.id });
  };

  return (
    <TopicListScreen
      onTopicPress={handleTopicPress}
      baseUrl="https://api.myapp.com"
      apiKey={userToken}
    />
  );
}
```

### Advanced Usage with Custom Hooks

```typescript
import {
  useTopicCatalog,
  createTopicCatalogClient,
  SearchPolicy
} from '@/modules/topic_catalog/module_api';

function CustomTopicBrowser() {
  const client = createTopicCatalogClient(API_BASE_URL, userToken);
  const [filters, setFilters] = useState<TopicFilters>({
    userLevel: 'intermediate',
    readyOnly: true,
  });

  const { topics, isLoading } = useTopicCatalog(filters, client);

  // Apply client-side business rules
  const recommendedTopics = SearchPolicy.getRecommendedTopics(
    topics,
    userLevel,
    5
  );

  return (
    <FlatList
      data={recommendedTopics}
      renderItem={({ item }) => (
        <TopicCard topic={item} onPress={handleTopicPress} />
      )}
    />
  );
}
```
