/**
 * API Client for React Native Learning App
 *
 * Adapted from web version with React Native specific features:
 * - AsyncStorage for caching
 * - React Native fetch polyfills
 * - Network state awareness
 * - Background sync capabilities
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import type {
  BiteSizedTopic,
  BiteSizedTopicDetail,
  LearningResults,
  ApiError,
} from '@/types';

// API Configuration
// API Configuration - Back to Expo Go compatible
const API_BASE_URL = __DEV__
  ? 'http://192.168.4.188:8000' // Development - Use your computer's IP for Expo Go
  : 'https://your-production-api.com'; // Production

const DEFAULT_TIMEOUT = 30000;
const CACHE_PREFIX = 'api_cache_';
const CACHE_EXPIRY_HOURS = 24;

interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: unknown;
  timeout?: number;
  useCache?: boolean;
  retryAttempts?: number;
}

interface CachedResponse<T> {
  data: T;
  timestamp: number;
  expiry: number;
}

class ApiClient {
  private isOnline: boolean = true;
  private requestQueue: Array<() => Promise<any>> = [];

  constructor() {
    this.initNetworkListener();
  }

  /**
   * Initialize network state listener
   */
  private initNetworkListener() {
    NetInfo.addEventListener(state => {
      const wasOffline = !this.isOnline;
      this.isOnline = state.isConnected ?? false;

      // Process queued requests when back online
      if (wasOffline && this.isOnline) {
        this.processRequestQueue();
      }
    });
  }

  /**
   * Process queued requests when network is restored
   */
  private async processRequestQueue() {
    const queue = [...this.requestQueue];
    this.requestQueue = [];

    for (const request of queue) {
      try {
        await request();
      } catch (error) {
        console.warn('Failed to process queued request:', error);
      }
    }
  }

  /**
   * Make HTTP request with caching and retry logic
   */
  private async request<T>(
    endpoint: string,
    options: RequestConfig = {}
  ): Promise<T> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = DEFAULT_TIMEOUT,
      useCache = method === 'GET',
      retryAttempts = 3,
    } = options;

    const url = `${API_BASE_URL}${endpoint}`;
    const cacheKey = `${CACHE_PREFIX}${method}_${endpoint}`;

    // Check cache first for GET requests
    if (useCache && method === 'GET') {
      const cached = await this.getCachedResponse<T>(cacheKey);
      if (cached) {
        console.log(`[API] Cache hit for ${endpoint}`);
        return cached;
      }
    }

    // Check network status
    if (!this.isOnline) {
      throw new Error('Network unavailable. Request queued for retry.');
    }

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retryAttempts; attempt++) {
      try {
        console.log(`[API] ${method} ${url} (attempt ${attempt + 1})`);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
          method,
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            ...headers,
          },
          body: body ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorData = await this.parseErrorResponse(response);
          throw new Error(errorData.message || `HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log(`[API] ${method} ${url} - Success`);

        // Cache successful GET responses
        if (useCache && method === 'GET') {
          await this.setCachedResponse(cacheKey, data);
        }

        return data;
      } catch (error: any) {
        lastError = error;
        console.warn(
          `[API] ${method} ${url} - Attempt ${attempt + 1} failed:`,
          error.message
        );

        // Don't retry for client errors (4xx) or abort errors
        if (
          error.name === 'AbortError' ||
          (error.message && error.message.includes('4'))
        ) {
          break;
        }

        // Don't retry on last attempt
        if (attempt === retryAttempts) {
          break;
        }

        // Exponential backoff
        const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
        await this.sleep(delay);
      }
    }

    throw lastError || new Error('Unknown error occurred');
  }

  /**
   * Parse error response from API
   */
  private async parseErrorResponse(response: Response): Promise<ApiError> {
    try {
      const data = await response.json();
      return {
        message: data.error?.message || data.message || response.statusText,
        code: data.error?.code || 'API_ERROR',
        status: response.status,
        details: data.error?.details,
      };
    } catch {
      return {
        message: response.statusText || 'Unknown error',
        code: 'PARSE_ERROR',
        status: response.status,
      };
    }
  }

  /**
   * Get cached response
   */
  private async getCachedResponse<T>(key: string): Promise<T | null> {
    try {
      const cached = await AsyncStorage.getItem(key);
      if (!cached) return null;

      const { data, expiry }: CachedResponse<T> = JSON.parse(cached);

      if (Date.now() > expiry) {
        await AsyncStorage.removeItem(key);
        return null;
      }

      return data;
    } catch (error) {
      console.warn('Cache read error:', error);
      return null;
    }
  }

  /**
   * Set cached response
   */
  private async setCachedResponse<T>(key: string, data: T): Promise<void> {
    try {
      const cached: CachedResponse<T> = {
        data,
        timestamp: Date.now(),
        expiry: Date.now() + CACHE_EXPIRY_HOURS * 60 * 60 * 1000,
      };
      await AsyncStorage.setItem(key, JSON.stringify(cached));
    } catch (error) {
      console.warn('Cache write error:', error);
    }
  }

  /**
   * Sleep utility for retry delays
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ================================
  // Public API Methods
  // ================================

  /**
   * Check API health status
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.request('/health', { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get all bite-sized topics
   */
  async getBiteSizedTopics(): Promise<BiteSizedTopic[]> {
    return this.request<BiteSizedTopic[]>('/api/learning/topics');
  }

  /**
   * Get detailed bite-sized topic by ID
   */
  async getBiteSizedTopicDetail(
    topicId: string
  ): Promise<BiteSizedTopicDetail> {
    console.log('📡 [Mobile API] Requesting topic detail:', topicId);
    try {
      const response = await this.request<BiteSizedTopicDetail>(
        `/api/learning/topics/${topicId}`
      );
      console.log('✅ [Mobile API] Topic detail received:', response?.title);
      return response;
    } catch (error) {
      console.error('❌ [Mobile API] Topic detail failed:', error);
      throw error;
    }
  }

  /**
   * Submit topic completion results
   */
  async submitTopicResults(
    topicId: string,
    results: LearningResults
  ): Promise<void> {
    try {
      await this.request(`/api/learning/topics/${topicId}/complete`, {
        method: 'POST',
        body: results,
        useCache: false,
      });
    } catch (error) {
      // Queue for retry when online
      if (!this.isOnline) {
        this.requestQueue.push(() => this.submitTopicResults(topicId, results));
      }
      throw error;
    }
  }

  /**
   * Clear all cached data
   */
  async clearCache(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith(CACHE_PREFIX));
      await AsyncStorage.multiRemove(cacheKeys);
      console.log(`[API] Cleared ${cacheKeys.length} cache entries`);
    } catch (error) {
      console.warn('Failed to clear cache:', error);
    }
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<{ size: number; entries: number }> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith(CACHE_PREFIX));

      let totalSize = 0;
      for (const key of cacheKeys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          totalSize += value.length;
        }
      }

      return {
        entries: cacheKeys.length,
        size: totalSize,
      };
    } catch {
      return { entries: 0, size: 0 };
    }
  }

  /**
   * Check network status
   */
  get networkStatus(): boolean {
    return this.isOnline;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
