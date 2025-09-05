# Infrastructure Module (Frontend)

## Purpose

This frontend module provides core technical infrastructure and shared UI components that support all other frontend modules. It handles HTTP communication, caching, shared UI components, and technical utilities without containing any business domain logic.

## Domain Responsibility

**"Providing technical infrastructure and shared UI components to all frontend modules"**

The Infrastructure frontend module owns all technical infrastructure:

- Base HTTP client and API communication
- Caching strategies and offline storage
- Shared UI components and design system
- Navigation infrastructure and routing
- Analytics and tracking services
- Error handling and logging utilities

## Architecture

### Module API (Public Interface)

```typescript
// module_api/index.ts
export { Button, Card, Progress, LoadingSpinner } from './ui';
export { useHttpClient } from './http';
export { useCache } from './cache';
export { useTheme } from './theme';
export { useAnalytics } from './analytics';
export type { Theme, CacheConfig, HttpConfig } from './types';

// module_api/ui.ts
export { Button } from '../components/Button';
export { Card } from '../components/Card';
export { Progress } from '../components/Progress';
export { LoadingSpinner } from '../components/LoadingSpinner';
export { ErrorBoundary } from '../components/ErrorBoundary';

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

// module_api/theme.ts
export function useTheme() {
  const [theme, setTheme] = useThemeStore(state => [
    state.theme,
    state.setTheme,
  ]);

  return {
    theme,
    colors: theme.colors,
    spacing: theme.spacing,
    typography: theme.typography,
    setTheme,
    toggleTheme: () =>
      setTheme(theme.mode === 'light' ? darkTheme : lightTheme),
  };
}
```

### Components (Shared UI)

```typescript
// components/Button.tsx
interface ButtonProps {
  title: string
  onPress: () => void
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  size?: 'small' | 'medium' | 'large'
  disabled?: boolean
  loading?: boolean
  icon?: string
  style?: ViewStyle
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  icon,
  style
}: ButtonProps) {
  const { theme } = useTheme()
  const buttonStyle = ButtonStyles.getButtonStyle(variant, size, theme)
  const textStyle = ButtonStyles.getTextStyle(variant, size, theme)

  return (
    <TouchableOpacity
      style={[buttonStyle, disabled && styles.disabled, style]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={ButtonStyles.getLoadingColor(variant, theme)}
        />
      ) : (
        <View style={styles.content}>
          {icon && (
            <Icon
              name={icon}
              size={ButtonStyles.getIconSize(size)}
              color={textStyle.color}
              style={styles.icon}
            />
          )}
          <Text style={textStyle}>{title}</Text>
        </View>
      )}
    </TouchableOpacity>
  )
}

// components/Card.tsx
interface CardProps {
  children: React.ReactNode
  style?: ViewStyle
  padding?: keyof Theme['spacing']
  shadow?: boolean
  borderRadius?: number
  onPress?: () => void
}

export function Card({
  children,
  style,
  padding = 'medium',
  shadow = true,
  borderRadius,
  onPress
}: CardProps) {
  const { theme } = useTheme()
  const cardStyle = CardStyles.getCardStyle(theme, {
    padding: theme.spacing[padding],
    shadow,
    borderRadius: borderRadius || theme.borderRadius.medium
  })

  const Component = onPress ? TouchableOpacity : View

  return (
    <Component
      style={[cardStyle, style]}
      onPress={onPress}
      activeOpacity={onPress ? 0.9 : 1}
    >
      {children}
    </Component>
  )
}

// components/Progress.tsx
interface ProgressProps {
  progress: number // 0-1
  color?: string
  backgroundColor?: string
  height?: number
  animated?: boolean
  showPercentage?: boolean
  style?: ViewStyle
}

export function Progress({
  progress,
  color,
  backgroundColor,
  height = 8,
  animated = true,
  showPercentage = false,
  style
}: ProgressProps) {
  const { theme } = useTheme()
  const progressValue = useSharedValue(0)

  const defaultColor = color || theme.colors.primary
  const defaultBackgroundColor = backgroundColor || theme.colors.surface

  useEffect(() => {
    if (animated) {
      progressValue.value = withSpring(progress, {
        damping: 15,
        stiffness: 150
      })
    } else {
      progressValue.value = progress
    }
  }, [progress, animated])

  const animatedStyle = useAnimatedStyle(() => ({
    width: `${progressValue.value * 100}%`
  }))

  return (
    <View style={[styles.container, style]}>
      <View
        style={[
          styles.track,
          {
            height,
            backgroundColor: defaultBackgroundColor,
            borderRadius: height / 2
          }
        ]}
      >
        <Animated.View
          style={[
            styles.fill,
            {
              height,
              backgroundColor: defaultColor,
              borderRadius: height / 2
            },
            animatedStyle
          ]}
        />
      </View>

      {showPercentage && (
        <Text style={[styles.percentage, { color: theme.colors.text }]}>
          {Math.round(progress * 100)}%
        </Text>
      )}
    </View>
  )
}

// components/LoadingSpinner.tsx
interface LoadingSpinnerProps {
  size?: 'small' | 'large'
  color?: string
  message?: string
}

export function LoadingSpinner({
  size = 'large',
  color,
  message
}: LoadingSpinnerProps) {
  const { theme } = useTheme()
  const spinnerColor = color || theme.colors.primary

  return (
    <View style={styles.container}>
      <ActivityIndicator size={size} color={spinnerColor} />
      {message && (
        <Text style={[styles.message, { color: theme.colors.textSecondary }]}>
          {message}
        </Text>
      )}
    </View>
  )
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

- **All Modules**: HTTP client, caching, shared UI components, theme system
- **Topic Catalog Module**: API client for topic endpoints
- **Learning Session Module**: Storage for session state
- **Learning Analytics Module**: Analytics tracking

### Dependencies

- **External Services**: Backend API, analytics services, secure storage
- **React Native**: Platform-specific APIs and components

### Communication Examples

```typescript
// All modules use infrastructure via module_api
import { Button, useHttpClient, useCache } from '@/modules/infrastructure';

// Topic Catalog using HTTP client
const httpClient = useHttpClient();
const topics = await httpClient.get('/api/catalog/topics');

// Learning Session using cache
const cache = useCache();
await cache.set('session-state', sessionData);
```

## Testing Strategy

### Component Tests (UI Components)

```typescript
// tests/components/Button.test.tsx
describe('Button', () => {
  it('renders with correct title', () => {
    render(<Button title="Test Button" onPress={jest.fn()} />)

    expect(screen.getByText('Test Button')).toBeTruthy()
  })

  it('calls onPress when pressed', () => {
    const mockOnPress = jest.fn()

    render(<Button title="Test" onPress={mockOnPress} />)
    fireEvent.press(screen.getByText('Test'))

    expect(mockOnPress).toHaveBeenCalled()
  })

  it('shows loading state correctly', () => {
    render(<Button title="Test" onPress={jest.fn()} loading={true} />)

    expect(screen.getByTestId('activity-indicator')).toBeTruthy()
    expect(screen.queryByText('Test')).toBeNull()
  })
})
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
