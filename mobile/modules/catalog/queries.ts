/**
 * Lesson Catalog React Query Hooks
 *
 * Server state management for lesson catalog data.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { catalogProvider } from './public';
import type {
  LessonFilters,
  PaginationInfo,
  UnitCreationRequest,
} from './models';

// Get the lesson catalog service instance
const catalog = catalogProvider();

// Query keys
export const catalogKeys = {
  all: ['catalog'] as const,
  units: (p?: { limit?: number; offset?: number }) =>
    ['catalog', 'units', p ?? {}] as const,
  unitDetail: (id: string) => ['catalog', 'units', 'detail', id] as const,
  browse: (
    filters?: LessonFilters,
    pagination?: Omit<PaginationInfo, 'hasMore'>
  ) => ['catalog', 'browse', filters, pagination] as const,
  search: (
    query: string,
    filters?: LessonFilters,
    pagination?: Omit<PaginationInfo, 'hasMore'>
  ) => ['catalog', 'search', query, filters, pagination] as const,
  detail: (lessonId: string) => ['catalog', 'detail', lessonId] as const,
  popular: (limit?: number) => ['catalog', 'popular', limit] as const,
  statistics: () => ['catalog', 'statistics'] as const,
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
    queryKey: catalogKeys.browse(filters, pagination),
    queryFn: () => catalog.browseLessons(filters, pagination),
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
    queryKey: catalogKeys.search(query, filters, pagination),
    queryFn: () => catalog.searchLessons(query, filters, pagination),
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
    queryKey: catalogKeys.detail(lessonId),
    queryFn: () => catalog.getLessonDetail(lessonId),
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
    queryKey: catalogKeys.popular(limit),
    queryFn: () => catalog.getPopularLessons(limit),
    staleTime: options?.staleTime ?? 15 * 60 * 1000, // 15 minutes
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? false,
    enabled: options?.enabled ?? true,
  });
}

/**
 * Browse units via lesson catalog service (delegates to units module)
 */
export function useCatalogUnits(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: catalogKeys.units(params),
    queryFn: () => catalog.browseUnits(params),
    staleTime: 5 * 60 * 1000,
    refetchInterval: data => {
      // If any unit is in progress, poll every 5 seconds
      // Otherwise, don't poll automatically
      const hasInProgressUnit =
        Array.isArray(data) && data.some(unit => unit.status === 'in_progress');
      return hasInProgressUnit ? 5000 : false;
    },
  });
}

export function useCatalogUnitDetail(unitId: string) {
  return useQuery({
    queryKey: catalogKeys.unitDetail(unitId),
    queryFn: () => catalog.getUnitDetail(unitId),
    enabled: !!unitId?.trim(),
    staleTime: 10 * 60 * 1000,
  });
}

// Alias for compatibility
export const useUnit = useCatalogUnitDetail;

/**
 * Get catalog statistics
 */
export function useCatalogStatistics(options?: {
  enabled?: boolean;
  staleTime?: number;
  refetchOnWindowFocus?: boolean;
}) {
  return useQuery({
    queryKey: catalogKeys.statistics(),
    queryFn: () => catalog.getCatalogStatistics(),
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
    mutationFn: () => catalog.refreshCatalog(),
    onSuccess: () => {
      // Invalidate all lesson catalog queries
      queryClient.invalidateQueries({
        queryKey: catalogKeys.all,
      });
    },
  });
}

/**
 * Create unit mutation
 */
export function useCreateUnit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UnitCreationRequest) => catalog.createUnit(request),
    onSuccess: response => {
      // Invalidate units list to show the new unit
      queryClient.invalidateQueries({
        queryKey: catalogKeys.units(),
      });

      // Optimistically add the new unit to the cache with in_progress status
      // This will make it appear immediately in the units list
      queryClient.setQueryData(catalogKeys.units(), (oldData: any) => {
        if (!oldData) return oldData;

        // Create optimistic unit data
        const optimisticUnit = {
          id: response.unitId,
          title: response.title,
          description: null,
          difficulty: 'beginner' as any,
          lessonCount: 0,
          difficultyLabel: 'Beginner',
          targetLessonCount: null,
          generatedFromTopic: true,
          status: response.status,
          creationProgress: null,
          errorMessage: null,
          statusLabel: 'Creating...',
          isInteractive: false,
          progressMessage: 'Creating unit content...',
        };

        // Add to the beginning of the array (newest first)
        return [optimisticUnit, ...oldData];
      });
    },
    onError: error => {
      console.error('Unit creation failed:', error);
      // Optionally show a toast notification here
    },
  });
}

/**
 * Retry unit creation mutation
 */
export function useRetryUnitCreation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (unitId: string) => catalog.retryUnitCreation(unitId),
    onSuccess: response => {
      // Invalidate units list to refresh status
      queryClient.invalidateQueries({
        queryKey: catalogKeys.units(),
      });

      // Optimistically update the unit status in cache
      queryClient.setQueryData(catalogKeys.units(), (oldData: any) => {
        if (!oldData) return oldData;

        return oldData.map((unit: any) =>
          unit.id === response.unitId
            ? {
                ...unit,
                status: response.status,
                errorMessage: null,
                statusLabel: 'Creating...',
                isInteractive: false,
                progressMessage: 'Retrying unit creation...',
                creationProgress: {
                  stage: 'retrying',
                  message: 'Retrying unit creation...',
                },
              }
            : unit
        );
      });
    },
    onError: error => {
      console.error('Unit retry failed:', error);
    },
  });
}

/**
 * Dismiss unit mutation
 */
export function useDismissUnit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (unitId: string) => catalog.dismissUnit(unitId),
    onSuccess: (_: any, unitId: string) => {
      // Invalidate units list to refresh
      queryClient.invalidateQueries({
        queryKey: catalogKeys.units(),
      });

      // Optimistically remove the unit from cache
      queryClient.setQueryData(catalogKeys.units(), (oldData: any) => {
        if (!oldData) return oldData;

        return oldData.filter((unit: any) => unit.id !== unitId);
      });
    },
    onError: error => {
      console.error('Unit dismiss failed:', error);
    },
  });
}

/**
 * Combined hook for lesson list screen
 */
export function useCatalog(
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
export function useCatalogHealth() {
  return useQuery({
    queryKey: ['catalog', 'health'],
    queryFn: () => catalog.checkHealth(),
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Check every 5 minutes
    refetchOnWindowFocus: false,
  });
}
