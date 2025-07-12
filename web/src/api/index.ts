/**
 * API Module Index
 *
 * This file provides a clean interface to all API functionality.
 * Import everything you need from this single entry point.
 *
 * Usage:
 * ```typescript
 * import { apiClient, ConversationWebSocket } from '@/api'
 * ```
 */

// Export main API client
export { ApiClient, apiClient, createApiClient } from './client'

// Export WebSocket client
export {
  ConversationWebSocket,
  createConversationWebSocket,
  ConnectionState,
  type WebSocketConfig,
  type WebSocketHandlers
} from './websocket'

// Re-export API types for convenience
export type {
  // Client configuration
  ApiClientConfig,
  RequestConfig,
  HttpMethod,

  // Request types
  CreateLearningPathRequest,
  StartConversationRequest,
  ContinueConversationRequest,
  WebSocketClientMessage,

  // Response types
  ApiResponse,
  PaginatedResponse,
  ApiErrorResponse,
  HealthCheckResponse,
  CreateLearningPathResponse,
  GetLearningPathsResponse,
  GetLearningPathResponse,
  StartConversationResponse,
  ContinueConversationResponse,
  GetProgressResponse,

  // Status codes
  HttpStatus,
  WebSocketCloseCode
} from '@/types/api'

// Re-export error classes
export {
  ApiError,
  TimeoutError,
  NetworkError,
  WebSocketError
} from '@/types/api'