/**
 * Learning Service
 *
 * This service encapsulates all business logic related to learning paths,
 * topics, and educational content. It provides a high-level interface
 * that components can use without directly calling the API.
 *
 * Responsibilities:
 * - Learning path CRUD operations
 * - Topic management
 * - Progress calculation
 * - Data validation and transformation
 * - Caching and optimization
 *
 * Usage:
 * ```typescript
 * import { learningService } from '@/services/learning'
 *
 * const paths = await learningService.getAllLearningPaths()
 * ```
 */

import type {
  LearningPath,
  LearningPathSummary,
  Topic,
  TopicStatus,
  UserLevel,
  CreateLearningPathRequest,
  AsyncResult,
  SearchFilters,
  SortOption
} from '@/types'

import { apiClient, ApiError } from '@/api'

/**
 * Options for creating a learning path
 */
export interface CreateLearningPathOptions {
  topic: string
  userLevel: UserLevel
  description?: string
}

/**
 * Learning path with computed properties
 */
export interface EnhancedLearningPath extends LearningPath {
  progressPercentage: number
  completedTopics: number
  estimatedTimeRemaining: number
  nextTopic: Topic | null
  isCompleted: boolean
}

/**
 * Statistics for learning paths
 */
export interface LearningStats {
  totalPaths: number
  completedPaths: number
  inProgressPaths: number
  totalTopics: number
  completedTopics: number
  totalEstimatedHours: number
  averageProgress: number
}

/**
 * Learning service class
 */
export class LearningService {
  private cache = new Map<string, { data: any; timestamp: number }>()
  private readonly CACHE_TTL = 5 * 60 * 1000 // 5 minutes

  /**
   * Get cached data if valid, otherwise null
   */
  private getCached<T>(key: string): T | null {
    const cached = this.cache.get(key)
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      return cached.data
    }
    this.cache.delete(key)
    return null
  }

  /**
   * Set data in cache
   */
  private setCached<T>(key: string, data: T): void {
    this.cache.set(key, { data, timestamp: Date.now() })
  }

  /**
   * Clear cache for specific key or all cache
   */
  private clearCache(key?: string): void {
    if (key) {
      this.cache.delete(key)
    } else {
      this.cache.clear()
    }
  }

  // ================================
  // Learning Path Operations
  // ================================

  /**
   * Create a new learning path
   */
  async createLearningPath(options: CreateLearningPathOptions): Promise<LearningPath> {
    try {
      // Validate input
      if (!options.topic.trim()) {
        throw new Error('Topic is required')
      }

      if (options.topic.length < 3) {
        throw new Error('Topic must be at least 3 characters long')
      }

      if (options.topic.length > 200) {
        throw new Error('Topic must be less than 200 characters')
      }

      const learningPath = await apiClient.createLearningPath(
        options.topic.trim(),
        options.userLevel
      )

      // Clear cache since we have new data
      this.clearCache('learning-paths')

      return learningPath
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new Error(`Failed to create learning path: ${error}`)
    }
  }

  /**
   * Get all learning paths with enhanced information
   */
  async getAllLearningPaths(): Promise<LearningPathSummary[]> {
    try {
      // Check cache first
      const cached = this.getCached<LearningPathSummary[]>('learning-paths')
      if (cached) {
        return cached
      }

      const paths = await apiClient.getLearningPaths()

      // Cache the result
      this.setCached('learning-paths', paths)

      return paths
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new Error(`Failed to fetch learning paths: ${error}`)
    }
  }

  /**
   * Get detailed learning path with computed properties
   */
  async getLearningPath(pathId: string): Promise<EnhancedLearningPath> {
    try {
      if (!pathId) {
        throw new Error('Path ID is required')
      }

      // Check cache first
      const cacheKey = `learning-path-${pathId}`
      const cached = this.getCached<EnhancedLearningPath>(cacheKey)
      if (cached) {
        return cached
      }

      const path = await apiClient.getLearningPath(pathId)
      const enhanced = this.enhanceLearningPath(path)

      // Cache the result
      this.setCached(cacheKey, enhanced)

      return enhanced
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new Error(`Failed to fetch learning path: ${error}`)
    }
  }

  /**
   * Search and filter learning paths
   */
  async searchLearningPaths(filters: SearchFilters): Promise<LearningPathSummary[]> {
    try {
      const allPaths = await this.getAllLearningPaths()

      let filtered = allPaths

      // Apply search term filter
      if (filters.searchTerm) {
        const searchTerm = filters.searchTerm.toLowerCase()
        filtered = filtered.filter(path =>
          path.topic_name.toLowerCase().includes(searchTerm) ||
          path.description.toLowerCase().includes(searchTerm)
        )
      }

      // Apply sorting
      if (filters.sortBy) {
        filtered = this.sortLearningPaths(filtered, filters.sortBy)
      }

      return filtered
    } catch (error) {
      throw new Error(`Failed to search learning paths: ${error}`)
    }
  }

  /**
   * Delete a learning path
   */
  async deleteLearningPath(pathId: string): Promise<void> {
    try {
      if (!pathId) {
        throw new Error('Path ID is required')
      }

      // Note: This would require a DELETE endpoint in the API
      // For now, we'll just clear the cache
      this.clearCache(`learning-path-${pathId}`)
      this.clearCache('learning-paths')

      // TODO: Implement actual deletion when API supports it
      throw new Error('Learning path deletion not yet implemented')
    } catch (error) {
      throw new Error(`Failed to delete learning path: ${error}`)
    }
  }

  // ================================
  // Topic Operations
  // ================================

  /**
   * Get topics for a learning path
   */
  async getTopics(pathId: string): Promise<Topic[]> {
    try {
      const path = await this.getLearningPath(pathId)
      return path.topics
    } catch (error) {
      throw new Error(`Failed to fetch topics: ${error}`)
    }
  }

  /**
   * Get a specific topic
   */
  async getTopic(pathId: string, topicId: string): Promise<Topic> {
    try {
      const topics = await this.getTopics(pathId)
      const topic = topics.find(t => t.id === topicId)

      if (!topic) {
        throw new Error(`Topic ${topicId} not found in path ${pathId}`)
      }

      return topic
    } catch (error) {
      throw new Error(`Failed to fetch topic: ${error}`)
    }
  }

  /**
   * Update topic status (local only - would need API endpoint)
   */
  updateTopicStatus(pathId: string, topicId: string, status: TopicStatus): void {
    // Clear relevant caches
    this.clearCache(`learning-path-${pathId}`)

    // TODO: Implement actual status update when API supports it
  }

  // ================================
  // Statistics and Analytics
  // ================================

  /**
   * Get learning statistics
   */
  async getLearningStats(): Promise<LearningStats> {
    try {
      const paths = await this.getAllLearningPaths()

      const stats: LearningStats = {
        totalPaths: paths?.length || 0,
        completedPaths: 0,
        inProgressPaths: 0,
        totalTopics: 0,
        completedTopics: 0,
        totalEstimatedHours: 0,
        averageProgress: 0
      }

      if (!paths || paths.length === 0) {
        return stats
      }

      for (const path of paths) {
        // Safely access path properties with fallbacks
        const totalTopics = path.total_topics || 0
        const progressCount = path.progress_count || 0
        const estimatedHours = path.estimated_total_hours || 0

        stats.totalTopics += totalTopics
        stats.completedTopics += progressCount
        stats.totalEstimatedHours += estimatedHours

        // Calculate progress with safe division
        const progress = totalTopics > 0 ? (progressCount / totalTopics) * 100 : 0
        if (progress >= 100) {
          stats.completedPaths++
        } else if (progress > 0) {
          stats.inProgressPaths++
        }
      }

      if (stats.totalTopics > 0) {
        stats.averageProgress = (stats.completedTopics / stats.totalTopics) * 100
      }

      return stats
    } catch (error) {
      throw new Error(`Failed to calculate learning stats: ${error}`)
    }
  }

  // ================================
  // Utility Methods
  // ================================

  /**
   * Enhance learning path with computed properties
   */
  private enhanceLearningPath(path: LearningPath): EnhancedLearningPath {
    // Safely access topics array with fallback
    const topics = path.topics || []
    const currentTopicIndex = path.current_topic_index || 0

    const completedTopics = topics.filter(
      topic => topic.status === 'completed' || topic.status === 'mastery'
    ).length

    const progressPercentage = topics.length > 0
      ? (completedTopics / topics.length) * 100
      : 0

    const estimatedTimeRemaining = topics
      .slice(currentTopicIndex)
      .reduce((total, topic) => total + (topic.estimated_duration || 0), 0)

    const nextTopic = currentTopicIndex < topics.length
      ? topics[currentTopicIndex]
      : null

    const isCompleted = completedTopics === topics.length && topics.length > 0

    return {
      ...path,
      progressPercentage,
      completedTopics,
      estimatedTimeRemaining,
      nextTopic,
      isCompleted
    }
  }

  /**
   * Sort learning paths by specified criteria
   */
  private sortLearningPaths(
    paths: LearningPathSummary[],
    sortBy: SortOption
  ): LearningPathSummary[] {
    return [...paths].sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.topic_name.localeCompare(b.topic_name)
        case 'created_date':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        case 'progress':
          const progressA = (a.progress_count / a.total_topics) * 100
          const progressB = (b.progress_count / b.total_topics) * 100
          return progressB - progressA
        default:
          return 0
      }
    })
  }

  /**
   * Validate user level
   */
  validateUserLevel(level: string): level is UserLevel {
    return ['beginner', 'intermediate', 'advanced'].includes(level)
  }

  /**
   * Calculate estimated completion time
   */
  calculateEstimatedCompletion(path: LearningPath): Date | null {
    if (path.current_topic_index >= path.topics.length) {
      return null // Already completed
    }

    const remainingMinutes = path.topics
      .slice(path.current_topic_index)
      .reduce((total, topic) => total + topic.estimated_duration, 0)

    // Assume 30 minutes of study per day
    const dailyStudyMinutes = 30
    const daysToComplete = Math.ceil(remainingMinutes / dailyStudyMinutes)

    const completionDate = new Date()
    completionDate.setDate(completionDate.getDate() + daysToComplete)

    return completionDate
  }
}

/**
 * Default learning service instance
 */
export const learningService = new LearningService()

/**
 * Create a new learning service instance
 */
export function createLearningService(): LearningService {
  return new LearningService()
}