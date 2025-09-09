/**
 * Infrastructure Module - Unit Tests
 *
 * Tests for infrastructure services and utilities.
 * Focus on HTTP client, cache management, and network utilities.
 */

import { InfrastructureService } from './service';
import { infrastructureProvider } from './public';
import type { HttpClientConfig, StorageConfig } from './models';

describe('Infrastructure Module', () => {
  describe('InfrastructureService', () => {
    const mockHttpConfig: HttpClientConfig = {
      baseURL: 'http://test.com',
      timeout: 5000,
    };

    const mockStorageConfig: StorageConfig = {
      prefix: 'test_',
    };

    it('should initialize with configuration', () => {
      const service = new InfrastructureService(
        mockHttpConfig,
        mockStorageConfig
      );
      expect(service).toBeDefined();
    });

    it('should provide network status', () => {
      const service = new InfrastructureService(
        mockHttpConfig,
        mockStorageConfig
      );
      const status = service.getNetworkStatus();

      expect(status).toHaveProperty('isConnected');
      expect(typeof status.isConnected).toBe('boolean');
    });
  });

  describe('Public Interface', () => {
    it('should provide infrastructure provider', () => {
      const provider = infrastructureProvider();

      expect(provider).toHaveProperty('request');
      expect(provider).toHaveProperty('getNetworkStatus');
      expect(provider).toHaveProperty('checkHealth');
      expect(provider).toHaveProperty('getStorageItem');
      expect(provider).toHaveProperty('setStorageItem');
      expect(provider).toHaveProperty('removeStorageItem');
      expect(provider).toHaveProperty('getStorageStats');
      expect(provider).toHaveProperty('clearStorage');
    });

    it('should return network status through provider', () => {
      const provider = infrastructureProvider();
      const status = provider.getNetworkStatus();

      expect(status).toHaveProperty('isConnected');
    });
  });
});
