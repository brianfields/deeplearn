/**
 * Learning Paths Hook
 *
 * This hook provides a complete interface for managing learning paths
 * including fetching, creating, searching, and caching.
 *
 * Features:
 * - Automatic data fetching
 * - Loading and error states
 * - Search and filtering
 * - Optimistic updates
 * - Cache management
 *
 * Usage:
 * ```typescript
 * const { learningPaths, isLoading, createPath, searchPaths } = useLearningPaths()
 * ```
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import type {
  LearningPathSummary,
  LearningPath,
  UserLevel,
  SearchFilters,
  AsyncResult
} from '@/types'

import {
  learningService,
  type CreateLearningPathOptions,
  type EnhancedLearningPath,
  type LearningStats
} from '@/services'

import { ApiError } from '@/api'

/**
 * Hook state interface
 */
interface UseLearningPathsState {
  learningPaths: LearningPathSummary[]
  isLoading: boolean
  error: string | null
  isCreating: boolean
  searchFilters: SearchFilters
  stats: LearningStats | null
}

/**
 * Hook return interface
 */
interface UseLearningPathsReturn extends UseLearningPathsState {
  // Data operations
  refreshPaths: () => Promise<void>
  createPath: (options: CreateLearningPathOptions) => Promise<LearningPath>
  getLearningPath: (pathId: string) => Promise<EnhancedLearningPath>

  // Search and filtering
  searchPaths: (filters: Partial<SearchFilters>) => void
  filteredPaths: LearningPathSummary[]
  clearSearch: () => void

  // Statistics
  refreshStats: () => Promise<void>

  // Utilities
  clearError: () => void
  isPathLoaded: (pathId: string) => boolean
}

/**
 * Learning paths management hook
 */
export function useLearningPaths(): UseLearningPathsReturn {
  const [state, setState] = useState<UseLearningPathsState>({
    learningPaths: [],
    isLoading: true,
    error: null,
    isCreating: false,
    searchFilters: { searchTerm: '' },
    stats: null
  })

  /**
   * Update specific state properties
   */
  const updateState = useCallback((updates: Partial<UseLearningPathsState>) => {
    setState(prev => ({ ...prev, ...updates }))
  }, [])

  /**
   * Load learning paths from service
   */
  const loadLearningPaths = useCallback(async () => {
    try {
      updateState({ isLoading: true, error: null })
      const paths = await learningService.getAllLearningPaths()
      updateState({ learningPaths: paths, isLoading: false })
    } catch (error) {
      const errorMessage = error instanceof ApiError
        ? error.message
        : 'Failed to load learning paths'
      updateState({ error: errorMessage, isLoading: false })
    }
  }, [updateState])

  /**
   * Load statistics
   */
  const loadStats = useCallback(async () => {
    try {
      const stats = await learningService.getLearningStats()
      updateState({ stats })
    } catch (error) {
      console.error('Failed to load stats:', error)
      // Don't update error state for stats failure
    }
  }, [updateState])

  /**
   * Initial data loading
   */
  useEffect(() => {
    loadLearningPaths()
    loadStats()
  }, [loadLearningPaths, loadStats])

  /**
   * Refresh learning paths
   */
  const refreshPaths = useCallback(async () => {
    await loadLearningPaths()
  }, [loadLearningPaths])

  /**
   * Refresh statistics
   */
  const refreshStats = useCallback(async () => {
    await loadStats()
  }, [loadStats])

  /**
   * Create a new learning path
   */
  const createPath = useCallback(async (options: CreateLearningPathOptions): Promise<LearningPath> => {
    try {
      updateState({ isCreating: true, error: null })

      const newPath = await learningService.createLearningPath(options)

      // Validate the response
      if (!newPath || !newPath.id) {
        throw new Error('Invalid response from server: missing learning path data')
      }

      // Optimistic update - add to local state
      const pathSummary: LearningPathSummary = {
        id: newPath.id,
        topic_name: newPath.topic_name || 'Untitled Learning Path',
        description: newPath.description || 'No description available',
        total_topics: newPath.topics?.length || 0,
        progress_count: 0,
        created_at: newPath.created_at || new Date().toISOString(),
        estimated_total_hours: newPath.estimated_total_hours || 0
      }

      updateState({
        learningPaths: [pathSummary, ...(state.learningPaths || [])],
        isCreating: false
      })

      // Refresh stats after creating
      refreshStats()

      return newPath
    } catch (error) {
      console.error('Error in createPath:', error)
      const errorMessage = error instanceof ApiError
        ? error.message
        : error instanceof Error
        ? error.message
        : 'Failed to create learning path'
      updateState({ error: errorMessage, isCreating: false })
      throw error
    }
  }, [state.learningPaths, updateState, refreshStats])

  /**
   * Get detailed learning path
   */
  const getLearningPath = useCallback(async (pathId: string): Promise<EnhancedLearningPath> => {
    try {
      return await learningService.getLearningPath(pathId)
    } catch (error) {
      const errorMessage = error instanceof ApiError
        ? error.message
        : 'Failed to load learning path details'
      updateState({ error: errorMessage })
      throw error
    }
  }, [updateState])

  /**
   * Update search filters
   */
  const searchPaths = useCallback((filters: Partial<SearchFilters>) => {
    updateState({
      searchFilters: { ...state.searchFilters, ...filters }
    })
  }, [state.searchFilters, updateState])

  /**
   * Clear search filters
   */
  const clearSearch = useCallback(() => {
    updateState({ searchFilters: { searchTerm: '' } })
  }, [updateState])

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    updateState({ error: null })
  }, [updateState])

  /**
   * Check if path is loaded
   */
  const isPathLoaded = useCallback((pathId: string): boolean => {
    return (state.learningPaths || []).some(path => path.id === pathId)
  }, [state.learningPaths])

  /**
   * Filter learning paths based on search criteria
   */
  const filteredPaths = useMemo(() => {
    let filtered = state.learningPaths || []

    // Apply search term filter
    if (state.searchFilters.searchTerm) {
      const searchTerm = state.searchFilters.searchTerm.toLowerCase()
      filtered = filtered.filter(path =>
        path.topic_name.toLowerCase().includes(searchTerm) ||
        path.description.toLowerCase().includes(searchTerm)
      )
    }

    // Apply difficulty filter
    if (state.searchFilters.difficulty !== undefined) {
      // This would require difficulty info in the summary
      // For now, we'll skip this filter
    }

    // Apply sorting
    if (state.searchFilters.sortBy) {
      filtered = [...filtered].sort((a, b) => {
        switch (state.searchFilters.sortBy) {
          case 'name':
            return a.topic_name.localeCompare(b.topic_name)
          case 'created_date':
            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          case 'progress':
            const progressA = a.total_topics > 0 ? (a.progress_count / a.total_topics) * 100 : 0
            const progressB = b.total_topics > 0 ? (b.progress_count / b.total_topics) * 100 : 0
            return progressB - progressA
          default:
            return 0
        }
      })
    }

    return filtered
  }, [state.learningPaths, state.searchFilters])

  return {
    // State
    learningPaths: state.learningPaths,
    isLoading: state.isLoading,
    error: state.error,
    isCreating: state.isCreating,
    searchFilters: state.searchFilters,
    stats: state.stats,

    // Operations
    refreshPaths,
    createPath,
    getLearningPath,

    // Search and filtering
    searchPaths,
    filteredPaths,
    clearSearch,

    // Statistics
    refreshStats,

    // Utilities
    clearError,
    isPathLoaded
  }
}

/**
 * Hook for managing a specific learning path
 */
export function useLearningPath(pathId: string | null) {
  const [state, setState] = useState<AsyncResult<EnhancedLearningPath>>({
    data: null,
    isLoading: false,
    error: null
  })

  /**
   * Load learning path details
   */
  const loadPath = useCallback(async () => {
    if (!pathId) return

    try {
      setState({ data: null, isLoading: true, error: null })
      const path = await learningService.getLearningPath(pathId)
      setState({ data: path, isLoading: false, error: null })
    } catch (error) {
      const errorMessage = error instanceof ApiError
        ? error.message
        : 'Failed to load learning path'
      setState({ data: null, isLoading: false, error: errorMessage })
    }
  }, [pathId])

  /**
   * Load path when pathId changes
   */
  useEffect(() => {
    loadPath()
  }, [loadPath])

  /**
   * Refresh current path
   */
  const refresh = useCallback(() => {
    loadPath()
  }, [loadPath])

  return {
    ...state,
    refresh
  }
}