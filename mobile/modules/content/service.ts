import {
  ContentRepo,
  type ApiUnitSyncEntry,
  type ApiUnitSyncResponse,
} from './repo';
import type {
  ApiUnitDetail,
  ApiUnitSummary,
  ContentError,
  Unit,
  UnitDetail,
  UpdateUnitSharingRequest,
  UserUnitCollections,
} from './models';
import { toUnitDTO, toUnitDetailDTO } from './models';
import {
  offlineCacheProvider,
  type CachedAsset,
  type CachedUnit,
  type CachedUnitDetail,
  type CacheMode,
  type DownloadStatus,
  type OfflineAssetPayload,
  type OfflineCacheProvider,
  type OfflineLessonPayload,
  type OfflineUnitPayload,
  type OfflineUnitSummaryPayload,
  type OutboxRecord,
  type SyncPullArgs,
  type SyncPullResponse,
  type SyncStatus,
} from '../offline_cache/public';
import {
  infrastructureProvider,
  type InfrastructureProvider,
} from '../infrastructure/public';
import {
  userIdentityProvider,
  type UserIdentityProvider,
} from '../user/public';

type NullableNumber = number | null | undefined;

type ListUnitsParams = {
  limit?: number;
  offset?: number;
  currentUserId?: number | null;
};

type UnitDetailOptions = { currentUserId?: number | null };

type ContentServiceDeps = {
  offlineCache: OfflineCacheProvider;
  infrastructure: InfrastructureProvider;
  userIdentity: UserIdentityProvider;
};

function createDefaultDeps(): ContentServiceDeps {
  return {
    offlineCache: offlineCacheProvider(),
    infrastructure: infrastructureProvider(),
    userIdentity: userIdentityProvider(),
  };
}

export class ContentService {
  private readonly repo: ContentRepo;
  private readonly offlineCache: OfflineCacheProvider;
  private readonly infrastructure: InfrastructureProvider;
  private readonly userIdentity: UserIdentityProvider;

  constructor(
    repo: ContentRepo,
    deps: ContentServiceDeps = createDefaultDeps()
  ) {
    this.repo = repo;
    this.offlineCache = deps.offlineCache;
    this.infrastructure = deps.infrastructure;
    this.userIdentity = deps.userIdentity;
  }

  async listUnits(params?: ListUnitsParams): Promise<Unit[]> {
    try {
      const cached = await this.ensureUnitsCached();
      const paged = this.applyPaging(cached, params?.limit, params?.offset);
      return paged.map(unit =>
        this.mapCachedUnitToUnit(unit, params?.currentUserId)
      );
    } catch (error) {
      throw this.handleError(error, 'Failed to list units');
    }
  }

  async getUserUnitCollections(
    userId: number,
    options?: { includeGlobal?: boolean; limit?: number; offset?: number }
  ): Promise<UserUnitCollections> {
    if (!Number.isFinite(userId) || userId <= 0) {
      return { units: [], ownedUnitIds: [] };
    }

    const includeGlobal = options?.includeGlobal ?? true;

    try {
      const cached = await this.ensureUnitsCached();
      const ownedUnits = cached
        .filter(unit => this.getOwnerId(unit) === userId)
        .map(unit => this.mapCachedUnitToUnit(unit, userId));

      const ownedUnitIds = new Set(ownedUnits.map(unit => unit.id));
      const mergedUnits: Unit[] = [...ownedUnits];

      if (includeGlobal) {
        cached.forEach(unit => {
          if (ownedUnitIds.has(unit.id)) {
            return;
          }
          if (!unit.isGlobal) {
            return;
          }
          mergedUnits.push(this.mapCachedUnitToUnit(unit, userId));
        });
      }

      const resultUnits =
        options?.limit !== undefined || options?.offset !== undefined
          ? this.applyPaging(mergedUnits, options?.limit, options?.offset)
          : mergedUnits;

      return { units: resultUnits, ownedUnitIds: Array.from(ownedUnitIds) };
    } catch (error) {
      throw this.handleError(error, 'Failed to load user units');
    }
  }

  async getUnitDetail(
    unitId: string,
    options?: UnitDetailOptions
  ): Promise<UnitDetail | null> {
    if (!unitId?.trim()) {
      return null;
    }

    try {
      await this.ensureUnitsCached();

      let cached = await this.offlineCache.getUnitDetail(unitId);

      if (!cached) {
        await this.runSyncCycle();
        cached = await this.offlineCache.getUnitDetail(unitId);
      }

      if (cached?.downloadStatus === 'completed') {
        if (cached.lessons.length === 0) {
          console.warn(
            '[ContentService] Downloaded unit missing lessons, forcing full sync',
            {
              unitId,
            }
          );
          await this.runSyncCycle({ force: true, payload: 'full' });
          cached = await this.offlineCache.getUnitDetail(unitId);
        }

        if (cached?.downloadStatus === 'completed') {
          return this.mapCachedUnitDetail(cached, options?.currentUserId);
        }
      }

      if (cached) {
        return this.mapCachedUnitMetadata(cached, options?.currentUserId);
      }

      const apiDetail = await this.repo.getUnitDetail(unitId);
      await this.cacheDetailFallback(apiDetail);
      return toUnitDetailDTO(apiDetail, options?.currentUserId);
    } catch (error: any) {
      if (error?.statusCode === 404) {
        return null;
      }
      throw this.handleError(error, `Failed to get unit ${unitId}`);
    }
  }

  async updateUnitSharing(
    unitId: string,
    request: UpdateUnitSharingRequest,
    currentUserId?: number | null
  ): Promise<Unit> {
    if (!unitId?.trim()) {
      throw this.handleError(
        new Error('Unit ID is required'),
        'Unit ID is required'
      );
    }

    try {
      const updated = await this.repo.updateUnitSharing(unitId, request);
      await this.offlineCache.cacheMinimalUnits([
        this.toOfflineUnitPayloadFromSummary(updated),
      ]);
      const cached = (await this.offlineCache.listUnits()).find(
        unit => unit.id === updated.id
      );
      if (cached) {
        return this.mapCachedUnitToUnit(cached, currentUserId);
      }
      return toUnitDTO(updated, currentUserId);
    } catch (error) {
      throw this.handleError(error, 'Failed to update unit sharing');
    }
  }

  async requestUnitDownload(unitId: string): Promise<void> {
    const cachedUnits = await this.offlineCache.listUnits();
    const existing = cachedUnits.find(unit => unit.id === unitId);
    if (!existing) {
      throw this.handleError(
        new Error(`Unit ${unitId} not cached`),
        `Unit ${unitId} is not cached`
      );
    }

    // Mark as full download with pending status
    const payload: OfflineUnitPayload = {
      id: existing.id,
      title: existing.title,
      description: existing.description,
      learnerLevel: existing.learnerLevel,
      isGlobal: existing.isGlobal,
      updatedAt: existing.updatedAt,
      schemaVersion: existing.schemaVersion,
      cacheMode: 'full',
      downloadStatus: 'pending',
      downloadedAt: null,
      syncedAt: Date.now(),
      unitPayload: existing.unitPayload ?? null,
    };
    await this.offlineCache.cacheMinimalUnits([payload]);

    console.info('[ContentService] Starting unit download', { unitId });

    // Sync to get lessons/assets metadata with full payload
    await this.runSyncCycle({ force: true, payload: 'full' });

    // Download assets
    try {
      await this.offlineCache.downloadUnitAssets(unitId);
      console.info('[ContentService] Unit download completed', { unitId });
    } catch (error) {
      console.error('[ContentService] Asset download failed', {
        unitId,
        error,
      });
      throw this.handleError(error, 'Failed to download unit assets');
    }
  }

  async removeUnitDownload(unitId: string): Promise<void> {
    if (!unitId?.trim()) {
      return;
    }

    const cached = await this.offlineCache.getUnitDetail(unitId);
    if (!cached) {
      return;
    }

    await this.offlineCache.markUnitCacheMode(unitId, 'minimal');
  }

  async resolveAsset(assetId: string): Promise<CachedAsset | null> {
    return this.offlineCache.resolveAsset(assetId);
  }

  async syncNow(): Promise<SyncStatus> {
    console.info('[ContentService] Forcing sync via syncNow');
    return this.offlineCache.runSyncCycle({
      processor: this.createOutboxProcessor(),
      pull: args => this.pullUpdates(args),
      force: true, // Always fetch all units, ignoring cursor
    });
  }

  async getSyncStatus(): Promise<SyncStatus> {
    return this.offlineCache.getSyncStatus();
  }

  private async ensureUnitsCached(): Promise<CachedUnit[]> {
    const cached = await this.offlineCache.listUnits();
    if (cached.length > 0) {
      return cached;
    }
    await this.runSyncCycle();
    return this.offlineCache.listUnits();
  }

  private async runSyncCycle(options?: { force?: boolean; payload?: CacheMode }): Promise<void> {
    await this.offlineCache.runSyncCycle({
      processor: this.createOutboxProcessor(),
      pull: args => this.pullUpdates(args),
      force: options?.force,
      payload: options?.payload,
    });
  }

  private async pullUpdates(args: SyncPullArgs): Promise<SyncPullResponse> {
    const userId = this.userIdentity.getUserId();
    console.info('[ContentService] Syncing units', {
      cursor: args.cursor,
      payload: args.payload,
    });

    if (!userId) {
      console.warn('[ContentService] No user logged in, skipping sync');
      // If no user is logged in, return empty response
      return {
        units: [],
        lessons: [],
        assets: [],
        cursor: args.cursor ?? null,
      };
    }

    const [response, existing] = await Promise.all([
      this.repo.syncUnits({
        userId,
        since: args.cursor ?? undefined,
        payload: args.payload,
      }),
      this.offlineCache.listUnits(),
    ]);

    console.info('[ContentService] Sync completed', {
      unitCount: response.units.length,
      cursor: response.cursor,
    });

    const existingMap = new Map(existing.map(unit => [unit.id, unit]));
    return this.toSyncPullResponse(response, args.payload, existingMap);
  }

  private toSyncPullResponse(
    response: ApiUnitSyncResponse,
    payloadMode: CacheMode,
    existingMap: Map<string, CachedUnit>
  ): SyncPullResponse {
    const units = new Array<OfflineUnitPayload>();
    const lessons = new Array<OfflineLessonPayload>();
    const assets = new Array<OfflineAssetPayload>();

    response.units.forEach(entry => {
      const payloads = this.toOfflinePayloads(entry, existingMap, payloadMode);
      units.push(payloads.unit);
      lessons.push(...payloads.lessons);
      assets.push(...payloads.assets);
    });

    return {
      units,
      lessons,
      assets,
      cursor: response.cursor ?? null,
    };
  }

  private toOfflinePayloads(
    entry: ApiUnitSyncEntry,
    existingMap: Map<string, CachedUnit>,
    payloadMode: CacheMode
  ): {
    unit: OfflineUnitPayload;
    lessons: OfflineLessonPayload[];
    assets: OfflineAssetPayload[];
  } {
    const existing = existingMap.get(entry.unit.id);
    const summary = entry.unit;
    const now = Date.now();
    const updatedAt = this.parseTimestamp(summary.updated_at) ?? now;
    const schemaVersion =
      summary.schema_version ?? existing?.schemaVersion ?? 1;

    const inferredCacheMode: CacheMode = existing?.cacheMode
      ? existing.cacheMode
      : entry.lessons.length > 0
        ? 'full'
        : payloadMode;

    const downloadStatus: DownloadStatus =
      existing?.downloadStatus ?? 'completed';
    const downloadedAt = existing?.downloadedAt ?? null;

    const unitPayload: OfflineUnitSummaryPayload = {
      id: summary.id,
      title: summary.title,
      description: summary.description ?? null,
      learner_level: summary.learner_level,
      lesson_order: summary.lesson_order ?? [],
      user_id: summary.user_id ?? null,
      is_global: summary.is_global ?? false,
      learning_objectives: summary.learning_objectives ?? null,
      target_lesson_count: summary.target_lesson_count ?? null,
      source_material: summary.source_material ?? null,
      generated_from_topic: summary.generated_from_topic ?? false,
      flow_type: summary.flow_type ?? 'standard',
      status: summary.status ?? existing?.unitPayload?.status ?? 'completed',
      creation_progress: summary.creation_progress ?? null,
      error_message: summary.error_message ?? null,
      has_podcast: summary.has_podcast ?? false,
      podcast_voice: summary.podcast_voice ?? null,
      podcast_duration_seconds: summary.podcast_duration_seconds ?? null,
      podcast_audio_url: (summary as any).podcast_audio_url ?? null,
      podcast_transcript: (summary as any).podcast_transcript ?? null,
      art_image_url: summary.art_image_url ?? null,
      art_image_description: summary.art_image_description ?? null,
      created_at: summary.created_at ?? undefined,
      updated_at: summary.updated_at ?? undefined,
      schema_version: schemaVersion,
    };

    const unit: OfflineUnitPayload = {
      id: summary.id,
      title: summary.title,
      description: summary.description ?? '',
      learnerLevel:
        summary.learner_level ?? existing?.learnerLevel ?? 'beginner',
      isGlobal: summary.is_global ?? existing?.isGlobal ?? false,
      updatedAt,
      schemaVersion,
      cacheMode: inferredCacheMode,
      downloadStatus,
      downloadedAt,
      syncedAt: now,
      unitPayload,
    };

    const orderIndex = new Map<string, number>();
    (summary.lesson_order ?? []).forEach((lessonId, index) => {
      orderIndex.set(lessonId, index + 1);
    });

    const lessonPayloads = entry.lessons.map((lesson, index) => {
      const lessonUpdatedAt = this.parseTimestamp(lesson.updated_at) ?? now;
      return {
        id: lesson.id,
        unitId: summary.id,
        title: lesson.title,
        position: orderIndex.get(lesson.id) ?? index + 1,
        payload: lesson,
        updatedAt: lessonUpdatedAt,
        schemaVersion: lesson.schema_version ?? 1,
      } satisfies OfflineLessonPayload;
    });

    const assetPayloads = entry.assets
      .map(asset => this.toOfflineAssetPayload(asset, summary.id, now))
      .filter((asset): asset is OfflineAssetPayload => Boolean(asset));

    return {
      unit,
      lessons: lessonPayloads,
      assets: assetPayloads,
    };
  }

  private toOfflineAssetPayload(
    asset: { [key: string]: any },
    unitId: string,
    fallbackTime: number
  ): OfflineAssetPayload | null {
    const type =
      asset.type === 'audio'
        ? 'audio'
        : asset.type === 'image'
          ? 'image'
          : null;
    if (!type) {
      return null;
    }
    const remoteUri = asset.presigned_url ?? asset.remote_url ?? null;
    if (!remoteUri) {
      return null;
    }
    const updatedAt = this.parseTimestamp(asset.updated_at) ?? fallbackTime;
    return {
      id: asset.id,
      unitId,
      type,
      remoteUri,
      checksum: asset.checksum ?? null,
      updatedAt,
    };
  }

  private mapCachedUnitToUnit(
    cached: CachedUnit,
    currentUserId?: number | null
  ): Unit {
    const apiSummary = this.buildApiUnitSummaryFromCached(cached);
    const dto = toUnitDTO(apiSummary, currentUserId);
    return {
      ...dto,
      cacheMode: cached.cacheMode,
      downloadStatus: cached.downloadStatus,
      downloadedAt: cached.downloadedAt ?? null,
      syncedAt: cached.syncedAt ?? null,
    };
  }

  private mapCachedUnitDetail(
    cached: CachedUnitDetail,
    currentUserId?: number | null
  ): UnitDetail {
    const apiDetail = this.buildApiUnitDetailFromCached(cached);
    const dto = toUnitDetailDTO(apiDetail, currentUserId);
    return {
      ...dto,
      cacheMode: cached.cacheMode,
      downloadStatus: cached.downloadStatus,
      downloadedAt: cached.downloadedAt ?? null,
      syncedAt: cached.syncedAt ?? null,
    };
  }

  private mapCachedUnitMetadata(
    cached: CachedUnitDetail,
    currentUserId?: number | null
  ): UnitDetail {
    const summary = this.mapCachedUnitToUnit(cached, currentUserId);
    const lessonOrder = Array.isArray(cached.unitPayload?.lesson_order)
      ? cached.unitPayload?.lesson_order ?? []
      : [];
    const fallbackLessonIds = cached.lessons.map(lesson => lesson.id);
    const lessonIds = lessonOrder.length > 0 ? lessonOrder : fallbackLessonIds;

    return {
      id: summary.id,
      title: summary.title,
      description: summary.description ?? null,
      difficulty: summary.difficulty,
      lessonIds,
      lessons: [],
      learningObjectives: summary.learningObjectives ?? null,
      targetLessonCount: summary.targetLessonCount ?? null,
      sourceMaterial:
        (cached.unitPayload?.source_material as string | null | undefined) ??
        null,
      generatedFromTopic: summary.generatedFromTopic,
      ownerUserId: summary.ownerUserId,
      isGlobal: summary.isGlobal,
      ownershipLabel: summary.ownershipLabel,
      isOwnedByCurrentUser: summary.isOwnedByCurrentUser,
      learningObjectiveProgress: null,
      hasPodcast: summary.hasPodcast,
      podcastVoice: summary.podcastVoice,
      podcastDurationSeconds: summary.podcastDurationSeconds,
      podcastTranscript: null,
      podcastAudioUrl: null,
      artImageUrl: summary.artImageUrl,
      artImageDescription: summary.artImageDescription,
      cacheMode: cached.cacheMode,
      downloadStatus: cached.downloadStatus,
      downloadedAt: cached.downloadedAt ?? null,
      syncedAt: cached.syncedAt ?? null,
    };
  }

  private buildApiUnitSummaryFromCached(cached: CachedUnit): ApiUnitSummary {
    const payload = cached.unitPayload;
    const lessonCount = Array.isArray(payload?.lesson_order)
      ? payload!.lesson_order!.length
      : 0;
    const creationProgress = this.normalizeCreationProgress(
      payload?.creation_progress
    );
    return {
      id: cached.id,
      title: payload?.title ?? cached.title,
      description: payload?.description ?? cached.description ?? null,
      learner_level: payload?.learner_level ?? cached.learnerLevel,
      lesson_count: lessonCount,
      target_lesson_count:
        (payload?.target_lesson_count as NullableNumber) ?? null,
      generated_from_topic: Boolean(payload?.generated_from_topic),
      status: (payload?.status as string) ?? 'completed',
      creation_progress: creationProgress,
      error_message: (payload?.error_message as string | null) ?? null,
      user_id: typeof payload?.user_id === 'number' ? payload.user_id : null,
      is_global: payload?.is_global ?? cached.isGlobal,
      created_at: payload?.created_at ?? undefined,
      updated_at:
        payload?.updated_at ?? new Date(cached.updatedAt).toISOString(),
      has_podcast: payload?.has_podcast ?? false,
      podcast_voice: payload?.podcast_voice ?? null,
      podcast_duration_seconds:
        (payload?.podcast_duration_seconds as NullableNumber) ?? null,
      art_image_url: payload?.art_image_url ?? null,
      art_image_description: payload?.art_image_description ?? null,
    };
  }

  private buildApiUnitDetailFromCached(
    cached: CachedUnitDetail
  ): ApiUnitDetail {
    const summary = this.buildApiUnitSummaryFromCached(cached);
    const lessonOrder =
      (cached.unitPayload?.lesson_order as string[] | undefined) ??
      cached.lessons.map(lesson => lesson.id);

    const lessons: ApiUnitDetail['lessons'] = cached.lessons.map(lesson =>
      this.buildApiLessonFromCached(lesson)
    );

    return {
      id: summary.id,
      title: summary.title,
      description: summary.description,
      learner_level: summary.learner_level,
      lesson_order: lessonOrder,
      lessons,
      learning_objectives:
        (cached.unitPayload?.learning_objectives as string[] | null) ?? null,
      target_lesson_count: summary.target_lesson_count ?? null,
      source_material:
        (cached.unitPayload?.source_material as string | null) ?? null,
      generated_from_topic: summary.generated_from_topic ?? false,
      user_id: summary.user_id ?? null,
      is_global: summary.is_global ?? false,
      learning_objective_progress: null,
      has_podcast: summary.has_podcast ?? false,
      podcast_voice: summary.podcast_voice ?? null,
      podcast_duration_seconds: summary.podcast_duration_seconds ?? null,
      podcast_transcript:
        (cached.unitPayload?.podcast_transcript as string | null) ?? null,
      podcast_audio_url:
        (cached.unitPayload?.podcast_audio_url as string | null) ?? null,
      art_image_url: summary.art_image_url ?? null,
      art_image_description: summary.art_image_description ?? null,
    };
  }

  private buildApiLessonFromCached(
    lesson: CachedUnitDetail['lessons'][number]
  ): ApiUnitDetail['lessons'][number] {
    const payload = (lesson.payload ?? {}) as Record<string, any>;
    const packagePayload =
      payload && typeof payload === 'object' ? (payload.package ?? {}) : {};

    const learningObjectives = Array.isArray(
      packagePayload?.learning_objectives
    )
      ? packagePayload.learning_objectives
      : [];
    const keyConcepts = Array.isArray(packagePayload?.key_concepts)
      ? packagePayload.key_concepts
      : [];

    const exerciseComponents = Array.isArray(packagePayload?.components)
      ? packagePayload.components
      : Array.isArray(packagePayload?.exercises)
        ? packagePayload.exercises
        : [];

    return {
      id: lesson.id,
      title: lesson.title,
      learner_level:
        (payload?.learner_level as string) ??
        (lesson.payload as Record<string, any> | undefined)?.learner_level ??
        'beginner',
      learning_objectives: learningObjectives,
      key_concepts: keyConcepts,
      exercise_count: exerciseComponents.length,
    };
  }

  private async cacheDetailFallback(detail: ApiUnitDetail): Promise<void> {
    const payload = this.toOfflineUnitPayloadFromSummary(detail);
    await this.offlineCache.cacheMinimalUnits([payload]);
  }

  private toOfflineUnitPayloadFromSummary(
    summary: ApiUnitSummary | ApiUnitDetail
  ): OfflineUnitPayload {
    const updatedAtSource =
      'updated_at' in summary ? (summary.updated_at ?? null) : null;
    const updatedAt = updatedAtSource
      ? this.parseTimestamp(updatedAtSource)
      : Date.now();
    const status =
      'status' in summary && summary.status ? summary.status : 'completed';
    const creationProgress =
      'creation_progress' in summary
        ? this.normalizeCreationProgress(summary.creation_progress)
        : null;
    const errorMessage =
      'error_message' in summary ? (summary.error_message ?? null) : null;
    const hasPodcast =
      'has_podcast' in summary ? (summary.has_podcast ?? false) : false;
    const podcastVoice =
      'podcast_voice' in summary ? (summary.podcast_voice ?? null) : null;
    const podcastDuration =
      'podcast_duration_seconds' in summary
        ? (summary.podcast_duration_seconds ?? null)
        : null;
    const podcastTranscript =
      'podcast_transcript' in summary
        ? (summary.podcast_transcript ?? null)
        : null;
    const podcastAudioUrl =
      'podcast_audio_url' in summary
        ? (summary.podcast_audio_url ?? null)
        : null;
    const artImageUrl =
      'art_image_url' in summary ? (summary.art_image_url ?? null) : null;
    const artImageDescription =
      'art_image_description' in summary
        ? (summary.art_image_description ?? null)
        : null;
    const createdAt =
      'created_at' in summary ? (summary.created_at ?? undefined) : undefined;

    return {
      id: summary.id,
      title: summary.title,
      description: summary.description ?? '',
      learnerLevel: summary.learner_level ?? 'beginner',
      isGlobal: Boolean(summary.is_global),
      updatedAt: updatedAt ?? Date.now(),
      schemaVersion: 1,
      cacheMode: 'minimal',
      downloadStatus: 'idle',
      downloadedAt: null,
      syncedAt: Date.now(),
      unitPayload: {
        id: summary.id,
        title: summary.title,
        description: summary.description ?? null,
        learner_level: summary.learner_level ?? 'beginner',
        lesson_order: 'lesson_order' in summary ? summary.lesson_order : [],
        user_id: summary.user_id ?? null,
        is_global: Boolean(summary.is_global),
        learning_objectives:
          'learning_objectives' in summary ? summary.learning_objectives : null,
        target_lesson_count: summary.target_lesson_count ?? null,
        generated_from_topic: summary.generated_from_topic ?? false,
        status,
        creation_progress: creationProgress,
        error_message: errorMessage,
        has_podcast: hasPodcast,
        podcast_voice: podcastVoice,
        podcast_duration_seconds: podcastDuration,
        podcast_audio_url: podcastAudioUrl,
        podcast_transcript: podcastTranscript,
        art_image_url: artImageUrl,
        art_image_description: artImageDescription,
        created_at: createdAt,
        updated_at:
          'updated_at' in summary
            ? (summary.updated_at ?? undefined)
            : undefined,
        schema_version: 1,
      },
    };
  }

  private normalizeCreationProgress(
    value: unknown
  ): ApiUnitSummary['creation_progress'] {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const stage = (value as Record<string, unknown>).stage;
    const message = (value as Record<string, unknown>).message;
    if (typeof stage !== 'string' || typeof message !== 'string') {
      return null;
    }
    return { stage, message };
  }

  private createOutboxProcessor() {
    return async (record: OutboxRecord): Promise<void> => {
      const headers = {
        'Content-Type': 'application/json',
        ...(record.headers ?? {}),
      } as Record<string, string>;
      await this.infrastructure.request(record.endpoint, {
        method: record.method,
        headers,
        body: record.payload ? JSON.stringify(record.payload) : undefined,
      });
    };
  }

  private applyPaging<T>(items: T[], limit?: number, offset?: number): T[] {
    const safeOffset = Math.max(0, offset ?? 0);
    if (typeof limit === 'number' && limit >= 0) {
      return items.slice(safeOffset, safeOffset + limit);
    }
    return items.slice(safeOffset);
  }

  private parseTimestamp(value: string | null | undefined): number | null {
    if (!value) {
      return null;
    }
    const parsed = Date.parse(value);
    return Number.isNaN(parsed) ? null : parsed;
  }

  private getOwnerId(unit: CachedUnit): number | null {
    const owner = unit.unitPayload?.user_id;
    return typeof owner === 'number' ? owner : null;
  }

  private handleError(error: any, defaultMessage: string): ContentError {
    if (error && typeof error === 'object' && 'code' in error) {
      return error as ContentError;
    }

    return {
      message: (error as Error)?.message || defaultMessage,
      code: 'CONTENT_SERVICE_ERROR',
      details: error,
    };
  }
}
