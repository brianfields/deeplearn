/**
 * API-specific types and interfaces
 *
 * This file contains types specifically for API communication,
 * including request/response formats and error handling.
 */

import type {
  LearningPath,
  LearningPathSummary,
  ConversationSession,
  Progress,
  HealthCheck,
  UserLevel,
  ChatMessage,
  WebSocketMessage
} from './index'

// ================================
// API Client Configuration
// ================================

/**
 * Configuration for the API client
 */
export interface ApiClientConfig {
  baseUrl: string
  timeout: number
  retryAttempts: number
  enableLogging: boolean
}

/**
 * HTTP methods supported by the API
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

/**
 * Request configuration for API calls
 */
export interface RequestConfig {
  method?: HttpMethod
  headers?: Record<string, string>
  body?: unknown
  timeout?: number
  retryAttempts?: number
}

// ================================
// Request Types
// ================================

/**
 * Request to create a new learning path
 */
export interface CreateLearningPathRequest {
  topic: string
  user_level: UserLevel
}

/**
 * Request to start a conversation
 */
export interface StartConversationRequest {
  path_id: string
  topic_id: string
}

/**
 * Request to continue a conversation
 */
export interface ContinueConversationRequest {
  path_id: string
  topic_id: string
}

/**
 * WebSocket message sent by client
 */
export interface WebSocketClientMessage {
  message: string
}

// ================================
// Response Types
// ================================

/**
 * Standard API response wrapper
 */
export interface ApiResponse<T = unknown> {
  data: T
  success: boolean
  message?: string
  timestamp: string
}

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
    hasNext: boolean
    hasPrev: boolean
  }
}

/**
 * Error response from API
 */
export interface ApiErrorResponse {
  error: {
    message: string
    code: string
    status: number
    details?: unknown
    timestamp: string
  }
  success: false
}

// ================================
// Endpoint Response Types
// ================================

/**
 * Response from health check endpoint
 */
export type HealthCheckResponse = ApiResponse<HealthCheck>

/**
 * Response from create learning path endpoint
 */
export type CreateLearningPathResponse = ApiResponse<LearningPath>

/**
 * Response from get learning paths endpoint
 */
export type GetLearningPathsResponse = ApiResponse<LearningPathSummary[]>

/**
 * Response from get learning path endpoint
 */
export type GetLearningPathResponse = ApiResponse<LearningPath>

/**
 * Response from start conversation endpoint
 */
export type StartConversationResponse = ApiResponse<ConversationSession>

/**
 * Response from continue conversation endpoint
 */
export type ContinueConversationResponse = ApiResponse<ConversationSession>

/**
 * Response from get progress endpoint
 */
export type GetProgressResponse = ApiResponse<Progress>

// ================================
// Error Types
// ================================

/**
 * Custom API error class
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number = 500,
    public code?: string,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }

  /**
   * Check if error is a network error
   */
  get isNetworkError(): boolean {
    return this.status === 0 || this.status >= 500
  }

  /**
   * Check if error is a client error
   */
  get isClientError(): boolean {
    return this.status >= 400 && this.status < 500
  }

  /**
   * Check if error is unauthorized
   */
  get isUnauthorized(): boolean {
    return this.status === 401
  }

  /**
   * Check if error is forbidden
   */
  get isForbidden(): boolean {
    return this.status === 403
  }

  /**
   * Check if error is not found
   */
  get isNotFound(): boolean {
    return this.status === 404
  }

  /**
   * Convert to plain object for serialization
   */
  toJSON() {
    return {
      name: this.name,
      message: this.message,
      status: this.status,
      code: this.code,
      details: this.details
    }
  }
}

/**
 * Network timeout error
 */
export class TimeoutError extends ApiError {
  constructor(timeout: number) {
    super(`Request timed out after ${timeout}ms`, 408, 'TIMEOUT')
    this.name = 'TimeoutError'
  }
}

/**
 * Network connection error
 */
export class NetworkError extends ApiError {
  constructor(message: string = 'Network connection failed') {
    super(message, 0, 'NETWORK_ERROR')
    this.name = 'NetworkError'
  }
}

/**
 * WebSocket connection error
 */
export class WebSocketError extends Error {
  constructor(
    message: string,
    public code?: number,
    public reason?: string
  ) {
    super(message)
    this.name = 'WebSocketError'
  }
}

// ================================
// Status Codes
// ================================

/**
 * HTTP status codes used by the API
 */
export enum HttpStatus {
  OK = 200,
  CREATED = 201,
  NO_CONTENT = 204,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  METHOD_NOT_ALLOWED = 405,
  CONFLICT = 409,
  UNPROCESSABLE_ENTITY = 422,
  INTERNAL_SERVER_ERROR = 500,
  BAD_GATEWAY = 502,
  SERVICE_UNAVAILABLE = 503,
  GATEWAY_TIMEOUT = 504
}

/**
 * WebSocket close codes
 */
export enum WebSocketCloseCode {
  NORMAL_CLOSURE = 1000,
  GOING_AWAY = 1001,
  PROTOCOL_ERROR = 1002,
  UNSUPPORTED_DATA = 1003,
  NO_STATUS_RECEIVED = 1005,
  ABNORMAL_CLOSURE = 1006,
  INVALID_FRAME_PAYLOAD_DATA = 1007,
  POLICY_VIOLATION = 1008,
  MESSAGE_TOO_BIG = 1009,
  MANDATORY_EXTENSION = 1010,
  INTERNAL_ERROR = 1011,
  SERVICE_RESTART = 1012,
  TRY_AGAIN_LATER = 1013,
  BAD_GATEWAY = 1014,
  TLS_HANDSHAKE = 1015
}