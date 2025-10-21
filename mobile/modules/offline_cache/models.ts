/**
 * Offline Cache Module - Models
 *
 * Type definitions for cached units, lessons, assets, and outbox records.
 */

export type CacheMode = 'minimal' | 'full';

export type DownloadStatus = 'idle' | 'pending' | 'completed' | 'failed';

export type AssetType = 'audio' | 'image';

export interface OfflineUnitSummaryPayload {
  id: string;
  title: string;
  description?: string | null;
  learner_level?: string;
  lesson_order?: string[];
  user_id?: number | null;
  is_global?: boolean;
  learning_objectives?: unknown;
  target_lesson_count?: number | null;
  source_material?: string | null;
  generated_from_topic?: boolean;
  flow_type?: string;
  status?: string;
  creation_progress?: unknown;
  error_message?: string | null;
  has_podcast?: boolean;
  podcast_voice?: string | null;
  podcast_duration_seconds?: number | null;
  podcast_audio_url?: string | null;
  podcast_transcript?: string | null;
  art_image_url?: string | null;
  art_image_description?: string | null;
  created_at?: string;
  updated_at?: string;
  schema_version?: number;
}

export interface CachedUnit {
  id: string;
  title: string;
  description: string;
  learnerLevel: string;
  isGlobal: boolean;
  updatedAt: number;
  schemaVersion: number;
  downloadStatus: DownloadStatus;
  cacheMode: CacheMode;
  downloadedAt?: number | null;
  syncedAt?: number | null;
  unitPayload?: OfflineUnitSummaryPayload | null;
}

export interface CachedLesson {
  id: string;
  unitId: string;
  title: string;
  position: number;
  payload: unknown;
  updatedAt: number;
  schemaVersion: number;
}

export interface CachedAsset {
  id: string;
  unitId: string;
  type: AssetType;
  remoteUri: string;
  checksum?: string | null;
  updatedAt: number;
  localPath?: string | null;
  status: DownloadStatus;
  downloadedAt?: number | null;
}

export interface CachedUnitDetail extends CachedUnit {
  lessons: CachedLesson[];
  assets: CachedAsset[];
}

export interface CachedUnitMetrics extends CachedUnit {
  lessonCount: number;
  assetCount: number;
  downloadedAssets: number;
  storageBytes: number;
}

export interface CacheOverview {
  units: CachedUnitMetrics[];
  totalStorageBytes: number;
  syncStatus: SyncStatus;
}

export interface OutboxRecord {
  id: string;
  endpoint: string;
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  payload: unknown;
  headers?: Record<string, string>;
  idempotencyKey: string;
  attempts: number;
  lastError?: string | null;
  nextAttemptAt: number;
  createdAt: number;
  updatedAt: number;
}

export interface OutboxRequest {
  id?: string;
  endpoint: string;
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  payload: unknown;
  headers?: Record<string, string>;
  idempotencyKey: string;
}

export interface SyncSnapshot {
  lastPulledAt?: number | null;
  lastCursor?: string | null;
  pendingWrites: number;
  cacheModeCounts: Record<CacheMode, number>;
}

export interface SyncStatus extends SyncSnapshot {
  lastSyncAttempt: number;
  lastSyncResult: 'idle' | 'success' | 'error';
  lastSyncError?: string | null;
}

export interface OfflineUnitPayload {
  id: string;
  title: string;
  description: string;
  learnerLevel: string;
  isGlobal: boolean;
  updatedAt: number;
  schemaVersion: number;
  cacheMode: CacheMode;
  downloadStatus?: DownloadStatus;
  downloadedAt?: number | null;
  syncedAt?: number | null;
  unitPayload?: OfflineUnitSummaryPayload | null;
}

export interface OfflineLessonPayload {
  id: string;
  unitId: string;
  title: string;
  position: number;
  payload: unknown;
  updatedAt: number;
  schemaVersion: number;
}

export interface OfflineAssetPayload {
  id: string;
  unitId: string;
  type: AssetType;
  remoteUri: string;
  checksum?: string | null;
  updatedAt: number;
}

export interface SyncPullArgs {
  cursor: string | null;
  payload: CacheMode;
}

export interface SyncPullResponse {
  units: OfflineUnitPayload[];
  lessons: OfflineLessonPayload[];
  assets: OfflineAssetPayload[];
  cursor: string | null;
}

export interface OfflineCacheConfig {
  assetDirectory: string;
  schemaVersion: number;
  maxOutboxAttempts: number;
  baseBackoffMs: number;
  maxBackoffMs: number;
}

export interface OutboxProcessResult {
  processed: number;
  remaining: number;
}

export type OutboxProcessor = (record: OutboxRecord) => Promise<void>;
