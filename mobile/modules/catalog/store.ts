/**
 * Lesson Catalog Zustand Store
 *
 * Client-side state management for lesson catalog UI state.
 */

import { create } from 'zustand';
import type { LessonFilters, LessonSortOptions } from './models';

interface CatalogState {
  // Search and filter state
  searchQuery: string;
  filters: LessonFilters;
  sortOptions: LessonSortOptions;

  // UI state
  showFilters: boolean;
  viewMode: 'list' | 'grid';

  // Recently viewed lessons
  recentLessonIds: string[];

  // Actions
  setSearchQuery: (query: string) => void;
  setFilters: (filters: LessonFilters) => void;
  setSortOptions: (options: LessonSortOptions) => void;
  setShowFilters: (show: boolean) => void;
  setViewMode: (mode: 'list' | 'grid') => void;
  addRecentLesson: (lessonId: string) => void;
  clearFilters: () => void;
  clearSearch: () => void;
  reset: () => void;
}

const initialState = {
  searchQuery: '',
  filters: {},
  sortOptions: {
    sortBy: 'relevance' as const,
    sortOrder: 'desc' as const,
  },
  showFilters: false,
  viewMode: 'list' as const,
  recentLessonIds: [],
};

export const useCatalogStore = create<CatalogState>((set, get) => ({
  ...initialState,

  // Search actions
  setSearchQuery: (query: string) => {
    set({ searchQuery: query });
  },

  clearSearch: () => {
    set({ searchQuery: '' });
  },

  // Filter actions
  setFilters: (filters: LessonFilters) => {
    set({ filters });
  },

  clearFilters: () => {
    set({ filters: {} });
  },

  // Sort actions
  setSortOptions: (options: LessonSortOptions) => {
    set({ sortOptions: options });
  },

  // UI actions
  setShowFilters: (show: boolean) => {
    set({ showFilters: show });
  },

  setViewMode: (mode: 'list' | 'grid') => {
    set({ viewMode: mode });
  },

  // Recent lessons
  addRecentLesson: (lessonId: string) => {
    const { recentLessonIds } = get();

    // Remove if already exists
    const filtered = recentLessonIds.filter(id => id !== lessonId);

    // Add to front and limit to 10
    const updated = [lessonId, ...filtered].slice(0, 10);

    set({ recentLessonIds: updated });
  },

  // Reset all state
  reset: () => {
    set(initialState);
  },
}));

// Selectors for common state combinations
export const useCatalogSelectors = () => {
  const store = useCatalogStore();

  return {
    // Combined search state
    searchState: {
      query: store.searchQuery,
      filters: store.filters,
      sortOptions: store.sortOptions,
    },

    // UI state
    uiState: {
      showFilters: store.showFilters,
      viewMode: store.viewMode,
    },

    // Has active filters
    hasActiveFilters:
      Object.keys(store.filters).length > 0 ||
      store.searchQuery.trim().length > 0,

    // Has search query
    hasSearchQuery: store.searchQuery.trim().length > 0,

    // Recent lessons
    recentLessons: store.recentLessonIds,
  };
};
