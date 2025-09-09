/**
 * Topic Catalog Public Interface
 *
 * The only interface other modules should import from.
 * Pure forwarder - no logic, just selects/forwards service methods.
 */

import { TopicCatalogService } from './service';
import { TopicCatalogRepo } from './repo';
import type {
  TopicSummary,
  TopicDetail,
  BrowseTopicsResponse,
  TopicFilters,
  CatalogStatistics,
  PaginationInfo,
} from './models';

// Public interface protocol
export interface TopicCatalogProvider {
  // Only expose what learning_session actually needs
  getTopicDetail(topicId: string): Promise<TopicDetail | null>;

  // Internal methods for topic_catalog's own screens (not cross-module)
  browseTopics(
    filters?: TopicFilters,
    pagination?: Omit<PaginationInfo, 'hasMore'>
  ): Promise<BrowseTopicsResponse>;
  searchTopics(
    query: string,
    filters?: TopicFilters,
    pagination?: Omit<PaginationInfo, 'hasMore'>
  ): Promise<BrowseTopicsResponse>;
  getPopularTopics(limit?: number): Promise<TopicSummary[]>;
  getCatalogStatistics(): Promise<CatalogStatistics>;
  refreshCatalog(): Promise<{
    refreshedTopics: number;
    totalTopics: number;
    timestamp: string;
  }>;
  checkHealth(): Promise<boolean>;
}

// Service instance (singleton)
let serviceInstance: TopicCatalogService | null = null;

function getServiceInstance(): TopicCatalogService {
  if (!serviceInstance) {
    const repo = new TopicCatalogRepo();
    serviceInstance = new TopicCatalogService(repo);
  }
  return serviceInstance;
}

// Public provider function
export function topicCatalogProvider(): TopicCatalogProvider {
  const service = getServiceInstance();

  // Pure forwarder - no logic
  return {
    getTopicDetail: service.getTopicDetail.bind(service),
    browseTopics: service.browseTopics.bind(service),
    searchTopics: service.searchTopics.bind(service),
    getPopularTopics: service.getPopularTopics.bind(service),
    getCatalogStatistics: service.getCatalogStatistics.bind(service),
    refreshCatalog: service.refreshCatalog.bind(service),
    checkHealth: service.checkHealth.bind(service),
  };
}

// Export types for other modules
export type {
  TopicSummary,
  TopicDetail,
  BrowseTopicsResponse,
  TopicFilters,
  CatalogStatistics,
  PaginationInfo,
} from './models';
