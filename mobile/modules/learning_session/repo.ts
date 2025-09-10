/**
 * Learning Session Repository
 *
 * HTTP client for learning session API endpoints.
 * Uses infrastructure module for HTTP requests.
 *
 * Note: Backend endpoints are not yet implemented.
 * This repo provides the interface for future backend integration.
 */

import { infrastructureProvider } from '../infrastructure/public';
import type {
  StartSessionRequest,
  UpdateProgressRequest,
  CompleteSessionRequest,
  SessionFilters,
  LearningSessionError,
} from './models';

// API wire types (matching future backend)
interface ApiLearningSession {
  id: string;
  topic_id: string;
  user_id?: string;
  status: 'active' | 'completed' | 'paused' | 'abandoned';
  started_at: string;
  completed_at?: string;
  current_component_index: number;
  total_components: number;
  progress_percentage: number;
  session_data: Record<string, any>;
}

interface ApiSessionProgress {
  session_id: string;
  component_id: string;
  component_type: string;
  started_at: string;
  completed_at?: string;
  is_correct?: boolean;
  user_answer?: any;
  time_spent_seconds: number;
  attempts: number;
}

interface ApiSessionResults {
  session_id: string;
  topic_id: string;
  total_components: number;
  completed_components: number;
  correct_answers: number;
  total_time_seconds: number;
  completion_percentage: number;
  score_percentage: number;
  achievements: string[];
}

interface ApiSessionListResponse {
  sessions: ApiLearningSession[];
  total: number;
}

// API endpoints (future)

const LEARNING_SESSION_BASE = '/api/v1/sessions';

export class LearningSessionRepo {
  private infrastructure = infrastructureProvider();

  /**
   * Start a new learning session
   */
  async startSession(
    request: StartSessionRequest
  ): Promise<ApiLearningSession> {
    try {
      const response = await this.infrastructure.request<ApiLearningSession>(
        `${LEARNING_SESSION_BASE}/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            topic_id: request.topicId,
            user_id: request.userId,
          }),
        }
      );
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to start session');
    }
  }

  /**
   * Get session by ID
   */
  async getSession(sessionId: string): Promise<ApiLearningSession | null> {
    try {
      const response = await this.infrastructure.request<ApiLearningSession>(
        `${LEARNING_SESSION_BASE}/${sessionId}`,
        { method: 'GET' }
      );
      return response;
    } catch (error) {
      if (
        error &&
        typeof error === 'object' &&
        'status' in error &&
        error.status === 404
      ) {
        return null;
      }
      throw this.handleError(error, `Failed to get session ${sessionId}`);
    }
  }

  /**
   * Update session progress
   */
  async updateProgress(
    request: UpdateProgressRequest
  ): Promise<ApiSessionProgress> {
    try {
      const response = await this.infrastructure.request<ApiSessionProgress>(
        `${LEARNING_SESSION_BASE}/${request.sessionId}/progress`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            component_id: request.componentId,
            user_answer: request.userAnswer,
            is_correct: request.isCorrect,
            time_spent_seconds: request.timeSpentSeconds,
          }),
        }
      );
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to update progress');
    }
  }

  /**
   * Complete session and get results
   */
  async completeSession(
    request: CompleteSessionRequest
  ): Promise<ApiSessionResults> {
    try {
      const response = await this.infrastructure.request<ApiSessionResults>(
        `${LEARNING_SESSION_BASE}/${request.sessionId}/complete`,
        {
          method: 'POST',
        }
      );
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to complete session');
    }
  }

  /**
   * Get user's sessions with filters
   */
  async getUserSessions(
    userId?: string,
    filters: SessionFilters = {},
    limit: number = 50,
    offset: number = 0
  ): Promise<ApiSessionListResponse> {
    try {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      if (filters.status) params.append('status', filters.status);
      if (filters.topicId) params.append('topic_id', filters.topicId);
      params.append('limit', limit.toString());
      params.append('offset', offset.toString());

      const response =
        await this.infrastructure.request<ApiSessionListResponse>(
          `${LEARNING_SESSION_BASE}?${params.toString()}`,
          { method: 'GET' }
        );
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to get user sessions');
    }
  }

  /**
   * Pause/resume session
   */
  async pauseSession(sessionId: string): Promise<ApiLearningSession> {
    try {
      const response = await this.infrastructure.request<ApiLearningSession>(
        `${LEARNING_SESSION_BASE}/${sessionId}/pause`,
        { method: 'POST' }
      );
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to pause session');
    }
  }

  /**
   * Check health of session service
   */
  async checkHealth(): Promise<boolean> {
    try {
      await this.infrastructure.request<{ status: string }>(
        `${LEARNING_SESSION_BASE}/health`,
        { method: 'GET' }
      );
      return true;
    } catch (error) {
      console.warn('[LearningSessionRepo] Health check failed:', error);
      return false;
    }
  }

  // ================================
  // Error Handling
  // ================================

  /**
   * Handle and transform repository errors
   */
  private handleError(
    error: any,
    defaultMessage: string
  ): LearningSessionError {
    console.error('[LearningSessionRepo]', defaultMessage, error);

    // If it's already a structured error from infrastructure
    if (error && typeof error === 'object') {
      if (error.code === 'INFRASTRUCTURE_ERROR') {
        return {
          code: 'LEARNING_SESSION_ERROR',
          message: error.message || defaultMessage,
          details: error.details,
        };
      }
    }

    // Generic error
    return {
      code: 'LEARNING_SESSION_ERROR',
      message: defaultMessage,
      details: error,
    };
  }
}
