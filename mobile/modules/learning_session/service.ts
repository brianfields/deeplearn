/**
 * Learning Session Service
 *
 * Business logic for learning session management, progress tracking, and session orchestration.
 * Returns DTOs only, never raw API responses.
 * Refactored from src/services/learning-service.ts with modular architecture.
 */

import { LearningSessionRepo } from './repo';
import { topicCatalogProvider } from '../topic_catalog/public';
import { infrastructureProvider } from '../infrastructure/public';
import type {
  LearningSession,
  SessionProgress,
  SessionResults,
  ComponentState,
  StartSessionRequest,
  UpdateProgressRequest,
  CompleteSessionRequest,
  SessionFilters,
  LearningSessionError,
} from './models';
import {
  toLearningSessionDTO,
  toSessionProgressDTO,
  toSessionResultsDTO,
} from './models';

export class LearningSessionService {
  private repo: LearningSessionRepo;
  private topicCatalog = topicCatalogProvider();
  private infrastructure = infrastructureProvider();

  constructor(repo: LearningSessionRepo) {
    this.repo = repo;
  }

  /**
   * Start a new learning session for a topic
   */
  async startSession(request: StartSessionRequest): Promise<LearningSession> {
    try {
      // Validate topic exists
      const topicDetail = await this.topicCatalog.getTopicDetail(
        request.topicId
      );
      if (!topicDetail) {
        throw new Error(`Topic ${request.topicId} not found`);
      }

      // Start session via repository
      const apiSession = await this.repo.startSession(request);

      // Convert to DTO
      const session = toLearningSessionDTO(apiSession);

      // Store session locally for offline access
      await this.infrastructure.setStorageItem(
        `learning_session_${session.id}`,
        JSON.stringify(session)
      );

      return session;
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to start learning session');
    }
  }

  /**
   * Get session by ID
   */
  async getSession(sessionId: string): Promise<LearningSession | null> {
    try {
      // Try to get from API first
      const apiSession = await this.repo.getSession(sessionId);
      if (apiSession) {
        return toLearningSessionDTO(apiSession);
      }

      // Fallback to local storage for offline access
      const stored = await this.infrastructure.getStorageItem(
        `learning_session_${sessionId}`
      );
      if (stored) {
        return JSON.parse(stored) as LearningSession;
      }

      return null;
    } catch (error) {
      throw this.handleServiceError(
        error,
        `Failed to get session ${sessionId}`
      );
    }
  }

  /**
   * Update progress for a component in the session
   */
  async updateProgress(
    request: UpdateProgressRequest
  ): Promise<SessionProgress> {
    try {
      // Update progress via repository
      const apiProgress = await this.repo.updateProgress(request);

      // Convert to DTO
      const progress = toSessionProgressDTO(apiProgress);

      // Update local session cache
      await this.updateLocalSessionProgress(request.sessionId, progress);

      return progress;
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to update session progress');
    }
  }

  /**
   * Complete session and get results
   */
  async completeSession(
    request: CompleteSessionRequest
  ): Promise<SessionResults> {
    try {
      // Complete session via repository
      const apiResults = await this.repo.completeSession(request);

      // Convert to DTO
      const results = toSessionResultsDTO(apiResults);

      // Update local session as completed
      await this.markSessionCompleted(request.sessionId, results);

      return results;
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to complete session');
    }
  }

  /**
   * Pause session
   */
  async pauseSession(sessionId: string): Promise<LearningSession> {
    try {
      const apiSession = await this.repo.pauseSession(sessionId);
      const session = toLearningSessionDTO(apiSession);

      // Update local cache
      await this.infrastructure.setStorageItem(
        `learning_session_${sessionId}`,
        JSON.stringify(session)
      );

      return session;
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to pause session');
    }
  }

  /**
   * Resume paused session
   */
  async resumeSession(sessionId: string): Promise<LearningSession> {
    try {
      // Get current session
      const session = await this.getSession(sessionId);
      if (!session) {
        throw new Error('Session not found');
      }

      if (session.status !== 'paused') {
        throw new Error('Session is not paused');
      }

      // For now, just update status locally (backend endpoint needed)
      const updatedSession: LearningSession = {
        ...session,
        status: 'active',
      };

      // Update local cache
      await this.infrastructure.setStorageItem(
        `learning_session_${sessionId}`,
        JSON.stringify(updatedSession)
      );

      return updatedSession;
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to resume session');
    }
  }

  /**
   * Get user's learning sessions with filters
   */
  async getUserSessions(
    userId?: string,
    filters: SessionFilters = {},
    limit: number = 50,
    offset: number = 0
  ): Promise<{ sessions: LearningSession[]; total: number }> {
    try {
      const apiResponse = await this.repo.getUserSessions(
        userId,
        filters,
        limit,
        offset
      );

      const sessions = apiResponse.sessions.map(toLearningSessionDTO);

      return {
        sessions,
        total: apiResponse.total,
      };
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to get user sessions');
    }
  }

  /**
   * Get session components with current state
   */
  async getSessionComponents(sessionId: string): Promise<ComponentState[]> {
    try {
      // Get session details
      const session = await this.getSession(sessionId);
      if (!session) {
        throw new Error('Session not found');
      }

      // Get topic details to get components
      const topicDetail = await this.topicCatalog.getTopicDetail(
        session.topicId
      );
      if (!topicDetail) {
        throw new Error('Topic not found');
      }

      // Convert components to component state
      const components: ComponentState[] = topicDetail.components.map(
        (component, index) => ({
          id: component.id || `component-${index}`,
          type: component.component_type as
            | 'mcq'
            | 'didactic_snippet'
            | 'glossary',
          title: component.title || `Component ${index + 1}`,
          content: component.content,
          isCompleted: index < session.currentComponentIndex,
          isCorrect: undefined, // Would be loaded from progress data
          userAnswer: undefined, // Would be loaded from progress data
          attempts: 0, // Would be loaded from progress data
          timeSpent: 0, // Would be loaded from progress data
          maxAttempts: component.component_type === 'mcq' ? 3 : undefined,
        })
      );

      return components;
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to get session components');
    }
  }

  /**
   * Check if user can start a new session for topic
   */
  async canStartSession(topicId: string, userId?: string): Promise<boolean> {
    try {
      // Check if topic exists
      const topicDetail = await this.topicCatalog.getTopicDetail(topicId);
      if (!topicDetail) {
        return false;
      }

      // Check if user has an active session for this topic
      if (userId) {
        const sessions = await this.getUserSessions(
          userId,
          {
            status: 'active',
            topicId,
          },
          1
        );

        if (sessions.sessions.length > 0) {
          return false; // Already has active session
        }
      }

      return true;
    } catch (error) {
      console.warn(
        '[LearningSessionService] Failed to check session eligibility:',
        error
      );
      return true; // Allow session start on error
    }
  }

  /**
   * Get learning statistics for user
   */
  async getUserStats(userId: string): Promise<{
    totalSessions: number;
    completedSessions: number;
    averageScore: number;
    totalTimeSpent: number;
    currentStreak: number;
  }> {
    try {
      // Get all user sessions
      const allSessions = await this.getUserSessions(userId, {}, 1000);

      const completedSessions = allSessions.sessions.filter(
        s => s.status === 'completed'
      );
      const totalTimeSpent = completedSessions.reduce((sum, s) => {
        // Estimate time spent based on progress
        return sum + (s.progressPercentage / 100) * s.estimatedTimeRemaining;
      }, 0);

      // Calculate streak (simplified - would need date-based logic)
      const currentStreak = this.calculateStreak(allSessions.sessions);

      return {
        totalSessions: allSessions.total,
        completedSessions: completedSessions.length,
        averageScore: 0, // Would need results data
        totalTimeSpent,
        currentStreak,
      };
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to get user statistics');
    }
  }

  /**
   * Check health of learning session service
   */
  async checkHealth(): Promise<boolean> {
    try {
      return await this.repo.checkHealth();
    } catch (error) {
      console.warn('[LearningSessionService] Health check failed:', error);
      return false;
    }
  }

  // ================================
  // Private Helper Methods
  // ================================

  private async updateLocalSessionProgress(
    sessionId: string,
    progress: SessionProgress
  ): Promise<void> {
    try {
      const session = await this.getSession(sessionId);
      if (!session) return;

      // Update session progress
      const updatedSession: LearningSession = {
        ...session,
        currentComponentIndex: Math.max(
          session.currentComponentIndex,
          progress.isCompleted
            ? session.currentComponentIndex + 1
            : session.currentComponentIndex
        ),
        progressPercentage: Math.min(
          100,
          ((session.currentComponentIndex + 1) / session.totalComponents) * 100
        ),
      };

      // Save updated session
      await this.infrastructure.setStorageItem(
        `learning_session_${sessionId}`,
        JSON.stringify(updatedSession)
      );

      // Save progress data
      await this.infrastructure.setStorageItem(
        `session_progress_${sessionId}_${progress.componentId}`,
        JSON.stringify(progress)
      );
    } catch (error) {
      console.warn('Failed to update local session progress:', error);
    }
  }

  private async markSessionCompleted(
    sessionId: string,
    results: SessionResults
  ): Promise<void> {
    try {
      const session = await this.getSession(sessionId);
      if (!session) return;

      const completedSession: LearningSession = {
        ...session,
        status: 'completed',
        completedAt: new Date().toISOString(),
        currentComponentIndex: session.totalComponents,
        progressPercentage: 100,
      };

      // Save completed session
      await this.infrastructure.setStorageItem(
        `learning_session_${sessionId}`,
        JSON.stringify(completedSession)
      );

      // Save results
      await this.infrastructure.setStorageItem(
        `session_results_${sessionId}`,
        JSON.stringify(results)
      );
    } catch (error) {
      console.warn('Failed to mark session as completed:', error);
    }
  }

  private calculateStreak(sessions: LearningSession[]): number {
    // Simplified streak calculation
    // In a real implementation, this would check consecutive days
    const completedSessions = sessions.filter(s => s.status === 'completed');
    return Math.min(completedSessions.length, 30); // Cap at 30 day streak
  }

  /**
   * Handle and transform service errors
   */
  private handleServiceError(
    error: any,
    defaultMessage: string
  ): LearningSessionError {
    console.error('[LearningSessionService]', defaultMessage, error);

    // If it's already a LearningSessionError, pass it through
    if (error && error.code === 'LEARNING_SESSION_ERROR') {
      return error;
    }

    // Transform other errors
    return {
      code: 'LEARNING_SESSION_ERROR',
      message: error?.message || defaultMessage,
      details: error,
    };
  }
}
