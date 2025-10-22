/**
 * Learning Session Service
 *
 * Business logic for learning session management, progress tracking, and session orchestration.
 * Returns DTOs only, never raw API responses.
 */

import { LearningSessionRepo } from './repo';
import { catalogProvider } from '../catalog/public';
import { infrastructureProvider } from '../infrastructure/public';
import { userIdentityProvider } from '../user/public';
import { offlineCacheProvider } from '../offline_cache/public';
import type {
  LearningSession,
  SessionProgress,
  SessionResults,
  UnitProgress,
  UnitLessonProgress,
  StartSessionRequest,
  UpdateProgressRequest,
  CompleteSessionRequest,
  SessionFilters,
  LearningSessionError,
} from './models';
import type { SessionExercise, MCQContentDTO } from './models';
import {
  toLearningSessionDTO,
  toSessionProgressDTO,
  toSessionResultsDTO,
} from './models';

const LEARNING_SESSION_BASE = '/api/v1/learning_session';

export class LearningSessionService {
  private repo: LearningSessionRepo;
  private catalog = catalogProvider();
  private infrastructure = infrastructureProvider();
  private userIdentity = userIdentityProvider();
  private offlineCache = offlineCacheProvider();

  constructor(repo: LearningSessionRepo) {
    this.repo = repo;
  }

  /**
   * Start a new learning session for a lesson
   */
  async startSession(request: StartSessionRequest): Promise<LearningSession> {
    try {
      // Validate lesson exists and get lesson details
      const lessonDetail = await this.catalog.getLessonDetail(request.lessonId);
      if (!lessonDetail) {
        throw new Error(`Lesson ${request.lessonId} not found`);
      }

      const userId = await this.resolveUserId(request.userId);

      // Start session via repository
      const apiSession = await this.repo.startSession({
        ...request,
        userId,
      });

      // Convert to DTO with lesson title
      const session = toLearningSessionDTO(apiSession, lessonDetail.title);

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
      const requestedUserId = await this.resolveSessionUserId(sessionId);

      // Try to get from API first
      const apiSession = await this.repo.getSession(sessionId, requestedUserId);
      if (apiSession) {
        // Get lesson title for display
        let lessonTitle: string | undefined;
        try {
          const lessonDetail = await this.catalog.getLessonDetail(
            apiSession.lesson_id
          );
          lessonTitle = lessonDetail?.title;
        } catch (error) {
          console.warn('Failed to fetch lesson title:', error);
        }

        const session = toLearningSessionDTO(apiSession, lessonTitle);
        await this.infrastructure.setStorageItem(
          `learning_session_${sessionId}`,
          JSON.stringify(session)
        );
        return session;
      }

      // Fallback to local storage for offline access
      const stored = await this.infrastructure.getStorageItem(
        `learning_session_${sessionId}`
      );
      if (stored) {
        try {
          const session = JSON.parse(stored) as LearningSession;
          return session;
        } catch (error) {
          console.warn('Failed to parse cached learning session:', error);
        }
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
   * Update progress for an exercise in the session
   */
  async updateProgress(
    request: UpdateProgressRequest
  ): Promise<SessionProgress> {
    const userId = await this.resolveSessionUserId(
      request.sessionId,
      request.userId
    );

    const normalizedAnswer =
      request.userAnswer === null || request.userAnswer === undefined
        ? null
        : typeof request.userAnswer === 'object'
          ? request.userAnswer
          : { value: request.userAnswer };

    await this.offlineCache.enqueueOutbox({
      endpoint: `${LEARNING_SESSION_BASE}/${request.sessionId}/progress`,
      method: 'PUT',
      payload: {
        exercise_id: request.exerciseId,
        exercise_type: request.exerciseType,
        user_answer: normalizedAnswer,
        is_correct: request.isCorrect,
        time_spent_seconds: request.timeSpentSeconds,
        user_id: userId,
      },
      headers: { 'Content-Type': 'application/json' },
      idempotencyKey: `progress-${request.sessionId}-${request.exerciseId}-${Date.now()}`,
    });

    try {
      const apiProgress = await this.repo.updateProgress({
        ...request,
        userId,
      });
      const progress = toSessionProgressDTO(apiProgress);
      await this.updateLocalSessionProgress(request.sessionId, progress);
      return progress;
    } catch (error) {
      console.warn('Falling back to optimistic progress due to error:', error);
      const fallback = this.buildOptimisticProgress(request, normalizedAnswer);
      await this.updateLocalSessionProgress(request.sessionId, fallback);
      return fallback;
    }
  }

  /**
   * Complete session and get results
   */
  async completeSession(
    request: CompleteSessionRequest
  ): Promise<SessionResults> {
    const userId = await this.resolveSessionUserId(
      request.sessionId,
      request.userId
    );

    const endpoint = new URL(
      `${LEARNING_SESSION_BASE}/${request.sessionId}/complete`,
      'http://localhost'
    );
    if (userId) {
      endpoint.searchParams.set('user_id', userId);
    }

    await this.offlineCache.enqueueOutbox({
      endpoint: endpoint.pathname + endpoint.search,
      method: 'POST',
      payload: {},
      headers: { 'Content-Type': 'application/json' },
      idempotencyKey: `complete-${request.sessionId}-${Date.now()}`,
    });

    try {
      const apiResults = await this.repo.completeSession({
        ...request,
        userId,
      });

      const results = toSessionResultsDTO(apiResults);
      await this.markSessionCompleted(request.sessionId, results);
      return results;
    } catch (error) {
      console.warn(
        'Falling back to optimistic completion due to error:',
        error
      );
      const fallback = await this.buildOptimisticResults(request.sessionId);
      await this.markSessionCompleted(request.sessionId, fallback);
      return fallback;
    }
  }

  /**
   * Pause session
   */
  async pauseSession(sessionId: string): Promise<LearningSession> {
    try {
      const userId = await this.resolveSessionUserId(sessionId);
      const apiSession = await this.repo.pauseSession(sessionId, userId);

      // Get lesson title for display
      let lessonTitle: string | undefined;
      try {
        const lessonDetail = await this.catalog.getLessonDetail(
          apiSession.lesson_id
        );
        lessonTitle = lessonDetail?.title;
      } catch (error) {
        console.warn('Failed to fetch lesson title:', error);
      }

      const session = toLearningSessionDTO(apiSession, lessonTitle);

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
      const resolvedUserId = await this.resolveUserId(userId);

      const apiResponse = await this.repo.getUserSessions(
        resolvedUserId,
        filters,
        limit,
        offset
      );

      // Get lesson titles for all sessions
      const sessions = await Promise.all(
        apiResponse.sessions.map(async apiSession => {
          let lessonTitle: string | undefined;
          try {
            const lessonDetail = await this.catalog.getLessonDetail(
              apiSession.lesson_id
            );
            lessonTitle = lessonDetail?.title;
          } catch (error) {
            console.warn('Failed to fetch lesson title:', error);
          }
          return toLearningSessionDTO(apiSession, lessonTitle);
        })
      );

      return {
        sessions,
        total: apiResponse.total,
      };
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to get user sessions');
    }
  }

  /**
   * Get session content aligned to package structure
   */
  async getSessionExercises(sessionId: string): Promise<SessionExercise[]> {
    try {
      // Get session details
      const session = await this.getSession(sessionId);
      if (!session) {
        throw new Error('Session not found');
      }

      // Get lesson details to get exercises
      const lessonDetail = await this.catalog.getLessonDetail(session.lessonId);
      if (!lessonDetail) {
        throw new Error('Lesson not found');
      }

      // Build exercise list from package (exclude non-assessment content)
      const exercises = (lessonDetail.exercises || [])
        .map((ex: any, index: number): SessionExercise | null => {
          if (ex.exercise_type !== 'mcq') {
            return null;
          }

          const options = (ex.options || []).map((opt: any) => ({
            label: opt.label,
            text: opt.text,
          }));

          const content: MCQContentDTO = {
            question: ex.stem,
            options,
            correct_answer: ex.answer_key?.label || 'A',
            explanation:
              ex.answer_key?.rationale_right ||
              `The correct answer is ${ex.answer_key?.label || 'A'}.`,
          };

          const title = ex.title
            ? ex.title
            : ex.stem
              ? ex.stem.slice(0, 50)
              : `Exercise ${index + 1}`;

          const dto: SessionExercise = {
            id: ex.id || `exercise-${index}`,
            type: 'mcq',
            title,
            content,
          };
          return dto;
        })
        .filter((e): e is SessionExercise => e !== null);

      return exercises;
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to get session exercises');
    }
  }

  /**
   * Check if user can start a new session for lesson
   */
  async canStartSession(lessonId: string, userId?: string): Promise<boolean> {
    try {
      // Check if lesson exists
      const lessonDetail = await this.catalog.getLessonDetail(lessonId);
      if (!lessonDetail) {
        return false;
      }

      const resolvedUserId = await this.resolveUserId(userId);
      const sessions = await this.getUserSessions(
        resolvedUserId,
        {
          status: 'active',
          lessonId,
        },
        1
      );

      if (sessions.sessions.length > 0) {
        return false; // Already has active session
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
      const resolvedUserId = await this.resolveUserId(userId);

      // Get all user sessions
      const allSessions = await this.getUserSessions(resolvedUserId, {}, 1000);

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

  private async resolveUserId(preferred?: string | null): Promise<string> {
    if (preferred && preferred.trim()) {
      return preferred.trim();
    }
    return this.userIdentity.getCurrentUserId();
  }

  private async resolveSessionUserId(
    sessionId: string,
    preferred?: string | null
  ): Promise<string> {
    if (preferred && preferred.trim()) {
      return preferred.trim();
    }

    try {
      const cached = await this.infrastructure.getStorageItem(
        `learning_session_${sessionId}`
      );
      if (cached) {
        const parsed = JSON.parse(cached);
        const candidate =
          typeof parsed?.userId === 'string' ? parsed.userId.trim() : null;
        if (candidate) {
          return candidate;
        }
      }
    } catch (error) {
      console.warn('Failed to resolve user id from cached session:', error);
    }

    return this.userIdentity.getCurrentUserId();
  }

  private buildOptimisticProgress(
    request: UpdateProgressRequest,
    normalizedAnswer: any
  ): SessionProgress {
    const timestamp = new Date().toISOString();
    const isCorrect = request.isCorrect ?? false;
    return {
      sessionId: request.sessionId,
      exerciseId: request.exerciseId,
      exerciseType: request.exerciseType,
      startedAt: timestamp,
      completedAt: timestamp,
      isCorrect,
      userAnswer: normalizedAnswer,
      timeSpentSeconds: request.timeSpentSeconds,
      attempts: 1,
      isCompleted: true,
      accuracy: isCorrect ? 1 : 0,
      attemptHistory: [
        {
          attemptNumber: 1,
          isCorrect,
          userAnswer: normalizedAnswer,
          timeSpentSeconds: request.timeSpentSeconds,
          submittedAt: timestamp,
        },
      ],
      hasBeenAnsweredCorrectly: isCorrect,
    };
  }

  private async buildOptimisticResults(
    sessionId: string
  ): Promise<SessionResults> {
    const session = await this.getSession(sessionId);
    const totalExercises = session?.totalExercises ?? 0;
    const completedExercises = session?.currentExerciseIndex ?? 0;
    const completionPercentage = totalExercises
      ? Math.round((completedExercises / totalExercises) * 100)
      : 0;
    return {
      sessionId,
      lessonId: session?.lessonId ?? '',
      totalExercises,
      completedExercises,
      correctExercises: 0,
      totalTimeSeconds: 0,
      completionPercentage,
      scorePercentage: completionPercentage,
      achievements: [],
      grade: 'F',
      timeDisplay: '0s',
      performanceSummary: 'Results stored locally. Sync pending.',
    };
  }

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
        currentExerciseIndex: Math.max(
          session.currentExerciseIndex,
          progress.isCompleted
            ? session.currentExerciseIndex + 1
            : session.currentExerciseIndex
        ),
        progressPercentage: Math.min(
          100,
          ((session.currentExerciseIndex + 1) / session.totalExercises) * 100
        ),
      };

      // Save updated session
      await this.infrastructure.setStorageItem(
        `learning_session_${sessionId}`,
        JSON.stringify(updatedSession)
      );

      // Save progress data
      await this.infrastructure.setStorageItem(
        `session_progress_${sessionId}_${progress.exerciseId}`,
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
        currentExerciseIndex: session.totalExercises,
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
   * Get aggregated unit progress for a user by delegating to backend
   */
  async getUnitProgress(userId: string, unitId: string): Promise<UnitProgress> {
    try {
      // For now, derive progress using lesson catalog + local heuristics if backend not available
      const unit = await this.catalog.getUnitDetail(unitId);
      if (!unit) {
        throw new Error('Unit not found');
      }

      // Compute per-lesson progress approximation using readiness (placeholder until richer data)
      const lessons: UnitLessonProgress[] = await Promise.all(
        unit.lessons.map(async l => {
          // Try to find the latest session for this lesson
          const { sessions } = await this.getUserSessions(
            userId,
            { lessonId: l.id },
            1,
            0
          );
          const s = sessions[0];
          const totalExercises = l.componentCount;
          const completedExercises = s
            ? Math.round(
                (s.progressPercentage / 100) *
                  (s.totalExercises || totalExercises)
              )
            : 0;
          const correctExercises = 0; // Unknown without results; backend provides this
          const progressPercentage = s
            ? s.progressPercentage
            : l.isReadyForLearning
              ? 0
              : 0;
          const lastActivityAt = s?.completedAt || s?.startedAt || null;
          return {
            lessonId: l.id,
            totalExercises,
            completedExercises,
            correctExercises,
            progressPercentage,
            lastActivityAt,
          };
        })
      );

      const totalLessons = lessons.length;
      const lessonsCompleted = lessons.filter(
        lp => lp.progressPercentage >= 100
      ).length;
      const avg =
        totalLessons > 0
          ? lessons.reduce((sum, lp) => sum + lp.progressPercentage, 0) /
            totalLessons
          : 0;

      return {
        unitId,
        totalLessons,
        lessonsCompleted,
        progressPercentage: avg,
        lessons,
      };
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to get unit progress');
    }
  }

  /**
   * Get the next lesson to resume within a unit, based on persistent unit session where possible.
   * Fallback: first lesson in unit that is not 100% complete.
   */
  async getNextLessonToResume(
    userId: string,
    unitId: string
  ): Promise<string | null> {
    try {
      const unit = await this.catalog.getUnitDetail(unitId);
      if (!unit) return null;

      // Prefer explicit order from unit
      const orderedLessonIds = unit.lessonIds.length
        ? unit.lessonIds
        : unit.lessons.map(l => l.id);

      // Look up progress for each lesson (latest session)
      for (const lessonId of orderedLessonIds) {
        const { sessions } = await this.getUserSessions(
          userId,
          { lessonId },
          1,
          0
        );
        const s = sessions[0];
        const total =
          s?.totalExercises ??
          unit.lessons.find(l => l.id === lessonId)?.componentCount ??
          0;
        const completed = s?.progressPercentage ?? 0;
        const isDone = total > 0 && Math.round(completed) >= 100;
        if (!isDone) return lessonId;
      }

      // If all done, return null
      return null;
    } catch (error) {
      throw this.handleServiceError(
        error,
        'Failed to get next lesson to resume'
      );
    }
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
