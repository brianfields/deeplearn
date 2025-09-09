/**
 * Topic Catalog React Query Hooks
 *
 * Server state management for topic catalog data.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { topicCatalogProvider } from './public';
import type { TopicFilters, PaginationInfo } from './models';

// Query keys
export const topicCatalogKeys = {
  all: ['topic_catalog'] as const,
  browse: (
    filters?: TopicFilters,
    pagination?: Omit<PaginationInfo, 'hasMore'>
  ) => ['topic_catalog', 'browse', filters, pagination] as const,
  search: (
    query: string,
    filters?: TopicFilters,
    pagination?: Omit<PaginationInfo, 'hasMore'>
  ) => ['topic_catalog', 'search', query, filters, pagination] as const,
  detail: (topicId: string) => ['topic_catalog', 'detail', topicId] as const,
  popular: (limit?: number) => ['topic_catalog', 'popular', limit] as const,
  statistics: () => ['topic_catalog', 'statistics'] as const,
};

// Service instance
const topicCatalog = topicCatalogProvider();

/**
 * Browse topics with optional filters
 */
export function useBrowseTopics(
  filters?: TopicFilters,
  pagination?: Omit<PaginationInfo, 'hasMore'>,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    refetchOnWindowFocus?: boolean;
  }
) {
  return useQuery({
    queryKey: topicCatalogKeys.browse(filters, pagination),
    queryFn: () => topicCatalog.browseTopics(filters, pagination),
    staleTime: options?.staleTime ?? 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? false,
    enabled: options?.enabled ?? true,
  });
}

/**
 * Search topics with query and filters
 */
export function useSearchTopics(
  query: string,
  filters?: TopicFilters,
  pagination?: Omit<PaginationInfo, 'hasMore'>,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    refetchOnWindowFocus?: boolean;
  }
) {
  return useQuery({
    queryKey: topicCatalogKeys.search(query, filters, pagination),
    queryFn: () => topicCatalog.searchTopics(query, filters, pagination),
    staleTime: options?.staleTime ?? 2 * 60 * 1000, // 2 minutes (search results change more frequently)
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? false,
    enabled: (options?.enabled ?? true) && query.trim().length > 0,
  });
}

/**
 * Get topic details by ID
 */
export function useTopicDetail(
  topicId: string,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    refetchOnWindowFocus?: boolean;
  }
) {
  return useQuery({
    queryKey: topicCatalogKeys.detail(topicId),
    queryFn: () => topicCatalog.getTopicDetail(topicId),
    staleTime: options?.staleTime ?? 10 * 60 * 1000, // 10 minutes (topic details change less frequently)
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? false,
    enabled: (options?.enabled ?? true) && !!topicId?.trim(),
  });
}

/**
 * Get popular topics
 */
export function usePopularTopics(
  limit?: number,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    refetchOnWindowFocus?: boolean;
  }
) {
  return useQuery({
    queryKey: topicCatalogKeys.popular(limit),
    queryFn: () => topicCatalog.getPopularTopics(limit),
    staleTime: options?.staleTime ?? 15 * 60 * 1000, // 15 minutes
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? false,
    enabled: options?.enabled ?? true,
  });
}

/**
 * Get catalog statistics
 */
export function useCatalogStatistics(options?: {
  enabled?: boolean;
  staleTime?: number;
  refetchOnWindowFocus?: boolean;
}) {
  return useQuery({
    queryKey: topicCatalogKeys.statistics(),
    queryFn: () => topicCatalog.getCatalogStatistics(),
    staleTime: options?.staleTime ?? 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? false,
    enabled: options?.enabled ?? true,
  });
}

/**
 * Refresh catalog mutation
 */
export function useRefreshCatalog() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => topicCatalog.refreshCatalog(),
    onSuccess: () => {
      // Invalidate all topic catalog queries
      queryClient.invalidateQueries({
        queryKey: topicCatalogKeys.all,
      });
    },
  });
}

/**
 * Combined hook for topic list screen
 */
export function useTopicCatalog(
  filters?: TopicFilters,
  searchQuery?: string,
  pagination?: Omit<PaginationInfo, 'hasMore'>
) {
  // Use search if there's a query, otherwise browse
  const shouldSearch = searchQuery?.trim().length > 0;

  const browseQuery = useBrowseTopics(filters, pagination, {
    enabled: !shouldSearch,
  });

  const searchQuery_ = useSearchTopics(searchQuery || '', filters, pagination, {
    enabled: shouldSearch,
  });

  // Return the active query
  const activeQuery = shouldSearch ? searchQuery_ : browseQuery;

  return {
    topics: activeQuery.data?.topics || [],
    totalCount: activeQuery.data?.total || 0,
    isLoading: activeQuery.isLoading,
    isError: activeQuery.isError,
    error: activeQuery.error,
    refetch: activeQuery.refetch,
    isFetching: activeQuery.isFetching,
    hasMore: activeQuery.data?.pagination?.hasMore || false,
  };
}

/**
 * Health check query
 */
export function useTopicCatalogHealth() {
  return useQuery({
    queryKey: ['topic_catalog', 'health'],
    queryFn: () => topicCatalog.checkHealth(),
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Check every 5 minutes
    refetchOnWindowFocus: false,
  });
}
