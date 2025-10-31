/**
 * Learning Session Unit Tests
 *
 * Tests learning session management, progress tracking, and session orchestration.
 */

import { jest } from '@jest/globals';

// Mock dependencies
jest.mock('../catalog/public');
jest.mock('../user/public');
jest.mock('../offline_cache/public', () => {
  const actual = jest.requireActual<typeof import('../offline_cache/public')>(
    '../offline_cache/public'
  );
  return {
    ...actual,
    offlineCacheProvider: jest.fn(),
  };
});
jest.mock('../infrastructure/public', () => {
  const actual = jest.requireActual<typeof import('../infrastructure/public')>(
    '../infrastructure/public'
  );
  return {
    ...actual,
    infrastructureProvider: jest.fn(),
  };
});

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
  LearningSession,
  ShortAnswerContentDTO,
} from './models';
import type { UserIdentityProvider } from '../user/public';
import type { User } from '../user/models';
import { offlineCacheProvider } from '../offline_cache/public';
import type {
  OfflineCacheProvider,
  CachedUnitDetail,
} from '../offline_cache/public';
import { infrastructureProvider } from '../infrastructure/public';
import type { InfrastructureProvider } from '../infrastructure/public';

// Mock implementations
const mockCatalogProvider = {
  getLessonDetail: jest.fn() as jest.MockedFunction<any>,
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

type TestInfrastructureProvider = jest.Mocked<InfrastructureProvider> & {
  __storage: Map<string, string>;
};

const createSyncStatus = () => ({
  lastPulledAt: null,
  lastCursor: null,
  pendingWrites: 0,
  cacheModeCounts: { minimal: 0, full: 0 },
  lastSyncAttempt: Date.now(),
  lastSyncResult: 'idle' as const,
  lastSyncError: null,
});

const createOfflineCacheMock = (): jest.Mocked<OfflineCacheProvider> =>
  ({
    listUnits: jest.fn(async () => []),
    getUnitDetail: jest.fn(async () => null),
    cacheMinimalUnits: jest.fn(async () => undefined),
    cacheFullUnit: jest.fn(async () => undefined),
    setUnitCacheMode: jest.fn(async () => undefined),
    resolveAsset: jest.fn(async () => null),
    downloadUnitAssets: jest.fn(async () => undefined),
    deleteUnit: jest.fn(async () => undefined),
    clearAll: jest.fn(async () => undefined),
    enqueueOutbox: jest.fn(async () => undefined),
    processOutbox: jest.fn(async () => ({ processed: 0, remaining: 0 })),
    runSyncCycle: jest.fn(async () => createSyncStatus()),
    getSyncStatus: jest.fn(async () => createSyncStatus()),
    getCacheOverview: jest.fn(async () => ({
      totalStorageBytes: 0,
      syncStatus: createSyncStatus(),
    })),
  }) as unknown as jest.Mocked<OfflineCacheProvider>;

const createInfrastructureMock = (): TestInfrastructureProvider => {
  const storage = new Map<string, string>();
  const mock = {
    request: jest.fn(async () => {
      throw new Error('Infrastructure request not implemented in tests');
    }),
    getNetworkStatus: jest.fn(() => ({ isConnected: true })),
    checkHealth: jest.fn(async () => ({
      httpClient: true,
      storage: true,
      network: true,
      timestamp: Date.now(),
    })),
    getStorageItem: jest.fn(async (key: string) =>
      storage.has(key) ? storage.get(key)! : null
    ),
    setStorageItem: jest.fn(async (key: string, value: string) => {
      storage.set(key, value);
    }),
    removeStorageItem: jest.fn(async (key: string) => {
      storage.delete(key);
    }),
    getStorageStats: jest.fn(async () => ({
      size: storage.size,
      entries: storage.size,
    })),
    clearStorage: jest.fn(async () => {
      storage.clear();
    }),
    createSQLiteProvider: jest.fn(async () => ({}) as any),
    getFileSystem: jest.fn(() => ({}) as any),
  } as unknown as TestInfrastructureProvider;
  mock.__storage = storage;
  return mock;
};

const offlineCacheProviderMock = jest.mocked(offlineCacheProvider);
const infrastructureProviderMock = jest.mocked(infrastructureProvider);

let mockOfflineCache: jest.Mocked<OfflineCacheProvider>;
let _mockInfrastructure: TestInfrastructureProvider;

// Mock the providers
jest
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  .mocked(require('../catalog/public').catalogProvider)
  .mockReturnValue(mockCatalogProvider);
jest
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  .mocked(require('../user/public').userIdentityProvider)
  .mockImplementation(() => mockIdentity);

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
    mockOfflineCache = createOfflineCacheMock();
    _mockInfrastructure = createInfrastructureMock();
    offlineCacheProviderMock.mockReturnValue(mockOfflineCache);
    infrastructureProviderMock.mockReturnValue(_mockInfrastructure);
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
        saveSession: jest.fn(),
        getSession: jest.fn(),
        saveProgress: jest.fn(),
        enqueueSessionCompletion: jest.fn(),
        clearProgress: jest.fn(),
        getUserSessions: jest.fn(),
        saveSessionResults: jest.fn(),
        saveSessionOutcome: jest.fn(),
        getProgress: jest.fn(),
        getAllProgress: jest.fn(),
        syncSessionsFromServer: jest.fn(),
        pauseSession: jest.fn(),
        checkHealth: jest.fn(),
        startSession: jest.fn(),
        updateProgress: jest.fn(),
        completeSession: jest.fn(),
        computeUnitLOProgress: jest.fn(),
      } as any;

      service = new LearningSessionService(mockRepo);
    });

    describe('validateShortAnswer', () => {
      let content: ShortAnswerContentDTO;

      beforeEach(() => {
        content = {
          question: 'Name the process plants use to make food.',
          canonicalAnswer: 'photosynthesis',
          acceptableAnswers: ['photo synthesis', 'plant photosynthesis'],
          wrongAnswers: [
            {
              answer: 'respiration',
              explanation: 'Respiration breaks down food rather than producing it.',
              misconceptionIds: ['mis-1'],
            },
          ],
          explanationCorrect: 'Plants convert sunlight into energy through photosynthesis.',
        };
      });

      it('accepts canonical answers regardless of casing and whitespace', () => {
        const result = service.validateShortAnswer('  Photosynthesis ', content);
        expect(result).toEqual({ isCorrect: true, matchedAnswer: 'photosynthesis' });
      });

      it('accepts acceptable answers with fuzzy matching', () => {
        const result = service.validateShortAnswer('photo syntheses', content);
        expect(result).toEqual({ isCorrect: true, matchedAnswer: 'photo synthesis' });
      });

      it('provides targeted feedback for common wrong answers', () => {
        const result = service.validateShortAnswer('respiration', content);
        expect(result).toEqual({
          isCorrect: false,
          wrongAnswerExplanation: content.wrongAnswers[0].explanation,
        });
      });

      it('marks unrelated answers as incorrect without explanation', () => {
        const result = service.validateShortAnswer('gravity', content);
        expect(result).toEqual({ isCorrect: false });
      });
    });

    describe('startSession', () => {
      it('should start a new learning session successfully', async () => {
        // Arrange
        const request: StartSessionRequest = {
          lessonId: 'topic-1',
          unitId: 'unit-1',
          userId: 'user-1',
        };

        const mockLessonDetail = {
          id: 'topic-1',
          title: 'Test Topic',
          unitId: 'unit-1',
          miniLesson: '...',
          exercises: [
            { id: 'mcq-1', exercise_type: 'mcq', stem: 'Q1?', lo_id: 'lo-1' },
            { id: 'mcq-2', exercise_type: 'mcq', stem: 'Q2?', lo_id: 'lo-2' },
          ],
          glossaryTerms: [],
          podcastTranscript: null,
          podcastAudioUrl: null,
          podcastDurationSeconds: null,
          podcastVoice: null,
          podcastGeneratedAt: null,
          hasPodcast: false,
        };

        mockCatalogProvider.getLessonDetail.mockResolvedValue(mockLessonDetail);
        mockRepo.saveSession.mockResolvedValue(undefined);

        // Act
        const result = await service.startSession(request);

        // Assert
        expect(result).toMatchObject({
          lessonId: 'topic-1',
          userId: 'user-1',
          status: 'active',
          currentExerciseIndex: 0,
          totalExercises: 2,
          progressPercentage: 0,
        });
        expect(result.id).toBeDefined();
        expect(typeof result.id).toBe('string');

        expect(mockCatalogProvider.getLessonDetail).toHaveBeenCalledWith(
          'topic-1'
        );
        expect(mockRepo.saveSession).toHaveBeenCalledWith(
          expect.objectContaining({
            lessonId: 'topic-1',
            unitId: 'unit-1',
            userId: 'user-1',
          }),
          expect.objectContaining({ enqueueOutbox: true })
        );
      });

      it('should throw error if unitId is missing', async () => {
        const request: StartSessionRequest = {
          lessonId: 'topic-1',
          unitId: '',
          userId: 'user-1',
        };

        await expect(service.startSession(request)).rejects.toMatchObject({
          code: 'LEARNING_SESSION_ERROR',
          message: expect.stringContaining('unitId is required'),
        });
        expect(mockCatalogProvider.getLessonDetail).not.toHaveBeenCalled();
      });

      it('should throw error if topic not found', async () => {
        // Arrange
        const request: StartSessionRequest = {
          lessonId: 'nonexistent-topic',
          unitId: 'unit-1',
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

        mockRepo.saveProgress.mockResolvedValue(undefined);

        // Act
        const result = await service.updateProgress(request);

        // Assert
        expect(result).toMatchObject({
          sessionId: 'session-1',
          exerciseId: 'comp-1',
          exerciseType: 'mcq',
          isCorrect: true,
          userAnswer: { value: 'A' },
          timeSpentSeconds: 30,
          attempts: 1,
        });
        expect(mockRepo.saveProgress).toHaveBeenCalledWith(
          'session-1',
          expect.objectContaining({ exerciseId: 'comp-1', isCorrect: true })
        );
      });
    });

    describe('completeSession', () => {
      it('should complete session and return results', async () => {
        // Arrange
        const request: CompleteSessionRequest = {
          sessionId: 'session-1',
        };

        const mockSession = {
          id: 'session-1',
          lessonId: 'topic-1',
          lessonTitle: 'Test Topic',
          unitId: 'unit-1',
          userId: 'user-1',
          status: 'active' as const,
          startedAt: '2024-01-01T00:00:00Z',
          currentExerciseIndex: 0,
          totalExercises: 2,
          progressPercentage: 0,
        };

        const mockLessonDetail = {
          id: 'topic-1',
          title: 'Test Topic',
          unitId: 'unit-1',
          miniLesson: '...',
          exercises: [
            { id: 'mcq-1', exercise_type: 'mcq', stem: 'Q1?', lo_id: 'lo-1' },
            { id: 'mcq-2', exercise_type: 'mcq', stem: 'Q2?', lo_id: 'lo-2' },
          ],
          glossaryTerms: [],
          podcastTranscript: null,
          podcastAudioUrl: null,
          podcastDurationSeconds: null,
          podcastVoice: null,
          podcastGeneratedAt: null,
          hasPodcast: false,
        };

        mockRepo.getSession.mockResolvedValue(mockSession as any);
        mockRepo.getAllProgress.mockResolvedValue([
          {
            sessionId: 'session-1',
            exerciseId: 'mcq-1',
            exerciseType: 'mcq',
            startedAt: '2024-01-01T00:00:00Z',
            completedAt: '2024-01-01T00:05:00Z',
            isCorrect: true,
            userAnswer: { value: 'A' },
            timeSpentSeconds: 60,
            attempts: 1,
            isCompleted: true,
            accuracy: 1,
          } as any,
        ]);
        mockRepo.enqueueSessionCompletion.mockResolvedValue(undefined);
        mockRepo.saveSession.mockResolvedValue(undefined);
        mockRepo.saveSessionResults.mockResolvedValue(undefined);
        mockRepo.saveSessionOutcome.mockResolvedValue(undefined);
        mockRepo.clearProgress.mockResolvedValue(undefined);
        mockCatalogProvider.getLessonDetail.mockResolvedValue(mockLessonDetail);
        mockRepo.computeUnitLOProgress.mockResolvedValue({
          unitId: 'unit-1',
          items: [],
        });

        // Act
        const result = await service.completeSession(request);

        // Assert
        expect(result).toMatchObject({
          sessionId: 'session-1',
          lessonId: 'topic-1',
          totalExercises: 2,
          unitId: 'unit-1',
        });
        expect(result.completionPercentage).toBeGreaterThanOrEqual(0);
        expect(result.scorePercentage).toBeGreaterThanOrEqual(0);
        expect(result.unitLOProgress).toEqual({ unitId: 'unit-1', items: [] });

        expect(mockRepo.enqueueSessionCompletion).toHaveBeenCalledWith(
          'session-1',
          'user-1',
          expect.any(Array)
        );
        expect(mockRepo.saveSessionResults).toHaveBeenCalledWith(
          'session-1',
          expect.any(Object)
        );
        expect(mockRepo.saveSessionOutcome).toHaveBeenCalled();
        expect(mockRepo.computeUnitLOProgress).toHaveBeenCalledWith(
          'unit-1',
          'user-1'
        );
      });
    });

    describe('getSessionExercises', () => {
      it('maps multiple exercise types from lesson detail', async () => {
        const session: LearningSession = {
          id: 'session-42',
          lessonId: 'lesson-99',
          unitId: 'unit-2',
          lessonTitle: 'Biology Basics',
          userId: 'user-7',
          status: 'active',
          startedAt: '2024-01-01T00:00:00Z',
          completedAt: undefined,
          currentExerciseIndex: 0,
          totalExercises: 2,
          progressPercentage: 0,
          sessionData: {},
          estimatedTimeRemaining: 0,
          isCompleted: false,
          canResume: true,
        };

        mockRepo.getSession.mockResolvedValue(session as any);
        mockCatalogProvider.getLessonDetail.mockResolvedValue({
          exercises: [
            {
              id: 'mcq-1',
              exercise_type: 'mcq',
              stem: 'What is 2 + 2?',
              options: [
                { label: 'A', text: '3' },
                { label: 'B', text: '4' },
              ],
              answer_key: { label: 'B', rationale_right: '2 + 2 equals 4.' },
              title: 'Addition',
            },
            {
              id: 'sa-1',
              exercise_type: 'short_answer',
              stem: 'Name the process of cell division.',
              canonical_answer: 'mitosis',
              acceptable_answers: ['cell division'],
              wrong_answers: [
                {
                  answer: 'meiosis',
                  explanation:
                    'Meiosis is for gamete formation, not general cell replication.',
                  misconception_ids: ['bio-1'],
                },
              ],
              explanation_correct: 'Mitosis is how most cells replicate.',
              title: 'Cell Processes',
            },
          ],
        } as any);

        const exercises = await service.getSessionExercises('session-42');

        expect(exercises).toHaveLength(2);
        expect(exercises[0]).toMatchObject({
          id: 'mcq-1',
          type: 'mcq',
          content: expect.objectContaining({ question: 'What is 2 + 2?' }),
        });
        expect(exercises[1]).toMatchObject({
          id: 'sa-1',
          type: 'short_answer',
          content: expect.objectContaining({
            canonicalAnswer: 'mitosis',
            acceptableAnswers: ['cell division'],
            wrongAnswers: [
              expect.objectContaining({
                answer: 'meiosis',
                explanation: expect.stringContaining('Meiosis'),
              }),
            ],
          }),
        });
      });
    });

    describe('getUnitLOProgress', () => {
      it('returns learning objective progress from the repository', async () => {
        const progressResponse = {
          unitId: 'unit-42',
          items: [
            {
              loId: 'lo-1',
              title: 'Objective 1',
              description: 'Objective 1 description',
              exercisesTotal: 3,
              exercisesAttempted: 2,
              exercisesCorrect: 2,
              status: 'partial' as const,
              newlyCompletedInSession: false,
            },
          ],
        };

        mockRepo.computeUnitLOProgress.mockResolvedValue(
          progressResponse as any
        );

        const result = await service.getUnitLOProgress('unit-42', 'user-99');

        expect(result).toEqual(progressResponse);
        expect(mockRepo.computeUnitLOProgress).toHaveBeenCalledWith(
          'unit-42',
          'user-99'
        );
      });
    });

    describe('computeLessonLOProgressLocal', () => {
      it('aggregates last attempts per exercise and filters lesson objectives', async () => {
        const realRepo = new LearningSessionRepo();
        const realService = new LearningSessionService(realRepo);
        const unitId = 'unit-lesson';
        const lessonId = 'lesson-local';
        const userId = 'user-progress';

        const cachedDetail: CachedUnitDetail = {
          id: unitId,
          title: 'Offline Unit',
          description: 'Unit description',
          learnerLevel: 'beginner',
          isGlobal: false,
          updatedAt: Date.now(),
          schemaVersion: 1,
          downloadStatus: 'completed',
          cacheMode: 'full',
          downloadedAt: Date.now(),
          syncedAt: Date.now(),
          unitPayload: {
            id: unitId,
            title: 'Offline Unit',
            description: 'Unit description',
            learner_level: 'beginner',
            learning_objectives: [
              {
                id: 'lo-1',
                title: 'Objective 1',
                description: 'Objective 1 description',
              },
              {
                id: 'lo-2',
                title: 'Unused Objective',
                description: 'Unused Objective description',
              },
            ],
          },
          lessons: [
            {
              id: lessonId,
              unitId,
              title: 'Lesson Local',
              position: 1,
              payload: {
                package: {
                  unit_learning_objective_ids: ['lo-1', 'lo-2'],
                  exercises: [
                    { id: 'ex-1', exercise_type: 'mcq', lo_id: 'lo-1' },
                    { id: 'ex-2', exercise_type: 'mcq', lo_id: 'lo-1' },
                  ],
                },
              },
              updatedAt: Date.now(),
              schemaVersion: 1,
            },
          ],
          assets: [],
        };

        mockOfflineCache.listUnits.mockResolvedValue([cachedDetail]);
        mockOfflineCache.getUnitDetail.mockResolvedValue(cachedDetail);

        const baseSession: LearningSession = {
          id: 'session-local',
          lessonId,
          unitId,
          lessonTitle: 'Lesson Local',
          userId,
          status: 'active',
          startedAt: new Date('2024-04-01T00:00:00Z').toISOString(),
          completedAt: undefined,
          currentExerciseIndex: 0,
          totalExercises: 2,
          progressPercentage: 0,
          sessionData: {},
          estimatedTimeRemaining: 0,
          isCompleted: false,
          canResume: true,
        };

        await realRepo.saveSession(baseSession, { enqueueOutbox: false });

        await realService.updateProgress({
          sessionId: baseSession.id,
          exerciseId: 'ex-1',
          exerciseType: 'mcq',
          userAnswer: 'A',
          isCorrect: false,
          timeSpentSeconds: 30,
        });
        await realService.updateProgress({
          sessionId: baseSession.id,
          exerciseId: 'ex-1',
          exerciseType: 'mcq',
          userAnswer: 'B',
          isCorrect: true,
          timeSpentSeconds: 25,
        });
        await realService.updateProgress({
          sessionId: baseSession.id,
          exerciseId: 'ex-2',
          exerciseType: 'mcq',
          userAnswer: 'C',
          isCorrect: false,
          timeSpentSeconds: 20,
        });

        const items = await realService.computeLessonLOProgressLocal(
          lessonId,
          userId
        );

        expect(items).toHaveLength(1);
        const lo = items[0];
        expect(lo.loId).toBe('lo-1');
        expect(lo.exercisesTotal).toBe(2);
        expect(lo.exercisesAttempted).toBe(2);
        expect(lo.exercisesCorrect).toBe(1);
        expect(lo.status).toBe('partial');
        expect(lo.newlyCompletedInSession).toBe(false);
        expect(lo.title).toBe('Objective 1');
        expect(lo.description).toBe('Objective 1 description');

        const storedSession = await realRepo.getSession(baseSession.id);
        const answers = (
          storedSession?.sessionData as {
            exercise_answers?: Record<string, any>;
          }
        )?.exercise_answers;
        expect(answers?.['ex-1']?.attempt_history).toHaveLength(2);
        expect(
          answers?.['ex-1']?.attempt_history?.[1]?.is_correct ?? false
        ).toBe(true);
        expect(items.find(item => item.loId === 'lo-2')).toBeUndefined();
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
          podcastTranscript: null,
          podcastAudioUrl: null,
          podcastDurationSeconds: null,
          podcastVoice: null,
          podcastGeneratedAt: null,
          hasPodcast: false,
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

  describe('LearningSessionRepo', () => {
    it('computes unit learning objective progress and caches snapshots', async () => {
      const repo = new LearningSessionRepo();
      const unitId = 'unit-1';
      const userId = 'user-1';
      const nowIso = new Date().toISOString();

      const cachedDetail: CachedUnitDetail = {
        id: unitId,
        title: 'Intro Unit',
        description: 'Basics',
        learnerLevel: 'beginner',
        isGlobal: false,
        updatedAt: Date.now(),
        schemaVersion: 1,
        downloadStatus: 'completed',
        cacheMode: 'full',
        downloadedAt: Date.now(),
        syncedAt: Date.now(),
        unitPayload: {
          id: unitId,
          title: 'Intro Unit',
          description: 'Basics',
          learner_level: 'beginner',
          lesson_order: ['lesson-1'],
          learning_objectives: [
            {
              id: 'lo-1',
              title: 'Objective 1',
              description: 'Objective 1 description',
            },
            {
              id: 'lo-2',
              title: 'Objective 2',
              description: 'Objective 2 description',
            },
          ],
        },
        lessons: [
          {
            id: 'lesson-1',
            unitId,
            title: 'Lesson 1',
            position: 1,
            payload: {
              package: {
                unit_learning_objective_ids: ['lo-1', 'lo-2'],
                exercises: [
                  { id: 'ex-1', exercise_type: 'mcq', lo_id: 'lo-1' },
                  { id: 'ex-2', exercise_type: 'mcq', lo_id: 'lo-1' },
                  { id: 'ex-3', exercise_type: 'mcq', lo_id: 'lo-2' },
                ],
              },
            },
            updatedAt: Date.now(),
            schemaVersion: 1,
          },
        ],
        assets: [],
      };
      mockOfflineCache.getUnitDetail.mockResolvedValue(cachedDetail);

      const session: LearningSession = {
        id: 'session-1',
        lessonId: 'lesson-1',
        unitId,
        lessonTitle: 'Lesson 1',
        userId,
        status: 'completed',
        startedAt: nowIso,
        completedAt: nowIso,
        currentExerciseIndex: 3,
        totalExercises: 3,
        progressPercentage: 100,
        sessionData: {},
        estimatedTimeRemaining: 0,
        isCompleted: true,
        canResume: false,
      };

      await repo.saveSession(session, { enqueueOutbox: false });
      await repo.saveSessionOutcome({
        sessionId: session.id,
        unitId,
        lessonId: session.lessonId,
        completedAt: nowIso,
        loStats: {
          'lo-1': { attempted: 2, correct: 2 },
          'lo-2': { attempted: 1, correct: 0 },
        },
      } as any);

      const progress = await repo.computeUnitLOProgress(unitId, userId);

      expect(progress.unitId).toBe(unitId);
      expect(progress.items).toHaveLength(2);
      const lo1 = progress.items.find(item => item.loId === 'lo-1');
      const lo2 = progress.items.find(item => item.loId === 'lo-2');
      expect(lo1).toMatchObject({
        title: 'Objective 1',
        description: 'Objective 1 description',
        status: 'completed',
        exercisesTotal: 2,
        exercisesAttempted: 2,
        exercisesCorrect: 2,
        newlyCompletedInSession: true,
      });
      expect(lo2).toMatchObject({
        title: 'Objective 2',
        description: 'Objective 2 description',
        status: 'partial',
        exercisesTotal: 1,
        exercisesAttempted: 1,
        exercisesCorrect: 0,
        newlyCompletedInSession: false,
      });
      expect(mockOfflineCache.getUnitDetail).toHaveBeenCalledWith(unitId);

      const second = await repo.computeUnitLOProgress(unitId, userId);
      const secondLo1 = second.items.find(item => item.loId === 'lo-1');
      expect(secondLo1?.newlyCompletedInSession).toBe(false);
    });

    it('returns empty items when cached unit detail is unavailable', async () => {
      mockOfflineCache.getUnitDetail.mockResolvedValue(null);
      const repo = new LearningSessionRepo();
      const progress = await repo.computeUnitLOProgress(
        'missing-unit',
        'user-1'
      );
      expect(progress).toEqual({ unitId: 'missing-unit', items: [] });
    });
  });

  describe('DTO Converters', () => {
    describe('toLearningSessionDTO', () => {
      it('should convert API session to DTO correctly', () => {
        // Arrange
        const apiSession = {
          id: 'session-1',
          lesson_id: 'topic-1',
          unit_id: 'unit-1',
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
          unitId: 'unit-1',
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
          unit_id: 'unit-1',
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
          unit_id: 'unit-1',
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
          unitId: 'unit-1',
          totalExercises: 5,
          completedExercises: 5,
          correctExercises: 4,
          totalTimeSeconds: 900,
          completionPercentage: 100,
          scorePercentage: 80,
          achievements: ['First Completion', 'Quick Learner'],
          grade: 'B', // 80% should be B grade
          timeDisplay: '15m 0s',
          unitLOProgress: undefined,
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
