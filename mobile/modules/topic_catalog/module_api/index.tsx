/**
 * Topic Catalog Module API.
 *
 * This is the public interface for the Topic Catalog module.
 * Other modules should only import from this file.
 */

// Main screen component
export { TopicListScreen } from '../screens/TopicListScreen';

// Reusable components
export { TopicCard } from '../components/TopicCard';
export { SearchFilters } from '../components/SearchFilters';

// Import for JSX usage
import { TopicListScreen as TopicListScreenComponent } from '../screens/TopicListScreen';
import { TopicSummary } from '../domain/entities/topic-summary';

// React Query hooks
export {
  useTopicCatalog,
  useSearchTopics,
  useTopicById,
  usePopularTopics,
  useCatalogStatistics,
  useRefreshCatalog,
  usePrefetchPopularTopics,
  topicCatalogKeys,
} from '../application/queries';

// HTTP client
export {
  TopicCatalogClient,
  createTopicCatalogClient,
  TopicCatalogError,
} from '../http_client/topic-catalog-client';

// Domain types and entities
export type {
  TopicSummary,
  TopicFilters,
  TopicSortOptions,
} from '../domain/entities/topic-summary';

// Domain business rules
export { TopicSummaryRules } from '../domain/entities/topic-summary';
export { SearchPolicy } from '../domain/policies/search-policy';

// HTTP client types
export type {
  SearchTopicsRequest,
  SearchTopicsResponse,
  CatalogStatistics,
} from '../http_client/topic-catalog-client';

// Navigation helpers (to be implemented)
export interface TopicCatalogNavigation {
  navigateToTopic: (topicId: string) => void;
  navigateToLearningSession: (topic: TopicSummary) => void;
  goBack: () => void;
}

/**
 * Factory function to create a configured Topic Catalog screen.
 */
export function createTopicCatalogScreen(config: {
  baseUrl?: string;
  apiKey?: string;
  onTopicPress: (topic: TopicSummary) => void;
}) {
  return function ConfiguredTopicListScreen() {
    return (
      <TopicListScreenComponent
        baseUrl={config.baseUrl}
        apiKey={config.apiKey}
        onTopicPress={config.onTopicPress}
      />
    );
  };
}

/**
 * Default configuration for the Topic Catalog module.
 */
export const defaultTopicCatalogConfig = {
  baseUrl: 'http://localhost:8000',
  cacheTime: 10 * 60 * 1000, // 10 minutes
  staleTime: 5 * 60 * 1000, // 5 minutes
  pageSize: 20,
};
