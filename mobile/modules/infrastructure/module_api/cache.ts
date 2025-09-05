/**
 * Cache API for Infrastructure module
 *
 * Provides caching functionality to other modules
 */

import { CacheManager } from '../adapters/storage/cache-manager';

// Create cache manager instances for different purposes
const apiCache = new CacheManager({
  keyPrefix: 'api_cache_',
  defaultTTL: 24 * 60 * 60 * 1000, // 24 hours
});

const userCache = new CacheManager({
  keyPrefix: 'user_cache_',
  defaultTTL: 7 * 24 * 60 * 60 * 1000, // 7 days
});

const sessionCache = new CacheManager({
  keyPrefix: 'session_cache_',
  defaultTTL: 60 * 60 * 1000, // 1 hour
});

export function useCache() {
  return {
    // API cache for HTTP responses
    api: {
      get: <T>(key: string) => apiCache.get<T>(key),
      set: <T>(key: string, data: T, ttl?: number) =>
        apiCache.set(key, data, ttl),
      delete: (key: string) => apiCache.delete(key),
      clear: () => apiCache.clear(),
      has: (key: string) => apiCache.has(key),
    },

    // User cache for user preferences and settings
    user: {
      get: <T>(key: string) => userCache.get<T>(key),
      set: <T>(key: string, data: T, ttl?: number) =>
        userCache.set(key, data, ttl),
      delete: (key: string) => userCache.delete(key),
      clear: () => userCache.clear(),
      has: (key: string) => userCache.has(key),
    },

    // Session cache for temporary data
    session: {
      get: <T>(key: string) => sessionCache.get<T>(key),
      set: <T>(key: string, data: T, ttl?: number) =>
        sessionCache.set(key, data, ttl),
      delete: (key: string) => sessionCache.delete(key),
      clear: () => sessionCache.clear(),
      has: (key: string) => sessionCache.has(key),
    },

    // Global cache operations
    clearAll: async () => {
      await Promise.all([
        apiCache.clear(),
        userCache.clear(),
        sessionCache.clear(),
      ]);
    },

    getStats: async () => {
      const [apiStats, userStats, sessionStats] = await Promise.all([
        apiCache.getStats(),
        userCache.getStats(),
        sessionCache.getStats(),
      ]);

      return {
        api: apiStats,
        user: userStats,
        session: sessionStats,
        total: {
          entries: apiStats.entries + userStats.entries + sessionStats.entries,
          size: apiStats.size + userStats.size + sessionStats.size,
        },
      };
    },
  };
}

export type { CacheConfig } from '../adapters/storage/cache-manager';
