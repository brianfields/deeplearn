/**
 * Topic Catalog Repository
 *
 * HTTP client for topic catalog API endpoints.
 * Uses infrastructure module for HTTP requests.
 */

import { infrastructureProvider } from '../infrastructure/public';
import type {
  SearchTopicsRequest,
  CatalogStatistics,
  TopicCatalogError,
} from './models';

// Backend API endpoints
const TOPIC_CATALOG_BASE = '/api/v1/topics';

// API response types (private to repo)
interface ApiBrowseTopicsResponse {
  topics: Array<{
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

interface ApiTopicDetail {
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

export class TopicCatalogRepo {
  private infrastructure = infrastructureProvider();

  /**
   * Browse topics with optional filters
   */
  async browseTopics(
    request: SearchTopicsRequest = {}
  ): Promise<ApiBrowseTopicsResponse> {
    try {
      const params = new URLSearchParams();

      if (request.userLevel) {
        params.append('user_level', request.userLevel);
      }
      if (request.limit !== undefined) {
        params.append('limit', request.limit.toString());
      }

      const endpoint = `${TOPIC_CATALOG_BASE}/?${params.toString()}`;

      const response =
        await this.infrastructure.request<ApiBrowseTopicsResponse>(endpoint, {
          method: 'GET',
        });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to browse topics');
    }
  }

  /**
   * Get topic details by ID
   */
  async getTopicDetail(topicId: string): Promise<ApiTopicDetail> {
    try {
      const endpoint = `${TOPIC_CATALOG_BASE}/${topicId}`;

      const response = await this.infrastructure.request<ApiTopicDetail>(
        endpoint,
        { method: 'GET' }
      );

      return response;
    } catch (error) {
      throw this.handleError(error, `Failed to get topic ${topicId}`);
    }
  }

  /**
   * Search topics with query and filters
   */
  async searchTopics(
    request: SearchTopicsRequest
  ): Promise<ApiBrowseTopicsResponse> {
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
      const endpoint = `${TOPIC_CATALOG_BASE}/search?${params.toString()}`;

      const response =
        await this.infrastructure.request<ApiBrowseTopicsResponse>(endpoint, {
          method: 'GET',
        });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to search topics');
    }
  }

  /**
   * Get popular topics
   */
  async getPopularTopics(limit: number = 10): Promise<ApiBrowseTopicsResponse> {
    try {
      const params = new URLSearchParams();
      params.append('limit', limit.toString());

      // Use the new popular endpoint
      const endpoint = `${TOPIC_CATALOG_BASE}/popular?${params.toString()}`;

      const topics = await this.infrastructure.request<
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
        topics,
        total: topics.length,
      };
    } catch (error) {
      throw this.handleError(error, 'Failed to get popular topics');
    }
  }

  /**
   * Get catalog statistics
   */
  async getCatalogStatistics(): Promise<CatalogStatistics> {
    try {
      const endpoint = `${TOPIC_CATALOG_BASE}/statistics`;

      const response = await this.infrastructure.request<{
        total_topics: number;
        topics_by_user_level: Record<string, number>;
        topics_by_readiness: Record<string, number>;
        average_duration: number;
        duration_distribution: Record<string, number>;
      }>(endpoint, {
        method: 'GET',
      });

      // Convert snake_case to camelCase
      return {
        totalTopics: response.total_topics,
        topicsByUserLevel: response.topics_by_user_level,
        topicsByReadiness: response.topics_by_readiness,
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
    refreshedTopics: number;
    totalTopics: number;
    timestamp: string;
  }> {
    try {
      const endpoint = `${TOPIC_CATALOG_BASE}/refresh`;

      const response = await this.infrastructure.request<{
        refreshed_topics: number;
        total_topics: number;
        timestamp: string;
      }>(endpoint, {
        method: 'POST',
      });

      // Convert snake_case to camelCase
      return {
        refreshedTopics: response.refreshed_topics,
        totalTopics: response.total_topics,
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
      console.warn('[TopicCatalogRepo] Health check failed:', error);
      return false;
    }
  }

  /**
   * Handle and transform errors
   */
  private handleError(error: any, defaultMessage: string): TopicCatalogError {
    console.error('[TopicCatalogRepo]', defaultMessage, error);

    // If it's already a structured error from infrastructure
    if (error && typeof error === 'object') {
      return {
        message: error.message || defaultMessage,
        code: error.code || 'TOPIC_CATALOG_ERROR',
        statusCode: error.status || error.statusCode,
        details: error.details || error,
      };
    }

    // Generic error
    return {
      message: defaultMessage,
      code: 'TOPIC_CATALOG_ERROR',
      details: error,
    };
  }
}
