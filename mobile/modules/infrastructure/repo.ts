/**
 * Infrastructure Module - Repository Layer
 *
 * External service connections and HTTP communication.
 * Returns raw API responses.
 */

import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig } from 'axios';
import NetInfo from '@react-native-community/netinfo';
import type {
  HttpClientConfig,
  RequestConfig,
  NetworkStatus,
  ApiError,
} from './models';

export class InfrastructureRepo {
  private httpClient: AxiosInstance;
  private networkStatus: NetworkStatus = { isConnected: true };

  constructor(config: HttpClientConfig) {
    this.httpClient = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...config.headers,
      },
    });

    this.initNetworkListener();
    this.setupInterceptors();
  }

  private initNetworkListener(): void {
    try {
      if (typeof NetInfo?.addEventListener === 'function') {
        NetInfo.addEventListener(state => {
          this.networkStatus = {
            isConnected: state.isConnected ?? false,
            type: state.type,
            isInternetReachable: state.isInternetReachable ?? undefined,
          };
        });
      } else {
        console.warn(
          '[NetInfo] Not available in this runtime; assuming online'
        );
        this.networkStatus = { isConnected: true } as any;
      }
    } catch (error) {
      // Expo Go may not include this native module; fail open for dev
      console.warn('[NetInfo] Listener unavailable; assuming online');
      this.networkStatus = { isConnected: true } as any;
    }
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.httpClient.interceptors.request.use(
      config => {
        console.log(`[HTTP] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      error => Promise.reject(error)
    );

    // Response interceptor
    this.httpClient.interceptors.response.use(
      response => {
        console.log(`[HTTP] ${response.status} ${response.config.url}`);
        return response;
      },
      error => {
        console.warn(
          `[HTTP] Error ${error.response?.status} ${error.config?.url}:`,
          error.message
        );
        return Promise.reject(this.transformError(error));
      }
    );
  }

  private transformError(error: any): ApiError {
    if (error.response) {
      // Server responded with error status
      return {
        message: error.response.data?.message || error.message,
        code: error.response.data?.code || 'HTTP_ERROR',
        status: error.response.status,
        details: error.response.data,
      };
    } else if (error.request) {
      // Network error
      return {
        message: 'Network error - please check your connection',
        code: 'NETWORK_ERROR',
        status: 0,
      };
    } else {
      // Other error
      return {
        message: error.message || 'Unknown error occurred',
        code: 'UNKNOWN_ERROR',
        status: 0,
      };
    }
  }

  async request<T>(endpoint: string, config: RequestConfig = {}): Promise<T> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout,
      retryAttempts = 3,
    } = config;

    // In Expo Go, NetInfo may be unavailable; treat unknown as online
    if (this.networkStatus.isConnected === false) {
      throw new Error('No network connection available');
    }

    const axiosConfig: AxiosRequestConfig = {
      method,
      url: endpoint,
      headers,
      data: body,
      timeout: timeout || this.httpClient.defaults.timeout,
    };

    let lastError: any;

    for (let attempt = 0; attempt <= retryAttempts; attempt++) {
      try {
        const response = await this.httpClient.request(axiosConfig);
        return response.data;
      } catch (error: any) {
        lastError = error;

        // Don't retry for client errors (4xx) or on last attempt
        if (error.status >= 400 && error.status < 500) {
          break;
        }
        if (attempt === retryAttempts) {
          break;
        }

        // Exponential backoff
        const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
        await this.sleep(delay);
      }
    }

    throw lastError;
  }

  getNetworkStatus(): NetworkStatus {
    return { ...this.networkStatus };
  }

  async healthCheck(): Promise<boolean> {
    try {
      await this.request('/health', { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
