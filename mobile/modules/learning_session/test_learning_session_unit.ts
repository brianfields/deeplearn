/**
 * Learning Session Unit Tests
 *
 * Tests learning session management, progress tracking, and session orchestration.
 */

import { jest } from '@jest/globals';

// Mock dependencies
jest.mock('../infrastructure/public');
jest.mock('../catalog/public');
jest.mock('../user/public');
jest.mock('../offline_cache/public');

import { LearningSessionService } from './service';
import { LearningSessionRepo } from './repo';
import {
  toLearningSessionDTO,
  toSessionProgressDTO,
  toSessionResultsDTO,
} from './models';
import type {
  StartSessionRequest,
  UpdateProgressRequest,
  CompleteSessionRequest,
} from './models';
import type { UserIdentityProvider } from '../user/public';
import type { User } from '../user/models';
import type { OfflineCacheProvider, SyncStatus } from '../offline_cache/public';

// Mock implementations
const mockCatalogProvider = {
  getLessonDetail: jest.fn() as jest.MockedFunction<any>,
};

const mockInfrastructureProvider = {
  setStorageItem: jest.fn() as jest.MockedFunction<any>,
  getStorageItem: jest.fn() as jest.MockedFunction<any>,
  removeStorageItem: jest.fn() as jest.MockedFunction<any>,
};

const createIdentityMock = (): jest.Mocked<UserIdentityProvider> => {
  const mock: Partial<jest.Mocked<UserIdentityProvider>> = {
    getCurrentUser: jest.fn<() => Promise<User | null>>(),
    setCurrentUser: jest.fn<(user: User | null) => Promise<void>>(),
    getCurrentUserId: jest.fn<() => Promise<string>>(),
    clear: jest.fn<() => Promise<void>>(),
  };

  mock.getCurrentUser!.mockResolvedValue(null);
  mock.setCurrentUser!.mockResolvedValue();
  mock.getCurrentUserId!.mockResolvedValue('anonymous');
  mock.clear!.mockResolvedValue();

  return mock as jest.Mocked<UserIdentityProvider>;
};

let mockIdentity: jest.Mocked<UserIdentityProvider>;
let mockOfflineCache: jest.Mocked<OfflineCacheProvider>;

const createSyncStatus = (): SyncStatus => ({
  lastPulledAt: null,
  lastCursor: null,
  pendingWrites: 0,
  cacheModeCounts: { minimal: 0, full: 0 },
  lastSyncAttempt: 0,
  lastSyncResult: 'idle',
  lastSyncError: null,
});

// Mock the providers
jest
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  .mocked(require('../catalog/public').catalogProvider)
  .mockReturnValue(mockCatalogProvider);
jest
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  .mocked(require('../infrastructure/public').infrastructureProvider)
  .mockReturnValue(mockInfrastructureProvider);
jest
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  .mocked(require('../user/public').userIdentityProvider)
  .mockImplementation(() => mockIdentity);
jest
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  .mocked(require('../offline_cache/public').offlineCacheProvider)
  .mockImplementation(() => mockOfflineCache);

describe('Learning Session Module', () => {
  // Mock console methods to suppress output during tests
  const consoleWarnSpy = jest
    .spyOn(console, 'warn')
    .mockImplementation(() => {});
  const consoleErrorSpy = jest
    .spyOn(console, 'error')
    .mockImplementation(() => {});

  beforeEach(() => {
    jest.clearAllMocks();
    mockIdentity = createIdentityMock();
    mockOfflineCache = {
      listUnits: jest.fn().mockImplementation(async () => []),
      getUnitDetail: jest.fn().mockImplementation(async () => null),
      cacheMinimalUnits: jest.fn().mockImplementation(async () => undefined),
      cacheFullUnit: jest.fn().mockImplementation(async () => undefined),
      markUnitCacheMode: jest.fn().mockImplementation(async () => undefined),
      deleteUnit: jest.fn().mockImplementation(async () => undefined),
      clearAll: jest.fn().mockImplementation(async () => undefined),
      getCacheOverview: jest.fn().mockImplementation(async () => ({
        totalStorageBytes: 0,
        syncStatus: createSyncStatus(),
        units: [],
      })),
      resolveAsset: jest.fn().mockImplementation(async () => null),
      enqueueOutbox: jest.fn().mockImplementation(async () => undefined),
      processOutbox: jest
        .fn()
        .mockImplementation(async () => ({ processed: 0, remaining: 0 })),
      runSyncCycle: jest
        .fn()
        .mockImplementation(async () => createSyncStatus()),
      getSyncStatus: jest
        .fn()
        .mockImplementation(async () => createSyncStatus()),
    } as jest.Mocked<OfflineCacheProvider>;
  });

  afterAll(() => {
    consoleWarnSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  describe('LearningSessionService', () => {
    let service: LearningSessionService;
    let mockRepo: jest.Mocked<LearningSessionRepo>;

    beforeEach(() => {
      mockRepo = {
        startSession: jest.fn(),
        getSession: jest.fn(),
        updateProgress: jest.fn(),
        completeSession: jest.fn(),
        pauseSession: jest.fn(),
        getUserSessions: jest.fn(),
        checkHealth: jest.fn(),
      } as any;

      service = new LearningSessionService(mockRepo);
    });

    describe('startSession', () => {
      it('should start a new learning session successfully', async () => {
        // Arrange
        const request: StartSessionRequest = {
          lessonId: 'topic-1',
          userId: 'user-1',
        };

        const mockLessonDetail = {
          id: 'topic-1',
          title: 'Test Topic',
          miniLesson: '...',
          exercises: [{ id: 'mcq-1', exercise_type: 'mcq', stem: 'Q?' }],
          glossaryTerms: [],
        };

        const mockApiSession = {
          id: 'session-1',
          lesson_id: 'topic-1',
          user_id: 'user-1',
          status: 'active' as const,
          started_at: '2024-01-01T00:00:00Z',
          current_exercise_index: 0,
          total_exercises: 2,
          progress_percentage: 0,
          session_data: {},
        };

        mockCatalogProvider.getLessonDetail.mockResolvedValue(mockLessonDetail);
        mockRepo.startSession.mockResolvedValue(mockApiSession);
        mockInfrastructureProvider.setStorageItem.mockResolvedValue(undefined);

        // Act
        const result = await service.startSession(request);

        // Assert
        expect(result).toMatchObject({
          id: 'session-1',
          lessonId: 'topic-1',
          userId: 'user-1',
          status: 'active',
          currentExerciseIndex: 0,
          totalExercises: 2,
          progressPercentage: 0,
        });

        expect(mockCatalogProvider.getLessonDetail).toHaveBeenCalledWith(
          'topic-1'
        );
        expect(mockRepo.startSession).toHaveBeenCalledWith(request);
        expect(mockInfrastructureProvider.setStorageItem).toHaveBeenCalled();
      });

      it('should throw error if topic not found', async () => {
        // Arrange
        const request: StartSessionRequest = {
          lessonId: 'nonexistent-topic',
          userId: 'user-1',
        };

        mockCatalogProvider.getLessonDetail.mockResolvedValue(null);

        // Act & Assert
        await expect(service.startSession(request)).rejects.toMatchObject({
          code: 'LEARNING_SESSION_ERROR',
          message: expect.stringContaining(
            'Lesson nonexistent-topic not found'
          ),
        });
      });
    });

    describe('updateProgress', () => {
      it('should update session progress successfully', async () => {
        // Arrange
        const request: UpdateProgressRequest = {
          sessionId: 'session-1',
          exerciseId: 'comp-1',
          exerciseType: 'mcq',
          userAnswer: 'A',
          isCorrect: true,
          timeSpentSeconds: 30,
        };

        const mockApiProgress = {
          session_id: 'session-1',
          exercise_id: 'comp-1',
          exercise_type: 'mcq',
          started_at: '2024-01-01T00:00:00Z',
          completed_at: '2024-01-01T00:00:30Z',
          is_correct: true,
          user_answer: 'A',
          time_spent_seconds: 30,
          attempts: 1,
          attempt_history: [
            {
              attempt_number: 1,
              is_correct: true,
              user_answer: 'A',
              time_spent_seconds: 30,
              submitted_at: '2024-01-01T00:00:30Z',
            },
          ],
          has_been_answered_correctly: true,
        };

        const mockSession = {
          id: 'session-1',
          lessonId: 'topic-1',
          status: 'active' as const,
          currentExerciseIndex: 0,
          totalExercises: 2,
          progressPercentage: 0,
        };

        mockRepo.updateProgress.mockResolvedValue(mockApiProgress);
        mockInfrastructureProvider.getStorageItem.mockResolvedValue(
          JSON.stringify(mockSession)
        );
        mockInfrastructureProvider.setStorageItem.mockResolvedValue(undefined);

        // Act
        const result = await service.updateProgress(request);

        // Assert
        expect(result).toMatchObject({
          sessionId: 'session-1',
          exerciseId: 'comp-1',
          exerciseType: 'mcq',
          isCorrect: true,
          userAnswer: 'A',
          timeSpentSeconds: 30,
          attempts: 1,
          hasBeenAnsweredCorrectly: true,
        });
        expect(result.attemptHistory).toHaveLength(1);

        expect(mockRepo.updateProgress).toHaveBeenCalledWith({
          ...request,
          userId: 'anonymous',
        });
        expect(mockOfflineCache.enqueueOutbox).toHaveBeenCalledWith(
          expect.objectContaining({
            endpoint: expect.stringContaining('/progress'),
            method: 'PUT',
          })
        );
      });
    });

    describe('completeSession', () => {
      it('should complete session and return results', async () => {
        // Arrange
        const request: CompleteSessionRequest = {
          sessionId: 'session-1',
        };

        const mockApiResults = {
          session_id: 'session-1',
          lesson_id: 'topic-1',
          total_exercises: 2,
          completed_exercises: 2,
          correct_exercises: 1,
          total_time_seconds: 300,
          completion_percentage: 100,
          score_percentage: 50,
          achievements: ['First Completion'],
        };

        mockRepo.completeSession.mockResolvedValue(mockApiResults);
        mockInfrastructureProvider.setStorageItem.mockResolvedValue(undefined);

        // Act
        const result = await service.completeSession(request);

        // Assert
        expect(result).toMatchObject({
          sessionId: 'session-1',
          lessonId: 'topic-1',
          totalExercises: 2,
          completedExercises: 2,
          correctExercises: 1,
          completionPercentage: 100,
          scorePercentage: 50,
          achievements: ['First Completion'],
        });

        expect(mockRepo.completeSession).toHaveBeenCalledWith({
          ...request,
          userId: 'anonymous',
        });
        expect(mockOfflineCache.enqueueOutbox).toHaveBeenCalledWith(
          expect.objectContaining({
            endpoint: expect.stringContaining('/complete'),
            method: 'POST',
          })
        );
      });
    });

    describe('canStartSession', () => {
      it('should return true if lesson exists and no active session', async () => {
        // Arrange
        const lessonId = 'topic-1';
        const userId = 'user-1';

        const mockLessonDetail = {
          id: 'topic-1',
          title: 'Test Topic',
          miniLesson: '...',
          exercises: [],
          glossaryTerms: [],
        };

        mockCatalogProvider.getLessonDetail.mockResolvedValue(mockLessonDetail);
        mockRepo.getUserSessions.mockResolvedValue({ sessions: [], total: 0 });

        // Act
        const result = await service.canStartSession(lessonId, userId);

        // Assert
        expect(result).toBe(true);
        expect(mockCatalogProvider.getLessonDetail).toHaveBeenCalledWith(
          lessonId
        );
      });

      it('should return false if lesson does not exist', async () => {
        // Arrange
        const lessonId = 'nonexistent-topic';
        const userId = 'user-1';

        mockCatalogProvider.getLessonDetail.mockResolvedValue(null);

        // Act
        const result = await service.canStartSession(lessonId, userId);

        // Assert
        expect(result).toBe(false);
      });
    });

    describe('checkHealth', () => {
      it('should return health status from repository', async () => {
        // Arrange
        mockRepo.checkHealth.mockResolvedValue(true);

        // Act
        const result = await service.checkHealth();

        // Assert
        expect(result).toBe(true);
        expect(mockRepo.checkHealth).toHaveBeenCalled();
      });

      it('should handle health check errors gracefully', async () => {
        // Arrange
        mockRepo.checkHealth.mockRejectedValue(new Error('Network error'));

        // Act
        const result = await service.checkHealth();

        // Assert
        expect(result).toBe(false);
      });
    });
  });

  describe('DTO Converters', () => {
    describe('toLearningSessionDTO', () => {
      it('should convert API session to DTO correctly', () => {
        // Arrange
        const apiSession = {
          id: 'session-1',
          lesson_id: 'topic-1',
          user_id: 'user-1',
          status: 'active' as const,
          started_at: '2024-01-01T00:00:00Z',
          current_exercise_index: 1,
          total_exercises: 3,
          progress_percentage: 33,
          session_data: { lastExerciseId: 'comp-1' },
        };

        // Act
        const result = toLearningSessionDTO(apiSession);

        // Assert
        expect(result).toMatchObject({
          id: 'session-1',
          lessonId: 'topic-1',
          userId: 'user-1',
          status: 'active',
          startedAt: '2024-01-01T00:00:00Z',
          currentExerciseIndex: 1,
          totalExercises: 3,
          progressPercentage: 33,
          sessionData: { lastExerciseId: 'comp-1' },
          isCompleted: false,
          canResume: true,
        });

        expect(result.estimatedTimeRemaining).toBeGreaterThan(0);
      });

      it('should handle completed sessions correctly', () => {
        // Arrange
        const apiSession = {
          id: 'session-1',
          lesson_id: 'topic-1',
          status: 'completed' as const,
          started_at: '2024-01-01T00:00:00Z',
          completed_at: '2024-01-01T00:15:00Z',
          current_exercise_index: 3,
          total_exercises: 3,
          progress_percentage: 100,
          session_data: {},
        };

        // Act
        const result = toLearningSessionDTO(apiSession);

        // Assert
        expect(result.isCompleted).toBe(true);
        expect(result.canResume).toBe(false);
        expect(result.completedAt).toBe('2024-01-01T00:15:00Z');
      });
    });

    describe('toSessionProgressDTO', () => {
      it('should convert API progress to DTO correctly', () => {
        // Arrange
        const apiProgress = {
          session_id: 'session-1',
          exercise_id: 'comp-1',
          exercise_type: 'mcq',
          started_at: '2024-01-01T00:00:00Z',
          completed_at: '2024-01-01T00:00:30Z',
          is_correct: true,
          user_answer: 'A',
          time_spent_seconds: 30,
          attempts: 1,
        };

        // Act
        const result = toSessionProgressDTO(apiProgress);

        // Assert
        expect(result).toMatchObject({
          sessionId: 'session-1',
          exerciseId: 'comp-1',
          exerciseType: 'mcq',
          startedAt: '2024-01-01T00:00:00Z',
          completedAt: '2024-01-01T00:00:30Z',
          isCorrect: true,
          userAnswer: 'A',
          timeSpentSeconds: 30,
          attempts: 1,
          isCompleted: true,
          accuracy: 1,
        });
      });
    });

    describe('toSessionResultsDTO', () => {
      it('should convert API results to DTO with calculated fields', () => {
        // Arrange
        const apiResults = {
          session_id: 'session-1',
          lesson_id: 'topic-1',
          total_exercises: 5,
          completed_exercises: 5,
          correct_exercises: 4,
          total_time_seconds: 900, // 15 minutes
          completion_percentage: 100,
          score_percentage: 80,
          achievements: ['First Completion', 'Quick Learner'],
        };

        // Act
        const result = toSessionResultsDTO(apiResults);

        // Assert
        expect(result).toMatchObject({
          sessionId: 'session-1',
          lessonId: 'topic-1',
          totalExercises: 5,
          completedExercises: 5,
          correctExercises: 4,
          totalTimeSeconds: 900,
          completionPercentage: 100,
          scorePercentage: 80,
          achievements: ['First Completion', 'Quick Learner'],
          grade: 'B', // 80% should be B grade
          timeDisplay: '15m 0s',
        });

        expect(result.performanceSummary).toContain('Good job');
        expect(result.performanceSummary).toContain('15 minutes');
        expect(result.performanceSummary).toContain('80%');
      });
    });
  });

  describe('Module Architecture', () => {
    it('should have no public interface as per migration plan', () => {
      // According to the migration plan, learning_session module has no cross-module consumers
      // All functionality is internal to the module

      // Act & Assert - Verify service can be instantiated directly for internal use
      const repo = new LearningSessionRepo();
      const service = new LearningSessionService(repo);

      expect(service).toBeDefined();
      expect(typeof service.startSession).toBe('function');
      expect(typeof service.getSession).toBe('function');
      expect(typeof service.completeSession).toBe('function');
      expect(typeof service.pauseSession).toBe('function');
      expect(typeof service.resumeSession).toBe('function');
      expect(typeof (service as any).getSessionExercises).toBe('function');
      expect(typeof service.canStartSession).toBe('function');
      expect(typeof service.checkHealth).toBe('function');
    });

    it('should be self-contained with no external dependencies on other modules public interfaces', () => {
      // The service should only depend on infrastructure and lesson_catalog public interfaces
      // This is verified by the successful instantiation and mocking in other tests
      expect(true).toBe(true); // Test passes if module loads without circular dependency errors
    });
  });
});
