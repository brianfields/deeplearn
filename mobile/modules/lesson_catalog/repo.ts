/**
 * Lesson Catalog Repository
 *
 * HTTP client for lesson catalog API endpoints.
 * Uses infrastructure module for HTTP requests.
 */

import { infrastructureProvider } from '../infrastructure/public';
import type {
  SearchLessonsRequest,
  CatalogStatistics,
  LessonCatalogError,
} from './models';

// Backend API endpoints
const LESSON_CATALOG_BASE = '/api/v1/lessons';

// API response types (private to repo)
interface ApiBrowseLessonsResponse {
  lessons: Array<{
    id: string;
    title: string;
    core_concept: string;
    user_level: string;
    learning_objectives: string[];
    key_concepts: string[];
    component_count: number;
  }>;
  total: number;
}

interface ApiLessonDetail {
  id: string;
  title: string;
  core_concept: string;
  user_level: string;
  learning_objectives: string[];
  key_concepts: string[];
  components: any[];
  created_at: string;
  component_count: number;
}

export class LessonCatalogRepo {
  private infrastructure = infrastructureProvider();

  /**
   * Browse lessons with optional filters
   */
  async browseLessons(
    request: SearchLessonsRequest = {}
  ): Promise<ApiBrowseLessonsResponse> {
    try {
      const params = new URLSearchParams();

      if (request.userLevel) {
        params.append('user_level', request.userLevel);
      }
      if (request.limit !== undefined) {
        params.append('limit', request.limit.toString());
      }

      const endpoint = `${LESSON_CATALOG_BASE}/?${params.toString()}`;

      const response =
        await this.infrastructure.request<ApiBrowseLessonsResponse>(endpoint, {
          method: 'GET',
        });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to browse lessons');
    }
  }

  /**
   * Get lesson details by ID
   */
  async getLessonDetail(lessonId: string): Promise<ApiLessonDetail> {
    try {
      const endpoint = `${LESSON_CATALOG_BASE}/${lessonId}`;

      const response = await this.infrastructure.request<ApiLessonDetail>(
        endpoint,
        { method: 'GET' }
      );

      return response;
    } catch (error) {
      throw this.handleError(error, `Failed to get lesson ${lessonId}`);
    }
  }

  /**
   * Search lessons with query and filters
   */
  async searchLessons(
    request: SearchLessonsRequest
  ): Promise<ApiBrowseLessonsResponse> {
    try {
      const params = new URLSearchParams();

      if (request.query) {
        params.append('query', request.query);
      }
      if (request.userLevel) {
        params.append('user_level', request.userLevel);
      }
      if (request.minDuration !== undefined) {
        params.append('min_duration', request.minDuration.toString());
      }
      if (request.maxDuration !== undefined) {
        params.append('max_duration', request.maxDuration.toString());
      }
      if (request.readyOnly !== undefined) {
        params.append('ready_only', request.readyOnly.toString());
      }
      if (request.limit !== undefined) {
        params.append('limit', request.limit.toString());
      }
      if (request.offset !== undefined) {
        params.append('offset', request.offset.toString());
      }

      // Use the new search endpoint
      const endpoint = `${LESSON_CATALOG_BASE}/search?${params.toString()}`;

      const response =
        await this.infrastructure.request<ApiBrowseLessonsResponse>(endpoint, {
          method: 'GET',
        });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to search lessons');
    }
  }

  /**
   * Get popular lessons
   */
  async getPopularLessons(
    limit: number = 10
  ): Promise<ApiBrowseLessonsResponse> {
    try {
      const params = new URLSearchParams();
      params.append('limit', limit.toString());

      // Use the new popular endpoint
      const endpoint = `${LESSON_CATALOG_BASE}/popular?${params.toString()}`;

      const lessons = await this.infrastructure.request<
        Array<{
          id: string;
          title: string;
          core_concept: string;
          user_level: string;
          learning_objectives: string[];
          key_concepts: string[];
          component_count: number;
        }>
      >(endpoint, {
        method: 'GET',
      });

      // Convert to browse response format
      return {
        lessons,
        total: lessons.length,
      };
    } catch (error) {
      throw this.handleError(error, 'Failed to get popular lessons');
    }
  }

  /**
   * Get catalog statistics
   */
  async getCatalogStatistics(): Promise<CatalogStatistics> {
    try {
      const endpoint = `${LESSON_CATALOG_BASE}/statistics`;

      const response = await this.infrastructure.request<{
        total_lessons: number;
        lessons_by_user_level: Record<string, number>;
        lessons_by_readiness: Record<string, number>;
        average_duration: number;
        duration_distribution: Record<string, number>;
      }>(endpoint, {
        method: 'GET',
      });

      // Convert snake_case to camelCase
      return {
        totalLessons: response.total_lessons,
        lessonsByUserLevel: response.lessons_by_user_level,
        lessonsByReadiness: response.lessons_by_readiness,
        averageDuration: response.average_duration,
        durationDistribution: response.duration_distribution,
      };
    } catch (error) {
      throw this.handleError(error, 'Failed to get catalog statistics');
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
      const endpoint = `${LESSON_CATALOG_BASE}/refresh`;

      const response = await this.infrastructure.request<{
        refreshed_lessons: number;
        total_lessons: number;
        timestamp: string;
      }>(endpoint, {
        method: 'POST',
      });

      // Convert snake_case to camelCase
      return {
        refreshedLessons: response.refreshed_lessons,
        totalLessons: response.total_lessons,
        timestamp: response.timestamp,
      };
    } catch (error) {
      throw this.handleError(error, 'Failed to refresh catalog');
    }
  }

  /**
   * Check health
   */
  async checkHealth(): Promise<boolean> {
    try {
      const networkStatus = this.infrastructure.getNetworkStatus();
      return networkStatus.isConnected;
    } catch (error) {
      console.warn('[LessonCatalogRepo] Health check failed:', error);
      return false;
    }
  }

  /**
   * Handle and transform errors
   */
  private handleError(error: any, defaultMessage: string): LessonCatalogError {
    console.error('[LessonCatalogRepo]', defaultMessage, error);

    // If it's already a structured error from infrastructure
    if (error && typeof error === 'object') {
      return {
        message: error.message || defaultMessage,
        code: error.code || 'LESSON_CATALOG_ERROR',
        statusCode: error.status || error.statusCode,
        details: error.details || error,
      };
    }

    // Generic error
    return {
      message: defaultMessage,
      code: 'LESSON_CATALOG_ERROR',
      details: error,
    };
  }
}
