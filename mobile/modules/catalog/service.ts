/**
 * Lesson Catalog Service
 *
 * Business logic for lesson browsing, search, and discovery.
 * Returns DTOs only, never raw API responses.
 */

import { CatalogRepo } from './repo';
import type {
  LessonSummary,
  LessonDetail,
  BrowseLessonsResponse,
  SearchLessonsRequest,
  LessonFilters,
  CatalogStatistics,
  CatalogError,
  PaginationInfo,
} from './models';
import {
  toLessonSummaryDTO,
  toLessonDetailDTO,
  toBrowseLessonsResponseDTO,
} from './models';
import {
  contentProvider,
  type ContentProvider,
  type Unit,
  type UnitDetail,
  type UserUnitCollections,
} from '../content/public';
import {
  contentCreatorProvider,
  type ContentCreatorProvider,
  type UnitCreationRequest,
  type UnitCreationResponse,
} from '../content_creator/public';
import {
  offlineCacheProvider,
  type OfflineCacheProvider,
} from '../offline_cache/public';

interface CatalogServiceDeps {
  readonly content: ContentProvider;
  readonly contentCreator: ContentCreatorProvider;
  readonly offlineCache: OfflineCacheProvider;
}

function createDefaultDeps(): CatalogServiceDeps {
  return {
    content: contentProvider(),
    contentCreator: contentCreatorProvider(),
    offlineCache: offlineCacheProvider(),
  };
}

export class CatalogService {
  constructor(
    private repo: CatalogRepo,
    private deps: CatalogServiceDeps = createDefaultDeps()
  ) {}

  /**
   * Browse lessons with optional filters
   */
  async browseLessons(
    filters: LessonFilters = {},
    pagination: Omit<PaginationInfo, 'hasMore'> = { limit: 100, offset: 0 }
  ): Promise<BrowseLessonsResponse> {
    try {
      const request: SearchLessonsRequest = {
        learnerLevel: filters.learnerLevel,
        readyOnly: filters.readyOnly,
        limit: pagination.limit,
        offset: pagination.offset,
      };

      const apiResponse = await this.repo.browseLessons(request);

      // Convert to DTO
      const response = toBrowseLessonsResponseDTO(
        apiResponse,
        filters,
        pagination
      );

      // Apply client-side filtering if needed
      return this.applyClientFilters(response, filters);
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to browse lessons');
    }
  }

  /**
   * Search lessons with query and filters
   */
  async searchLessons(
    query: string,
    filters: LessonFilters = {},
    pagination: Omit<PaginationInfo, 'hasMore'> = { limit: 100, offset: 0 }
  ): Promise<BrowseLessonsResponse> {
    try {
      const request: SearchLessonsRequest = {
        query: query.trim() || undefined,
        learnerLevel: filters.learnerLevel,
        minDuration: filters.minDuration,
        maxDuration: filters.maxDuration,
        readyOnly: filters.readyOnly,
        limit: pagination.limit,
        offset: pagination.offset,
      };

      const apiResponse = await this.repo.searchLessons(request);

      // Convert to DTO
      const response = toBrowseLessonsResponseDTO(
        apiResponse,
        { ...filters, query },
        pagination
      );

      // Apply client-side filtering
      return this.applyClientFilters(response, { ...filters, query });
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to search lessons');
    }
  }

  /**
   * Get lesson details by ID
   * LOCAL-FIRST: Checks offline cache first, only goes to network if not cached
   */
  async getLessonDetail(lessonId: string): Promise<LessonDetail | null> {
    try {
      if (!lessonId?.trim()) {
        return null;
      }

      // STEP 1: Try to find lesson in offline cache (fast, works offline)
      const cachedLesson = await this.findLessonInCache(lessonId);
      if (cachedLesson) {
        console.info(
          `[CatalogService] Found lesson ${lessonId} in offline cache`
        );
        return cachedLesson;
      }

      // STEP 2: If not in cache, try network (for lessons not part of downloaded units)
      console.info(
        `[CatalogService] Lesson ${lessonId} not in cache, fetching from network`
      );
      const apiResponse = await this.repo.getLessonDetail(lessonId);
      return toLessonDetailDTO(apiResponse);
    } catch (error: any) {
      // Return null for 404s, throw for other errors
      if (error.statusCode === 404) {
        return null;
      }
      throw this.handleServiceError(error, `Failed to get lesson ${lessonId}`);
    }
  }

  /**
   * Find a lesson in the offline cache by searching all cached units
   * Returns the lesson detail if found, null otherwise
   */
  private async findLessonInCache(
    lessonId: string
  ): Promise<LessonDetail | null> {
    try {
      // Get all cached units
      const units = await this.deps.offlineCache.listUnits();

      // Search through each unit's lessons
      for (const unit of units) {
        const unitDetail = await this.deps.offlineCache.getUnitDetail(unit.id);
        if (!unitDetail) continue;

        // Find the lesson in this unit
        const cachedLesson = unitDetail.lessons.find(l => l.id === lessonId);
        if (cachedLesson && cachedLesson.payload) {
          // Convert cached lesson to LessonDetail
          // The payload contains the full lesson package
          const payload = cachedLesson.payload as any;
          // Backend stores lesson content inside a "package" field
          const lessonPackage = payload.package || {};

          return {
            id: cachedLesson.id,
            title: cachedLesson.title,
            learnerLevel: (payload.learner_level || 'beginner') as
              | 'beginner'
              | 'intermediate'
              | 'advanced',
            learningObjectives: lessonPackage.objectives || [],
            keyConcepts: lessonPackage.key_concepts || [],
            miniLesson: lessonPackage.mini_lesson || '',
            exercises: lessonPackage.exercises || [],
            glossaryTerms: lessonPackage.glossary || {},
            exerciseCount: lessonPackage.exercises?.length || 0,
            createdAt: new Date(cachedLesson.updatedAt).toISOString(),
            estimatedDuration: payload.duration_minutes || 0,
            isReadyForLearning: true, // If it's cached, it's ready
            learnerLevelLabel:
              payload.learner_level === 'beginner'
                ? 'Beginner'
                : payload.learner_level === 'intermediate'
                  ? 'Intermediate'
                  : 'Advanced',
            durationDisplay: `${payload.duration_minutes || 0} min`,
            readinessStatus: 'ready',
            tags: payload.tags || [],
            unitId: cachedLesson.unitId,
          };
        }
      }

      return null;
    } catch (error) {
      console.warn('[CatalogService] Error searching offline cache:', error);
      return null; // Fall through to network fetch
    }
  }

  /**
   * Get popular lessons
   */
  async getPopularLessons(limit: number = 10): Promise<LessonSummary[]> {
    try {
      const apiResponse = await this.repo.getPopularLessons(limit);
      return apiResponse.lessons.map(toLessonSummaryDTO);
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to get popular lessons');
    }
  }

  /**
   * Get catalog statistics
   */
  async getCatalogStatistics(): Promise<CatalogStatistics> {
    try {
      return await this.repo.getCatalogStatistics();
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to get catalog statistics');
    }
  }

  /**
   * Refresh catalog
   */
  async refreshCatalog(): Promise<{
    refreshedLessons: number;
    totalLessons: number;
    timestamp: string;
  }> {
    try {
      return await this.repo.refreshCatalog();
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to refresh catalog');
    }
  }

  /**
   * Check if service is healthy
   */
  async checkHealth(): Promise<boolean> {
    try {
      return await this.repo.checkHealth();
    } catch (error) {
      console.warn('[CatalogService] Health check failed:', error);
      return false;
    }
  }

  /**
   * Apply client-side filters to response
   */
  private applyClientFilters(
    response: BrowseLessonsResponse,
    filters: LessonFilters
  ): BrowseLessonsResponse {
    let filteredLessons = response.lessons;

    // Apply query filter (client-side search)
    if (filters.query?.trim()) {
      const query = filters.query.toLowerCase();
      filteredLessons = filteredLessons.filter(lesson =>
        this.matchesQuery(lesson, query)
      );
    }

    // Apply duration filters
    if (filters.minDuration !== undefined) {
      filteredLessons = filteredLessons.filter(
        lesson => lesson.estimatedDuration >= filters.minDuration!
      );
    }

    if (filters.maxDuration !== undefined) {
      filteredLessons = filteredLessons.filter(
        lesson => lesson.estimatedDuration <= filters.maxDuration!
      );
    }

    // Apply readiness filter
    if (filters.readyOnly) {
      filteredLessons = filteredLessons.filter(
        lesson => lesson.isReadyForLearning
      );
    }

    return {
      ...response,
      lessons: filteredLessons,
      total: filteredLessons.length,
    };
  }

  /**
   * Check if lesson matches search query
   */
  private matchesQuery(lesson: LessonSummary, query: string): boolean {
    if (!query.trim()) return true;

    const searchTerm = query.toLowerCase();
    return (
      lesson.title.toLowerCase().includes(searchTerm) ||
      lesson.keyConcepts.some(concept =>
        concept.toLowerCase().includes(searchTerm)
      ) ||
      lesson.learningObjectives.some(objective =>
        objective.toLowerCase().includes(searchTerm)
      ) ||
      lesson.tags.some(tag => tag.toLowerCase().includes(searchTerm))
    );
  }

  /**
   * Handle and transform service errors
   */
  private handleServiceError(error: any, defaultMessage: string): CatalogError {
    console.error('[CatalogService]', defaultMessage, error);

    if (error && typeof error === 'object' && 'code' in error) {
      const typed = error as CatalogError & { statusCode?: number };
      return {
        message: typed.message ?? defaultMessage,
        code: typed.code ?? 'CATALOG_SERVICE_ERROR',
        statusCode: typed.statusCode,
        details: 'details' in typed ? typed.details : typed,
      };
    }

    return {
      message: (error as Error)?.message || defaultMessage,
      code: 'CATALOG_SERVICE_ERROR',
      details: error,
    };
  }

  /**
   * Browse units with status information
   * Added for unit-based browsing in the catalog UI.
   */
  async browseUnits(params?: {
    limit?: number;
    offset?: number;
    currentUserId?: number | null;
  }): Promise<Unit[]> {
    try {
      return await this.deps.content.listUnits(params);
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to browse units');
    }
  }

  /**
   * Get unit details (delegates to units module)
   */
  async getUnitDetail(
    unitId: string,
    currentUserId?: number | null
  ): Promise<UnitDetail | null> {
    if (!unitId?.trim()) return null;
    try {
      return await this.deps.content.getUnitDetail(unitId, {
        currentUserId: currentUserId ?? null,
      });
    } catch (error) {
      throw this.handleServiceError(error, `Failed to get unit ${unitId}`);
    }
  }

  async getUserUnitCollections(
    userId: number,
    options?: { includeGlobal?: boolean; limit?: number; offset?: number }
  ): Promise<UserUnitCollections> {
    try {
      return await this.deps.content.getUserUnitCollections(userId, options);
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to load user units');
    }
  }

  async toggleUnitSharing(
    unitId: string,
    request: { makeGlobal: boolean; actingUserId?: number | null }
  ): Promise<Unit> {
    if (!unitId?.trim()) {
      throw this.handleServiceError(
        new Error('Unit ID is required'),
        'Unit ID is required'
      );
    }

    try {
      return await this.deps.content.updateUnitSharing(
        unitId,
        {
          isGlobal: request.makeGlobal,
          actingUserId: request.actingUserId ?? undefined,
        },
        request.actingUserId ?? null
      );
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to update unit sharing');
    }
  }

  /**
   * Create a new unit from mobile app
   */
  async createUnit(
    request: UnitCreationRequest
  ): Promise<UnitCreationResponse> {
    try {
      // Validate request
      if (!request.topic?.trim()) {
        throw new Error('Topic is required');
      }

      const validDifficulties = ['beginner', 'intermediate', 'advanced'];
      if (!validDifficulties.includes(request.difficulty)) {
        throw new Error('Invalid difficulty level');
      }

      if (
        request.targetLessonCount !== null &&
        request.targetLessonCount !== undefined
      ) {
        if (request.targetLessonCount < 1 || request.targetLessonCount > 20) {
          throw new Error('Target lesson count must be between 1 and 20');
        }
      }

      const response = await this.deps.contentCreator.createUnit(request);

      if (request.shareGlobally && request.ownerUserId) {
        try {
          await this.deps.content.updateUnitSharing(
            response.unitId,
            {
              isGlobal: true,
              actingUserId: request.ownerUserId,
            },
            request.ownerUserId
          );
        } catch (error) {
          console.warn(
            '[CatalogService] Failed to apply global sharing after creation',
            error
          );
        }
      }

      return response;
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to create unit');
    }
  }

  /**
   * Retry failed unit creation
   */
  async retryUnitCreation(unitId: string): Promise<UnitCreationResponse> {
    try {
      if (!unitId?.trim()) {
        throw new Error('Unit ID is required');
      }

      return await this.deps.contentCreator.retryUnitCreation(unitId);
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to retry unit creation');
    }
  }

  /**
   * Dismiss (delete) a failed unit
   */
  async dismissUnit(unitId: string): Promise<void> {
    try {
      if (!unitId?.trim()) {
        throw new Error('Unit ID is required');
      }

      await this.deps.contentCreator.dismissUnit(unitId);
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to dismiss unit');
    }
  }
}
