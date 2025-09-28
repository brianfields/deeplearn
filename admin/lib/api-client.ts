/**
 * Base HTTP client configuration for admin dashboard.
 *
 * Provides a configured axios instance with:
 * - Base URL pointing to backend API
 * - Request/response interceptors
 * - Error handling
 * - Authentication headers (when implemented)
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1';

// Create axios instance with base configuration
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens (when implemented)
apiClient.interceptors.request.use(
  (config) => {
    // TODO: Add authentication token when auth is implemented
    // const token = getAuthToken();
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling common errors
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle common HTTP errors
    if (error.response?.status === 401) {
      // TODO: Handle unauthorized - redirect to login
      console.error('Unauthorized access - redirect to login');
    } else if (error.response?.status === 403) {
      // TODO: Handle forbidden - show access denied message
      console.error('Access forbidden');
    } else if (error.response?.status && error.response.status >= 500) {
      // TODO: Handle server errors - show error toast
      console.error('Server error:', error.response.data);
    }

    return Promise.reject(error);
  }
);

// Helper function to handle API errors consistently
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    } else if (error.response?.data?.message) {
      return error.response.data.message;
    } else if (error.message) {
      return error.message;
    }
  }

  return 'An unexpected error occurred';
};

export default apiClient;
