/**
 * Learning Session Service
 *
 * Business logic for learning session management, progress tracking, and session orchestration.
 * Returns DTOs only, never raw API responses.
 */

import { LearningSessionRepo } from './repo';
import { catalogProvider } from '../catalog/public';
import { userIdentityProvider } from '../user/public';
import type {
  LearningSession,
  SessionProgress,
  SessionResults,
  UnitProgress,
  UnitLessonProgress,
  UnitLOProgress,
  StartSessionRequest,
  UpdateProgressRequest,
  CompleteSessionRequest,
  SessionFilters,
  LearningSessionError,
} from './models';
import type { SessionExercise, MCQContentDTO } from './models';
import { toLearningSessionDTO } from './models';

export class LearningSessionService {
  private repo: LearningSessionRepo;
  private catalog = catalogProvider();
  private userIdentity = userIdentityProvider();

  constructor(repo: LearningSessionRepo) {
    this.repo = repo;
  }

  // ================================
  // Private Helper Methods (defined first for use throughout)
  // ================================

  private generateSessionId(): string {
    // Generate a proper UUID v4
    // In React Native, crypto.randomUUID() is available via the crypto polyfill
    if (
      typeof globalThis !== 'undefined' &&
      globalThis.crypto &&
      typeof globalThis.crypto.randomUUID === 'function'
    ) {
      return globalThis.crypto.randomUUID();
    }
    // Fallback UUID v4 implementation for environments without crypto.randomUUID
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  /**
   * Start a new learning session for a lesson
   * Creates session locally first, syncs to server via outbox
   */
  async startSession(request: StartSessionRequest): Promise<LearningSession> {
    try {
      if (!request.unitId?.trim()) {
        throw new Error('unitId is required to start a learning session');
      }
      // Validate lesson exists and get lesson details
      const lessonDetail = await this.catalog.getLessonDetail(request.lessonId);
      if (!lessonDetail) {
        throw new Error(`Lesson ${request.lessonId} not found`);
      }

      if (lessonDetail.unitId && lessonDetail.unitId !== request.unitId) {
        throw new Error('Lesson does not belong to the provided unit');
      }
      const unitId = lessonDetail.unitId ?? request.unitId;

      const userId = await this.resolveUserId(request.userId);

      // Generate session ID locally
      const sessionId = this.generateSessionId();

      // Count exercises from lesson detail
      const totalExercises = lessonDetail.exercises?.length || 0;

      // Create session locally
      const session: LearningSession = {
        id: sessionId,
        lessonId: request.lessonId,
        unitId,
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

      await this.repo.saveSession(session, {
        enqueueOutbox: true,
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
      return await this.repo.getSession(sessionId);
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
    await this.repo.saveProgress(request.sessionId, progress);

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

    await this.repo.enqueueSessionCompletion(
      request.sessionId,
      userId ?? null,
      progressUpdates
    );

    const session = await this.getSession(request.sessionId);
    let unitProgress: UnitLOProgress | undefined;

    if (session?.unitId) {
      try {
        const outcome = await this.buildSessionOutcome(
          session,
          progressUpdates
        );
        if (outcome) {
          await this.repo.saveSessionOutcome(outcome as any);
        }
      } catch (error) {
        console.warn(
          'Failed to persist session outcome for LO progress:',
          error
        );
      }

      try {
        unitProgress = await this.repo.computeUnitLOProgress(
          session.unitId,
          userId
        );
      } catch (error) {
        console.warn('Failed to compute unit LO progress:', error);
      }
    }

    // Build optimistic results (no network call)
    const results = await this.buildOptimisticResults(request.sessionId);
    const enrichedResults: SessionResults = {
      ...results,
      unitId: session?.unitId ?? results.unitId,
      unitLOProgress: unitProgress,
    };
    await this.markSessionCompleted(request.sessionId, enrichedResults);

    // Clean up local progress data
    await this.clearSessionProgressData(request.sessionId);

    return enrichedResults;
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

      await this.repo.saveSession(session, { enqueueOutbox: false });

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

      await this.repo.saveSession(updatedSession, { enqueueOutbox: false });

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
      return this.repo.getUserSessions(resolvedUserId, filters, limit);
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

      const syncedCount = await this.repo.syncSessionsFromServer(
        resolvedUserId,
        async apiSession => {
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
        }
      );

      console.info(
        `[LearningSessionService] Synced ${syncedCount} sessions from server`
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
      const session = await this.repo.getSession(sessionId);
      const candidate =
        typeof session?.userId === 'string' ? session.userId.trim() : null;
      if (candidate) {
        return candidate;
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
      const progress = await this.repo.getProgress(sessionId, exercise.id);
      if (progress && progress.isCompleted) {
        completedExercises++;
        if (progress.isCorrect === true) {
          correctExercises++;
        }
        totalTimeSeconds += progress.timeSpentSeconds || 0;
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
      unitId: session?.unitId ?? '',
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
      unitLOProgress: undefined,
    };
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

      await this.repo.saveSession(completedSession, { enqueueOutbox: false });
      await this.repo.saveSessionResults(sessionId, results);
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
    const progressRecords = await this.repo.getAllProgress(sessionId);
    return progressRecords.map(progress => ({
      exercise_id: progress.exerciseId,
      exercise_type: progress.exerciseType,
      user_answer: progress.userAnswer,
      is_correct: progress.isCorrect,
      time_spent_seconds: progress.timeSpentSeconds,
    }));
  }

  private async buildSessionOutcome(
    session: LearningSession,
    progressUpdates: Array<{
      exercise_id: string;
      is_correct: boolean | undefined;
    }>
  ): Promise<{
    sessionId: string;
    unitId: string;
    lessonId: string;
    completedAt: string;
    loStats: Record<string, { attempted: number; correct: number }>;
  } | null> {
    try {
      const lessonDetail = await this.catalog.getLessonDetail(session.lessonId);
      if (!lessonDetail) {
        return null;
      }

      const exerciseToLo = new Map<string, string>();
      for (const exercise of lessonDetail.exercises ?? []) {
        const exerciseId = (exercise as { id?: unknown }).id;
        const loId = (exercise as { lo_id?: unknown }).lo_id;
        if (typeof exerciseId === 'string' && typeof loId === 'string') {
          exerciseToLo.set(exerciseId, loId);
        }
      }

      if (exerciseToLo.size === 0) {
        return null;
      }

      const loStats = new Map<string, { attempted: number; correct: number }>();
      for (const update of progressUpdates) {
        const loId = exerciseToLo.get(update.exercise_id);
        if (!loId) {
          continue;
        }
        const bucket = loStats.get(loId) ?? { attempted: 0, correct: 0 };
        bucket.attempted += 1;
        if (update.is_correct === true) {
          bucket.correct += 1;
        }
        loStats.set(loId, bucket);
      }

      const serializedStats: Record<
        string,
        { attempted: number; correct: number }
      > = {};
      for (const [loId, stats] of loStats.entries()) {
        serializedStats[loId] = stats;
      }

      return {
        sessionId: session.id,
        unitId: session.unitId,
        lessonId: session.lessonId,
        completedAt: new Date().toISOString(),
        loStats: serializedStats,
      };
    } catch (error) {
      console.warn('Failed to build session outcome summary:', error);
      return null;
    }
  }

  /**
   * Clear all session progress data after completion
   */
  private async clearSessionProgressData(sessionId: string): Promise<void> {
    try {
      await this.repo.clearProgress(sessionId);
    } catch (error) {
      console.warn('Failed to clear session progress data:', error);
    }
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

  async getUnitLOProgress(
    unitId: string,
    userId?: string
  ): Promise<UnitLOProgress> {
    try {
      const resolvedUserId = await this.resolveUserId(userId);
      return await this.repo.computeUnitLOProgress(unitId, resolvedUserId);
    } catch (error) {
      throw this.handleServiceError(
        error,
        'Failed to compute unit learning objective progress'
      );
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
