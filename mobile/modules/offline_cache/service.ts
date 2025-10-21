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
  CachedAsset,
  CachedLesson,
  CachedUnit,
  CachedUnitDetail,
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

      const cursor =
        (await this.repository.getMetadata(META_LAST_CURSOR)) || null;
      const units = await this.repository.listUnits();
      const payload: CacheMode = units.some(unit => unit.cacheMode === 'full')
        ? 'full'
        : 'minimal';

      const response = await options.pull({ cursor, payload });
      await this.applySyncPull(response);

      await this.repository.setMetadata(META_LAST_PULL_AT, String(Date.now()));
      await this.persistLastSyncStatus({
        lastSyncAttempt: startedAt,
        lastSyncResult: 'success',
        lastSyncError: null,
      });
    } catch (error: any) {
      lastError = error?.message || String(error);
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
    if (response.units.length > 0) {
      await this.repository.upsertUnits(
        response.units.map(unit => this.mapUnitPayload(unit))
      );
    }

    // Upsert lessons incrementally (no deletion, preserves unchanged lessons)
    if (response.lessons.length > 0) {
      const mapped = response.lessons.map(this.mapLessonPayload);
      await this.repository.upsertLessons(mapped);
    }

    // Upsert assets incrementally, preserving local metadata for unchanged assets
    if (response.assets.length > 0) {
      const mapped = await this.mergeAssetMetadata(response.assets);
      await this.repository.upsertAssets(mapped);
    }

    if (response.cursor !== null) {
      await this.repository.setMetadata(META_LAST_CURSOR, response.cursor);
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
