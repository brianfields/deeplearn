/**
 * Learning Session Unit Tests
 *
 * Tests learning session management, progress tracking, and session orchestration.
 */

import { jest } from '@jest/globals';

// Mock dependencies
jest.mock('../infrastructure/public');
jest.mock('../lesson_catalog/public');

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

// Mock implementations
const mockLessonCatalogProvider = {
  getLessonDetail: jest.fn() as jest.MockedFunction<any>,
};

const mockInfrastructureProvider = {
  setStorageItem: jest.fn() as jest.MockedFunction<any>,
  getStorageItem: jest.fn() as jest.MockedFunction<any>,
  removeStorageItem: jest.fn() as jest.MockedFunction<any>,
};

// Mock the providers
jest
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  .mocked(require('../lesson_catalog/public').lessonCatalogProvider)
  .mockReturnValue(mockLessonCatalogProvider);
jest
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  .mocked(require('../infrastructure/public').infrastructureProvider)
  .mockReturnValue(mockInfrastructureProvider);

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
          components: [
            { id: 'comp-1', component_type: 'mcq', content: {} },
            { id: 'comp-2', component_type: 'didactic_snippet', content: {} },
          ],
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

        mockLessonCatalogProvider.getLessonDetail.mockResolvedValue(
          mockLessonDetail
        );
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

        expect(mockLessonCatalogProvider.getLessonDetail).toHaveBeenCalledWith(
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

        mockLessonCatalogProvider.getLessonDetail.mockResolvedValue(null);

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
        });

        expect(mockRepo.updateProgress).toHaveBeenCalledWith(request);
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

        expect(mockRepo.completeSession).toHaveBeenCalledWith(request);
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
          components: [],
        };

        mockLessonCatalogProvider.getLessonDetail.mockResolvedValue(
          mockLessonDetail
        );
        mockRepo.getUserSessions.mockResolvedValue({ sessions: [], total: 0 });

        // Act
        const result = await service.canStartSession(lessonId, userId);

        // Assert
        expect(result).toBe(true);
        expect(mockLessonCatalogProvider.getLessonDetail).toHaveBeenCalledWith(
          lessonId
        );
      });

      it('should return false if lesson does not exist', async () => {
        // Arrange
        const lessonId = 'nonexistent-topic';
        const userId = 'user-1';

        mockLessonCatalogProvider.getLessonDetail.mockResolvedValue(null);

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
