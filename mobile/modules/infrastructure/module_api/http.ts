/**
 * HTTP API for Infrastructure module
 *
 * Provides HTTP client functionality to other modules
 */

import { HttpClient } from '../adapters/http/http-client';

// Configuration for different environments
const getBaseURL = (): string => {
  if (__DEV__) {
    return 'http://192.168.4.188:8000'; // Development - Use your computer's IP for Expo Go
  }
  return 'https://your-production-api.com'; // Production
};

// Create HTTP client instance
const httpClient = new HttpClient(getBaseURL());

export function useHttpClient() {
  return {
    get: httpClient.get.bind(httpClient),
    post: httpClient.post.bind(httpClient),
    put: httpClient.put.bind(httpClient),
    delete: httpClient.delete.bind(httpClient),
    networkStatus: httpClient.networkStatus,
  };
}

export type {
  RequestConfig,
  HttpResponse,
  ApiError,
} from '../adapters/http/http-client';
