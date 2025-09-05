/**
 * Cache Manager for React Native Learning App
 *
 * Provides caching functionality using AsyncStorage with TTL support
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export interface CachedItem<T> {
  data: T;
  timestamp: number;
  expiry: number;
}

export interface CacheConfig {
  defaultTTL?: number; // Time to live in milliseconds
  keyPrefix?: string;
}

export class CacheManager {
  private defaultTTL: number;
  private keyPrefix: string;

  constructor(config: CacheConfig = {}) {
    this.defaultTTL = config.defaultTTL || 24 * 60 * 60 * 1000; // 24 hours
    this.keyPrefix = config.keyPrefix || 'cache_';
  }

  /**
   * Get cached item
   */
  async get<T>(key: string): Promise<T | null> {
    try {
      const cached = await AsyncStorage.getItem(this.buildKey(key));
      if (!cached) return null;

      const { data, expiry }: CachedItem<T> = JSON.parse(cached);

      if (Date.now() > expiry) {
        await this.delete(key);
        return null;
      }

      return data;
    } catch (error) {
      console.warn('Cache get error:', error);
      return null;
    }
  }

  /**
   * Set cached item with TTL
   */
  async set<T>(key: string, data: T, ttl?: number): Promise<void> {
    try {
      const cached: CachedItem<T> = {
        data,
        timestamp: Date.now(),
        expiry: Date.now() + (ttl || this.defaultTTL),
      };
      await AsyncStorage.setItem(this.buildKey(key), JSON.stringify(cached));
    } catch (error) {
      console.warn('Cache set error:', error);
    }
  }

  /**
   * Delete cached item
   */
  async delete(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.buildKey(key));
    } catch (error) {
      console.warn('Cache delete error:', error);
    }
  }

  /**
   * Clear all cached items with this prefix
   */
  async clear(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith(this.keyPrefix));
      await AsyncStorage.multiRemove(cacheKeys);
      console.log(`[Cache] Cleared ${cacheKeys.length} cache entries`);
    } catch (error) {
      console.warn('Cache clear error:', error);
    }
  }

  /**
   * Get cache statistics
   */
  async getStats(): Promise<{ size: number; entries: number }> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith(this.keyPrefix));

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
   * Check if key exists and is not expired
   */
  async has(key: string): Promise<boolean> {
    const item = await this.get(key);
    return item !== null;
  }

  /**
   * Get all cache keys
   */
  async keys(): Promise<string[]> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      return keys
        .filter(key => key.startsWith(this.keyPrefix))
        .map(key => key.replace(this.keyPrefix, ''));
    } catch {
      return [];
    }
  }

  /**
   * Build full cache key with prefix
   */
  private buildKey(key: string): string {
    return `${this.keyPrefix}${key}`;
  }
}
