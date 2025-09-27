/**
 * Lesson Catalog Service
 *
 * Business logic for lesson browsing, search, and discovery.
 * Returns DTOs only, never raw API responses.
 */

import { CatalogRepo } from './repo';
import type { Unit, UnitDetail, UserUnitCollections } from './models';
import type {
  LessonSummary,
  LessonDetail,
  BrowseLessonsResponse,
  SearchLessonsRequest,
  LessonFilters,
  CatalogStatistics,
  CatalogError,
  PaginationInfo,
  UnitCreationRequest,
  UnitCreationResponse,
} from './models';
import {
  toLessonSummaryDTO,
  toLessonDetailDTO,
  toBrowseLessonsResponseDTO,
  toUnitDTO,
  toUnitDetailDTO,
} from './models';

export class CatalogService {
  constructor(private repo: CatalogRepo) {}

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
   */
  async getLessonDetail(lessonId: string): Promise<LessonDetail | null> {
    try {
      if (!lessonId?.trim()) {
        return null;
      }

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

    // If it's already a CatalogError, pass it through
    if (error && error.code === 'TOPIC_CATALOG_ERROR') {
      return error;
    }

    // Transform other errors
    return {
      message: error?.message || defaultMessage,
      code: 'CATALOG_SERVICE_ERROR',
      statusCode: error?.statusCode,
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
      const limit = params?.limit;
      const offset = params?.offset;
      const currentUserId = params?.currentUserId;
      const apiUnits = await this.repo.listUnits({ limit, offset });
      return apiUnits.map(api => toUnitDTO(api, currentUserId));
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
      const api = await this.repo.getUnitDetail(unitId);
      return toUnitDetailDTO(api, currentUserId);
    } catch (error: any) {
      if (error?.statusCode === 404) return null;
      throw this.handleServiceError(error, `Failed to get unit ${unitId}`);
    }
  }

  async getUserUnitCollections(
    userId: number,
    options?: { includeGlobal?: boolean; limit?: number; offset?: number }
  ): Promise<UserUnitCollections> {
    if (!Number.isFinite(userId) || userId <= 0) {
      return { personalUnits: [], globalUnits: [] };
    }

    const includeGlobal = options?.includeGlobal ?? true;
    const paging = { limit: options?.limit, offset: options?.offset };

    try {
      const personalPromise = this.repo.listPersonalUnits(userId, paging);
      const globalPromise = includeGlobal
        ? this.repo.listGlobalUnits(paging)
        : Promise.resolve([]);

      const [personalApi, globalApi] = await Promise.all([
        personalPromise,
        globalPromise,
      ]);

      const personalUnits = personalApi.map(api => toUnitDTO(api, userId));

      const personalIds = new Set(personalUnits.map(unit => unit.id));
      const globalUnits = globalApi
        .filter(api => !personalIds.has(api.id))
        .map(api => toUnitDTO(api, userId));

      return { personalUnits, globalUnits };
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
      const updated = await this.repo.updateUnitSharing(unitId, {
        isGlobal: request.makeGlobal,
        actingUserId: request.actingUserId ?? undefined,
      });
      return toUnitDTO(updated, request.actingUserId ?? null);
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

      const response = await this.repo.createUnit(request);

      if (request.shareGlobally && request.ownerUserId) {
        try {
          await this.repo.updateUnitSharing(response.unitId, {
            isGlobal: true,
            actingUserId: request.ownerUserId,
          });
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

      return await this.repo.retryUnitCreation(unitId);
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

      await this.repo.dismissUnit(unitId);
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to dismiss unit');
    }
  }

  private formatDifficulty(
    d: 'beginner' | 'intermediate' | 'advanced' | string
  ): string {
    const map: Record<string, string> = {
      beginner: 'Beginner',
      intermediate: 'Intermediate',
      advanced: 'Advanced',
    };
    return map[d] ?? 'Unknown';
  }

  private formatDuration(minutes: number): string {
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const remaining = minutes % 60;
    return remaining === 0 ? `${hours} hr` : `${hours} hr ${remaining} min`;
  }
}
