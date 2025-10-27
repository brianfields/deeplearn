import { describe, expect, it, jest, beforeEach } from '@jest/globals';
import { ContentService } from './service';
import { ContentRepo } from './repo';
import type { ApiUnitRead } from './repo';
import type {
  CachedAsset,
  CachedUnit,
  CachedUnitDetail,
  OfflineCacheProvider,
  SyncStatus,
} from '../offline_cache/public';
import type { InfrastructureProvider } from '../infrastructure/public';
import type { UserIdentityProvider } from '../user/public';

describe('ContentService (offline cache integration)', () => {
  let repo: jest.Mocked<ContentRepo>;
  let offlineCache: jest.Mocked<OfflineCacheProvider>;
  let infrastructure: InfrastructureProvider;
  let infrastructureMocks: any;
  let userIdentity: jest.Mocked<UserIdentityProvider>;
  let service: ContentService;

  const baseUnit: CachedUnit = {
    id: 'unit-1',
    title: 'Intro Unit',
    description: 'Basics',
    learnerLevel: 'beginner',
    isGlobal: false,
    updatedAt: Date.now(),
    schemaVersion: 1,
    downloadStatus: 'idle',
    cacheMode: 'minimal',
    downloadedAt: null,
    syncedAt: Date.now(),
    unitPayload: {
      id: 'unit-1',
      title: 'Intro Unit',
      description: 'Basics',
      learner_level: 'beginner',
      lesson_order: ['lesson-1'],
      status: 'completed',
      updated_at: new Date().toISOString(),
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
  };

  beforeEach(() => {
    repo = {
      listUnits: jest.fn(),
      getUnitDetail: jest.fn(),
      getUserUnitCollections: jest.fn(),
      updateUnitSharing: jest.fn(),
      addUnitToMyUnits: jest.fn(),
      removeUnitFromMyUnits: jest.fn(),
      syncUnits: jest.fn(),
    } as unknown as jest.Mocked<ContentRepo>;

    const createSyncStatus = (): SyncStatus => ({
      lastPulledAt: null,
      lastCursor: null,
      pendingWrites: 0,
      cacheModeCounts: { minimal: 0, full: 0 },
      lastSyncAttempt: 0,
      lastSyncResult: 'idle',
      lastSyncError: null,
    });

    offlineCache = {
      listUnits: jest
        .fn<OfflineCacheProvider['listUnits']>()
        .mockResolvedValue([baseUnit]),
      getUnitDetail: jest
        .fn<OfflineCacheProvider['getUnitDetail']>()
        .mockResolvedValue(null),
      cacheMinimalUnits: jest
        .fn<OfflineCacheProvider['cacheMinimalUnits']>()
        .mockResolvedValue(undefined),
      cacheFullUnit: jest
        .fn<OfflineCacheProvider['cacheFullUnit']>()
        .mockResolvedValue(undefined),
      setUnitCacheMode: jest
        .fn<OfflineCacheProvider['setUnitCacheMode']>()
        .mockResolvedValue(undefined),
      downloadUnitAssets: jest
        .fn<OfflineCacheProvider['downloadUnitAssets']>()
        .mockResolvedValue(undefined),
      deleteUnit: jest
        .fn<OfflineCacheProvider['deleteUnit']>()
        .mockResolvedValue(undefined),
      clearAll: jest
        .fn<OfflineCacheProvider['clearAll']>()
        .mockResolvedValue(undefined),
      getCacheOverview: jest
        .fn<OfflineCacheProvider['getCacheOverview']>()
        .mockResolvedValue({
          totalStorageBytes: 0,
          syncStatus: createSyncStatus(),
          units: [],
        }),
      resolveAsset: jest
        .fn<OfflineCacheProvider['resolveAsset']>()
        .mockResolvedValue(null),
      enqueueOutbox: jest
        .fn<OfflineCacheProvider['enqueueOutbox']>()
        .mockResolvedValue(undefined),
      processOutbox: jest
        .fn<OfflineCacheProvider['processOutbox']>()
        .mockResolvedValue({ processed: 0, remaining: 0 }),
      syncOutbox: jest
        .fn<OfflineCacheProvider['syncOutbox']>()
        .mockResolvedValue({ processed: 0, remaining: 0 }),
      runSyncCycle: jest
        .fn<OfflineCacheProvider['runSyncCycle']>()
        .mockResolvedValue(createSyncStatus()),
      getSyncStatus: jest
        .fn<OfflineCacheProvider['getSyncStatus']>()
        .mockResolvedValue(createSyncStatus()),
    } as jest.Mocked<OfflineCacheProvider>;

    infrastructureMocks = {
      request: jest.fn(),
    };
    infrastructure = infrastructureMocks as unknown as InfrastructureProvider;

    userIdentity = {
      getCurrentUser: jest.fn(async () => null),
      setCurrentUser: jest.fn(async () => undefined),
      getCurrentUserId: jest.fn(async () => ''),
      getUserId: jest.fn(() => null),
      clear: jest.fn(async () => undefined),
    } as unknown as jest.Mocked<UserIdentityProvider>;

    service = new ContentService(repo, {
      offlineCache,
      infrastructure,
      userIdentity,
    });
  });

  it('returns cached units with offline metadata', async () => {
    const units = await service.listUnits();

    expect(units).toHaveLength(1);
    expect(units[0]).toMatchObject({
      id: 'unit-1',
      cacheMode: 'minimal',
      downloadStatus: 'idle',
      syncedAt: expect.any(Number),
    });
    expect(units[0].learningObjectives).toEqual([
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
    ]);
    expect(repo.listUnits).not.toHaveBeenCalled();
  });

  it('returns cached unit detail when available', async () => {
    const cachedDetail: CachedUnitDetail = {
      ...baseUnit,
      cacheMode: 'full',
      downloadStatus: 'completed',
      lessons: [
        {
          id: 'lesson-1',
          unitId: 'unit-1',
          title: 'Lesson 1',
          position: 1,
          payload: {
            learner_level: 'beginner',
            package: {
              unit_learning_objective_ids: ['lo-1'],
              exercises: [
                {
                  id: 'exercise-1',
                  exercise_type: 'mcq',
                  lo_id: 'lo-1',
                },
              ],
              key_concepts: [],
            },
          },
          updatedAt: Date.now(),
          schemaVersion: 1,
        },
      ],
      assets: [],
    };
    offlineCache.getUnitDetail.mockImplementationOnce(async () => cachedDetail);

    const detail = await service.getUnitDetail('unit-1');

    expect(detail).not.toBeNull();
    expect(detail).toMatchObject({
      id: 'unit-1',
      lessons: expect.any(Array),
      cacheMode: 'full',
    });
    expect(detail?.learningObjectives).toEqual([
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
    ]);
    expect(detail?.lessons[0]).toMatchObject({
      learningObjectiveIds: ['lo-1'],
      learningObjectives: ['Objective 1 description'],
    });
    expect(repo.getUnitDetail).not.toHaveBeenCalled();
  });

  it('requests full unit download via offline cache', async () => {
    offlineCache.listUnits.mockImplementationOnce(async () => [baseUnit]);
    offlineCache.runSyncCycle.mockImplementationOnce(async () => ({
      lastPulledAt: null,
      lastCursor: null,
      pendingWrites: 0,
      cacheModeCounts: { minimal: 0, full: 0 },
      lastSyncAttempt: Date.now(),
      lastSyncResult: 'success',
      lastSyncError: null,
    }));

    await service.requestUnitDownload('unit-1');

    expect(offlineCache.cacheMinimalUnits).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({
          cacheMode: 'full',
          downloadStatus: 'pending',
        }),
      ])
    );
    expect(offlineCache.runSyncCycle).toHaveBeenCalledWith(
      expect.objectContaining({ force: true, payload: 'full' })
    );
    expect(offlineCache.downloadUnitAssets).toHaveBeenCalledWith('unit-1');
  });

  it('removes full downloads when requested', async () => {
    const detail: CachedUnitDetail = {
      ...baseUnit,
      downloadStatus: 'completed',
      downloadedAt: Date.now(),
      lessons: [],
      assets: [],
    };
    offlineCache.getUnitDetail.mockResolvedValueOnce(detail);

    await service.removeUnitDownload('unit-1');

    expect(offlineCache.setUnitCacheMode).toHaveBeenCalledWith(
      'unit-1',
      'minimal'
    );
  });

  it('resolves assets via offline cache provider', async () => {
    const asset: CachedAsset = {
      id: 'asset-1',
      unitId: 'unit-1',
      type: 'image',
      remoteUri: 'https://example.com/image.png',
      checksum: null,
      updatedAt: Date.now(),
      status: 'completed',
      localPath: 'file://cached.png',
      downloadedAt: Date.now(),
    };
    offlineCache.resolveAsset.mockImplementationOnce(async () => asset);

    const result = await service.resolveAsset('asset-1');
    expect(result).toEqual(asset);
    expect(offlineCache.resolveAsset).toHaveBeenCalledWith('asset-1');
  });

  it('adds unit to My Units and caches summary', async () => {
    const apiUnit: ApiUnitRead = {
      id: 'unit-2',
      title: 'Global Unit',
      description: 'Desc',
      learner_level: 'beginner',
      lesson_count: 3,
      status: 'completed',
      lesson_order: [],
      user_id: 99,
      is_global: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    repo.addUnitToMyUnits.mockResolvedValue({
      unit: apiUnit,
      is_in_my_units: true,
    });

    await service.addUnitToMyUnits(7, 'unit-2');

    expect(repo.addUnitToMyUnits).toHaveBeenCalledWith({
      userId: 7,
      unitId: 'unit-2',
    });
    expect(offlineCache.cacheMinimalUnits).toHaveBeenCalledWith([
      expect.objectContaining({ id: 'unit-2' }),
    ]);
  });

  it('removes unit from My Units and caches summary', async () => {
    const apiUnit: ApiUnitRead = {
      id: 'unit-3',
      title: 'Shared Unit',
      description: null,
      learner_level: 'advanced',
      lesson_count: 5,
      status: 'completed',
      lesson_order: ['l-1'],
      user_id: 5,
      is_global: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    repo.removeUnitFromMyUnits.mockResolvedValue({
      unit: apiUnit,
      is_in_my_units: false,
    });

    await service.removeUnitFromMyUnits(4, ' unit-3 ');

    expect(repo.removeUnitFromMyUnits).toHaveBeenCalledWith({
      userId: 4,
      unitId: 'unit-3',
    });
    // After removal, a force sync is triggered to refresh the cache
    expect(offlineCache.runSyncCycle).toHaveBeenCalledWith(
      expect.objectContaining({ force: true })
    );
  });

  it('throws content error when add to My Units validation fails', async () => {
    await expect(service.addUnitToMyUnits(0, 'unit-4')).rejects.toMatchObject({
      message: 'Valid user ID is required',
      code: 'CONTENT_SERVICE_ERROR',
    });
    expect(repo.addUnitToMyUnits).not.toHaveBeenCalled();
  });

  it('surfaces backend errors when removal fails', async () => {
    repo.removeUnitFromMyUnits.mockRejectedValue(new Error('Forbidden'));

    await expect(
      service.removeUnitFromMyUnits(3, 'unit-5')
    ).rejects.toMatchObject({
      message: 'Forbidden',
      code: 'CONTENT_SERVICE_ERROR',
    });
  });
});
