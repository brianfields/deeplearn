/**
 * Topic Catalog Service
 *
 * Business logic for topic browsing, search, and discovery.
 * Returns DTOs only, never raw API responses.
 */

import { TopicCatalogRepo } from './repo';
import type {
  TopicSummary,
  TopicDetail,
  BrowseTopicsResponse,
  SearchTopicsRequest,
  TopicFilters,
  CatalogStatistics,
  TopicCatalogError,
  PaginationInfo,
} from './models';
import {
  toTopicSummaryDTO,
  toTopicDetailDTO,
  toBrowseTopicsResponseDTO,
} from './models';

export class TopicCatalogService {
  constructor(private repo: TopicCatalogRepo) {}

  /**
   * Browse topics with optional filters
   */
  async browseTopics(
    filters: TopicFilters = {},
    pagination: Omit<PaginationInfo, 'hasMore'> = { limit: 100, offset: 0 }
  ): Promise<BrowseTopicsResponse> {
    try {
      const request: SearchTopicsRequest = {
        userLevel: filters.userLevel,
        readyOnly: filters.readyOnly,
        limit: pagination.limit,
        offset: pagination.offset,
      };

      const apiResponse = await this.repo.browseTopics(request);

      // Convert to DTO
      const response = toBrowseTopicsResponseDTO(
        apiResponse,
        filters,
        pagination
      );

      // Apply client-side filtering if needed
      return this.applyClientFilters(response, filters);
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to browse topics');
    }
  }

  /**
   * Search topics with query and filters
   */
  async searchTopics(
    query: string,
    filters: TopicFilters = {},
    pagination: Omit<PaginationInfo, 'hasMore'> = { limit: 100, offset: 0 }
  ): Promise<BrowseTopicsResponse> {
    try {
      const request: SearchTopicsRequest = {
        query: query.trim() || undefined,
        userLevel: filters.userLevel,
        minDuration: filters.minDuration,
        maxDuration: filters.maxDuration,
        readyOnly: filters.readyOnly,
        limit: pagination.limit,
        offset: pagination.offset,
      };

      const apiResponse = await this.repo.searchTopics(request);

      // Convert to DTO
      const response = toBrowseTopicsResponseDTO(
        apiResponse,
        { ...filters, query },
        pagination
      );

      // Apply client-side filtering
      return this.applyClientFilters(response, { ...filters, query });
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to search topics');
    }
  }

  /**
   * Get topic details by ID
   */
  async getTopicDetail(topicId: string): Promise<TopicDetail | null> {
    try {
      if (!topicId?.trim()) {
        return null;
      }

      const apiResponse = await this.repo.getTopicDetail(topicId);
      return toTopicDetailDTO(apiResponse);
    } catch (error: any) {
      // Return null for 404s, throw for other errors
      if (error.statusCode === 404) {
        return null;
      }
      throw this.handleServiceError(error, `Failed to get topic ${topicId}`);
    }
  }

  /**
   * Get popular topics
   */
  async getPopularTopics(limit: number = 10): Promise<TopicSummary[]> {
    try {
      const apiResponse = await this.repo.getPopularTopics(limit);
      return apiResponse.topics.map(toTopicSummaryDTO);
    } catch (error) {
      throw this.handleServiceError(error, 'Failed to get popular topics');
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
    refreshedTopics: number;
    totalTopics: number;
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
      console.warn('[TopicCatalogService] Health check failed:', error);
      return false;
    }
  }

  /**
   * Apply client-side filters to response
   */
  private applyClientFilters(
    response: BrowseTopicsResponse,
    filters: TopicFilters
  ): BrowseTopicsResponse {
    let filteredTopics = response.topics;

    // Apply query filter (client-side search)
    if (filters.query?.trim()) {
      const query = filters.query.toLowerCase();
      filteredTopics = filteredTopics.filter(topic =>
        this.matchesQuery(topic, query)
      );
    }

    // Apply duration filters
    if (filters.minDuration !== undefined) {
      filteredTopics = filteredTopics.filter(
        topic => topic.estimatedDuration >= filters.minDuration!
      );
    }

    if (filters.maxDuration !== undefined) {
      filteredTopics = filteredTopics.filter(
        topic => topic.estimatedDuration <= filters.maxDuration!
      );
    }

    // Apply readiness filter
    if (filters.readyOnly) {
      filteredTopics = filteredTopics.filter(topic => topic.isReadyForLearning);
    }

    return {
      ...response,
      topics: filteredTopics,
      total: filteredTopics.length,
    };
  }

  /**
   * Check if topic matches search query
   */
  private matchesQuery(topic: TopicSummary, query: string): boolean {
    if (!query.trim()) return true;

    const searchTerm = query.toLowerCase();
    return (
      topic.title.toLowerCase().includes(searchTerm) ||
      topic.coreConcept.toLowerCase().includes(searchTerm) ||
      topic.keyConcepts.some(concept =>
        concept.toLowerCase().includes(searchTerm)
      ) ||
      topic.learningObjectives.some(objective =>
        objective.toLowerCase().includes(searchTerm)
      ) ||
      topic.tags.some(tag => tag.toLowerCase().includes(searchTerm))
    );
  }

  /**
   * Handle and transform service errors
   */
  private handleServiceError(
    error: any,
    defaultMessage: string
  ): TopicCatalogError {
    console.error('[TopicCatalogService]', defaultMessage, error);

    // If it's already a TopicCatalogError, pass it through
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
}
