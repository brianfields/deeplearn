import { useState, useEffect, useCallback } from 'react'
import { duolingoLearningService } from '@/services/duolingo-learning'
import type { BiteSizedTopicDetail, LearningResults } from '@/types'

export interface UseDuolingoLearningOptions {
  autoPreload?: boolean
  maxCachedTopics?: number
}

export interface UseDuolingoLearningReturn {
  // Loading states
  isLoading: boolean
  isPreloading: boolean
  error: string | null

  // Topic management
  topic: BiteSizedTopicDetail | null
  isOfflineAvailable: boolean

  // Session management
  currentStreak: number
  todayProgress: number

  // Cache stats
  cacheStats: ReturnType<typeof duolingoLearningService.getCacheStats>

  // Actions
  loadTopic: (topicId: string) => Promise<BiteSizedTopicDetail>
  bulkLoadTopics: (topicIds: string[]) => Promise<Map<string, BiteSizedTopicDetail>>
  submitResults: (topicId: string, results: LearningResults) => Promise<void>
  clearCache: () => void
  refreshStats: () => void
}

export function useDuolingoLearning(options: UseDuolingoLearningOptions = {}): UseDuolingoLearningReturn {
  const { autoPreload = true } = options

  const [isLoading, setIsLoading] = useState(false)
  const [isPreloading, setIsPreloading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [topic, setTopic] = useState<BiteSizedTopicDetail | null>(null)
  const [cacheStats, setCacheStats] = useState(duolingoLearningService.getCacheStats())

  // Refresh stats periodically
  const refreshStats = useCallback(() => {
    setCacheStats(duolingoLearningService.getCacheStats())
  }, [])

  useEffect(() => {
    refreshStats()
    const interval = setInterval(refreshStats, 5000) // Update every 5 seconds
    return () => clearInterval(interval)
  }, [refreshStats])

  const loadTopic = useCallback(async (topicId: string): Promise<BiteSizedTopicDetail> => {
    try {
      setIsLoading(true)
      setError(null)

      const topicData = await duolingoLearningService.loadTopic(topicId, autoPreload)
      setTopic(topicData)
      refreshStats()

      return topicData
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load topic'
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [autoPreload, refreshStats])

  const bulkLoadTopics = useCallback(async (topicIds: string[]): Promise<Map<string, BiteSizedTopicDetail>> => {
    try {
      setIsPreloading(true)
      setError(null)

      const topics = await duolingoLearningService.bulkLoadTopics(topicIds)
      refreshStats()

      return topics
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to bulk load topics'
      setError(errorMessage)
      throw err
    } finally {
      setIsPreloading(false)
    }
  }, [refreshStats])

  const submitResults = useCallback(async (topicId: string, results: LearningResults): Promise<void> => {
    try {
      await duolingoLearningService.submitTopicResults(topicId, results)
      refreshStats()
    } catch (err) {
      console.warn('Failed to submit results:', err)
      // Don't throw here - results are saved locally anyway
    }
  }, [refreshStats])

  const clearCache = useCallback(() => {
    duolingoLearningService.clearCache()
    setTopic(null)
    refreshStats()
  }, [refreshStats])

  const isOfflineAvailable = topic ? duolingoLearningService.isTopicAvailableOffline(topic.id) : false

  return {
    // Loading states
    isLoading,
    isPreloading,
    error,

    // Topic management
    topic,
    isOfflineAvailable,

    // Session management
    currentStreak: cacheStats.currentStreak,
    todayProgress: cacheStats.todayProgress,

    // Cache stats
    cacheStats,

    // Actions
    loadTopic,
    bulkLoadTopics,
    submitResults,
    clearCache,
    refreshStats
  }
}

export default useDuolingoLearning