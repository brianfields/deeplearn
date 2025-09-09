/**
 * Topic Catalog Zustand Store
 *
 * Client-side state management for topic catalog UI state.
 */

import { create } from 'zustand';
import type { TopicFilters, TopicSortOptions } from './models';

interface TopicCatalogState {
  // Search and filter state
  searchQuery: string;
  filters: TopicFilters;
  sortOptions: TopicSortOptions;

  // UI state
  showFilters: boolean;
  viewMode: 'list' | 'grid';

  // Recently viewed topics
  recentTopicIds: string[];

  // Actions
  setSearchQuery: (query: string) => void;
  setFilters: (filters: TopicFilters) => void;
  setSortOptions: (options: TopicSortOptions) => void;
  setShowFilters: (show: boolean) => void;
  setViewMode: (mode: 'list' | 'grid') => void;
  addRecentTopic: (topicId: string) => void;
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
  recentTopicIds: [],
};

export const useTopicCatalogStore = create<TopicCatalogState>((set, get) => ({
  ...initialState,

  // Search actions
  setSearchQuery: (query: string) => {
    set({ searchQuery: query });
  },

  clearSearch: () => {
    set({ searchQuery: '' });
  },

  // Filter actions
  setFilters: (filters: TopicFilters) => {
    set({ filters });
  },

  clearFilters: () => {
    set({ filters: {} });
  },

  // Sort actions
  setSortOptions: (options: TopicSortOptions) => {
    set({ sortOptions: options });
  },

  // UI actions
  setShowFilters: (show: boolean) => {
    set({ showFilters: show });
  },

  setViewMode: (mode: 'list' | 'grid') => {
    set({ viewMode: mode });
  },

  // Recent topics
  addRecentTopic: (topicId: string) => {
    const { recentTopicIds } = get();

    // Remove if already exists
    const filtered = recentTopicIds.filter(id => id !== topicId);

    // Add to front and limit to 10
    const updated = [topicId, ...filtered].slice(0, 10);

    set({ recentTopicIds: updated });
  },

  // Reset all state
  reset: () => {
    set(initialState);
  },
}));

// Selectors for common state combinations
export const useTopicCatalogSelectors = () => {
  const store = useTopicCatalogStore();

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

    // Recent topics
    recentTopics: store.recentTopicIds,
  };
};
