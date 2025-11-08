/**
 * Lesson Catalog Service
 *
 * Business logic for lesson browsing, search, and discovery.
 * Returns DTOs only, never raw API responses.
 */

import { CatalogRepo } from './repo';
import { LearningSessionRepo } from '../learning_session/repo';
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
import { toLessonSummaryDTO, toBrowseLessonsResponseDTO } from './models';
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
import type { UnitLOProgress } from '../learning_session/models';

interface CatalogServiceDeps {
  readonly content: ContentProvider;
  readonly contentCreator: ContentCreatorProvider;
}

function createDefaultDeps(): CatalogServiceDeps {
  return {
    content: contentProvider(),
    contentCreator: contentCreatorProvider(),
  };
}

export class CatalogService {
  constructor(
    private repo: CatalogRepo,
    private deps: CatalogServiceDeps = createDefaultDeps(),
    private learningSessionRepo: LearningSessionRepo = new LearningSessionRepo()
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
    if (!lessonId?.trim()) {
      return null;
    }

    try {
      const lesson = await this.repo.getLesson(lessonId);
      return lesson;
    } catch (error: any) {
      if (error && typeof error === 'object' && 'statusCode' in error) {
        const typed = error as CatalogError & { statusCode?: number };
        if (typed.statusCode === 404) {
          return null;
        }
      }

      throw this.handleServiceError(error, `Failed to get lesson ${lessonId}`);
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
   * Fetches fresh data from the server, not from offline cache.
   */
  async browseUnits(params?: {
    limit?: number;
    offset?: number;
    currentUserId?: number | null;
  }): Promise<Unit[]> {
    try {
      return await this.deps.content.browseCatalogUnits(params);
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

  async computeUnitLOProgressLocal(
    unitId: string,
    userId: string
  ): Promise<UnitLOProgress> {
    const trimmedUnitId = unitId?.trim();
    const trimmedUserId = userId?.trim();

    if (!trimmedUnitId || !trimmedUserId) {
      return { unitId: trimmedUnitId ?? unitId ?? '', items: [] };
    }

    try {
      return await this.learningSessionRepo.computeUnitLOProgress(
        trimmedUnitId,
        trimmedUserId
      );
    } catch (error) {
      throw this.handleServiceError(
        error,
        'Failed to compute unit learning objective progress locally'
      );
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
      // Validate coach-driven request
      if (!request.learnerDesires?.trim()) {
        throw new Error('Learner desires required');
      }
      if (!request.unitTitle?.trim()) {
        throw new Error('Unit title required');
      }
      if (
        !request.learningObjectives ||
        request.learningObjectives.length === 0
      ) {
        throw new Error('Learning objectives required');
      }
      if (
        !request.targetLessonCount ||
        request.targetLessonCount < 1 ||
        request.targetLessonCount > 20
      ) {
        throw new Error('Target lesson count must be between 1 and 20');
      }
      if (!request.conversationId?.trim()) {
        throw new Error('Conversation ID required');
      }

      const response = await this.deps.contentCreator.createUnit(request);

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
