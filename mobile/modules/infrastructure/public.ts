/**
 * Infrastructure Module - Public Interface
 *
 * The only interface other modules should import from.
 * Pure forwarder - no logic, just selects/forwards service methods.
 */

import { InfrastructureService } from './service';
import { Platform } from 'react-native';
import type {
  HttpClientConfig,
  RequestConfig,
  StorageConfig,
  StorageStats,
  NetworkStatus,
  InfrastructureHealth,
} from './models';

// Public interface protocol
export interface InfrastructureProvider {
  request<T>(endpoint: string, config?: RequestConfig): Promise<T>;
  getNetworkStatus(): NetworkStatus;
  checkHealth(): Promise<InfrastructureHealth>;
  // Simple storage for non-React Query data (user preferences, settings)
  getStorageItem(key: string): Promise<string | null>;
  setStorageItem(key: string, value: string): Promise<void>;
  removeStorageItem(key: string): Promise<void>;
  getStorageStats(): Promise<StorageStats>;
  clearStorage(): Promise<void>;
}

// Default configuration
const DEV_BASE_URL: string = Platform.select({
  ios: 'http://127.0.0.1:8000',
  android: 'http://10.0.2.2:8000',
  default: 'http://127.0.0.1:8000',
}) as string;

const DEFAULT_HTTP_CONFIG: HttpClientConfig = {
  baseURL: __DEV__ ? DEV_BASE_URL : 'https://your-production-api.com',
  timeout: 30000,
  retryAttempts: 3,
};

const DEFAULT_STORAGE_CONFIG: StorageConfig = {
  prefix: 'app_storage_',
};

// Service instance (singleton)
let serviceInstance: InfrastructureService | null = null;

function getServiceInstance(): InfrastructureService {
  if (!serviceInstance) {
    serviceInstance = new InfrastructureService(
      DEFAULT_HTTP_CONFIG,
      DEFAULT_STORAGE_CONFIG
    );
  }
  return serviceInstance;
}

// Public provider function
export function infrastructureProvider(): InfrastructureProvider {
  const service = getServiceInstance();

  // Pure forwarder - no logic
  return {
    request: service.request.bind(service),
    getNetworkStatus: service.getNetworkStatus.bind(service),
    checkHealth: service.checkHealth.bind(service),
    getStorageItem: service.getStorageItem.bind(service),
    setStorageItem: service.setStorageItem.bind(service),
    removeStorageItem: service.removeStorageItem.bind(service),
    getStorageStats: service.getStorageStats.bind(service),
    clearStorage: service.clearStorage.bind(service),
  };
}

// Export types for other modules
export type {
  HttpClientConfig,
  RequestConfig,
  StorageConfig,
  StorageStats,
  NetworkStatus,
  InfrastructureHealth,
} from './models';
