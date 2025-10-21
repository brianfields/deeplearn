import { afterEach, beforeEach, describe, expect, it, jest } from '@jest/globals';
import type { OfflineCacheConfig, OfflineUnitPayload, OutboxProcessor } from './models';
import { OfflineCacheRepository, OFFLINE_CACHE_MIGRATIONS } from './repo';
import { OfflineCacheService } from './service';
import {
  FileSystemService,
  SQLiteDatabaseProvider,
} from '../infrastructure/public';

const fileSystemMock = require('expo-file-system');

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
});
