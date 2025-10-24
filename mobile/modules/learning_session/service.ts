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
import { toLearningSessionDTO } from './models';

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

  // ================================
  // Private Helper Methods (defined first for use throughout)
  // ================================

  private generateSessionId(): string {
    // Generate a UUID-like session ID
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
  }

  /**
   * Start a new learning session for a lesson
   * Creates session locally first, syncs to server via outbox
   */
  async startSession(request: StartSessionRequest): Promise<LearningSession> {
    try {
      // Validate lesson exists and get lesson details
      const lessonDetail = await this.catalog.getLessonDetail(request.lessonId);
      if (!lessonDetail) {
        throw new Error(`Lesson ${request.lessonId} not found`);
      }

      const userId = await this.resolveUserId(request.userId);

      // Generate session ID locally
      const sessionId = this.generateSessionId();

      // Count exercises from lesson detail
      const totalExercises = lessonDetail.exercises?.length || 0;

      // Create session locally
      const session: LearningSession = {
        id: sessionId,
        lessonId: request.lessonId,
        lessonTitle: lessonDetail.title,
        userId,
        status: 'active',
        startedAt: new Date().toISOString(),
        completedAt: undefined,
        currentExerciseIndex: 0,
        totalExercises,
        progressPercentage: 0,
        sessionData: {},
        estimatedTimeRemaining: totalExercises * 3 * 60, // 3 min per exercise
        isCompleted: false,
        canResume: true,
      };

      // Store locally
      await this.infrastructure.setStorageItem(
        `learning_session_${session.id}`,
        JSON.stringify(session)
      );

      // Add to user's session index
      if (session.userId) {
        await this.addToLocalSessionIndex(session.userId, session.id);
      }

      // Enqueue creation to server
      await this.offlineCache.enqueueOutbox({
        endpoint: `${LEARNING_SESSION_BASE}/`,
        method: 'POST',
        payload: {
          lesson_id: request.lessonId,
          user_id: userId,
          session_id: sessionId, // Pass our local ID to server
        },
        headers: { 'Content-Type': 'application/json' },
        idempotencyKey: `start-session-${sessionId}`,
      });

      return session;
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to start learning session');
    }
  }

  /**
   * Get session by ID
   * LOCAL-FIRST: Always reads from local storage
   */
  async getSession(sessionId: string): Promise<LearningSession | null> {
    try {
      // Read from local storage (fast, works offline)
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
   * Note: Progress is now stored locally and sent in batch on completion
   */
  async updateProgress(
    request: UpdateProgressRequest
  ): Promise<SessionProgress> {
    const normalizedAnswer =
      request.userAnswer === null || request.userAnswer === undefined
        ? null
        : typeof request.userAnswer === 'object'
          ? request.userAnswer
          : { value: request.userAnswer };

    // Build optimistic progress immediately (no network call)
    const progress = this.buildOptimisticProgress(request, normalizedAnswer);

    // Store locally only
    await this.updateLocalSessionProgress(request.sessionId, progress);

    return progress;
  }

  /**
   * Complete session and get results
   * Note: All progress is batched and sent with the completion request
   */
  async completeSession(
    request: CompleteSessionRequest
  ): Promise<SessionResults> {
    const userId = await this.resolveSessionUserId(
      request.sessionId,
      request.userId
    );

    // Collect all pending progress updates
    const progressUpdates = await this.collectPendingProgress(
      request.sessionId
    );

    const endpoint = new URL(
      `${LEARNING_SESSION_BASE}/${request.sessionId}/complete`,
      'http://localhost'
    );
    if (userId) {
      endpoint.searchParams.set('user_id', userId);
    }

    // Single outbox entry with all progress data
    await this.offlineCache.enqueueOutbox({
      endpoint: endpoint.pathname + endpoint.search,
      method: 'POST',
      payload: {
        progress_updates: progressUpdates,
      },
      headers: { 'Content-Type': 'application/json' },
      idempotencyKey: `complete-${request.sessionId}-${Date.now()}`,
    });

    // Build optimistic results (no network call)
    const results = await this.buildOptimisticResults(request.sessionId);
    await this.markSessionCompleted(request.sessionId, results);

    // Clean up local progress data
    await this.clearSessionProgressData(request.sessionId);

    return results;
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

      // Add to user's session index
      if (session.userId) {
        await this.addToLocalSessionIndex(session.userId, session.id);
      }

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
   * Always uses local storage for fast, reliable access
   */
  async getUserSessions(
    userId?: string,
    filters: SessionFilters = {},
    limit: number = 50,
    _offset: number = 0
  ): Promise<{ sessions: LearningSession[]; total: number }> {
    try {
      const resolvedUserId = await this.resolveUserId(userId);
      return this.getLocalUserSessions(resolvedUserId, filters, limit);
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to get user sessions');
    }
  }

  /**
   * Sync sessions from server and update local storage
   * Call this explicitly when you want to pull latest data from server
   */
  async syncSessionsFromServer(userId?: string): Promise<void> {
    try {
      const resolvedUserId = await this.resolveUserId(userId);

      const apiResponse = await this.repo.getUserSessions(
        resolvedUserId,
        {},
        100, // Get a reasonable batch
        0
      );

      // Store each session locally and add to index
      for (const apiSession of apiResponse.sessions) {
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
          `learning_session_${session.id}`,
          JSON.stringify(session)
        );

        if (session.userId) {
          await this.addToLocalSessionIndex(session.userId, session.id);
        }
      }

      console.info(
        `[LearningSessionService] Synced ${apiResponse.sessions.length} sessions from server`
      );
    } catch (error) {
      console.warn('[LearningSessionService] Failed to sync sessions:', error);
      // Don't throw - sync failures shouldn't break the app
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

    // Collect progress data to calculate actual score
    const exercises = await this.getSessionExercises(sessionId);
    let correctExercises = 0;
    let completedExercises = 0;
    let totalTimeSeconds = 0;

    for (const exercise of exercises) {
      const progressKey = `session_progress_${sessionId}_${exercise.id}`;
      const progressData =
        await this.infrastructure.getStorageItem(progressKey);

      if (progressData) {
        try {
          const progress: SessionProgress = JSON.parse(progressData);
          if (progress.isCompleted) {
            completedExercises++;
            if (progress.isCorrect === true) {
              correctExercises++;
            }
            totalTimeSeconds += progress.timeSpentSeconds || 0;
          }
        } catch (error) {
          console.warn(
            `Failed to parse progress for exercise ${exercise.id}:`,
            error
          );
        }
      }
    }

    const completionPercentage = totalExercises
      ? Math.round((completedExercises / totalExercises) * 100)
      : 0;
    const scorePercentage = totalExercises
      ? Math.round((correctExercises / totalExercises) * 100)
      : 0;

    // Calculate grade based on score
    let grade: 'A' | 'B' | 'C' | 'D' | 'F';
    if (scorePercentage >= 90) {
      grade = 'A';
    } else if (scorePercentage >= 80) {
      grade = 'B';
    } else if (scorePercentage >= 70) {
      grade = 'C';
    } else if (scorePercentage >= 60) {
      grade = 'D';
    } else {
      grade = 'F';
    }

    const minutes = Math.floor(totalTimeSeconds / 60);
    const seconds = totalTimeSeconds % 60;
    const timeDisplay = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;

    return {
      sessionId,
      lessonId: session?.lessonId ?? '',
      totalExercises,
      completedExercises,
      correctExercises,
      totalTimeSeconds,
      completionPercentage,
      scorePercentage,
      achievements: [],
      grade,
      timeDisplay,
      performanceSummary: `You got ${correctExercises} out of ${totalExercises} correct.`,
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

      // Add to user's session index
      if (updatedSession.userId) {
        await this.addToLocalSessionIndex(
          updatedSession.userId,
          updatedSession.id
        );
      }

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

      // Add to user's session index
      if (completedSession.userId) {
        await this.addToLocalSessionIndex(
          completedSession.userId,
          completedSession.id
        );
      }

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
   * Collect all pending progress updates for a session
   */
  private async collectPendingProgress(sessionId: string): Promise<
    Array<{
      exercise_id: string;
      exercise_type: string;
      user_answer: any;
      is_correct: boolean | undefined;
      time_spent_seconds: number;
    }>
  > {
    const session = await this.getSession(sessionId);
    if (!session) {
      return [];
    }

    const exercises = await this.getSessionExercises(sessionId);
    const progressUpdates = [];

    for (const exercise of exercises) {
      const progressKey = `session_progress_${sessionId}_${exercise.id}`;
      const progressData =
        await this.infrastructure.getStorageItem(progressKey);

      if (progressData) {
        try {
          const progress: SessionProgress = JSON.parse(progressData);
          progressUpdates.push({
            exercise_id: progress.exerciseId,
            exercise_type: progress.exerciseType,
            user_answer: progress.userAnswer,
            is_correct: progress.isCorrect,
            time_spent_seconds: progress.timeSpentSeconds,
          });
        } catch (error) {
          console.warn(
            `Failed to parse progress for exercise ${exercise.id}:`,
            error
          );
        }
      }
    }

    return progressUpdates;
  }

  /**
   * Clear all session progress data after completion
   */
  private async clearSessionProgressData(sessionId: string): Promise<void> {
    try {
      const session = await this.getSession(sessionId);
      if (!session) {
        return;
      }

      const exercises = await this.getSessionExercises(sessionId);

      // Remove progress data for each exercise
      for (const exercise of exercises) {
        const progressKey = `session_progress_${sessionId}_${exercise.id}`;
        await this.infrastructure.removeStorageItem(progressKey);
      }
    } catch (error) {
      console.warn('Failed to clear session progress data:', error);
    }
  }

  /**
   * Get all locally stored session IDs for a user
   * Maintains an index of session IDs per user for efficient querying
   */
  private async getLocalSessionIds(userId: string): Promise<string[]> {
    const indexKey = `user_session_index_${userId}`;
    const stored = await this.infrastructure.getStorageItem(indexKey);
    if (stored) {
      try {
        return JSON.parse(stored) as string[];
      } catch (error) {
        console.warn('Failed to parse local session index:', error);
      }
    }
    return [];
  }

  /**
   * Add a session ID to the user's local session index
   */
  private async addToLocalSessionIndex(
    userId: string,
    sessionId: string
  ): Promise<void> {
    const indexKey = `user_session_index_${userId}`;
    const sessionIds = await this.getLocalSessionIds(userId);
    if (!sessionIds.includes(sessionId)) {
      sessionIds.push(sessionId);
      await this.infrastructure.setStorageItem(
        indexKey,
        JSON.stringify(sessionIds)
      );
    }
  }

  /**
   * Get user sessions from local storage only
   * Used for offline operation
   */
  private async getLocalUserSessions(
    userId: string,
    filters: SessionFilters = {},
    limit: number = 50
  ): Promise<{ sessions: LearningSession[]; total: number }> {
    const sessionIds = await this.getLocalSessionIds(userId);
    const sessions: LearningSession[] = [];

    for (const sessionId of sessionIds) {
      try {
        const stored = await this.infrastructure.getStorageItem(
          `learning_session_${sessionId}`
        );
        if (!stored) continue;

        const session: LearningSession = JSON.parse(stored);

        // Apply filters
        if (filters.status && session.status !== filters.status) continue;
        if (filters.lessonId && session.lessonId !== filters.lessonId) continue;

        sessions.push(session);
      } catch (error) {
        console.warn(`Failed to load local session ${sessionId}:`, error);
      }
    }

    // Sort by most recent first
    sessions.sort((a, b) => {
      const dateA = new Date(b.startedAt).getTime();
      const dateB = new Date(a.startedAt).getTime();
      return dateA - dateB;
    });

    // Apply limit
    const limitedSessions = sessions.slice(0, limit);

    return {
      sessions: limitedSessions,
      total: sessions.length,
    };
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
