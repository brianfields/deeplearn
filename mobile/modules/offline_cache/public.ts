/**
 * Offline Cache Module - Public Interface
 *
 * Provides access to the offline cache service for other modules.
 */

import * as FileSystem from 'expo-file-system';
import { infrastructureProvider } from '../infrastructure/public';
import { OfflineCacheRepository, OFFLINE_CACHE_MIGRATIONS } from './repo';
import { OfflineCacheService, SyncCycleOptions } from './service';
import type {
  CacheMode,
  CacheOverview,
  CachedAsset,
  CachedUnit,
  CachedUnitDetail,
  OfflineAssetPayload,
  OfflineLessonPayload,
  OfflineUnitPayload,
  OutboxProcessResult,
  OutboxProcessor,
  OutboxRequest,
  SyncStatus,
} from './models';

export interface OfflineCacheProvider {
  listUnits(): Promise<CachedUnit[]>;
  getUnitDetail(unitId: string): Promise<CachedUnitDetail | null>;
  cacheMinimalUnits(units: OfflineUnitPayload[]): Promise<void>;
  cacheFullUnit(
    unit: OfflineUnitPayload,
    lessons: OfflineLessonPayload[],
    assets: OfflineAssetPayload[]
  ): Promise<void>;
  setUnitCacheMode(unitId: string, cacheMode: CacheMode): Promise<void>;
  resolveAsset(assetId: string): Promise<CachedAsset | null>;
  downloadUnitAssets(unitId: string): Promise<void>;
  enqueueOutbox(request: OutboxRequest): Promise<void>;
  processOutbox(processor: OutboxProcessor): Promise<OutboxProcessResult>;
  syncOutbox(
    httpRequest: (
      endpoint: string,
      options: {
        method: string;
        headers: Record<string, string>;
        body?: string;
      }
    ) => Promise<unknown>
  ): Promise<OutboxProcessResult>;
  runSyncCycle(options: SyncCycleOptions): Promise<SyncStatus>;
  getSyncStatus(): Promise<SyncStatus>;
  deleteUnit(unitId: string): Promise<void>;
  clearAll(): Promise<void>;
  getCacheOverview(): Promise<CacheOverview>;
}

let servicePromise: Promise<OfflineCacheService> | null = null;

async function ensureService(): Promise<OfflineCacheService> {
  if (!servicePromise) {
    servicePromise = initializeService();
  }
  return servicePromise;
}

async function initializeService(): Promise<OfflineCacheService> {
  const infrastructure = infrastructureProvider();
  const sqliteProvider = await infrastructure.createSQLiteProvider({
    databaseName: 'offline_unit_cache.db',
    enableForeignKeys: true,
    migrations: OFFLINE_CACHE_MIGRATIONS,
  });
  const fileSystem = infrastructure.getFileSystem();
  const repository = new OfflineCacheRepository(sqliteProvider);
  const assetRoot = (FileSystem.documentDirectory ?? 'file://documents')
    .replace(/\/$/, '')
    .concat('/offline-cache');
  const service = new OfflineCacheService(repository, fileSystem, {
    assetDirectory: assetRoot,
    schemaVersion: 1,
    maxOutboxAttempts: 5,
    baseBackoffMs: 1000,
    maxBackoffMs: 60000,
  });
  await service.initialize();
  return service;
}

export function offlineCacheProvider(): OfflineCacheProvider {
  return {
    async listUnits() {
      const service = await ensureService();
      return service.listUnits();
    },
    async getUnitDetail(unitId: string) {
      const service = await ensureService();
      return service.getUnitDetail(unitId);
    },
    async cacheMinimalUnits(units: OfflineUnitPayload[]) {
      const service = await ensureService();
      await service.cacheMinimalUnits(units);
    },
    async cacheFullUnit(
      unit: OfflineUnitPayload,
      lessons: OfflineLessonPayload[],
      assets: OfflineAssetPayload[]
    ) {
      const service = await ensureService();
      await service.cacheFullUnit(unit, lessons, assets);
    },
    async setUnitCacheMode(unitId: string, cacheMode: CacheMode) {
      const service = await ensureService();
      await service.setUnitCacheMode(unitId, cacheMode);
    },
    async resolveAsset(assetId: string) {
      const service = await ensureService();
      return service.resolveAsset(assetId);
    },
    async downloadUnitAssets(unitId: string) {
      const service = await ensureService();
      await service.downloadUnitAssets(unitId);
    },
    async deleteUnit(unitId: string) {
      const service = await ensureService();
      await service.deleteUnit(unitId);
    },
    async clearAll() {
      const service = await ensureService();
      await service.clearAll();
    },
    async enqueueOutbox(request: OutboxRequest) {
      const service = await ensureService();
      await service.enqueueOutbox(request);
    },
    async processOutbox(processor: OutboxProcessor) {
      const service = await ensureService();
      return service.processOutbox(processor);
    },
    async syncOutbox(httpRequest) {
      const service = await ensureService();
      return service.syncOutbox(httpRequest);
    },
    async runSyncCycle(options: SyncCycleOptions) {
      const service = await ensureService();
      return service.runSyncCycle(options);
    },
    async getSyncStatus() {
      const service = await ensureService();
      return service.getSyncStatus();
    },
    async getCacheOverview() {
      const service = await ensureService();
      return service.getCacheOverview();
    },
  };
}

export type {
  CachedUnit,
  CachedUnitDetail,
  CachedAsset,
  CachedUnitMetrics,
  CacheOverview,
  CacheMode,
  DownloadStatus,
  OfflineUnitPayload,
  OfflineLessonPayload,
  OfflineAssetPayload,
  OfflineUnitSummaryPayload,
  OutboxRecord,
  OutboxRequest,
  OutboxProcessor,
  OutboxProcessResult,
  SyncPullArgs,
  SyncPullResponse,
  SyncStatus,
} from './models';
export type { SyncCycleOptions } from './service';
