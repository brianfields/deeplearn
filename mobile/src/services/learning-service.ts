/**
 * React Native Learning Service
 *
 * Adapted from web version with mobile-specific optimizations:
 * - AsyncStorage for persistence
 * - Background sync
 * - Offline-first approach
 * - Mobile performance optimizations
 */

import AsyncStorage from '@react-native-async-storage/async-storage'
import { apiClient } from './api-client'
import type {
  BiteSizedTopicDetail,
  LearningResults,
  TopicProgress,
  LearningSession
} from '@/types'

// Cache configuration
const CACHE_PREFIX = 'learning_'
const CACHE_EXPIRY_HOURS = 24
const MAX_CACHED_TOPICS = 20

interface CachedTopic {
  data: BiteSizedTopicDetail
  cachedAt: number
  lastAccessed: number
}

export class LearningService {
  private cache: Map<string, CachedTopic> = new Map()
  private preloadingQueue: Set<string> = new Set()
  private currentSession: LearningSession | null = null

  constructor() {
    this.loadCacheFromStorage()
    this.loadSessionFromStorage()
  }

  // ================================
  // Topic Loading & Caching
  // ================================

  /**
   * Load a topic with caching and preloading
   */
  async loadTopic(
    topicId: string,
    preloadNext: boolean = true,
    forceRefresh: boolean = false
  ): Promise<BiteSizedTopicDetail> {
    console.log('🔍 [Mobile Learning] Loading topic:', topicId)

    // Check cache first (unless forcing refresh)
    if (!forceRefresh) {
      const cached = this.getCachedTopic(topicId)
      if (cached) {
        console.log('📦 [Mobile Learning] Found in cache:', cached.data.title)
        this.updateLastAccessed(topicId)
        return cached.data
      }
    }

    // Load from API
    console.log('📡 [Mobile Learning] Loading from API...')
    try {
      const topic = await apiClient.getBiteSizedTopicDetail(topicId)
      console.log('✅ [Mobile Learning] API call succeeded:', topic?.title)

      // Cache the topic
      this.cacheTopic(topicId, topic)

      // Preload next topics if requested
      if (preloadNext) {
        this.preloadNextTopics(topicId)
      }

      return topic
    } catch (error) {
      console.error('❌ [Mobile Learning] API call failed:', error)
      throw error
    }
  }

  /**
   * Bulk load multiple topics for a learning session
   */
  async bulkLoadTopics(topicIds: string[]): Promise<Map<string, BiteSizedTopicDetail>> {
    const results = new Map<string, BiteSizedTopicDetail>()
    const uncachedIds: string[] = []

    // Check cache for each topic
    for (const topicId of topicIds) {
      const cached = this.getCachedTopic(topicId)
      if (cached) {
        results.set(topicId, cached.data)
        this.updateLastAccessed(topicId)
      } else {
        uncachedIds.push(topicId)
      }
    }

    // Load uncached topics in parallel
    if (uncachedIds.length > 0) {
      const loadPromises = uncachedIds.map(async (topicId) => {
        const topic = await apiClient.getBiteSizedTopicDetail(topicId)
        this.cacheTopic(topicId, topic)
        return { topicId, topic }
      })

      const loadedTopics = await Promise.all(loadPromises)
      for (const { topicId, topic } of loadedTopics) {
        results.set(topicId, topic)
      }
    }

    this.persistCacheToStorage()
    return results
  }

  /**
   * Preload next topics in background
   */
  private async preloadNextTopics(currentTopicId: string) {
    // Get next topics to preload (this would come from learning path)
    const nextTopicIds = await this.getNextTopicIds(currentTopicId)

    for (const topicId of nextTopicIds.slice(0, 3)) { // Preload next 3
      if (!this.cache.has(topicId) && !this.preloadingQueue.has(topicId)) {
        this.preloadingQueue.add(topicId)

        // Preload in background
        this.loadTopic(topicId, false).then(() => {
          this.preloadingQueue.delete(topicId)
        }).catch((error) => {
          console.warn(`Failed to preload topic ${topicId}:`, error)
          this.preloadingQueue.delete(topicId)
        })
      }
    }
  }

  // ================================
  // Progress Management
  // ================================

  /**
   * Start a new learning session
   */
  startLearningSession(topicIds: string[]): LearningSession {
    const session: LearningSession = {
      sessionId: `session_${Date.now()}`,
      topicIds,
      currentTopicIndex: 0,
      startTime: Date.now(),
      totalTimeSpent: 0,
      streak: this.getCurrentStreak(),
      dailyGoal: 5, // 5 topics per day default
      dailyProgress: this.getTodayProgress()
    }

    this.currentSession = session
    this.persistSessionToStorage()
    return session
  }

  /**
   * Save topic progress locally
   */
  async saveTopicProgress(topicId: string, progress: Partial<TopicProgress>): Promise<void> {
    const existing = await this.getTopicProgress(topicId)
    const updated: TopicProgress = {
      topicId,
      currentComponentIndex: 0,
      completedComponents: [],
      startTime: Date.now(),
      timeSpent: 0,
      score: 0,
      interactionResults: [],
      completed: false,
      lastUpdated: Date.now(),
      ...existing,
      ...progress
    }

    await AsyncStorage.setItem(
      `${CACHE_PREFIX}progress_${topicId}`,
      JSON.stringify(updated)
    )

    // Update session progress
    if (this.currentSession && updated.completed) {
      this.updateSessionProgress()
    }
  }

  /**
   * Get topic progress
   */
  async getTopicProgress(topicId: string): Promise<TopicProgress | null> {
    try {
      const stored = await AsyncStorage.getItem(`${CACHE_PREFIX}progress_${topicId}`)
      return stored ? JSON.parse(stored) : null
    } catch (error) {
      console.warn('Failed to get topic progress:', error)
      return null
    }
  }

  /**
   * Submit results and update streaks
   */
  async submitTopicResults(topicId: string, results: LearningResults): Promise<void> {
    // Save progress locally first
    await this.saveTopicProgress(topicId, {
      completed: true,
      timeSpent: results.timeSpent,
      score: results.finalScore,
      interactionResults: results.interactionResults
    })

    // Update streak
    await this.updateStreak()

    // Submit to server (optional - can be done in background)
    try {
      await apiClient.submitTopicResults(topicId, results)
    } catch (error) {
      console.warn('Failed to submit results to server:', error)
      // Store for later sync
      await this.queueForSync(topicId, results)
    }
  }

  // ================================
  // Cache Management
  // ================================

  private getCachedTopic(topicId: string): CachedTopic | null {
    const cached = this.cache.get(topicId)
    if (!cached) return null

    // Check if expired
    const now = Date.now()
    const age = now - cached.cachedAt
    const maxAge = CACHE_EXPIRY_HOURS * 60 * 60 * 1000

    if (age > maxAge) {
      this.cache.delete(topicId)
      return null
    }

    return cached
  }

  private cacheTopic(topicId: string, topic: BiteSizedTopicDetail): void {
    const now = Date.now()
    const cached: CachedTopic = {
      data: topic,
      cachedAt: now,
      lastAccessed: now
    }

    this.cache.set(topicId, cached)

    // Cleanup old cache entries if needed
    if (this.cache.size > MAX_CACHED_TOPICS) {
      this.cleanupCache()
    }

    this.persistCacheToStorage()
  }

  private updateLastAccessed(topicId: string): void {
    const cached = this.cache.get(topicId)
    if (cached) {
      cached.lastAccessed = Date.now()
      this.cache.set(topicId, cached)
    }
  }

  private cleanupCache(): void {
    // Remove least recently accessed items
    const entries = Array.from(this.cache.entries())
    entries.sort((a, b) => a[1].lastAccessed - b[1].lastAccessed)

    const toRemove = entries.slice(0, entries.length - MAX_CACHED_TOPICS + 5)
    for (const [topicId] of toRemove) {
      this.cache.delete(topicId)
    }
  }

  // ================================
  // Persistence
  // ================================

  private async loadCacheFromStorage(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem(`${CACHE_PREFIX}cache`)
      if (stored) {
        const data = JSON.parse(stored)
        this.cache = new Map(Object.entries(data))
      }
    } catch (error) {
      console.warn('Failed to load cache from storage:', error)
    }
  }

  private async persistCacheToStorage(): Promise<void> {
    try {
      const data = Object.fromEntries(this.cache.entries())
      await AsyncStorage.setItem(`${CACHE_PREFIX}cache`, JSON.stringify(data))
    } catch (error) {
      console.warn('Failed to persist cache to storage:', error)
    }
  }

  private async loadSessionFromStorage(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem(`${CACHE_PREFIX}session`)
      if (stored) {
        this.currentSession = JSON.parse(stored)
      }
    } catch (error) {
      console.warn('Failed to load session from storage:', error)
    }
  }

  private async persistSessionToStorage(): Promise<void> {
    try {
      if (this.currentSession) {
        await AsyncStorage.setItem(
          `${CACHE_PREFIX}session`,
          JSON.stringify(this.currentSession)
        )
      }
    } catch (error) {
      console.warn('Failed to persist session to storage:', error)
    }
  }

  // ================================
  // Helper Methods
  // ================================

  private async getNextTopicIds(currentTopicId: string): Promise<string[]> {
    // This would integrate with your learning path service
    // For now, return empty array
    return []
  }

  private getCurrentStreak(): number {
    // Would be loaded from AsyncStorage
    return 0
  }

  private getTodayProgress(): number {
    // Would be loaded from AsyncStorage
    return 0
  }

  private async updateStreak(): Promise<void> {
    const currentStreak = this.getCurrentStreak()
    const newStreak = currentStreak + 1

    await AsyncStorage.setItem(`${CACHE_PREFIX}streak`, newStreak.toString())

    // Update daily progress
    const today = new Date().toDateString()
    const currentDaily = this.getTodayProgress()
    await AsyncStorage.setItem(
      `${CACHE_PREFIX}daily_${today}`,
      (currentDaily + 1).toString()
    )
  }

  private updateSessionProgress(): void {
    if (!this.currentSession) return

    // Logic to update session progress
    this.currentSession.totalTimeSpent = Date.now() - this.currentSession.startTime
    this.persistSessionToStorage()
  }

  private async queueForSync(topicId: string, results: LearningResults): Promise<void> {
    try {
      // Store failed submissions for later sync
      const queue = JSON.parse(
        await AsyncStorage.getItem(`${CACHE_PREFIX}sync_queue`) || '[]'
      )
      queue.push({ topicId, results, timestamp: Date.now() })
      await AsyncStorage.setItem(`${CACHE_PREFIX}sync_queue`, JSON.stringify(queue))
    } catch (error) {
      console.warn('Failed to queue for sync:', error)
    }
  }

  // ================================
  // Public API
  // ================================

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      cachedTopics: this.cache.size,
      preloading: this.preloadingQueue.size,
      currentStreak: this.getCurrentStreak(),
      todayProgress: this.getTodayProgress()
    }
  }

  /**
   * Clear all cached data
   */
  async clearCache(): Promise<void> {
    this.cache.clear()
    try {
      const keys = await AsyncStorage.getAllKeys()
      const cacheKeys = keys.filter(key => key.startsWith(CACHE_PREFIX))
      await AsyncStorage.multiRemove(cacheKeys)
    } catch (error) {
      console.warn('Failed to clear cache:', error)
    }
  }

  /**
   * Check if topic is available offline
   */
  isTopicAvailableOffline(topicId: string): boolean {
    return this.getCachedTopic(topicId) !== null
  }
}

// Export singleton instance
export const learningService = new LearningService()
export default learningService