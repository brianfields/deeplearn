/**
 * Learning Session React Query Hooks
 *
 * Server state management for learning session data.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { LearningSessionService } from './service';
import { LearningSessionRepo } from './repo';
import { DEFAULT_ANONYMOUS_USER_ID } from '../user/public';
import type {
  StartSessionRequest,
  UpdateProgressRequest,
  CompleteSessionRequest,
  SessionFilters,
  LearningSession,
} from './models';

// Service instance
const repo = new LearningSessionRepo();
const learningSession = new LearningSessionService(repo);

// Query keys
export const learningSessionKeys = {
  all: ['learning_session'] as const,
  sessions: () => ['learning_session', 'sessions'] as const,
  session: (sessionId: string) =>
    ['learning_session', 'session', sessionId] as const,
  exercises: (sessionId: string) =>
    ['learning_session', 'exercises', sessionId] as const,
  userSessions: (userId?: string, filters?: SessionFilters) =>
    [
      'learning_session',
      'user_sessions',
      userId ?? DEFAULT_ANONYMOUS_USER_ID,
      filters,
    ] as const,
  userStats: (userId: string) =>
    ['learning_session', 'user_stats', userId] as const,
  canStart: (lessonId: string, userId?: string) =>
    [
      'learning_session',
      'can_start',
      lessonId,
      userId ?? DEFAULT_ANONYMOUS_USER_ID,
    ] as const,
  health: () => ['learning_session', 'health'] as const,
  unitProgress: (userId: string, unitId: string) =>
    ['learning_session', 'unit_progress', userId, unitId] as const,
  unitLOProgressRoot: () => ['learning_session', 'unit_lo_progress'] as const,
  unitLOProgress: (userId: string, unitId: string) =>
    ['learning_session', 'unit_lo_progress', userId, unitId] as const,
  lessonLOProgress: (lessonId: string, userId: string) =>
    ['learning_session', 'lesson_lo_progress', lessonId, userId] as const,
  nextLessonToResume: (userId: string, unitId: string) =>
    ['learning_session', 'next_resume', userId, unitId] as const,
};

/**
 * Get session by ID
 */
export function useSession(
  sessionId: string,
  options?: {
    enabled?: boolean;
    staleTime?: number;
    refetchOnWindowFocus?: boolean;
  }
) {
  return useQuery({
    queryKey: learningSessionKeys.session(sessionId),
    queryFn: () => learningSession.getSession(sessionId),
    enabled: options?.enabled ?? !!sessionId,
    staleTime: options?.staleTime ?? 30 * 1000, // 30 seconds (session state changes frequently)
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? true,
  });
}

/**
 * Get session exercises with state
 */
export function useSessionExercises(
  sessionId: string,
  options?: {
    enabled?: boolean;
    staleTime?: number;
  }
) {
  return useQuery({
    queryKey: learningSessionKeys.exercises(sessionId),
    queryFn: () => learningSession.getSessionExercises(sessionId),
    enabled: options?.enabled ?? !!sessionId,
    staleTime: options?.staleTime ?? 60 * 1000, // 1 minute
    refetchOnWindowFocus: false, // Exercises don't change often
  });
}

/**
 * Get user's learning sessions
 */
export function useUserSessions(
  userId?: string,
  filters: SessionFilters = {},
  limit: number = 50,
  offset: number = 0,
  options?: {
    enabled?: boolean;
    staleTime?: number;
  }
) {
  return useQuery({
    queryKey: learningSessionKeys.userSessions(userId, filters),
    queryFn: () =>
      learningSession.getUserSessions(userId, filters, limit, offset),
    enabled: options?.enabled ?? !!userId,
    staleTime: options?.staleTime ?? 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
}

/**
 * Get user learning statistics
 */
export function useUserStats(
  userId: string,
  options?: {
    enabled?: boolean;
    staleTime?: number;
  }
) {
  return useQuery({
    queryKey: learningSessionKeys.userStats(userId),
    queryFn: () => learningSession.getUserStats(userId),
    enabled: options?.enabled ?? !!userId,
    staleTime: options?.staleTime ?? 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

/**
 * Check if user can start session for lesson
 */
export function useCanStartSession(
  lessonId: string,
  userId?: string,
  options?: {
    enabled?: boolean;
    staleTime?: number;
  }
) {
  return useQuery({
    queryKey: learningSessionKeys.canStart(lessonId, userId),
    queryFn: () => learningSession.canStartSession(lessonId, userId),
    enabled: options?.enabled ?? !!lessonId,
    staleTime: options?.staleTime ?? 30 * 1000, // 30 seconds
    refetchOnWindowFocus: true,
  });
}

/**
 * Sync sessions from server
 * Call this to pull latest session data from server and update local storage
 */
export function useSyncSessions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId?: string) =>
      learningSession.syncSessionsFromServer(userId),
    onSuccess: (_data, userId) => {
      // Invalidate all user session queries to refetch from updated local storage
      queryClient.invalidateQueries({
        queryKey: learningSessionKeys.userSessions(userId),
      });

      // Invalidate unit progress which depends on session data
      queryClient.invalidateQueries({
        queryKey: learningSessionKeys.unitProgress(
          userId ?? DEFAULT_ANONYMOUS_USER_ID,
          ''
        ),
      });

      queryClient.invalidateQueries({
        queryKey: learningSessionKeys.unitLOProgressRoot(),
      });
      queryClient.invalidateQueries({
        queryKey: ['learning_session', 'lesson_lo_progress'],
        exact: false,
      });
    },
  });
}

/**
 * Start new learning session mutation
 */
export function useStartSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: StartSessionRequest) =>
      learningSession.startSession(request),
    onSuccess: (session: LearningSession, request) => {
      const cacheUserId =
        session.userId ?? request.userId ?? DEFAULT_ANONYMOUS_USER_ID;

      // Update session cache
      queryClient.setQueryData(
        learningSessionKeys.session(session.id),
        session
      );

      // Invalidate user sessions
      queryClient.invalidateQueries({
        queryKey: learningSessionKeys.userSessions(cacheUserId),
      });

      // Invalidate can start check
      queryClient.invalidateQueries({
        queryKey: learningSessionKeys.canStart(request.lessonId, cacheUserId),
      });

      if (session.unitId) {
        queryClient.invalidateQueries({
          queryKey: learningSessionKeys.unitProgress(
            cacheUserId,
            session.unitId
          ),
        });

        queryClient.invalidateQueries({
          queryKey: learningSessionKeys.unitLOProgress(
            cacheUserId,
            session.unitId
          ),
        });
      }
    },
  });
}

export function useLessonLOProgress(
  lessonId: string,
  userId: string,
  options?: { enabled?: boolean; staleTime?: number }
) {
  return useQuery({
    queryKey: learningSessionKeys.lessonLOProgress(lessonId, userId),
    queryFn: () => learningSession.computeLessonLOProgressLocal(lessonId, userId),
    enabled: options?.enabled ?? Boolean(lessonId && userId),
    staleTime: options?.staleTime ?? 30 * 1000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Update session progress mutation
 */
export function useUpdateProgress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UpdateProgressRequest) =>
      learningSession.updateProgress(request),
    onSuccess: (progress, request) => {
      // Invalidate session data to refetch updated progress
      queryClient.invalidateQueries({
        queryKey: learningSessionKeys.session(request.sessionId),
      });

      // Invalidate exercises to update completion state
      queryClient.invalidateQueries({
        queryKey: learningSessionKeys.exercises(request.sessionId),
      });
    },
  });
}

/**
 * Complete session mutation
 */
export function useCompleteSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CompleteSessionRequest) =>
      learningSession.completeSession(request),
    onSuccess: (results, request) => {
      // Invalidate session data
      queryClient.invalidateQueries({
        queryKey: learningSessionKeys.session(request.sessionId),
      });

      // Invalidate user sessions and stats
      queryClient.invalidateQueries({
        queryKey: learningSessionKeys.userSessions(),
      });

      // Note: userStats requires userId, skipping invalidation for now
      // TODO: Add user context and invalidate user stats
      // queryClient.invalidateQueries({
      //   queryKey: learningSessionKeys.userStats(userId),
      // });

      const userKey = request.userId ?? DEFAULT_ANONYMOUS_USER_ID;
      if (results.unitId) {
        queryClient.invalidateQueries({
          queryKey: learningSessionKeys.unitProgress(userKey, results.unitId),
        });
        queryClient.invalidateQueries({
          queryKey: learningSessionKeys.unitLOProgress(userKey, results.unitId),
        });
      }
    },
  });
}

/**
 * Pause session mutation
 */
export function usePauseSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => learningSession.pauseSession(sessionId),
    onSuccess: (session: LearningSession) => {
      // Update session cache
      queryClient.setQueryData(
        learningSessionKeys.session(session.id),
        session
      );
    },
  });
}

/**
 * Resume session mutation
 */
export function useResumeSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => learningSession.resumeSession(sessionId),
    onSuccess: (session: LearningSession) => {
      // Update session cache
      queryClient.setQueryData(
        learningSessionKeys.session(session.id),
        session
      );
    },
  });
}

/**
 * Learning session health check
 */
export function useLearningSessionHealth() {
  return useQuery({
    queryKey: learningSessionKeys.health(),
    queryFn: () => learningSession.checkHealth(),
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Check every 5 minutes
    refetchOnWindowFocus: false,
  });
}

/**
 * Get aggregated unit progress for a user
 */
export function useUnitProgress(
  userId: string,
  unitId: string,
  options?: {
    enabled?: boolean;
    staleTime?: number;
  }
) {
  return useQuery({
    queryKey: learningSessionKeys.unitProgress(userId, unitId),
    queryFn: () => learningSession.getUnitProgress(userId, unitId),
    enabled: options?.enabled ?? (!!userId && !!unitId),
    staleTime: options?.staleTime ?? 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

export function useUnitLOProgress(
  userId: string,
  unitId: string,
  options?: { enabled?: boolean; staleTime?: number }
) {
  return useQuery({
    queryKey: learningSessionKeys.unitLOProgress(userId, unitId),
    queryFn: () => learningSession.getUnitLOProgress(unitId, userId),
    enabled: options?.enabled ?? (!!userId && !!unitId),
    staleTime: options?.staleTime ?? 30 * 1000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Get next lesson to resume within a unit
 */
export function useNextLessonToResume(
  userId: string,
  unitId: string,
  options?: { enabled?: boolean; staleTime?: number }
) {
  return useQuery({
    queryKey: learningSessionKeys.nextLessonToResume(userId, unitId),
    queryFn: () => learningSession.getNextLessonToResume(userId, unitId),
    enabled: options?.enabled ?? (!!userId && !!unitId),
    staleTime: options?.staleTime ?? 60 * 1000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Combined hook for active learning session
 * Provides session data, components, and mutation functions
 */
export function useActiveLearningSession(sessionId: string) {
  const sessionQuery = useSession(sessionId);
  const exercisesQuery = useSessionExercises(sessionId, {
    enabled: !!sessionId && sessionQuery.data?.status === 'active',
  });

  const updateProgressMutation = useUpdateProgress();
  const pauseSessionMutation = usePauseSession();
  const completeSessionMutation = useCompleteSession();

  return {
    // Data
    session: sessionQuery.data,
    exercises: exercisesQuery.data,

    // Loading states
    isLoading: sessionQuery.isLoading || exercisesQuery.isLoading,
    isError: sessionQuery.isError || exercisesQuery.isError,
    error: sessionQuery.error || exercisesQuery.error,

    // Actions
    updateProgress: updateProgressMutation.mutateAsync,
    pauseSession: () => pauseSessionMutation.mutateAsync(sessionId),
    completeSession: () => completeSessionMutation.mutateAsync({ sessionId }),

    // Action states
    isUpdatingProgress: updateProgressMutation.isPending,
    isPausing: pauseSessionMutation.isPending,
    isCompleting: completeSessionMutation.isPending,

    // Refetch functions
    refetchSession: sessionQuery.refetch,
    refetchExercises: exercisesQuery.refetch,
  };
}
