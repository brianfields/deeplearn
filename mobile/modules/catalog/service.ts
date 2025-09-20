/**
 * Lesson Catalog Service
 *
 * Business logic for lesson browsing, search, and discovery.
 * Returns DTOs only, never raw API responses.
 */

import { CatalogRepo } from './repo';
import type { Unit, UnitDetail } from './models';
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
   * Browse units (delegates to units module)
   * Added for unit-based browsing in the catalog UI.
   */
  async browseUnits(params?: {
    limit?: number;
    offset?: number;
  }): Promise<Unit[]> {
    const apiUnits = await this.repo.listUnits(params);
    return apiUnits.map(u => ({
      id: u.id,
      title: u.title,
      description: u.description,
      difficulty: (u.difficulty as any) ?? 'beginner',
      lessonCount: u.lesson_count,
      difficultyLabel: this.formatDifficulty(
        (u.difficulty as any) ?? 'beginner'
      ),
    }));
  }

  /**
   * Get unit details (delegates to units module)
   */
  async getUnitDetail(unitId: string): Promise<UnitDetail | null> {
    if (!unitId?.trim()) return null;
    try {
      const api = await this.repo.getUnitDetail(unitId);
      const difficulty = (api.difficulty as any) ?? 'beginner';
      return {
        id: api.id,
        title: api.title,
        description: api.description,
        difficulty,
        lessonIds: [...(api.lesson_order ?? [])],
        lessons: api.lessons.map(l => ({
          id: l.id,
          title: l.title,
          coreConcept: l.core_concept,
          userLevel: l.user_level as any,
          learningObjectives: l.learning_objectives,
          keyConcepts: l.key_concepts,
          componentCount: l.exercise_count,
          estimatedDuration: Math.max(5, l.exercise_count * 3),
          isReadyForLearning: l.exercise_count > 0,
          difficultyLevel: this.formatDifficulty(l.user_level as any),
          durationDisplay: this.formatDuration(
            Math.max(5, l.exercise_count * 3)
          ),
          readinessStatus: l.exercise_count > 0 ? 'Ready' : 'Draft',
          tags: (l.key_concepts ?? []).slice(0, 3),
        })),
      };
    } catch (err: any) {
      if (err?.statusCode === 404) return null;
      throw err;
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
