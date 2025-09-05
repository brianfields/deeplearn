/**
 * HTTP client for Topic Catalog API.
 *
 * Handles communication with the backend Topic Catalog module.
 */

import { TopicSummary } from '../domain/entities/topic-summary';

type RequestInit = {
  method?: string;
  headers?: Record<string, string>;
  body?: string;
};

export interface SearchTopicsRequest {
  query?: string;
  userLevel?: 'beginner' | 'intermediate' | 'advanced';
  minDuration?: number;
  maxDuration?: number;
  readyOnly?: boolean;
  limit?: number;
  offset?: number;
}

export interface SearchTopicsResponse {
  topics: TopicSummary[];
  totalCount: number;
  query?: string;
  filters: Record<string, any>;
  pagination: {
    limit: number;
    offset: number;
  };
}

export interface CatalogStatistics {
  totalTopics: number;
  topicsByUserLevel: Record<string, number>;
  topicsByReadiness: Record<string, number>;
  averageDuration: number;
  durationDistribution: Record<string, number>;
}

export class TopicCatalogClient {
  private baseUrl: string;
  private apiKey?: string;

  constructor(baseUrl: string, apiKey?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = apiKey;
  }

  /**
   * Search topics with filters and pagination.
   */
  async searchTopics(
    request: SearchTopicsRequest
  ): Promise<SearchTopicsResponse> {
    const params = new URLSearchParams();

    if (request.query) params.append('query', request.query);
    if (request.userLevel) params.append('user_level', request.userLevel);
    if (request.minDuration !== undefined)
      params.append('min_duration', request.minDuration.toString());
    if (request.maxDuration !== undefined)
      params.append('max_duration', request.maxDuration.toString());
    if (request.readyOnly !== undefined)
      params.append('ready_only', request.readyOnly.toString());
    if (request.limit !== undefined)
      params.append('limit', request.limit.toString());
    if (request.offset !== undefined)
      params.append('offset', request.offset.toString());

    const url = `${this.baseUrl}/api/v1/catalog/topics/search?${params.toString()}`;

    const response = await this.fetch(url);
    return response.json();
  }

  /**
   * Get a specific topic by ID.
   */
  async getTopicById(topicId: string): Promise<TopicSummary> {
    const url = `${this.baseUrl}/api/v1/catalog/topics/${topicId}`;
    const response = await this.fetch(url);
    return response.json();
  }

  /**
   * Get popular topics.
   */
  async getPopularTopics(limit: number = 10): Promise<TopicSummary[]> {
    const url = `${this.baseUrl}/api/v1/catalog/topics/popular?limit=${limit}`;
    const response = await this.fetch(url);
    return response.json();
  }

  /**
   * Get catalog statistics.
   */
  async getCatalogStatistics(): Promise<CatalogStatistics> {
    const url = `${this.baseUrl}/api/v1/catalog/statistics`;
    const response = await this.fetch(url);
    return response.json();
  }

  /**
   * Refresh the catalog.
   */
  async refreshCatalog(): Promise<{
    refreshedTopics: number;
    totalTopics: number;
    timestamp: string;
  }> {
    const url = `${this.baseUrl}/api/v1/catalog/refresh`;
    const response = await this.fetch(url, { method: 'POST' });
    return response.json();
  }

  /**
   * Check module health.
   */
  async checkHealth(): Promise<{
    status: string;
    service: string;
    timestamp: string;
    dependencies: Record<string, string>;
    statistics: Record<string, any>;
  }> {
    const url = `${this.baseUrl}/api/v1/catalog/health`;
    const response = await this.fetch(url);
    return response.json();
  }

  /**
   * Internal fetch wrapper with error handling and auth.
   */
  private async fetch(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new TopicCatalogError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    return response;
  }
}

/**
 * Topic Catalog specific error class.
 */
export class TopicCatalogError extends Error {
  constructor(
    message: string,
    public readonly statusCode?: number,
    public readonly details?: any
  ) {
    super(message);
    this.name = 'TopicCatalogError';
  }
}

/**
 * Factory function to create a configured client.
 */
export function createTopicCatalogClient(
  baseUrl: string = 'http://localhost:8000',
  apiKey?: string
): TopicCatalogClient {
  return new TopicCatalogClient(baseUrl, apiKey);
}
