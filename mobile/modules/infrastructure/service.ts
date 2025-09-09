/**
 * Infrastructure Module - Service Layer
 *
 * Business logic and orchestration for infrastructure services.
 * Returns DTOs only, never raw API responses.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { InfrastructureRepo } from './repo';
import type {
  HttpClientConfig,
  RequestConfig,
  StorageConfig,
  StorageStats,
  NetworkStatus,
  InfrastructureHealth,
} from './models';

export class InfrastructureService {
  private repo: InfrastructureRepo;
  private storageConfig: StorageConfig;

  constructor(httpConfig: HttpClientConfig, storageConfig: StorageConfig) {
    this.repo = new InfrastructureRepo(httpConfig);
    this.storageConfig = storageConfig;
  }

  // HTTP Client Methods (no caching - let React Query handle it)
  async request<T>(endpoint: string, config: RequestConfig = {}): Promise<T> {
    return this.repo.request<T>(endpoint, config);
  }

  getNetworkStatus(): NetworkStatus {
    return this.repo.getNetworkStatus();
  }

  async checkHealth(): Promise<InfrastructureHealth> {
    const [httpHealth, storageHealth, networkStatus] = await Promise.allSettled(
      [
        this.repo.healthCheck(),
        this.checkStorageHealth(),
        Promise.resolve(this.repo.getNetworkStatus()),
      ]
    );

    return {
      httpClient: httpHealth.status === 'fulfilled' ? httpHealth.value : false,
      storage:
        storageHealth.status === 'fulfilled' ? storageHealth.value : false,
      network:
        networkStatus.status === 'fulfilled'
          ? networkStatus.value.isConnected
          : false,
      timestamp: Date.now(),
    };
  }

  // Simple storage utilities (for non-React Query data like user preferences)
  async getStorageItem(key: string): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(`${this.storageConfig.prefix}${key}`);
    } catch (error) {
      console.warn('[Storage] Read error:', error);
      return null;
    }
  }

  async setStorageItem(key: string, value: string): Promise<void> {
    try {
      await AsyncStorage.setItem(`${this.storageConfig.prefix}${key}`, value);
    } catch (error) {
      console.warn('[Storage] Write error:', error);
    }
  }

  async removeStorageItem(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(`${this.storageConfig.prefix}${key}`);
    } catch (error) {
      console.warn('[Storage] Remove error:', error);
    }
  }

  async getStorageStats(): Promise<StorageStats> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const storageKeys = keys.filter(key =>
        key.startsWith(this.storageConfig.prefix)
      );

      let totalSize = 0;
      for (const key of storageKeys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          totalSize += value.length;
        }
      }

      return {
        entries: storageKeys.length,
        size: totalSize,
      };
    } catch {
      return { entries: 0, size: 0 };
    }
  }

  async clearStorage(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const storageKeys = keys.filter(key =>
        key.startsWith(this.storageConfig.prefix)
      );
      await AsyncStorage.multiRemove(storageKeys);
      console.log(`[Storage] Cleared ${storageKeys.length} entries`);
    } catch (error) {
      console.warn('[Storage] Clear error:', error);
    }
  }

  private async checkStorageHealth(): Promise<boolean> {
    try {
      const testKey = `${this.storageConfig.prefix}health_check`;
      const testData = JSON.stringify({ test: true, timestamp: Date.now() });

      await AsyncStorage.setItem(testKey, testData);
      const retrieved = await AsyncStorage.getItem(testKey);
      await AsyncStorage.removeItem(testKey);

      return retrieved !== null;
    } catch {
      return false;
    }
  }
}
