/**
 * Offline Cache Module - Service Layer
 *
 * Coordinates caching flows, asset downloads, outbox processing, and sync orchestration.
 */

import {
  FileSystemService,
  OLDEST_SUPPORTED_UNIT_SCHEMA,
} from '../infrastructure/public';
import { OfflineCacheRepository } from './repo';
import type {
  CacheOverview,
  CachedAsset,
  CachedLesson,
  CachedUnit,
  CachedUnitDetail,
  CachedUnitMetrics,
  CacheMode,
  DownloadStatus,
  OfflineAssetPayload,
  OfflineCacheConfig,
  OfflineLessonPayload,
  OfflineUnitPayload,
  OutboxProcessResult,
  OutboxProcessor,
  OutboxRequest,
  SyncPullArgs,
  SyncPullResponse,
  SyncSnapshot,
  SyncStatus,
} from './models';

const META_LAST_CURSOR = 'offline_cache_last_cursor';
const META_LAST_PULL_AT = 'offline_cache_last_pull_at';
const META_LAST_SYNC = 'offline_cache_last_sync_status';

export interface SyncCycleOptions {
  processor: OutboxProcessor;
  pull: (args: SyncPullArgs) => Promise<SyncPullResponse>;
  force?: boolean;
}

export class OfflineCacheService {
  private repository: OfflineCacheRepository;
  private fileSystem: FileSystemService;
  private config: OfflineCacheConfig;
  private status: SyncStatus | null = null;

  constructor(
    repository: OfflineCacheRepository,
    fileSystem: FileSystemService,
    config: OfflineCacheConfig
  ) {
    this.repository = repository;
    this.fileSystem = fileSystem;
    this.config = config;
  }

  async initialize(): Promise<void> {
    await this.repository.initialize();
    const schemaVersion = Math.max(
      this.config.schemaVersion,
      OLDEST_SUPPORTED_UNIT_SCHEMA
    );
    await this.repository.deleteUnitsBelowSchemaVersion(schemaVersion);
    this.status = await this.refreshSyncStatus();
  }

  async listUnits(): Promise<CachedUnit[]> {
    return this.repository.listUnits();
  }

  async getUnitDetail(unitId: string): Promise<CachedUnitDetail | null> {
    return this.repository.buildUnitDetail(unitId);
  }

  async cacheMinimalUnits(units: OfflineUnitPayload[]): Promise<void> {
    if (units.length === 0) {
      return;
    }
    const mapped = units.map(unit => this.mapUnitPayload(unit));
    await this.repository.upsertUnits(mapped);
    this.status = await this.refreshSyncStatus();
  }

  async cacheFullUnit(
    unit: OfflineUnitPayload,
    lessons: OfflineLessonPayload[],
    assets: OfflineAssetPayload[]
  ): Promise<void> {
    const cachedUnit = this.mapUnitPayload({
      ...unit,
      cacheMode: 'full',
      downloadStatus: unit.downloadStatus ?? 'completed',
      downloadedAt: Date.now(),
    });
    await this.repository.upsertUnits([cachedUnit]);

    const cachedLessons = lessons.map(this.mapLessonPayload);
    await this.repository.replaceLessons(unit.id, cachedLessons);

    const cachedAssets = assets.map(asset => this.mapAssetPayload(asset));
    await this.repository.replaceAssets(unit.id, cachedAssets);

    this.status = await this.refreshSyncStatus();
  }

  async markUnitCacheMode(unitId: string, cacheMode: CacheMode): Promise<void> {
    const unit = await this.repository.getUnit(unitId);
    if (!unit) {
      return;
    }

    const updated: CachedUnit = {
      ...unit,
      cacheMode,
      downloadStatus: cacheMode === 'full' ? unit.downloadStatus : 'idle',
      downloadedAt:
        cacheMode === 'full' ? (unit.downloadedAt ?? Date.now()) : null,
    };
    await this.repository.upsertUnits([updated]);

    if (cacheMode === 'minimal') {
      await this.repository.replaceLessons(unitId, []);
      await this.repository.removeAssets(unitId);
    }

    this.status = await this.refreshSyncStatus();
  }

  async deleteUnit(unitId: string): Promise<void> {
    const detail = await this.repository.buildUnitDetail(unitId);
    if (detail) {
      await Promise.all(
        detail.assets.map(async asset => {
          if (asset.localPath) {
            await this.fileSystem.deleteFile(asset.localPath);
          }
        })
      );
    }
    await this.repository.deleteUnit(unitId);
    this.status = await this.refreshSyncStatus();
  }

  async clearAll(): Promise<void> {
    console.log('[OfflineCache] Clearing all cached data');

    const assets = await this.repository.listAllAssets();
    console.log('[OfflineCache] Deleting asset files', {
      assetCount: assets.length,
    });

    await Promise.all(
      assets.map(async asset => {
        if (asset.localPath) {
          await this.fileSystem.deleteFile(asset.localPath);
        }
      })
    );

    await this.repository.clearAll();
    this.status = await this.refreshSyncStatus();

    console.log('[OfflineCache] All cached data cleared');
  }

  async resolveAsset(assetId: string): Promise<CachedAsset | null> {
    const asset = await this.repository.getAssetById(assetId);
    if (!asset) {
      return null;
    }

    if (asset.localPath) {
      const info = await this.fileSystem.getInfo(asset.localPath);
      if (info.exists) {
        return asset;
      }
    }

    const targetPath = this.buildAssetPath(asset);
    const download = await this.fileSystem.downloadFile(
      asset.remoteUri,
      targetPath,
      {
        skipIfExists: true,
      }
    );
    if (download.status === 'completed') {
      const timestamp = Date.now();
      await this.repository.updateAssetLocation(
        asset.id,
        download.uri,
        'completed',
        timestamp
      );
      return {
        ...asset,
        localPath: download.uri,
        status: 'completed',
        downloadedAt: timestamp,
      };
    }

    return {
      ...asset,
      status: 'failed',
    };
  }

  async downloadUnitAssets(unitId: string): Promise<void> {
    console.log('[OfflineCache] Starting asset download', { unitId });

    const unit = await this.repository.getUnit(unitId);
    if (!unit) {
      console.warn('[OfflineCache] Unit not found for download', { unitId });
      return;
    }

    // Mark as in progress
    await this.repository.upsertUnits([
      {
        ...unit,
        downloadStatus: 'in_progress',
      },
    ]);
    console.log('[OfflineCache] Marked unit as in_progress', { unitId });

    const detail = await this.repository.buildUnitDetail(unitId);
    if (!detail) {
      console.warn('[OfflineCache] Unit detail not found', { unitId });
      return;
    }

    console.log('[OfflineCache] AssetDownload: Downloading assets', {
      unitId,
      assetCount: detail.assets.length,
    });

    // Download all assets
    await Promise.allSettled(
      detail.assets.map(async asset => {
        if (asset.localPath) {
          const info = await this.fileSystem.getInfo(asset.localPath);
          if (info.exists) {
            console.log(
              '[OfflineCache] AssetDownload: Asset already downloaded',
              {
                localPath: asset.localPath,
              }
            );
            return; // Already downloaded
          }
        }

        const targetPath = this.buildAssetPath(asset);
        try {
          console.log('[OfflineCache] AssetDownload: Downloading asset', {
            remoteUri: asset.remoteUri,
            targetPath,
          });
          const download = await this.fileSystem.downloadFile(
            asset.remoteUri,
            targetPath,
            { skipIfExists: true }
          );
          console.log('[OfflineCache] AssetDownload: Download result', {
            status: download.status,
            uri: download.uri,
            bytesWritten: download.bytesWritten,
          });
          if (download.status === 'completed') {
            await this.repository.updateAssetLocation(
              asset.id,
              download.uri,
              'completed',
              Date.now()
            );
          }
        } catch (error) {
          console.error('[OfflineCache] AssetDownload: Error', {
            error,
            assetId: asset.id,
          });
        }
      })
    );

    // Mark as completed
    const updatedUnit = await this.repository.getUnit(unitId);
    if (updatedUnit) {
      await this.repository.upsertUnits([
        {
          ...updatedUnit,
          downloadStatus: 'completed',
          downloadedAt: Date.now(),
        },
      ]);
      console.log('[OfflineCache] AssetDownload: Unit download completed', {
        unitId,
      });
    }

    this.status = await this.refreshSyncStatus();
  }

  async enqueueOutbox(request: OutboxRequest): Promise<void> {
    const recordId = request.id ?? this.generateId();
    const record: OutboxRequest & { id: string } = {
      ...request,
      id: recordId,
    };
    await this.repository.enqueueOutbox(record, Date.now());
    this.status = await this.refreshSyncStatus();
  }

  async processOutbox(
    processor: OutboxProcessor
  ): Promise<OutboxProcessResult> {
    const now = Date.now();
    const records = await this.repository.listOutbox();
    const due = records.find(item => item.nextAttemptAt <= now);
    if (!due) {
      const remaining = await this.repository.countOutbox();
      return { processed: 0, remaining };
    }

    try {
      await processor(due);
      await this.repository.deleteOutbox(due.id);
      const remaining = await this.repository.countOutbox();
      this.status = await this.refreshSyncStatus();
      return { processed: 1, remaining };
    } catch (error: any) {
      const attempts = due.attempts + 1;
      const delay = Math.min(
        this.config.baseBackoffMs * Math.pow(2, attempts - 1),
        this.config.maxBackoffMs
      );
      const nextAttemptAt = Date.now() + delay;
      await this.repository.updateOutboxFailure(
        due.id,
        attempts,
        error?.message || String(error),
        nextAttemptAt,
        Date.now()
      );
      const remaining = await this.repository.countOutbox();
      this.status = await this.refreshSyncStatus();
      return { processed: 0, remaining };
    }
  }

  async runSyncCycle(options: SyncCycleOptions): Promise<SyncStatus> {
    const startedAt = Date.now();
    let lastError: string | null = null;

    console.log('[OfflineCache] Starting sync cycle', {
      force: options.force,
      timestamp: new Date().toISOString(),
    });

    try {
      // Push pending writes
      // Attempt to process due records until none remain
      // but avoid tight loop if processor returns failures
      for (let i = 0; i < this.config.maxOutboxAttempts; i += 1) {
        const result = await this.processOutbox(options.processor);
        if (result.processed === 0) {
          break;
        }
      }

      // Use cursor for incremental sync, or null for full sync when forced
      const cursor = options.force
        ? null
        : (await this.repository.getMetadata(META_LAST_CURSOR)) || null;
      const units = await this.repository.listUnits();
      const payload: CacheMode = units.some(unit => unit.cacheMode === 'full')
        ? 'full'
        : 'minimal';

      console.log('[OfflineCache] Pulling updates', {
        cursor: cursor ? new Date(cursor).toISOString() : 'null',
        payload,
        cachedUnitCount: units.length,
        force: options.force,
      });

      const response = await options.pull({ cursor, payload });

      console.log('[OfflineCache] Received sync response', {
        units: response.units.length,
        lessons: response.lessons.length,
        assets: response.assets.length,
        cursor: response.cursor
          ? new Date(response.cursor).toISOString()
          : 'null',
      });

      await this.applySyncPull(response);

      await this.repository.setMetadata(META_LAST_PULL_AT, String(Date.now()));
      await this.persistLastSyncStatus({
        lastSyncAttempt: startedAt,
        lastSyncResult: 'success',
        lastSyncError: null,
      });

      console.log('[OfflineCache] Sync cycle completed successfully', {
        duration: Date.now() - startedAt,
      });
    } catch (error: any) {
      lastError = error?.message || String(error);
      console.error('[OfflineCache] Sync cycle failed', {
        error: lastError,
        duration: Date.now() - startedAt,
      });
      await this.persistLastSyncStatus({
        lastSyncAttempt: startedAt,
        lastSyncResult: 'error',
        lastSyncError: lastError,
      });
    }

    this.status = await this.refreshSyncStatus();
    if (lastError) {
      this.status = {
        ...this.status,
        lastSyncResult: 'error',
        lastSyncError: lastError,
        lastSyncAttempt: startedAt,
      };
    }
    return this.status;
  }

  async getSyncStatus(): Promise<SyncStatus> {
    if (!this.status) {
      this.status = await this.refreshSyncStatus();
    }
    return this.status;
  }

  async getCacheOverview(): Promise<CacheOverview> {
    const units = await this.repository.listUnits();
    const metrics = await Promise.all(
      units.map(async unit => {
        const detail = await this.repository.buildUnitDetail(unit.id);
        let lessonCount = 0;
        let assetCount = 0;
        let downloadedAssets = 0;
        let storageBytes = 0;

        if (detail) {
          lessonCount = detail.lessons.length;
          assetCount = detail.assets.length;
          await Promise.all(
            detail.assets.map(async asset => {
              if (!asset.localPath) {
                return;
              }
              const info = await this.fileSystem.getInfo(asset.localPath);
              if (info.exists) {
                downloadedAssets += 1;
                storageBytes += info.size ?? 0;
              }
            })
          );
        }

        const metricsEntry: CachedUnitMetrics = {
          ...unit,
          lessonCount,
          assetCount,
          downloadedAssets,
          storageBytes,
        };
        return metricsEntry;
      })
    );

    const totalStorageBytes = metrics.reduce(
      (sum, metric) => sum + metric.storageBytes,
      0
    );
    const syncStatus = await this.getSyncStatus();
    return { units: metrics, totalStorageBytes, syncStatus };
  }

  private mapUnitPayload(payload: OfflineUnitPayload): CachedUnit {
    const downloadStatus: DownloadStatus =
      payload.downloadStatus ?? 'completed';
    return {
      id: payload.id,
      title: payload.title,
      description: payload.description,
      learnerLevel: payload.learnerLevel,
      isGlobal: payload.isGlobal,
      updatedAt: payload.updatedAt,
      schemaVersion: payload.schemaVersion,
      downloadStatus,
      cacheMode: payload.cacheMode,
      downloadedAt: payload.downloadedAt ?? null,
      syncedAt: payload.syncedAt ?? null,
      unitPayload: payload.unitPayload ?? null,
    };
  }

  private mapLessonPayload = (payload: OfflineLessonPayload): CachedLesson => ({
    id: payload.id,
    unitId: payload.unitId,
    title: payload.title,
    position: payload.position,
    payload: payload.payload,
    updatedAt: payload.updatedAt,
    schemaVersion: payload.schemaVersion,
  });

  private mapAssetPayload(payload: OfflineAssetPayload): CachedAsset {
    return {
      id: payload.id,
      unitId: payload.unitId,
      type: payload.type,
      remoteUri: payload.remoteUri,
      checksum: payload.checksum ?? null,
      updatedAt: payload.updatedAt,
      status: 'pending',
      localPath: null,
      downloadedAt: null,
    };
  }

  private buildAssetPath(asset: CachedAsset): string {
    const extension = asset.type === 'audio' ? '.mp3' : '.img';
    return `${this.config.assetDirectory}/${asset.id}${extension}`;
  }

  private async applySyncPull(response: SyncPullResponse): Promise<void> {
    console.log('[OfflineCache] Applying sync pull', {
      units: response.units.length,
      lessons: response.lessons.length,
      assets: response.assets.length,
      cursor: response.cursor,
    });

    if (response.units.length > 0) {
      await this.repository.upsertUnits(
        response.units.map(unit => this.mapUnitPayload(unit))
      );
      console.log('[OfflineCache] Upserted units', {
        count: response.units.length,
        unitIds: response.units.map(u => u.id),
      });
    }

    // Upsert lessons incrementally (no deletion, preserves unchanged lessons)
    if (response.lessons.length > 0) {
      const mapped = response.lessons.map(this.mapLessonPayload);
      await this.repository.upsertLessons(mapped);
      console.log('[OfflineCache] Upserted lessons', { count: mapped.length });
    }

    // Upsert assets incrementally, preserving local metadata for unchanged assets
    if (response.assets.length > 0) {
      const mapped = await this.mergeAssetMetadata(response.assets);
      await this.repository.upsertAssets(mapped);
      console.log('[OfflineCache] Upserted assets', { count: mapped.length });
    }

    if (response.cursor !== null) {
      await this.repository.setMetadata(META_LAST_CURSOR, response.cursor);
      console.log('[OfflineCache] Updated cursor', {
        cursor: response.cursor,
      });
    }
  }

  private async mergeAssetMetadata(
    incomingAssets: OfflineAssetPayload[]
  ): Promise<CachedAsset[]> {
    // Fetch all existing assets to check for local metadata
    const assetIds = incomingAssets.map(a => a.id);
    const existingMap = new Map<string, CachedAsset>();

    // Batch fetch existing assets
    for (const assetId of assetIds) {
      const existing = await this.repository.getAssetById(assetId);
      if (existing) {
        existingMap.set(assetId, existing);
      }
    }

    // Map incoming assets, preserving local metadata when asset hasn't changed
    return incomingAssets.map(incomingAsset => {
      const newAsset = this.mapAssetPayload(incomingAsset);
      const existingAsset = existingMap.get(incomingAsset.id);

      // If asset exists and hasn't changed (same checksum & updatedAt), preserve local metadata
      if (
        existingAsset &&
        existingAsset.checksum === newAsset.checksum &&
        existingAsset.updatedAt === newAsset.updatedAt &&
        existingAsset.localPath
      ) {
        return {
          ...newAsset,
          localPath: existingAsset.localPath,
          status: existingAsset.status,
          downloadedAt: existingAsset.downloadedAt,
        };
      }

      return newAsset;
    });
  }

  private async refreshSyncStatus(): Promise<SyncStatus> {
    const units = await this.repository.listUnits();
    const pendingWrites = await this.repository.countOutbox();
    const cacheModeCounts: Record<CacheMode, number> = {
      minimal: 0,
      full: 0,
    };
    units.forEach(unit => {
      cacheModeCounts[unit.cacheMode] += 1;
    });

    const lastCursor = await this.repository.getMetadata(META_LAST_CURSOR);
    const lastPulledAtRaw =
      await this.repository.getMetadata(META_LAST_PULL_AT);
    const lastPulledAt = lastPulledAtRaw ? Number(lastPulledAtRaw) : null;
    const persistedStatus = await this.loadLastSyncStatus();

    const snapshot: SyncSnapshot = {
      lastCursor: lastCursor ?? null,
      lastPulledAt,
      pendingWrites,
      cacheModeCounts,
    };

    return {
      ...snapshot,
      ...persistedStatus,
    };
  }

  private async loadLastSyncStatus(): Promise<
    Pick<SyncStatus, 'lastSyncAttempt' | 'lastSyncResult' | 'lastSyncError'>
  > {
    const raw = await this.repository.getMetadata(META_LAST_SYNC);
    if (!raw) {
      return {
        lastSyncAttempt: 0,
        lastSyncResult: 'idle',
        lastSyncError: null,
      };
    }
    try {
      const parsed = JSON.parse(raw);
      return {
        lastSyncAttempt: parsed.lastSyncAttempt ?? 0,
        lastSyncResult: parsed.lastSyncResult ?? 'idle',
        lastSyncError: parsed.lastSyncError ?? null,
      };
    } catch {
      return {
        lastSyncAttempt: 0,
        lastSyncResult: 'idle',
        lastSyncError: null,
      };
    }
  }

  private async persistLastSyncStatus(status: {
    lastSyncAttempt: number;
    lastSyncResult: SyncStatus['lastSyncResult'];
    lastSyncError: string | null;
  }): Promise<void> {
    await this.repository.setMetadata(META_LAST_SYNC, JSON.stringify(status));
  }

  private generateId(): string {
    const random = Math.random().toString(36).slice(2);
    return `outbox_${Date.now()}_${random}`;
  }
}
