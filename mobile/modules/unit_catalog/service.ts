/**
 * Lesson Catalog Service
 *
 * Business logic for lesson browsing, search, and discovery.
 * Returns DTOs only, never raw API responses.
 */

import { LessonCatalogRepo } from './repo';
import { unitsProvider, type Unit, type UnitDetail } from '../units/public';
import type {
  LessonSummary,
  LessonDetail,
  BrowseLessonsResponse,
  SearchLessonsRequest,
  LessonFilters,
  CatalogStatistics,
  LessonCatalogError,
  PaginationInfo,
} from './models';
import {
  toLessonSummaryDTO,
  toLessonDetailDTO,
  toBrowseLessonsResponseDTO,
} from './models';

export class LessonCatalogService {
  constructor(private repo: LessonCatalogRepo) {}

  /**
   * Browse lessons with optional filters
   */
  async browseLessons(
    filters: LessonFilters = {},
    pagination: Omit<PaginationInfo, 'hasMore'> = { limit: 100, offset: 0 }
  ): Promise<BrowseLessonsResponse> {
    try {
      const request: SearchLessonsRequest = {
        userLevel: filters.userLevel,
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
        userLevel: filters.userLevel,
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
      console.warn('[LessonCatalogService] Health check failed:', error);
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
      lesson.coreConcept.toLowerCase().includes(searchTerm) ||
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
  private handleServiceError(
    error: any,
    defaultMessage: string
  ): LessonCatalogError {
    console.error('[LessonCatalogService]', defaultMessage, error);

    // If it's already a LessonCatalogError, pass it through
    if (error && error.code === 'TOPIC_CATALOG_ERROR') {
      return error;
    }

    // Transform other errors
    return {
      message: error?.message || defaultMessage,
      code: 'TOPIC_CATALOG_SERVICE_ERROR',
      statusCode: error?.statusCode,
      details: error,
    };
  }

  /**
   * Browse units (delegates to units module)
   * Added for unit-based browsing in the catalog UI.
   */
  async browseUnits(params?: {
    limit?: number;
    offset?: number;
  }): Promise<Unit[]> {
    const units = unitsProvider();
    return units.list(params);
  }

  /**
   * Get unit details (delegates to units module)
   */
  async getUnitDetail(unitId: string): Promise<UnitDetail | null> {
    if (!unitId?.trim()) return null;
    const units = unitsProvider();
    return units.detail(unitId);
  }
}
