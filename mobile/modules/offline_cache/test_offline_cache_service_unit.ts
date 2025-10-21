import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  jest,
} from '@jest/globals';
import * as ExpoFileSystem from 'expo-file-system';
import type {
  OfflineCacheConfig,
  OfflineUnitPayload,
  OutboxProcessor,
} from './models';
import { OfflineCacheRepository, OFFLINE_CACHE_MIGRATIONS } from './repo';
import { OfflineCacheService } from './service';
import {
  FileSystemService,
  SQLiteDatabaseProvider,
} from '../infrastructure/public';

const fileSystemMock = ExpoFileSystem as any;

describe('OfflineCacheService', () => {
  let repository: OfflineCacheRepository;
  let service: OfflineCacheService;

  const baseConfig: OfflineCacheConfig = {
    assetDirectory: 'file://mock-cache',
    schemaVersion: 1,
    maxOutboxAttempts: 3,
    baseBackoffMs: 25,
    maxBackoffMs: 100,
  };

  beforeEach(async () => {
    if (typeof fileSystemMock.__reset === 'function') {
      fileSystemMock.__reset();
    }
    const provider = new SQLiteDatabaseProvider({
      databaseName: `test-${Date.now()}-${Math.random()}`,
      enableForeignKeys: true,
      migrations: OFFLINE_CACHE_MIGRATIONS,
    });
    repository = new OfflineCacheRepository(provider);
    const fileSystem = new FileSystemService();
    service = new OfflineCacheService(repository, fileSystem, baseConfig);
    await service.initialize();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('caches minimal units and retrieves them from SQLite', async () => {
    const payload: OfflineUnitPayload[] = [
      {
        id: 'unit-1',
        title: 'Intro Unit',
        description: 'Basics',
        learnerLevel: 'A1',
        isGlobal: true,
        updatedAt: Date.now(),
        schemaVersion: 1,
        cacheMode: 'minimal',
        unitPayload: {
          id: 'unit-1',
          title: 'Intro Unit',
          description: 'Basics',
          learner_level: 'A1',
          lesson_order: [],
          status: 'completed',
          updated_at: new Date().toISOString(),
          schema_version: 1,
        },
      },
    ];

    await service.cacheMinimalUnits(payload);
    const units = await service.listUnits();
    expect(units).toHaveLength(1);
    expect(units[0]).toMatchObject({ id: 'unit-1', cacheMode: 'minimal' });
  });

  it('downloads missing asset and updates SQLite metadata', async () => {
    const now = Date.now();
    await service.cacheFullUnit(
      {
        id: 'unit-asset',
        title: 'Asset Unit',
        description: 'Has assets',
        learnerLevel: 'B1',
        isGlobal: false,
        updatedAt: now,
        schemaVersion: 1,
        cacheMode: 'full',
        unitPayload: {
          id: 'unit-asset',
          title: 'Asset Unit',
          description: 'Has assets',
          learner_level: 'B1',
          lesson_order: [],
          status: 'completed',
          updated_at: new Date(now).toISOString(),
          schema_version: 1,
        },
      },
      [],
      [
        {
          id: 'asset-1',
          unitId: 'unit-asset',
          type: 'audio',
          remoteUri: 'https://example.com/audio.mp3',
          updatedAt: now,
        },
      ]
    );

    const resolved = await service.resolveAsset('asset-1');
    expect(resolved?.localPath).toContain('asset-1');
    expect(resolved?.status).toBe('completed');
  });

  it('queues outbox entries and applies exponential backoff on failure', async () => {
    await service.enqueueOutbox({
      endpoint: '/progress',
      method: 'POST',
      payload: { value: 42 },
      idempotencyKey: 'progress-1',
    });

    const failingProcessor: OutboxProcessor = async () => {
      throw new Error('network');
    };

    const firstAttempt = await service.processOutbox(failingProcessor);
    expect(firstAttempt.processed).toBe(0);

    const records = await repository.listOutbox();
    expect(records[0].attempts).toBe(1);
    expect(records[0].lastError).toBe('network');

    const noWork = await service.processOutbox(async () => undefined);
    expect(noWork.processed).toBe(0);
  });

  it('runs sync cycle, pushes outbox, pulls updates, and records status', async () => {
    jest.useFakeTimers();
    await service.enqueueOutbox({
      endpoint: '/progress',
      method: 'POST',
      payload: { score: 99 },
      idempotencyKey: 'sync-1',
    });

    const processor: OutboxProcessor = jest.fn(async () => undefined);
    const pull = jest.fn(async () => ({
      units: [
        {
          id: 'unit-sync',
          title: 'Synced Unit',
          description: 'Pulled from server',
          learnerLevel: 'B2',
          isGlobal: true,
          updatedAt: Date.now(),
          schemaVersion: 1,
          cacheMode: 'minimal' as const,
          unitPayload: {
            id: 'unit-sync',
            title: 'Synced Unit',
            description: 'Pulled from server',
            learner_level: 'B2',
            lesson_order: [],
            status: 'completed',
            updated_at: new Date().toISOString(),
            schema_version: 1,
          },
        },
      ],
      lessons: [],
      assets: [],
      cursor: 'cursor-1',
    }));

    const status = await service.runSyncCycle({ processor, pull });
    jest.useRealTimers();

    expect(processor).toHaveBeenCalled();
    expect(pull).toHaveBeenCalledWith(
      expect.objectContaining({ cursor: null, payload: 'minimal' })
    );
    expect(status.lastSyncResult).toBe('success');
    expect(status.lastCursor).toBe('cursor-1');
    expect(status.pendingWrites).toBe(0);

    const units = await service.listUnits();
    expect(units.find(unit => unit.id === 'unit-sync')).toBeTruthy();
  });

  it('deletes a cached unit and clears local asset files', async () => {
    const timestamp = Date.now();
    await service.cacheFullUnit(
      {
        id: 'unit-delete',
        title: 'Delete Me',
        description: 'Temporary',
        learnerLevel: 'B2',
        isGlobal: false,
        updatedAt: timestamp,
        schemaVersion: 1,
        cacheMode: 'full',
        unitPayload: {
          id: 'unit-delete',
          title: 'Delete Me',
          description: 'Temporary',
          learner_level: 'B2',
          lesson_order: [],
          status: 'completed',
          updated_at: new Date(timestamp).toISOString(),
          schema_version: 1,
        },
      },
      [
        {
          id: 'lesson-delete',
          unitId: 'unit-delete',
          title: 'Lesson',
          position: 1,
          payload: { content: 'hello' },
          updatedAt: timestamp,
          schemaVersion: 1,
        },
      ],
      [
        {
          id: 'asset-delete',
          unitId: 'unit-delete',
          type: 'audio',
          remoteUri: 'https://example.com/delete.mp3',
          updatedAt: timestamp,
        },
      ]
    );

    const resolved = await service.resolveAsset('asset-delete');
    expect(resolved?.localPath).toBeTruthy();
    if (!resolved?.localPath) {
      throw new Error('Expected resolved asset to include local path');
    }

    await service.deleteUnit('unit-delete');
    const unitsAfterDelete = await service.listUnits();
    expect(unitsAfterDelete.find(unit => unit.id === 'unit-delete')).toBeUndefined();

    const info = await fileSystemMock.getInfoAsync(resolved.localPath);
    expect(info.exists).toBe(false);
  });

  it('provides cache overview metrics including storage usage', async () => {
    const timestamp = Date.now();
    await service.cacheFullUnit(
      {
        id: 'unit-overview',
        title: 'Overview Unit',
        description: 'Stats',
        learnerLevel: 'C1',
        isGlobal: true,
        updatedAt: timestamp,
        schemaVersion: 1,
        cacheMode: 'full',
        unitPayload: {
          id: 'unit-overview',
          title: 'Overview Unit',
          description: 'Stats',
          learner_level: 'C1',
          lesson_order: ['lesson-1', 'lesson-2'],
          status: 'completed',
          updated_at: new Date(timestamp).toISOString(),
          schema_version: 1,
        },
      },
      [
        {
          id: 'lesson-1',
          unitId: 'unit-overview',
          title: 'Lesson 1',
          position: 1,
          payload: { value: 1 },
          updatedAt: timestamp,
          schemaVersion: 1,
        },
        {
          id: 'lesson-2',
          unitId: 'unit-overview',
          title: 'Lesson 2',
          position: 2,
          payload: { value: 2 },
          updatedAt: timestamp,
          schemaVersion: 1,
        },
      ],
      [
        {
          id: 'asset-keep',
          unitId: 'unit-overview',
          type: 'image',
          remoteUri: 'https://example.com/art.png',
          updatedAt: timestamp,
        },
      ]
    );

    await service.resolveAsset('asset-keep');
    const overview = await service.getCacheOverview();

    expect(overview.totalStorageBytes).toBeGreaterThan(0);
    expect(overview.units).toHaveLength(1);
    const [unitMetrics] = overview.units;
    expect(unitMetrics.lessonCount).toBe(2);
    expect(unitMetrics.assetCount).toBe(1);
    expect(unitMetrics.downloadedAssets).toBe(1);
    expect(unitMetrics.storageBytes).toBeGreaterThan(0);
    expect(overview.syncStatus).toHaveProperty('pendingWrites');
  });

  it('preserves asset local paths during incremental sync', async () => {
    const now = Date.now();
    const unitId = 'unit-incremental';
    const assetId = 'asset-preserved';

    // Initial cache: download a full unit with assets
    await service.cacheFullUnit(
      {
        id: unitId,
        title: 'Incremental Unit',
        description: 'Has assets',
        learnerLevel: 'A2',
        isGlobal: false,
        updatedAt: now,
        schemaVersion: 1,
        cacheMode: 'full',
      },
      [
        {
          id: 'lesson-1',
          unitId,
          title: 'Lesson 1',
          position: 1,
          payload: { content: 'test' },
          updatedAt: now,
          schemaVersion: 1,
        },
      ],
      [
        {
          id: assetId,
          unitId,
          type: 'audio',
          remoteUri: 'https://example.com/audio.mp3',
          checksum: 'abc123',
          updatedAt: now,
        },
      ]
    );

    // Download the asset to set local path
    const resolvedAsset = await service.resolveAsset(assetId);
    expect(resolvedAsset?.localPath).toBeTruthy();
    const originalLocalPath = resolvedAsset?.localPath;

    // Run sync that returns the same asset (unchanged checksum and updatedAt)
    const processor: OutboxProcessor = jest.fn(async () => undefined);
    const pull = jest.fn(async () => ({
      units: [
        {
          id: unitId,
          title: 'Incremental Unit Updated',
          description: 'Has assets',
          learnerLevel: 'A2',
          isGlobal: false,
          updatedAt: now + 1000, // Unit metadata changed
          schemaVersion: 1,
          cacheMode: 'full' as const,
        },
      ],
      lessons: [
        {
          id: 'lesson-1',
          unitId,
          title: 'Lesson 1 Updated',
          position: 1,
          payload: { content: 'updated' },
          updatedAt: now + 1000,
          schemaVersion: 1,
        },
      ],
      assets: [
        {
          id: assetId,
          unitId,
          type: 'audio' as const,
          remoteUri: 'https://example.com/audio.mp3',
          checksum: 'abc123', // Same checksum
          updatedAt: now, // Same updatedAt
        },
      ],
      cursor: 'cursor-incremental',
    }));

    await service.runSyncCycle({ processor, pull });

    // Verify asset still has local path preserved
    const unitDetail = await service.getUnitDetail(unitId);
    expect(unitDetail).toBeTruthy();
    const asset = unitDetail?.assets.find(a => a.id === assetId);
    expect(asset).toBeTruthy();
    expect(asset?.localPath).toBe(originalLocalPath);
    expect(asset?.status).toBe('completed');
    expect(asset?.downloadedAt).toBeTruthy();

    // Verify lesson was updated
    const lesson = unitDetail?.lessons.find(l => l.id === 'lesson-1');
    expect(lesson?.title).toBe('Lesson 1 Updated');
  });

  it('resets asset local path when asset content changes', async () => {
    const now = Date.now();
    const unitId = 'unit-changed';
    const assetId = 'asset-changed';

    // Initial cache with asset
    await service.cacheFullUnit(
      {
        id: unitId,
        title: 'Changed Unit',
        description: 'Assets will change',
        learnerLevel: 'B1',
        isGlobal: false,
        updatedAt: now,
        schemaVersion: 1,
        cacheMode: 'full',
      },
      [],
      [
        {
          id: assetId,
          unitId,
          type: 'audio',
          remoteUri: 'https://example.com/audio.mp3',
          checksum: 'old-checksum',
          updatedAt: now,
        },
      ]
    );

    // Download the asset
    const resolvedAsset = await service.resolveAsset(assetId);
    expect(resolvedAsset?.localPath).toBeTruthy();

    // Sync with changed asset (different checksum)
    const processor: OutboxProcessor = jest.fn(async () => undefined);
    const pull = jest.fn(async () => ({
      units: [
        {
          id: unitId,
          title: 'Changed Unit',
          description: 'Assets will change',
          learnerLevel: 'B1',
          isGlobal: false,
          updatedAt: now + 1000,
          schemaVersion: 1,
          cacheMode: 'full' as const,
        },
      ],
      lessons: [],
      assets: [
        {
          id: assetId,
          unitId,
          type: 'audio' as const,
          remoteUri: 'https://example.com/audio-v2.mp3',
          checksum: 'new-checksum', // Changed!
          updatedAt: now + 1000,
        },
      ],
      cursor: 'cursor-changed',
    }));

    await service.runSyncCycle({ processor, pull });

    // Verify asset local path was reset (needs re-download)
    const unitDetail = await service.getUnitDetail(unitId);
    const asset = unitDetail?.assets.find(a => a.id === assetId);
    expect(asset).toBeTruthy();
    expect(asset?.localPath).toBeNull();
    expect(asset?.status).toBe('pending');
    expect(asset?.checksum).toBe('new-checksum');
  });
});
