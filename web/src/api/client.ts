/**
 * API Client for the Learning Platform
 *
 * This module provides a robust HTTP client with:
 * - Automatic retry logic
 * - Request/response logging
 * - Error handling and transformation
 * - TypeScript support
 * - Request timeout handling
 *
 * Usage:
 * ```typescript
 * import { apiClient } from '@/api/client'
 *
 * const learningPaths = await apiClient.getLearningPaths()
 * ```
 */

import type {
  LearningPath,
  LearningPathSummary,
  ConversationSession,
  Progress,
  HealthCheck,
  CreateLearningPathRequest,
  BiteSizedTopic,
  BiteSizedTopicDetail
} from '@/types'

import type {
  ApiClientConfig,
  RequestConfig,
  HttpMethod,
  ApiResponse,
  CreateLearningPathResponse,
  GetLearningPathsResponse,
  GetLearningPathResponse,
  StartConversationResponse,
  ContinueConversationResponse,
  GetProgressResponse,
  HealthCheckResponse
} from '@/types/api'

import {
  ApiError,
  TimeoutError,
  NetworkError,
  HttpStatus
} from '@/types/api'

/**
 * Default configuration for the API client
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
  enableLogging: process.env.NODE_ENV === 'development'
}

/**
 * Main API client class
 */
export class ApiClient {
  private config: ApiClientConfig

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  /**
   * Make a HTTP request with error handling and retries
   */
  private async request<T>(
    endpoint: string,
    options: RequestConfig = {}
  ): Promise<T> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = this.config.timeout,
      retryAttempts = this.config.retryAttempts
    } = options

    const url = `${this.config.baseUrl}${endpoint}`
    let lastError: Error

    for (let attempt = 0; attempt <= retryAttempts; attempt++) {
      try {
        if (this.config.enableLogging) {
          console.log(`[API] ${method} ${url}`, { body, attempt })
        }

        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), timeout)

        const response = await fetch(url, {
          method,
          headers: {
            'Content-Type': 'application/json',
            ...headers
          },
          body: body ? JSON.stringify(body) : undefined,
          signal: controller.signal
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          const errorData = await this.parseErrorResponse(response)
          throw new ApiError(
            errorData.message || `HTTP ${response.status}`,
            response.status,
            errorData.code,
            errorData.details
          )
        }

        const data = await response.json()

        if (this.config.enableLogging) {
          console.log(`[API] ${method} ${url} - Success`, { data })
        }

        return data
      } catch (error) {
        lastError = this.transformError(error, attempt, retryAttempts)

        if (this.config.enableLogging) {
          console.error(`[API] ${method} ${url} - Attempt ${attempt + 1} failed`, lastError)
        }

        // Don't retry for client errors (4xx)
        if (lastError instanceof ApiError && lastError.isClientError) {
          break
        }

        // Don't retry on last attempt
        if (attempt === retryAttempts) {
          break
        }

        // Exponential backoff
        const delay = Math.min(1000 * Math.pow(2, attempt), 5000)
        await this.sleep(delay)
      }
    }

    throw lastError!
  }

  /**
   * Parse error response from API
   */
  private async parseErrorResponse(response: Response) {
    try {
      const data = await response.json()
      return data.error || data
    } catch {
      return { message: response.statusText }
    }
  }

  /**
   * Transform and categorize errors
   */
  private transformError(error: any, attempt: number, maxAttempts: number): Error {
    if (error.name === 'AbortError') {
      return new TimeoutError(this.config.timeout)
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      return new NetworkError('Failed to connect to the server')
    }

    if (error instanceof ApiError) {
      return error
    }

    return new ApiError(
      error.message || 'Unknown error occurred',
      0,
      'UNKNOWN_ERROR',
      { originalError: error, attempt, maxAttempts }
    )
  }

  /**
   * Sleep utility for retry delays
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  // ================================
  // Public API Methods
  // ================================

  /**
   * Check API health status
   */
  async healthCheck(): Promise<HealthCheck> {
    const response = await this.request<HealthCheck>('/health')
    return response
  }

  /**
   * Create a new learning path
   */
  async createLearningPath(
    topic: string,
    userLevel: string = 'beginner'
  ): Promise<LearningPath> {
    const response = await this.request<LearningPath>(
      '/api/learning-paths',
      {
        method: 'POST',
        body: { topic, user_level: userLevel } as CreateLearningPathRequest
      }
    )
    return response
  }

  /**
   * Get all learning paths (summary view)
   */
  async getLearningPaths(): Promise<LearningPathSummary[]> {
    const response = await this.request<LearningPathSummary[]>('/api/learning-paths')
    return response
  }

  /**
   * Get detailed learning path by ID
   */
  async getLearningPath(pathId: string): Promise<LearningPath> {
    const response = await this.request<LearningPath>(
      `/api/learning-paths/${pathId}`
    )
    return response
  }

  /**
   * Start a new conversation for a topic
   */
  async startConversation(pathId: string, topicId: string): Promise<ConversationSession> {
    const response = await this.request<ConversationSession>(
      `/api/conversations/start?path_id=${pathId}&topic_id=${topicId}`,
      { method: 'POST' }
    )
    return response
  }

  /**
   * Continue an existing conversation
   */
  async continueConversation(pathId: string, topicId: string): Promise<ConversationSession> {
    const response = await this.request<ConversationSession>(
      `/api/conversations/continue?path_id=${pathId}&topic_id=${topicId}`,
      { method: 'POST' }
    )
    return response
  }

  /**
   * Get overall learning progress
   */
  async getProgress(): Promise<Progress> {
    const response = await this.request<Progress>('/api/progress')
    return response
  }

  // ================================
  // Bite-Sized Topic Methods
  // ================================

  /**
   * Get all bite-sized topics
   */
  async getBiteSizedTopics(): Promise<BiteSizedTopic[]> {
    const response = await this.request<BiteSizedTopic[]>('/api/bite-sized-topics')
    return response
  }

  /**
   * Get detailed bite-sized topic by ID
   */
  async getBiteSizedTopicDetail(topicId: string): Promise<BiteSizedTopicDetail> {
    const response = await this.request<BiteSizedTopicDetail>(
      `/api/bite-sized-topics/${topicId}`
    )
    return response
  }

  /**
   * Start a conversation for a bite-sized topic
   */
  async startBiteSizedTopicConversation(topicId: string): Promise<ConversationSession> {
    const response = await this.request<ConversationSession>(
      `/api/bite-sized-topics/${topicId}/start-conversation`,
      { method: 'POST' }
    )
    return response
  }

  /**
   * Update client configuration
   */
  updateConfig(config: Partial<ApiClientConfig>): void {
    this.config = { ...this.config, ...config }
  }

  /**
   * Get current configuration
   */
  getConfig(): ApiClientConfig {
    return { ...this.config }
  }
}

/**
 * Default API client instance
 */
export const apiClient = new ApiClient()

/**
 * Create a new API client with custom configuration
 */
export function createApiClient(config: Partial<ApiClientConfig>): ApiClient {
  return new ApiClient(config)
}