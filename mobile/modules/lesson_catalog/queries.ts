/**
 * Lesson Catalog React Query Hooks
 *
 * Server state management for lesson catalog data.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { lessonCatalogProvider } from './public';
import type { LessonFilters, PaginationInfo } from './models';

// Get the lesson catalog service instance
const lessonCatalog = lessonCatalogProvider();

// Query keys
export const lessonCatalogKeys = {
  all: ['lesson_catalog'] as const,
  browse: (
    filters?: LessonFilters,
    pagination?: Omit<PaginationInfo, 'hasMore'>
  ) => ['lesson_catalog', 'browse', filters, pagination] as const,
  search: (
    query: string,
    filters?: LessonFilters,
    pagination?: Omit<PaginationInfo, 'hasMore'>
  ) => ['lesson_catalog', 'search', query, filters, pagination] as const,
  detail: (lessonId: string) => ['lesson_catalog', 'detail', lessonId] as const,
  popular: (limit?: number) => ['lesson_catalog', 'popular', limit] as const,
  statistics: () => ['lesson_catalog', 'statistics'] as const,
};

/**
 * Browse lessons with optional filters
 */
export function useBrowseLessons(
  filters?: LessonFilters,
  pagination?: Omit<PaginationInfo, 'hasMore'>,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    refetchOnWindowFocus?: boolean;
  }
) {
  return useQuery({
    queryKey: lessonCatalogKeys.browse(filters, pagination),
    queryFn: () => lessonCatalog.browseLessons(filters, pagination),
    staleTime: options?.staleTime ?? 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? false,
    enabled: options?.enabled ?? true,
  });
}

/**
 * Search lessons with query and filters
 */
export function useSearchLessons(
  query: string,
  filters?: LessonFilters,
  pagination?: Omit<PaginationInfo, 'hasMore'>,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    refetchOnWindowFocus?: boolean;
  }
) {
  return useQuery({
    queryKey: lessonCatalogKeys.search(query, filters, pagination),
    queryFn: () => lessonCatalog.searchLessons(query, filters, pagination),
    staleTime: options?.staleTime ?? 2 * 60 * 1000, // 2 minutes (search results change more frequently)
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? false,
    enabled: (options?.enabled ?? true) && query.trim().length > 0,
  });
}

/**
 * Get lesson details by ID
 */
export function useLessonDetail(
  lessonId: string,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    refetchOnWindowFocus?: boolean;
  }
) {
  return useQuery({
    queryKey: lessonCatalogKeys.detail(lessonId),
    queryFn: () => lessonCatalog.getLessonDetail(lessonId),
    staleTime: options?.staleTime ?? 10 * 60 * 1000, // 10 minutes (lesson details change less frequently)
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? false,
    enabled: (options?.enabled ?? true) && !!lessonId?.trim(),
  });
}

/**
 * Get popular lessons
 */
export function usePopularLessons(
  limit?: number,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    refetchOnWindowFocus?: boolean;
  }
) {
  return useQuery({
    queryKey: lessonCatalogKeys.popular(limit),
    queryFn: () => lessonCatalog.getPopularLessons(limit),
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
    queryKey: lessonCatalogKeys.statistics(),
    queryFn: () => lessonCatalog.getCatalogStatistics(),
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
    mutationFn: () => lessonCatalog.refreshCatalog(),
    onSuccess: () => {
      // Invalidate all lesson catalog queries
      queryClient.invalidateQueries({
        queryKey: lessonCatalogKeys.all,
      });
    },
  });
}

/**
 * Combined hook for lesson list screen
 */
export function useLessonCatalog(
  filters?: LessonFilters,
  searchQuery?: string,
  pagination?: Omit<PaginationInfo, 'hasMore'>
) {
  // Use search if there's a query, otherwise browse
  const shouldSearch = !!(searchQuery && searchQuery?.trim().length > 0);

  const browseQuery = useBrowseLessons(filters, pagination, {
    enabled: !shouldSearch,
  });

  const searchQuery_ = useSearchLessons(
    searchQuery || '',
    filters,
    pagination,
    {
      enabled: shouldSearch,
    }
  );

  // Return the active query
  const activeQuery = shouldSearch ? searchQuery_ : browseQuery;

  return {
    lessons: activeQuery.data?.lessons || [],
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
export function useLessonCatalogHealth() {
  return useQuery({
    queryKey: ['lesson_catalog', 'health'],
    queryFn: () => lessonCatalog.checkHealth(),
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Check every 5 minutes
    refetchOnWindowFocus: false,
  });
}
