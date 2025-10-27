import {
  ContentRepo,
  type ApiLessonRead,
  type ApiUnitSyncEntry,
  type ApiUnitSyncResponse,
} from './repo';
import type {
  ApiUnitDetail,
  ApiUnitSummary,
  ApiUnitLearningObjective,
  ContentError,
  Unit,
  UnitDetail,
  UpdateUnitSharingRequest,
  UserUnitCollections,
  AddToMyUnitsRequest,
  RemoveFromMyUnitsRequest,
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

  async browseCatalogUnits(params?: ListUnitsParams): Promise<Unit[]> {
    try {
      // Fetch fresh data from server for catalog browsing
      const apiUnits = await this.repo.listUnits({
        limit: params?.limit,
        offset: params?.offset,
      });

      return apiUnits.map(apiUnit =>
        toUnitDTO(apiUnit, params?.currentUserId ?? null)
      );
    } catch (error) {
      throw this.handleError(error, 'Failed to browse catalog units');
    }
  }

  async getUserUnitCollections(
    userId: number,
    options?: { includeGlobal?: boolean; limit?: number; offset?: number }
  ): Promise<UserUnitCollections> {
    if (!Number.isInteger(userId) || userId <= 0) {
      return { units: [], ownedUnitIds: [] };
    }

    const includeGlobal = options?.includeGlobal ?? true;

    try {
      // Read from offline cache for offline support
      // The cache is populated by sync, which includes units owned by user + My Units
      const cached = await this.ensureUnitsCached();

      // Units owned by this user
      const ownedUnits = cached
        .filter(unit => this.getOwnerId(unit) === userId)
        .map(unit => this.mapCachedUnitToUnit(unit, userId));

      const ownedUnitIds = new Set(ownedUnits.map(unit => unit.id));

      // Start with owned units
      const mergedUnits: Unit[] = [...ownedUnits];

      if (includeGlobal) {
        // Add global units that are in the cache (which includes My Units via sync)
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

  async addUnitToMyUnits(userId: number, unitId: string): Promise<void> {
    if (!Number.isInteger(userId) || userId <= 0) {
      throw this.handleError(
        new Error('Valid user ID is required'),
        'Valid user ID is required'
      );
    }

    const trimmedUnitId = unitId?.trim();
    if (!trimmedUnitId) {
      throw this.handleError(
        new Error('Unit ID is required'),
        'Unit ID is required'
      );
    }

    const request: AddToMyUnitsRequest = {
      userId,
      unitId: trimmedUnitId,
    };

    try {
      const response = await this.repo.addUnitToMyUnits(request);
      // Cache immediately for instant feedback
      await this.offlineCache.cacheMinimalUnits([
        this.toOfflineUnitPayloadFromSummary(response.unit),
      ]);
      // Trigger regular sync to ensure cache stays consistent
      // Use regular sync (not force) to avoid clearing other cached units
      await this.runSyncCycle();
    } catch (error) {
      throw this.handleError(error, 'Failed to add unit to My Units');
    }
  }

  async removeUnitFromMyUnits(userId: number, unitId: string): Promise<void> {
    if (!Number.isInteger(userId) || userId <= 0) {
      throw this.handleError(
        new Error('Valid user ID is required'),
        'Valid user ID is required'
      );
    }

    const trimmedUnitId = unitId?.trim();
    if (!trimmedUnitId) {
      throw this.handleError(
        new Error('Unit ID is required'),
        'Unit ID is required'
      );
    }

    const request: RemoveFromMyUnitsRequest = {
      userId,
      unitId: trimmedUnitId,
    };

    try {
      // Remove from My Units on server
      await this.repo.removeUnitFromMyUnits(request);
    } catch (error: any) {
      // If unit is already not in My Units (404), that's the desired state
      // Continue to sync to clean up the cache
      if (error?.statusCode !== 404) {
        throw this.handleError(error, 'Failed to remove unit from My Units');
      }
      console.info(
        '[ContentService] Unit already not in My Units, syncing cache',
        {
          unitId: trimmedUnitId,
        }
      );
    }

    // Check if unit was downloaded - if so, delete it after server removal
    // We do this AFTER server removal to avoid leaving orphaned downloads if removal fails
    const cachedUnit = await this.offlineCache.getUnitDetail(trimmedUnitId);
    if (cachedUnit) {
      console.info('[ContentService] Deleting unit from cache', {
        unitId: trimmedUnitId,
        downloadStatus: cachedUnit.downloadStatus,
        cacheMode: cachedUnit.cacheMode,
      });
      await this.offlineCache.deleteUnit(trimmedUnitId);

      // Verify deletion
      const afterDelete = await this.offlineCache.getUnitDetail(trimmedUnitId);
      console.info('[ContentService] After deletion, unit in cache:', {
        unitId: trimmedUnitId,
        stillExists: !!afterDelete,
      });
    }

    // Trigger force sync to fully refresh cache and remove from minimal cache
    // Force sync clears minimal units and replaces with fresh data from server
    // For downloaded units, they're already deleted above
    console.info('[ContentService] Starting force sync after removal', {
      unitId: trimmedUnitId,
    });
    await this.runSyncCycle({ force: true });

    // Verify unit is not in cache after sync
    const afterSync = await this.offlineCache.getUnitDetail(trimmedUnitId);
    console.info('[ContentService] After force sync, unit in cache:', {
      unitId: trimmedUnitId,
      exists: !!afterSync,
    });
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

    await this.offlineCache.setUnitCacheMode(unitId, 'minimal');
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

  private async runSyncCycle(options?: {
    force?: boolean;
    payload?: CacheMode;
  }): Promise<void> {
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

    // Don't assume units are downloaded just because we synced their metadata
    // Default to 'idle' - units must be explicitly downloaded via requestUnitDownload
    const downloadStatus: DownloadStatus = existing?.downloadStatus ?? 'idle';
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

    const assetIds = new Set(assetPayloads.map(asset => asset.id));
    entry.lessons.forEach(lesson => {
      const lessonAsset = this.toLessonPodcastAssetPayload(
        lesson,
        summary.id,
        now
      );
      if (lessonAsset && !assetIds.has(lessonAsset.id)) {
        assetPayloads.push(lessonAsset);
        assetIds.add(lessonAsset.id);
      }
    });

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

  private toLessonPodcastAssetPayload(
    lesson: ApiLessonRead,
    unitId: string,
    fallbackTime: number
  ): OfflineAssetPayload | null {
    const remoteUri =
      typeof lesson.podcast_audio_url === 'string'
        ? lesson.podcast_audio_url
        : null;
    if (!remoteUri) {
      return null;
    }

    const generatedAt = this.parseTimestamp(lesson.podcast_generated_at);
    const updatedAt =
      generatedAt ?? this.parseTimestamp(lesson.updated_at) ?? fallbackTime;

    return {
      id: `lesson-podcast-${lesson.id}`,
      unitId,
      type: 'audio',
      remoteUri,
      checksum: null,
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
      ? (cached.unitPayload?.lesson_order ?? [])
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
      podcastTranscript: cached.unitPayload?.podcast_transcript ?? null,
      podcastAudioUrl: cached.unitPayload?.podcast_audio_url ?? null,
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

    const podcastDurationSeconds =
      (payload?.podcast_duration_seconds as NullableNumber) ?? null;

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
      podcast_duration_seconds: podcastDurationSeconds,
      art_image_url: payload?.art_image_url ?? null,
      art_image_description: payload?.art_image_description ?? null,
      learning_objectives: this.parseCachedLearningObjectives(
        payload?.learning_objectives
      ),
    };
  }

  private buildApiUnitDetailFromCached(
    cached: CachedUnitDetail
  ): ApiUnitDetail {
    const summary = this.buildApiUnitSummaryFromCached(cached);
    const lessonOrder =
      (cached.unitPayload?.lesson_order as string[] | undefined) ??
      cached.lessons.map(lesson => lesson.id);

    const canonicalObjectives =
      this.parseCachedLearningObjectives(
        cached.unitPayload?.learning_objectives
      ) ?? [];
    const objectiveById = new Map<
      string,
      { title: string; description: string }
    >();
    for (const objective of canonicalObjectives) {
      objectiveById.set(objective.id, {
        title: objective.title,
        description: objective.description,
      });
    }

    const lessons: ApiUnitDetail['lessons'] = cached.lessons.map(lesson =>
      this.buildApiLessonFromCached(lesson, objectiveById)
    );

    return {
      id: summary.id,
      title: summary.title,
      description: summary.description,
      learner_level: summary.learner_level,
      lesson_order: lessonOrder,
      lessons,
      learning_objectives: canonicalObjectives,
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
    lesson: CachedUnitDetail['lessons'][number],
    objectivesById: Map<string, { title: string; description: string }>
  ): ApiUnitDetail['lessons'][number] {
    const payload = (lesson.payload ?? {}) as Record<string, any>;
    const packagePayload =
      payload && typeof payload === 'object' ? (payload.package ?? {}) : {};

    const unitLearningObjectiveIds = Array.isArray(
      packagePayload?.unit_learning_objective_ids
    )
      ? packagePayload.unit_learning_objective_ids.filter(
          (value: unknown): value is string => typeof value === 'string'
        )
      : [];
    const fallbackObjectives = Array.isArray(
      packagePayload?.learning_objectives
    )
      ? packagePayload.learning_objectives.filter(
          (value: unknown): value is string => typeof value === 'string'
        )
      : [];
    const learningObjectives =
      unitLearningObjectiveIds.length > 0
        ? unitLearningObjectiveIds.map((id: string) => {
            const objective = objectivesById.get(id);
            if (!objective) {
              return id;
            }
            return objective.description || objective.title;
          })
        : fallbackObjectives;
    const keyConcepts = Array.isArray(packagePayload?.key_concepts)
      ? packagePayload.key_concepts
      : [];

    const exerciseComponents = Array.isArray(packagePayload?.components)
      ? packagePayload.components
      : Array.isArray(packagePayload?.exercises)
        ? packagePayload.exercises
        : [];

    const rawPodcastTranscript =
      typeof payload?.podcast_transcript === 'string'
        ? payload.podcast_transcript
        : null;
    const rawPodcastVoice =
      typeof payload?.podcast_voice === 'string' ? payload.podcast_voice : null;
    const rawPodcastAudioUrl =
      typeof payload?.podcast_audio_url === 'string'
        ? payload.podcast_audio_url
        : null;
    const rawGeneratedAt = (payload as Record<string, unknown> | undefined)
      ?.podcast_generated_at;
    const podcastGeneratedAt =
      typeof rawGeneratedAt === 'string'
        ? rawGeneratedAt
        : rawGeneratedAt instanceof Date
          ? rawGeneratedAt.toISOString()
          : null;
    const rawDuration = (payload as Record<string, unknown> | undefined)
      ?.podcast_duration_seconds;
    const parsedDuration =
      typeof rawDuration === 'number'
        ? rawDuration
        : typeof rawDuration === 'string'
          ? Number.parseInt(rawDuration, 10)
          : null;
    const podcastDurationSeconds =
      typeof parsedDuration === 'number' && Number.isFinite(parsedDuration)
        ? parsedDuration
        : null;
    const hasPodcast =
      typeof payload?.has_podcast === 'boolean'
        ? payload.has_podcast
        : Boolean(
            rawPodcastAudioUrl ||
              rawPodcastTranscript ||
              podcastDurationSeconds ||
              rawPodcastVoice
          );

    return {
      id: lesson.id,
      title: lesson.title,
      learner_level:
        (payload?.learner_level as string) ??
        (lesson.payload as Record<string, any> | undefined)?.learner_level ??
        'beginner',
      learning_objective_ids: unitLearningObjectiveIds,
      learning_objectives: learningObjectives,
      key_concepts: keyConcepts,
      exercise_count: exerciseComponents.length,
      has_podcast: hasPodcast,
      podcast_voice: rawPodcastVoice,
      podcast_duration_seconds: podcastDurationSeconds,
      podcast_generated_at: podcastGeneratedAt,
      podcast_audio_url: rawPodcastAudioUrl,
      podcast_transcript: rawPodcastTranscript,
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

  private parseCachedLearningObjectives(
    raw: unknown
  ): ApiUnitLearningObjective[] | null {
    if (!raw) {
      return null;
    }
    if (typeof raw === 'string') {
      const value = raw.trim();
      if (!value) {
        return null;
      }
      return [
        {
          id: value,
          title: value,
          description: value,
        },
      ];
    }
    if (!Array.isArray(raw)) {
      return null;
    }

    const objectives: ApiUnitLearningObjective[] = [];
    for (const entry of raw) {
      if (!entry) {
        continue;
      }
      if (typeof entry === 'string') {
        const value = entry.trim();
        if (value) {
          objectives.push({ id: value, title: value, description: value });
        }
        continue;
      }
      if (typeof entry === 'object') {
        const maybeId =
          typeof (entry as { id?: unknown }).id === 'string'
            ? ((entry as { id?: string }).id as string)
            : typeof (entry as { lo_id?: unknown }).lo_id === 'string'
              ? ((entry as { lo_id?: string }).lo_id as string)
              : null;
        const maybeTitle =
          typeof (entry as { title?: unknown }).title === 'string'
            ? ((entry as { title?: string }).title as string)
            : typeof (entry as { short_title?: unknown }).short_title ===
                'string'
              ? ((entry as { short_title?: string }).short_title as string)
              : typeof (entry as { text?: unknown }).text === 'string'
                ? ((entry as { text?: string }).text as string)
                : null;
        const maybeDescription =
          typeof (entry as { description?: unknown }).description === 'string'
            ? ((entry as { description?: string }).description as string)
            : typeof (entry as { text?: unknown }).text === 'string'
              ? ((entry as { text?: string }).text as string)
              : typeof (entry as { objective?: unknown }).objective === 'string'
                ? ((entry as { objective?: string }).objective as string)
                : null;
        if (maybeId && (maybeTitle || maybeDescription)) {
          const title = (maybeTitle ?? maybeDescription ?? '').trim();
          const description = (maybeDescription ?? maybeTitle ?? '').trim();
          if (title && description) {
            objectives.push({
              id: maybeId,
              title,
              description,
            });
          }
        }
      }
    }

    return objectives.length > 0 ? objectives : null;
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
