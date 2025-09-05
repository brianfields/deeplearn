# Topic Catalog Module (Frontend)

## Purpose

This frontend module provides the user interface for topic discovery, browsing, search, and selection. It enables learners to find and choose topics for learning through an intuitive, mobile-optimized interface.

## Domain Responsibility

**"Topic discovery and selection user interface"**

The Topic Catalog frontend module owns all UI aspects of topic discovery:

- Topic browsing and listing interfaces
- Search and filtering user interactions
- Topic selection and preview
- Offline topic availability indicators
- Topic metadata display and formatting
- Navigation to learning sessions

## Architecture

### Module API (Public Interface)

```typescript
// module_api/index.ts
export { useTopicCatalog } from './queries';
export { useTopicCatalogStore } from './store';
export { useTopicCatalogNavigation } from './navigation';
export type { Topic, TopicFilters, TopicSummary } from './types';

// module_api/queries.ts
export function useTopicCatalog() {
  return {
    useTopics: (filters?: TopicFilters) =>
      useQuery({
        queryKey: ['topics', filters],
        queryFn: () => loadTopicsUseCase(filters),
        staleTime: 5 * 60 * 1000,
        select: topics =>
          topics.map(topic => TopicFormatter.formatForDisplay(topic)),
      }),

    useSearchTopics: (query: string) =>
      useQuery({
        queryKey: ['topics', 'search', query],
        queryFn: () => searchTopicsUseCase(query),
        enabled: query.length > 2,
      }),

    useTopicMetadata: (topicId: string) =>
      useQuery({
        queryKey: ['topics', topicId, 'metadata'],
        queryFn: () => getTopicMetadataUseCase(topicId),
      }),
  };
}

// module_api/navigation.ts
export function useTopicCatalogNavigation() {
  const navigation = useNavigation();

  return {
    navigateToTopicDetail: (topic: Topic) =>
      navigation.navigate('TopicCatalog', {
        screen: 'TopicDetail',
        params: { topic },
      }),

    navigateToSearch: () =>
      navigation.navigate('TopicCatalog', { screen: 'Search' }),
  };
}
```

### Screens (UI Layer)

```typescript
// screens/TopicListScreen.tsx
export function TopicListScreen() {
  const { useTopics } = useTopicCatalog()
  const { navigateToLearningSession } = useLearningSessionNavigation()
  const { getTopicProgress } = useLearningAnalytics()

  const { data: topics, isLoading, refetch } = useTopics()

  const handleTopicSelect = (topic: Topic) => {
    navigateToLearningSession(topic)
  }

  return (
    <SafeAreaView style={styles.container}>
      <SearchBar onSearchPress={() => navigateToSearch()} />
      <FlatList
        data={topics}
        renderItem={({ item }) => (
          <TopicCard
            topic={item}
            progress={getTopicProgress(item.id)}
            onPress={() => handleTopicSelect(item)}
          />
        )}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={refetch} />
        }
      />
    </SafeAreaView>
  )
}

// screens/TopicDetailScreen.tsx
export function TopicDetailScreen({ route }: Props) {
  const { topic } = route.params
  const { useTopicMetadata } = useTopicCatalog()
  const { navigateToLearningSession } = useLearningSessionNavigation()

  const { data: metadata, isLoading } = useTopicMetadata(topic.id)

  return (
    <ScrollView style={styles.container}>
      <TopicHeader topic={topic} metadata={metadata} />
      <TopicDescription description={topic.description} />
      <LearningObjectives objectives={topic.learning_objectives} />
      <TopicStats
        duration={topic.estimated_duration}
        difficulty={topic.difficulty}
        componentCount={topic.component_count}
      />
      <Button
        title="Start Learning"
        onPress={() => navigateToLearningSession(topic)}
      />
    </ScrollView>
  )
}
```

### Components (Reusable UI)

```typescript
// components/TopicCard.tsx
interface TopicCardProps {
  topic: Topic
  progress?: TopicProgress
  onPress: () => void
}

export function TopicCard({ topic, progress, onPress }: TopicCardProps) {
  const formattedDuration = TopicFormatter.formatDuration(topic.estimated_duration)
  const difficultyColor = TopicRules.getDifficultyColor(topic.difficulty)

  return (
    <TouchableOpacity style={styles.card} onPress={onPress}>
      <View style={styles.header}>
        <Text style={styles.title}>{topic.title}</Text>
        <DifficultyBadge level={topic.difficulty} color={difficultyColor} />
      </View>

      <Text style={styles.description} numberOfLines={2}>
        {topic.description}
      </Text>

      <View style={styles.footer}>
        <Text style={styles.duration}>{formattedDuration}</Text>
        {progress && (
          <ProgressIndicator
            percentage={progress.completion_percentage}
            size="small"
          />
        )}
      </View>
    </TouchableOpacity>
  )
}

// components/SearchBar.tsx
export function SearchBar({ onSearchPress }: { onSearchPress: () => void }) {
  return (
    <TouchableOpacity style={styles.searchBar} onPress={onSearchPress}>
      <Icon name="search" size={20} color="#666" />
      <Text style={styles.placeholder}>Search topics...</Text>
    </TouchableOpacity>
  )
}
```

### Navigation (Module Stack)

```typescript
// navigation/TopicCatalogStack.tsx
const Stack = createNativeStackNavigator<TopicCatalogStackParamList>()

export function TopicCatalogStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen
        name="TopicList"
        component={TopicListScreen}
        options={{ title: 'Topics' }}
      />
      <Stack.Screen
        name="TopicDetail"
        component={TopicDetailScreen}
        options={{ title: 'Topic Details' }}
      />
      <Stack.Screen
        name="Search"
        component={SearchScreen}
        options={{ title: 'Search Topics' }}
      />
    </Stack.Navigator>
  )
}
```

### Application Layer (Use Cases)

```typescript
// application/loadTopics.usecase.ts
export async function loadTopicsUseCase(
  filters?: TopicFilters
): Promise<Topic[]> {
  try {
    // Check cache first
    const cachedTopics = await TopicCacheAdapter.getTopics(filters);
    if (cachedTopics && !TopicCacheRules.isExpired(cachedTopics)) {
      return cachedTopics.data;
    }

    // Load from API
    const topics = await topicCatalogApi.getTopics(filters);

    // Cache for offline access
    await TopicCacheAdapter.cacheTopics(topics, filters);

    // Track analytics
    AnalyticsAdapter.track('topics_loaded', {
      count: topics.length,
      filters: filters,
    });

    return topics;
  } catch (error) {
    // Fallback to cache on network error
    const cachedTopics = await TopicCacheAdapter.getTopics(filters);
    if (cachedTopics) {
      return cachedTopics.data;
    }
    throw error;
  }
}

// application/searchTopics.usecase.ts
export async function searchTopicsUseCase(
  query: string
): Promise<SearchResults> {
  // Client-side pre-filtering for responsiveness
  const cachedTopics = await TopicCacheAdapter.getAllTopics();
  const clientResults = TopicSearchRules.filterByQuery(cachedTopics, query);

  // Server-side search for comprehensive results
  const serverResults = await topicCatalogApi.searchTopics(query);

  // Merge and deduplicate results
  const mergedResults = TopicSearchRules.mergeResults(
    clientResults,
    serverResults
  );

  return {
    topics: mergedResults,
    query: query,
    total: mergedResults.length,
  };
}
```

### Domain Layer (Business Rules)

```typescript
// domain/business-rules/topic-rules.ts
export class TopicRules {
  static getDifficultyColor(difficulty: number): string {
    const colors = {
      1: '#4CAF50', // Green - Beginner
      2: '#8BC34A', // Light Green
      3: '#FFC107', // Amber - Intermediate
      4: '#FF9800', // Orange
      5: '#F44336', // Red - Advanced
    };
    return colors[difficulty] || colors[3];
  }

  static filterByDifficulty(
    topics: Topic[],
    minLevel: number,
    maxLevel: number
  ): Topic[] {
    return topics.filter(
      topic => topic.difficulty >= minLevel && topic.difficulty <= maxLevel
    );
  }

  static sortByRelevance(topics: Topic[], query: string): Topic[] {
    return topics.sort((a, b) => {
      const scoreA = this.calculateRelevanceScore(a, query);
      const scoreB = this.calculateRelevanceScore(b, query);
      return scoreB - scoreA;
    });
  }

  private static calculateRelevanceScore(topic: Topic, query: string): number {
    const lowerQuery = query.toLowerCase();
    let score = 0;

    // Title match gets highest score
    if (topic.title.toLowerCase().includes(lowerQuery)) score += 10;

    // Description match gets medium score
    if (topic.description.toLowerCase().includes(lowerQuery)) score += 5;

    // Tag match gets lower score
    if (topic.tags?.some(tag => tag.toLowerCase().includes(lowerQuery)))
      score += 2;

    return score;
  }
}

// domain/formatters/topic-formatter.ts
export class TopicFormatter {
  static formatDuration(minutes: number): string {
    if (minutes < 60) {
      return `${minutes} min`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0
      ? `${hours}h ${remainingMinutes}m`
      : `${hours}h`;
  }

  static formatDifficulty(level: number): string {
    const labels = {
      1: 'Beginner',
      2: 'Easy',
      3: 'Intermediate',
      4: 'Advanced',
      5: 'Expert',
    };
    return labels[level] || 'Unknown';
  }

  static formatForDisplay(topic: Topic): DisplayTopic {
    return {
      ...topic,
      formattedDuration: this.formatDuration(topic.estimated_duration),
      formattedDifficulty: this.formatDifficulty(topic.difficulty),
      difficultyColor: TopicRules.getDifficultyColor(topic.difficulty),
    };
  }
}
```

### HTTP Client (API Communication)

```typescript
// http_client/api.ts
class TopicCatalogAPI {
  async getTopics(filters?: TopicFilters): Promise<Topic[]> {
    const params = new URLSearchParams();
    if (filters?.difficulty_range) {
      params.append('min_difficulty', filters.difficulty_range[0].toString());
      params.append('max_difficulty', filters.difficulty_range[1].toString());
    }
    if (filters?.tags) {
      params.append('tags', filters.tags.join(','));
    }

    const response = await httpClient.get(`/api/catalog/topics?${params}`);
    return response.data.topics.map(TopicApiMapper.fromApi);
  }

  async searchTopics(query: string): Promise<Topic[]> {
    const response = await httpClient.get(
      `/api/catalog/search?q=${encodeURIComponent(query)}`
    );
    return response.data.topics.map(TopicApiMapper.fromApi);
  }

  async getTopicMetadata(topicId: string): Promise<TopicMetadata> {
    const response = await httpClient.get(
      `/api/catalog/topics/${topicId}/metadata`
    );
    return TopicMetadataMapper.fromApi(response.data);
  }
}

// http_client/mappers.ts
export class TopicApiMapper {
  static fromApi(apiTopic: ApiTopic): Topic {
    return {
      id: apiTopic.id,
      title: apiTopic.title,
      description: apiTopic.description,
      difficulty: apiTopic.difficulty,
      estimated_duration: apiTopic.estimated_duration,
      component_count: apiTopic.component_count,
      tags: apiTopic.tags || [],
      created_at: new Date(apiTopic.created_at),
      updated_at: new Date(apiTopic.updated_at),
    };
  }
}
```

## Cross-Module Communication

### Provides to Other Modules

- **Learning Session Module**: Topic selection for starting sessions
- **Learning Analytics Module**: Topic metadata for progress display

### Dependencies

- **Learning Session Module**: Navigation to learning sessions
- **Learning Analytics Module**: Progress data for topic display
- **Infrastructure Module**: HTTP client, caching, analytics

### Communication Examples

```typescript
// Navigate to Learning Session module
const { navigateToLearningSession } = useLearningSessionNavigation();
navigateToLearningSession(selectedTopic);

// Get progress data from Learning Analytics module
const { getTopicProgress } = useLearningAnalytics();
const progress = getTopicProgress(topic.id);
```

## Testing Strategy

### Screen Tests (UI Behavior)

```typescript
// tests/screens/TopicListScreen.test.tsx
const mockTopics = [
  { id: '1', title: 'React Basics', difficulty: 2 },
  { id: '2', title: 'Advanced TypeScript', difficulty: 4 }
]

jest.mock('../../module_api', () => ({
  useTopicCatalog: () => ({
    useTopics: () => ({ data: mockTopics, isLoading: false })
  })
}))

describe('TopicListScreen', () => {
  it('renders topic list', () => {
    render(<TopicListScreen />, { wrapper: TestWrapper })

    expect(screen.getByText('React Basics')).toBeTruthy()
    expect(screen.getByText('Advanced TypeScript')).toBeTruthy()
  })

  it('navigates to learning session on topic press', () => {
    const mockNavigate = jest.fn()
    jest.mocked(useLearningSessionNavigation).mockReturnValue({
      navigateToLearningSession: mockNavigate
    })

    render(<TopicListScreen />, { wrapper: TestWrapper })

    fireEvent.press(screen.getByText('React Basics'))
    expect(mockNavigate).toHaveBeenCalledWith(mockTopics[0])
  })
})
```

### Domain Tests (Business Logic)

```typescript
// tests/domain/topic-rules.test.ts
describe('TopicRules', () => {
  it('filters topics by difficulty range', () => {
    const topics = [
      { id: '1', difficulty: 1 },
      { id: '2', difficulty: 3 },
      { id: '3', difficulty: 5 },
    ];

    const filtered = TopicRules.filterByDifficulty(topics, 2, 4);

    expect(filtered).toHaveLength(1);
    expect(filtered[0].id).toBe('2');
  });

  it('calculates relevance score correctly', () => {
    const topic = {
      title: 'React Hooks',
      description: 'Learn React hooks',
      tags: ['react'],
    };

    const score = TopicRules.calculateRelevanceScore(topic, 'react');

    expect(score).toBeGreaterThan(0);
  });
});
```

### Application Tests (Use Cases)

```typescript
// tests/application/loadTopics.test.ts
jest.mock('../http_client/api');
jest.mock('../adapters/cache.adapter');

describe('loadTopicsUseCase', () => {
  it('loads topics from API when cache is expired', async () => {
    TopicCacheAdapter.getTopics.mockResolvedValue(null);
    topicCatalogApi.getTopics.mockResolvedValue(mockTopics);

    const result = await loadTopicsUseCase();

    expect(topicCatalogApi.getTopics).toHaveBeenCalled();
    expect(TopicCacheAdapter.cacheTopics).toHaveBeenCalledWith(mockTopics);
    expect(result).toEqual(mockTopics);
  });
});
```

## Performance Optimizations

### Caching Strategy

- **Topic List Caching**: Cache topic lists for offline browsing
- **Search Result Caching**: Cache search results for repeated queries
- **Image Caching**: Cache topic thumbnails and icons

### UI Optimizations

- **Lazy Loading**: Load topic details only when needed
- **Virtualization**: Use FlatList for large topic lists
- **Debounced Search**: Debounce search input to reduce API calls

## Anti-Patterns to Avoid

❌ **Learning session management in topic catalog**
❌ **Progress calculation logic in UI components**
❌ **Business logic in screen components**
❌ **Direct API calls from components**
❌ **Cross-module imports from internal directories**

## Module Evolution

This module can be extended with:

- **Advanced Search**: Filters, sorting, auto-complete
- **Topic Recommendations**: Personalized topic suggestions
- **Social Features**: Topic ratings, reviews, bookmarks
- **Offline Support**: Full offline topic browsing
- **Accessibility**: Enhanced accessibility features

The modular architecture ensures these features can be added without affecting learning session or analytics functionality.
