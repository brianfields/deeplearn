/**
 * Learning Session Repository
 *
 * HTTP client and local storage orchestrator for learning session data.
 * Coordinates AsyncStorage, offline cache outbox, and server sync flows so
 * services can focus purely on business rules and DTO mapping.
 */

import { infrastructureProvider } from '../infrastructure/public';
import { offlineCacheProvider } from '../offline_cache/public';
import type {
  LearningSession,
  SessionProgress,
  SessionResults,
  StartSessionRequest,
  UpdateProgressRequest,
  CompleteSessionRequest,
  SessionFilters,
  LearningSessionError,
} from './models';
import type { OutboxRequest } from '../offline_cache/public';

// API wire types (matching future backend)
interface ApiLearningSession {
  id: string;
  lesson_id: string;
  user_id?: string;
  status: 'active' | 'completed' | 'paused' | 'abandoned';
  started_at: string;
  completed_at?: string;
  current_exercise_index: number;
  total_exercises: number;
  progress_percentage: number;
  session_data: Record<string, any>;
}

interface ApiSessionProgress {
  session_id: string;
  exercise_id: string;
  exercise_type: string;
  started_at: string;
  completed_at?: string;
  is_correct?: boolean;
  user_answer?: any;
  time_spent_seconds: number;
  attempts: number;
}

interface ApiSessionResults {
  session_id: string;
  lesson_id: string;
  total_exercises: number;
  completed_exercises: number;
  correct_exercises: number;
  total_time_seconds: number;
  completion_percentage: number;
  score_percentage: number;
  achievements: string[];
}

interface ApiSessionListResponse {
  sessions: ApiLearningSession[];
  total: number;
}

interface SaveSessionOptions {
  enqueueOutbox?: boolean;
  idempotencyKey?: string;
  updateIndex?: boolean;
}

type CompletionProgressPayload = {
  exercise_id: string;
  exercise_type: string;
  user_answer: any;
  is_correct: boolean | undefined;
  time_spent_seconds: number;
};

const LEARNING_SESSION_BASE = '/api/v1/learning_session';

export class LearningSessionRepo {
  private infrastructure = infrastructureProvider();
  private offlineCache = offlineCacheProvider();

  // ================================
  // Storage Helpers
  // ================================

  private getSessionKey(sessionId: string): string {
    return `learning_session_${sessionId}`;
  }

  private getSessionResultsKey(sessionId: string): string {
    return `session_results_${sessionId}`;
  }

  private getProgressKey(sessionId: string, exerciseId: string): string {
    return `session_progress_${sessionId}_${exerciseId}`;
  }

  private getProgressIndexKey(sessionId: string): string {
    return `session_progress_index_${sessionId}`;
  }

  private getUserSessionIndexKey(userId: string): string {
    return `user_session_index_${userId}`;
  }

  private async readJson<T>(key: string): Promise<T | null> {
    const stored = await this.infrastructure.getStorageItem(key);
    if (!stored) {
      return null;
    }
    try {
      return JSON.parse(stored) as T;
    } catch (error) {
      console.warn('[LearningSessionRepo] Failed to parse storage item', {
        key,
        error,
      });
      return null;
    }
  }

  private async writeJson(key: string, value: unknown): Promise<void> {
    await this.infrastructure.setStorageItem(key, JSON.stringify(value));
  }

  private async removeItem(key: string): Promise<void> {
    await this.infrastructure.removeStorageItem(key);
  }

  private async updateIndex(key: string, id: string): Promise<string[]> {
    const existing = await this.readJson<string[]>(key);
    const items = Array.isArray(existing) ? existing : [];
    if (!items.includes(id)) {
      items.push(id);
      await this.writeJson(key, items);
    }
    return items;
  }

  private buildStartSessionOutbox(
    session: LearningSession,
    idempotencyKey?: string
  ): OutboxRequest | null {
    if (!session.userId) {
      return null;
    }
    return {
      endpoint: `${LEARNING_SESSION_BASE}/`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      payload: {
        lesson_id: session.lessonId,
        user_id: session.userId,
        session_id: session.id,
      },
      idempotencyKey: idempotencyKey ?? `start-session-${session.id}`,
    };
  }

  private buildCompletionOutbox(
    sessionId: string,
    userId: string | null,
    lessonId: string | null,
    progressUpdates: CompletionProgressPayload[],
    idempotencyKey?: string
  ): OutboxRequest {
    const endpoint = new URL(
      `${LEARNING_SESSION_BASE}/${sessionId}/complete`,
      'http://localhost'
    );
    if (userId) {
      endpoint.searchParams.set('user_id', userId);
    }

    return {
      endpoint: endpoint.pathname + endpoint.search,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      payload: {
        progress_updates: progressUpdates,
        lesson_id: lessonId, // Include lesson_id so backend can create session if needed
      },
      idempotencyKey:
        idempotencyKey ?? `complete-${sessionId}-${Date.now().toString()}`,
    };
  }

  // ================================
  // Local Storage Operations
  // ================================

  async saveSession(
    session: LearningSession,
    options: SaveSessionOptions = {}
  ): Promise<void> {
    await this.writeJson(this.getSessionKey(session.id), session);

    const shouldUpdateIndex = options.updateIndex ?? true;
    if (shouldUpdateIndex && session.userId) {
      await this.addToUserSessionIndex(session.userId, session.id);
    }

    if (options.enqueueOutbox) {
      const outbox = this.buildStartSessionOutbox(
        session,
        options.idempotencyKey
      );
      if (outbox) {
        await this.offlineCache.enqueueOutbox(outbox);
      }
    }
  }

  async getSession(sessionId: string): Promise<LearningSession | null> {
    return this.readJson<LearningSession>(this.getSessionKey(sessionId));
  }

  async saveProgress(
    sessionId: string,
    progress: SessionProgress
  ): Promise<void> {
    await this.writeJson(
      this.getProgressKey(sessionId, progress.exerciseId),
      progress
    );
    await this.updateIndex(
      this.getProgressIndexKey(sessionId),
      progress.exerciseId
    );
  }

  async getProgress(
    sessionId: string,
    exerciseId: string
  ): Promise<SessionProgress | null> {
    return this.readJson<SessionProgress>(
      this.getProgressKey(sessionId, exerciseId)
    );
  }

  async getAllProgress(sessionId: string): Promise<SessionProgress[]> {
    const index =
      (await this.readJson<string[]>(this.getProgressIndexKey(sessionId))) ??
      [];
    const progresses: SessionProgress[] = [];
    for (const exerciseId of index) {
      const progress = await this.getProgress(sessionId, exerciseId);
      if (progress) {
        progresses.push(progress);
      }
    }
    return progresses;
  }

  async clearProgress(sessionId: string): Promise<void> {
    const index =
      (await this.readJson<string[]>(this.getProgressIndexKey(sessionId))) ??
      [];
    for (const exerciseId of index) {
      await this.removeItem(this.getProgressKey(sessionId, exerciseId));
    }
    await this.removeItem(this.getProgressIndexKey(sessionId));
  }

  async getUserSessionIds(userId: string): Promise<string[]> {
    return (
      (await this.readJson<string[]>(this.getUserSessionIndexKey(userId))) ?? []
    );
  }

  async addToUserSessionIndex(
    userId: string,
    sessionId: string
  ): Promise<void> {
    await this.updateIndex(this.getUserSessionIndexKey(userId), sessionId);
  }

  async getUserSessions(
    userId: string,
    filters: SessionFilters = {},
    limit: number = 50
  ): Promise<{ sessions: LearningSession[]; total: number }> {
    const sessionIds = await this.getUserSessionIds(userId);
    const sessions: LearningSession[] = [];

    for (const sessionId of sessionIds) {
      const session = await this.getSession(sessionId);
      if (!session) {
        continue;
      }
      if (filters.status && session.status !== filters.status) {
        continue;
      }
      if (filters.lessonId && session.lessonId !== filters.lessonId) {
        continue;
      }
      sessions.push(session);
    }

    sessions.sort((a, b) => {
      const dateA = new Date(b.startedAt).getTime();
      const dateB = new Date(a.startedAt).getTime();
      return dateA - dateB;
    });

    return {
      sessions: sessions.slice(0, limit),
      total: sessions.length,
    };
  }

  async saveSessionResults(
    sessionId: string,
    results: SessionResults
  ): Promise<void> {
    await this.writeJson(this.getSessionResultsKey(sessionId), results);
  }

  async enqueueSessionCompletion(
    sessionId: string,
    userId: string | null,
    progressUpdates: CompletionProgressPayload[],
    idempotencyKey?: string
  ): Promise<void> {
    // Look up session locally to get lesson_id for backend
    const session = await this.getSession(sessionId);
    const lessonId = session?.lessonId ?? null;

    const outbox = this.buildCompletionOutbox(
      sessionId,
      userId,
      lessonId,
      progressUpdates,
      idempotencyKey
    );
    await this.offlineCache.enqueueOutbox(outbox);
  }

  async syncSessionsFromServer(
    userId: string,
    transform?: (
      apiSession: ApiLearningSession
    ) => Promise<LearningSession | null>
  ): Promise<number> {
    const response = await this.fetchUserSessions(userId, {}, 100, 0);
    let saved = 0;
    for (const apiSession of response.sessions) {
      const mapped = transform ? await transform(apiSession) : null;
      const session = mapped ?? this.mapApiSession(apiSession);
      if (!session) {
        continue;
      }
      await this.saveSession(session, { enqueueOutbox: false });
      saved += 1;
    }
    return saved;
  }

  private mapApiSession(api: ApiLearningSession): LearningSession {
    const remainingExercises = Math.max(
      0,
      api.total_exercises - api.current_exercise_index
    );
    const estimatedTimeRemaining = remainingExercises * 3 * 60;
    return {
      id: api.id,
      lessonId: api.lesson_id,
      userId: api.user_id,
      status: api.status,
      startedAt: api.started_at,
      completedAt: api.completed_at,
      currentExerciseIndex: api.current_exercise_index,
      totalExercises: api.total_exercises,
      progressPercentage: api.progress_percentage,
      sessionData: api.session_data,
      estimatedTimeRemaining,
      isCompleted: api.status === 'completed',
      canResume: api.status === 'active' || api.status === 'paused',
    };
  }

  // ================================
  // HTTP Operations
  // ================================

  /**
   * Start a new learning session
   */
  async startSession(
    request: StartSessionRequest
  ): Promise<ApiLearningSession> {
    try {
      if (!request.userId) {
        throw new Error('userId is required to start a learning session');
      }
      const response = await this.infrastructure.request<ApiLearningSession>(
        `${LEARNING_SESSION_BASE}/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            lesson_id: request.lessonId,
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
   * Fetch session by ID from server
   */
  async fetchSession(
    sessionId: string,
    userId: string
  ): Promise<ApiLearningSession | null> {
    try {
      const params = new URLSearchParams();
      params.append('user_id', userId);
      const query = params.toString();
      const endpoint = `${LEARNING_SESSION_BASE}/${sessionId}${
        query ? `?${query}` : ''
      }`;

      const response = await this.infrastructure.request<ApiLearningSession>(
        endpoint,
        { method: 'GET' }
      );
      return response;
    } catch (error) {
      if (
        error &&
        typeof error === 'object' &&
        'status' in error &&
        (error as { status?: number }).status === 404
      ) {
        return null;
      }
      throw this.handleError(error, `Failed to get session ${sessionId}`);
    }
  }

  /**
   * Update session progress via HTTP
   */
  async updateProgress(
    request: UpdateProgressRequest
  ): Promise<ApiSessionProgress> {
    try {
      if (!request.userId) {
        throw new Error(
          'userId is required to update learning session progress'
        );
      }
      const response = await this.infrastructure.request<ApiSessionProgress>(
        `${LEARNING_SESSION_BASE}/${request.sessionId}/progress`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            exercise_id: request.exerciseId,
            exercise_type: request.exerciseType,
            user_answer:
              request.userAnswer === null || request.userAnswer === undefined
                ? null
                : typeof request.userAnswer === 'object'
                  ? request.userAnswer
                  : { value: request.userAnswer },
            is_correct: request.isCorrect,
            time_spent_seconds: request.timeSpentSeconds,
            user_id: request.userId,
          }),
        }
      );
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to update progress');
    }
  }

  /**
   * Complete session and get results via HTTP
   */
  async completeSession(
    request: CompleteSessionRequest
  ): Promise<ApiSessionResults> {
    try {
      if (!request.userId) {
        throw new Error('userId is required to complete a learning session');
      }
      const params = new URLSearchParams();
      if (request.userId) {
        params.append('user_id', request.userId);
      }
      const query = params.toString();
      const endpoint = `${LEARNING_SESSION_BASE}/${request.sessionId}/complete${
        query ? `?${query}` : ''
      }`;

      const response = await this.infrastructure.request<ApiSessionResults>(
        endpoint,
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
   * Pause session via HTTP
   */
  async pauseSession(
    sessionId: string,
    userId: string
  ): Promise<ApiLearningSession> {
    try {
      if (!userId) {
        throw new Error('userId is required to pause a learning session');
      }
      const params = new URLSearchParams();
      params.append('user_id', userId);

      const response = await this.infrastructure.request<ApiLearningSession>(
        `${LEARNING_SESSION_BASE}/${sessionId}/pause?${params.toString()}`,
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
  // HTTP Helpers
  // ================================

  private async fetchUserSessions(
    userId: string,
    filters: SessionFilters = {},
    limit: number = 50,
    offset: number = 0
  ): Promise<ApiSessionListResponse> {
    try {
      const params = new URLSearchParams();
      params.append('user_id', userId);
      if (filters.status) params.append('status', filters.status);
      if (filters.lessonId) params.append('lesson_id', filters.lessonId);
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

  // ================================
  // Error Handling
  // ================================

  private handleError(
    error: any,
    defaultMessage: string
  ): LearningSessionError {
    console.error('[LearningSessionRepo]', defaultMessage, error);

    if (error && typeof error === 'object') {
      if ((error as { code?: string }).code === 'INFRASTRUCTURE_ERROR') {
        const infraError = error as {
          code: string;
          message?: string;
          details?: unknown;
        };
        return {
          code: 'LEARNING_SESSION_ERROR',
          message: infraError.message || defaultMessage,
          details: infraError.details,
        };
      }
    }

    return {
      code: 'LEARNING_SESSION_ERROR',
      message: defaultMessage,
      details: error,
    };
  }
}
