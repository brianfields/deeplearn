# Infrastructure Module (Frontend)

## Purpose

This frontend module provides core technical infrastructure services that enable backend communication, data persistence, and cross-cutting technical concerns for all other frontend modules. It handles HTTP communication, caching, analytics, and technical utilities without containing any business domain logic or UI components.

## Domain Responsibility

**"Providing technical infrastructure services to all frontend modules"**

The Infrastructure frontend module owns all technical infrastructure:

- HTTP client and API communication
- Caching strategies and offline storage
- Analytics and tracking services
- Network state management
- Error handling and logging utilities
- Storage adapters and data persistence

## Architecture

### Module API (Public Interface)

```typescript
// module_api/index.ts
export { useHttpClient } from './http';
export { useCache } from './cache';
export { useAnalytics } from './analytics';
export { useStorage } from './storage';
export type { CacheConfig, HttpConfig, AnalyticsConfig } from './types';

// module_api/http.ts
export function useHttpClient() {
  return {
    get: (url: string, config?: RequestConfig) => httpClient.get(url, config),
    post: (url: string, data?: any, config?: RequestConfig) =>
      httpClient.post(url, data, config),
    put: (url: string, data?: any, config?: RequestConfig) =>
      httpClient.put(url, data, config),
    delete: (url: string, config?: RequestConfig) =>
      httpClient.delete(url, config),
  };
}

// module_api/analytics.ts
export function useAnalytics() {
  return {
    track: (event: string, properties?: Record<string, any>) =>
      analyticsClient.track(event, properties),
    screen: (screenName: string, properties?: Record<string, any>) =>
      analyticsClient.screen(screenName, properties),
    setUserProperties: (properties: Record<string, any>) =>
      analyticsClient.setUserProperties(properties),
  };
}

// module_api/storage.ts
export function useStorage() {
  return {
    setSecure: (key: string, value: string) =>
      storageClient.setSecure(key, value),
    getSecure: (key: string) => storageClient.getSecure(key),
    set: (key: string, value: any) => storageClient.set(key, value),
    get: (key: string) => storageClient.get(key),
    remove: (key: string) => storageClient.remove(key),
    clear: () => storageClient.clear(),
  };
}
```

### Adapters (Infrastructure Implementation)

```typescript
// adapters/analytics/analytics-client.ts
export class AnalyticsClient {
  private providers: AnalyticsProvider[];

  constructor() {
    this.providers = [new FirebaseAnalytics(), new MixpanelAnalytics()];
  }

  track(event: string, properties?: Record<string, any>): void {
    this.providers.forEach(provider => {
      try {
        provider.track(event, properties);
      } catch (error) {
        console.warn('Analytics provider error:', error);
      }
    });
  }

  screen(screenName: string, properties?: Record<string, any>): void {
    this.providers.forEach(provider => {
      try {
        provider.screen(screenName, properties);
      } catch (error) {
        console.warn('Analytics provider error:', error);
      }
    });
  }

  setUserProperties(properties: Record<string, any>): void {
    this.providers.forEach(provider => {
      try {
        provider.setUserProperties(properties);
      } catch (error) {
        console.warn('Analytics provider error:', error);
      }
    });
  }
}

// adapters/storage/storage-client.ts
export class StorageClient {
  async setSecure(key: string, value: string): Promise<void> {
    try {
      await Keychain.setInternetCredentials(key, key, value);
    } catch (error) {
      console.warn('Secure storage set error:', error);
      throw error;
    }
  }

  async getSecure(key: string): Promise<string | null> {
    try {
      const credentials = await Keychain.getInternetCredentials(key);
      return credentials ? credentials.password : null;
    } catch (error) {
      console.warn('Secure storage get error:', error);
      return null;
    }
  }

  async set(key: string, value: any): Promise<void> {
    try {
      const serialized = JSON.stringify(value);
      await AsyncStorage.setItem(key, serialized);
    } catch (error) {
      console.warn('Storage set error:', error);
      throw error;
    }
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const value = await AsyncStorage.getItem(key);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      console.warn('Storage get error:', error);
      return null;
    }
  }

  async remove(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.warn('Storage remove error:', error);
      throw error;
    }
  }

  async clear(): Promise<void> {
    try {
      await AsyncStorage.clear();
    } catch (error) {
      console.warn('Storage clear error:', error);
      throw error;
    }
  }
}
```

### Domain Layer (Technical Logic)

```typescript
// domain/http/http-client.ts
export class HttpClient {
  private baseURL: string;
  private defaultTimeout: number;
  private interceptors: RequestInterceptor[];

  constructor(config: HttpConfig) {
    this.baseURL = config.baseURL;
    this.defaultTimeout = config.timeout || 30000;
    this.interceptors = [];
  }

  addInterceptor(interceptor: RequestInterceptor): void {
    this.interceptors.push(interceptor);
  }

  async get<T>(url: string, config?: RequestConfig): Promise<T> {
    return this.request<T>('GET', url, undefined, config);
  }

  async post<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>('POST', url, data, config);
  }

  private async request<T>(
    method: string,
    url: string,
    data?: any,
    config?: RequestConfig
  ): Promise<T> {
    const fullURL = this.buildURL(url);
    const requestConfig = this.buildRequestConfig(method, data, config);

    // Apply interceptors
    for (const interceptor of this.interceptors) {
      await interceptor.onRequest?.(requestConfig);
    }

    try {
      const response = await this.executeRequest(fullURL, requestConfig);

      // Apply response interceptors
      for (const interceptor of this.interceptors) {
        await interceptor.onResponse?.(response);
      }

      return response.data;
    } catch (error) {
      // Apply error interceptors
      for (const interceptor of this.interceptors) {
        await interceptor.onError?.(error);
      }
      throw error;
    }
  }

  private buildURL(url: string): string {
    return url.startsWith('http') ? url : `${this.baseURL}${url}`;
  }

  private async executeRequest(
    url: string,
    config: RequestConfig
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), config.timeout);

    try {
      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new HttpError(response.status, response.statusText);
      }

      const data = await response.json();
      return { data, status: response.status, headers: response.headers };
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }
}

// domain/cache/cache-manager.ts
export class CacheManager {
  private storage: AsyncStorage;
  private defaultTTL: number;

  constructor(config: CacheConfig) {
    this.storage = AsyncStorage;
    this.defaultTTL = config.defaultTTL || 300000; // 5 minutes
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const cached = await this.storage.getItem(this.buildKey(key));
      if (!cached) return null;

      const { data, expiry } = JSON.parse(cached);

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

  async set<T>(key: string, data: T, ttl?: number): Promise<void> {
    try {
      const expiry = Date.now() + (ttl || this.defaultTTL);
      const cached = JSON.stringify({ data, expiry });

      await this.storage.setItem(this.buildKey(key), cached);
    } catch (error) {
      console.warn('Cache set error:', error);
    }
  }

  async delete(key: string): Promise<void> {
    try {
      await this.storage.removeItem(this.buildKey(key));
    } catch (error) {
      console.warn('Cache delete error:', error);
    }
  }

  async clear(): Promise<void> {
    try {
      const keys = await this.storage.getAllKeys();
      const appKeys = keys.filter(key => key.startsWith(this.getPrefix()));
      await this.storage.multiRemove(appKeys);
    } catch (error) {
      console.warn('Cache clear error:', error);
    }
  }

  private buildKey(key: string): string {
    return `${this.getPrefix()}:${key}`;
  }

  private getPrefix(): string {
    return '@deeplearn_cache';
  }
}

// domain/theme/theme-manager.ts
export class ThemeManager {
  private currentTheme: Theme;
  private listeners: ThemeChangeListener[];

  constructor(initialTheme: Theme) {
    this.currentTheme = initialTheme;
    this.listeners = [];
  }

  getTheme(): Theme {
    return this.currentTheme;
  }

  setTheme(theme: Theme): void {
    this.currentTheme = theme;
    this.notifyListeners(theme);
    this.persistTheme(theme);
  }

  addListener(listener: ThemeChangeListener): void {
    this.listeners.push(listener);
  }

  removeListener(listener: ThemeChangeListener): void {
    const index = this.listeners.indexOf(listener);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  private notifyListeners(theme: Theme): void {
    this.listeners.forEach(listener => listener(theme));
  }

  private async persistTheme(theme: Theme): Promise<void> {
    try {
      await AsyncStorage.setItem('@theme', JSON.stringify(theme));
    } catch (error) {
      console.warn('Failed to persist theme:', error);
    }
  }
}
```

### Adapters (Infrastructure Implementation)

```typescript
// adapters/http.adapter.ts
export class HttpAdapter {
  private httpClient: HttpClient;

  constructor() {
    this.httpClient = new HttpClient({
      baseURL: Config.API_BASE_URL,
      timeout: 30000,
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor for authentication
    this.httpClient.addInterceptor({
      onRequest: async config => {
        const token = await AuthStorage.getToken();
        if (token) {
          config.headers = {
            ...config.headers,
            Authorization: `Bearer ${token}`,
          };
        }
      },
    });

    // Response interceptor for error handling
    this.httpClient.addInterceptor({
      onError: async error => {
        if (error.status === 401) {
          // Handle authentication error
          await AuthStorage.clearToken();
          NavigationService.navigateToLogin();
        }
      },
    });

    // Network status interceptor
    this.httpClient.addInterceptor({
      onRequest: async config => {
        const isOnline = await NetInfo.fetch().then(state => state.isConnected);
        if (!isOnline) {
          throw new NetworkError('No internet connection');
        }
      },
    });
  }

  getClient(): HttpClient {
    return this.httpClient;
  }
}

// adapters/analytics.adapter.ts
export class AnalyticsAdapter {
  private providers: AnalyticsProvider[];

  constructor() {
    this.providers = [
      new FirebaseAnalytics(),
      new MixpanelAnalytics(),
      // Add more providers as needed
    ];
  }

  track(event: string, properties?: Record<string, any>): void {
    this.providers.forEach(provider => {
      try {
        provider.track(event, properties);
      } catch (error) {
        console.warn(`Analytics provider error:`, error);
      }
    });
  }

  setUserProperties(properties: Record<string, any>): void {
    this.providers.forEach(provider => {
      try {
        provider.setUserProperties(properties);
      } catch (error) {
        console.warn(`Analytics provider error:`, error);
      }
    });
  }

  screen(screenName: string, properties?: Record<string, any>): void {
    this.providers.forEach(provider => {
      try {
        provider.screen(screenName, properties);
      } catch (error) {
        console.warn(`Analytics provider error:`, error);
      }
    });
  }
}

// adapters/storage.adapter.ts
export class StorageAdapter {
  private cacheManager: CacheManager;

  constructor() {
    this.cacheManager = new CacheManager({
      defaultTTL: 300000, // 5 minutes
    });
  }

  async get<T>(key: string): Promise<T | null> {
    return this.cacheManager.get<T>(key);
  }

  async set<T>(key: string, data: T, ttl?: number): Promise<void> {
    return this.cacheManager.set(key, data, ttl);
  }

  async delete(key: string): Promise<void> {
    return this.cacheManager.delete(key);
  }

  async clear(): Promise<void> {
    return this.cacheManager.clear();
  }

  // Specialized storage methods
  async storeSecurely(key: string, data: string): Promise<void> {
    // Use secure storage for sensitive data
    await Keychain.setInternetCredentials(key, key, data);
  }

  async getSecurely(key: string): Promise<string | null> {
    try {
      const credentials = await Keychain.getInternetCredentials(key);
      return credentials ? credentials.password : null;
    } catch (error) {
      return null;
    }
  }
}
```

## Cross-Module Communication

### Provides to Other Modules

- **All Modules**: HTTP client, caching, analytics, secure storage
- **Topic Catalog Module**: API client for topic endpoints, caching for topic data
- **Learning Session Module**: Storage for session state, analytics for learning events
- **Learning Analytics Module**: Analytics tracking, data persistence
- **UI System Module**: HTTP client for theme assets, storage for theme preferences

### Dependencies

- **External Services**: Backend API, analytics services, secure storage
- **React Native**: Platform-specific APIs and components

### Communication Examples

```typescript
// All modules use infrastructure via module_api
import {
  useHttpClient,
  useCache,
  useAnalytics,
  useStorage,
} from '@/modules/infrastructure';

// Topic Catalog using HTTP client and caching
const httpClient = useHttpClient();
const cache = useCache();

const topics = await httpClient.get('/api/catalog/topics');
await cache.api.set('topics', topics, 300000); // Cache for 5 minutes

// Learning Session using storage and analytics
const storage = useStorage();
const analytics = useAnalytics();

await storage.set('session-state', sessionData);
analytics.track('session_started', { topicId: topic.id });

// UI System using storage for theme persistence
const storage = useStorage();
const savedTheme = await storage.get('theme_preference');
```

## Testing Strategy

### Service Tests (Technical Services)

```typescript
// tests/adapters/analytics-client.test.ts
describe('AnalyticsClient', () => {
  it('tracks events to all providers', () => {
    const mockFirebase = { track: jest.fn() };
    const mockMixpanel = { track: jest.fn() };

    const client = new AnalyticsClient();
    client.providers = [mockFirebase, mockMixpanel];

    client.track('test_event', { prop: 'value' });

    expect(mockFirebase.track).toHaveBeenCalledWith('test_event', {
      prop: 'value',
    });
    expect(mockMixpanel.track).toHaveBeenCalledWith('test_event', {
      prop: 'value',
    });
  });

  it('handles provider errors gracefully', () => {
    const mockProvider = {
      track: jest.fn().mockImplementation(() => {
        throw new Error('Provider error');
      }),
    };

    const client = new AnalyticsClient();
    client.providers = [mockProvider];

    expect(() => client.track('test_event')).not.toThrow();
  });
});
```

### Domain Tests (Technical Logic)

```typescript
// tests/domain/http-client.test.ts
describe('HttpClient', () => {
  it('makes GET requests correctly', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: 'test' }),
    });
    global.fetch = mockFetch;

    const client = new HttpClient({ baseURL: 'https://api.test.com' });
    const result = await client.get('/test');

    expect(mockFetch).toHaveBeenCalledWith(
      'https://api.test.com/test',
      expect.any(Object)
    );
    expect(result).toEqual({ data: 'test' });
  });
});
```

### Integration Tests (Adapters)

```typescript
// tests/adapters/storage.test.ts
describe('StorageAdapter', () => {
  it('stores and retrieves data correctly', async () => {
    const adapter = new StorageAdapter();
    const testData = { id: 1, name: 'test' };

    await adapter.set('test-key', testData);
    const retrieved = await adapter.get('test-key');

    expect(retrieved).toEqual(testData);
  });
});
```

## Design System

### Theme Structure

```typescript
// domain/theme/themes.ts
export const lightTheme: Theme = {
  mode: 'light',
  colors: {
    primary: '#007AFF',
    secondary: '#5856D6',
    success: '#34C759',
    warning: '#FF9500',
    error: '#FF3B30',
    background: '#FFFFFF',
    surface: '#F2F2F7',
    text: '#000000',
    textSecondary: '#8E8E93',
    border: '#C6C6C8',
  },
  spacing: {
    xs: 4,
    small: 8,
    medium: 16,
    large: 24,
    xl: 32,
  },
  typography: {
    h1: { fontSize: 32, fontWeight: 'bold' },
    h2: { fontSize: 24, fontWeight: 'bold' },
    body: { fontSize: 16, fontWeight: 'normal' },
    caption: { fontSize: 12, fontWeight: 'normal' },
  },
  borderRadius: {
    small: 4,
    medium: 8,
    large: 12,
  },
};
```

### Component Variants

```typescript
// domain/styles/button-styles.ts
export class ButtonStyles {
  static getButtonStyle(
    variant: ButtonVariant,
    size: ButtonSize,
    theme: Theme
  ): ViewStyle {
    const baseStyle = {
      borderRadius: theme.borderRadius.medium,
      alignItems: 'center',
      justifyContent: 'center',
      ...this.getSizeStyle(size, theme),
    };

    switch (variant) {
      case 'primary':
        return {
          ...baseStyle,
          backgroundColor: theme.colors.primary,
        };
      case 'secondary':
        return {
          ...baseStyle,
          backgroundColor: theme.colors.secondary,
        };
      case 'outline':
        return {
          ...baseStyle,
          backgroundColor: 'transparent',
          borderWidth: 1,
          borderColor: theme.colors.primary,
        };
      default:
        return baseStyle;
    }
  }
}
```

## Performance Considerations

### HTTP Optimization

- **Request Caching**: Cache GET requests to reduce network calls
- **Request Deduplication**: Prevent duplicate simultaneous requests
- **Retry Logic**: Automatic retry with exponential backoff

### Storage Optimization

- **Cache Management**: Automatic cleanup of expired cache entries
- **Storage Limits**: Monitor and manage storage usage
- **Compression**: Compress large cached data

### UI Performance

- **Component Memoization**: Memoize expensive component renders
- **Image Optimization**: Optimize and cache images
- **Animation Performance**: Use native animations where possible

## Anti-Patterns to Avoid

❌ **Business domain logic in infrastructure**
❌ **Module-specific knowledge in shared components**
❌ **Tight coupling between infrastructure and business logic**
❌ **Exposing implementation details in module API**
❌ **Platform-specific code in shared components**

## Module Evolution

This module can be extended with:

- **Advanced Caching**: Redis integration, cache strategies
- **Offline Support**: Advanced offline synchronization
- **Performance Monitoring**: APM integration, performance metrics
- **Accessibility**: Enhanced accessibility features
- **Internationalization**: Multi-language support

The infrastructure module provides a stable foundation that allows other modules to focus on business logic while abstracting away technical complexity.
