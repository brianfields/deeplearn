/**
 * HTTP Client for React Native Learning App
 *
 * Provides HTTP communication with caching, retry logic, and offline support
 */

import NetInfo from '@react-native-community/netinfo';

export interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: unknown;
  timeout?: number;
  retryAttempts?: number;
}

export interface HttpResponse<T = any> {
  data: T;
  status: number;
  headers: Headers;
}

export interface ApiError {
  message: string;
  code: string;
  status: number;
  details?: any;
}

export class HttpClient {
  private baseURL: string;
  private defaultTimeout: number;
  private isOnline: boolean = true;

  constructor(baseURL: string, timeout: number = 30000) {
    this.baseURL = baseURL;
    this.defaultTimeout = timeout;
    this.initNetworkListener();
  }

  /**
   * Initialize network state listener
   */
  private initNetworkListener(): void {
    NetInfo.addEventListener(state => {
      this.isOnline = state.isConnected ?? false;
    });
  }

  /**
   * Make HTTP request with retry logic
   */
  async request<T>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<HttpResponse<T>> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = this.defaultTimeout,
      retryAttempts = 3,
    } = config;

    const url = this.buildURL(endpoint);

    // Check network status
    if (!this.isOnline) {
      throw new Error('Network unavailable');
    }

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retryAttempts; attempt++) {
      try {
        console.log(`[HTTP] ${method} ${url} (attempt ${attempt + 1})`);

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
        console.log(`[HTTP] ${method} ${url} - Success`);

        return {
          data,
          status: response.status,
          headers: response.headers,
        };
      } catch (error: any) {
        lastError = error;
        console.warn(
          `[HTTP] ${method} ${url} - Attempt ${attempt + 1} failed:`,
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
   * GET request
   */
  async get<T>(
    endpoint: string,
    config?: Omit<RequestConfig, 'method' | 'body'>
  ): Promise<HttpResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T>(
    endpoint: string,
    body?: unknown,
    config?: Omit<RequestConfig, 'method' | 'body'>
  ): Promise<HttpResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'POST', body });
  }

  /**
   * PUT request
   */
  async put<T>(
    endpoint: string,
    body?: unknown,
    config?: Omit<RequestConfig, 'method' | 'body'>
  ): Promise<HttpResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PUT', body });
  }

  /**
   * DELETE request
   */
  async delete<T>(
    endpoint: string,
    config?: Omit<RequestConfig, 'method' | 'body'>
  ): Promise<HttpResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  /**
   * Check if client is online
   */
  get networkStatus(): boolean {
    return this.isOnline;
  }

  /**
   * Build full URL from endpoint
   */
  private buildURL(endpoint: string): string {
    return endpoint.startsWith('http')
      ? endpoint
      : `${this.baseURL}${endpoint}`;
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
   * Sleep utility for retry delays
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
