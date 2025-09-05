/**
 * React Query hooks for Topic Catalog.
 *
 * Provides data fetching, caching, and state management for topic catalog operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  TopicCatalogClient,
  SearchTopicsRequest,
  SearchTopicsResponse,
} from '../http_client/topic-catalog-client';
import { TopicFilters } from '../domain/entities/topic-summary';

// Query keys for React Query
export const topicCatalogKeys = {
  all: ['topicCatalog'] as const,
  search: (request: SearchTopicsRequest) =>
    [...topicCatalogKeys.all, 'search', request] as const,
  topic: (id: string) => [...topicCatalogKeys.all, 'topic', id] as const,
  popular: (limit: number) =>
    [...topicCatalogKeys.all, 'popular', limit] as const,
  statistics: () => [...topicCatalogKeys.all, 'statistics'] as const,
};

/**
 * Hook for searching topics with filters and pagination.
 */
export function useSearchTopics(
  request: SearchTopicsRequest,
  client: TopicCatalogClient,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    cacheTime?: number;
  }
) {
  return useQuery({
    queryKey: topicCatalogKeys.search(request),
    queryFn: () => client.searchTopics(request),
    enabled: options?.enabled ?? true,
    staleTime: options?.staleTime ?? 5 * 60 * 1000, // 5 minutes
    gcTime: options?.cacheTime ?? 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook for getting a specific topic by ID.
 */
export function useTopicById(
  topicId: string,
  client: TopicCatalogClient,
  options?: {
    enabled?: boolean;
    staleTime?: number;
  }
) {
  return useQuery({
    queryKey: topicCatalogKeys.topic(topicId),
    queryFn: () => client.getTopicById(topicId),
    enabled: (options?.enabled ?? true) && !!topicId,
    staleTime: options?.staleTime ?? 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook for getting popular topics.
 */
export function usePopularTopics(
  limit: number = 10,
  client: TopicCatalogClient,
  options?: {
    enabled?: boolean;
    staleTime?: number;
  }
) {
  return useQuery({
    queryKey: topicCatalogKeys.popular(limit),
    queryFn: () => client.getPopularTopics(limit),
    enabled: options?.enabled ?? true,
    staleTime: options?.staleTime ?? 15 * 60 * 1000, // 15 minutes
  });
}

/**
 * Hook for getting catalog statistics.
 */
export function useCatalogStatistics(
  client: TopicCatalogClient,
  options?: {
    enabled?: boolean;
    staleTime?: number;
  }
) {
  return useQuery({
    queryKey: topicCatalogKeys.statistics(),
    queryFn: () => client.getCatalogStatistics(),
    enabled: options?.enabled ?? true,
    staleTime: options?.staleTime ?? 30 * 60 * 1000, // 30 minutes
  });
}

/**
 * Hook for refreshing the catalog.
 */
export function useRefreshCatalog(client: TopicCatalogClient) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => client.refreshCatalog(),
    onSuccess: () => {
      // Invalidate all topic catalog queries to refetch fresh data
      queryClient.invalidateQueries({ queryKey: topicCatalogKeys.all });
    },
  });
}

/**
 * Higher-level hook that combines search with client-side filtering and sorting.
 */
export function useTopicCatalog(
  filters: TopicFilters,
  client: TopicCatalogClient,
  options?: {
    enabled?: boolean;
    limit?: number;
    offset?: number;
  }
) {
  const searchRequest: SearchTopicsRequest = {
    query: filters.query,
    userLevel: filters.userLevel,
    minDuration: filters.minDuration,
    maxDuration: filters.maxDuration,
    readyOnly: filters.readyOnly,
    limit: options?.limit ?? 20,
    offset: options?.offset ?? 0,
  };

  const query = useSearchTopics(searchRequest, client, {
    enabled: options?.enabled,
  });

  const data = query.data as SearchTopicsResponse | undefined;

  return {
    ...query,
    topics: data?.topics ?? [],
    totalCount: data?.totalCount ?? 0,
    hasMore: (data?.topics.length ?? 0) === (options?.limit ?? 20),
  };
}

/**
 * Hook for infinite scroll/pagination of topics.
 */
export function useInfiniteTopics(
  filters: TopicFilters,
  client: TopicCatalogClient,
  pageSize: number = 20
) {
  const queryClient = useQueryClient();

  return {
    // This would use useInfiniteQuery in a real implementation
    // For now, we'll use a simple approach with manual pagination
    loadMore: (currentOffset: number) => {
      const nextRequest: SearchTopicsRequest = {
        ...filters,
        limit: pageSize,
        offset: currentOffset + pageSize,
      };

      return queryClient.fetchQuery({
        queryKey: topicCatalogKeys.search(nextRequest),
        queryFn: () => client.searchTopics(nextRequest),
      });
    },
  };
}

/**
 * Hook for prefetching popular topics (useful for home screen).
 */
export function usePrefetchPopularTopics(
  client: TopicCatalogClient,
  limit: number = 10
) {
  const queryClient = useQueryClient();

  const prefetch = () => {
    queryClient.prefetchQuery({
      queryKey: topicCatalogKeys.popular(limit),
      queryFn: () => client.getPopularTopics(limit),
      staleTime: 15 * 60 * 1000, // 15 minutes
    });
  };

  return { prefetch };
}
