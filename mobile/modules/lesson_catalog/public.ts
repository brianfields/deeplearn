/**
 * Lesson Catalog Public Interface
 *
 * The only interface other modules should import from.
 * Pure forwarder - no logic, just selects/forwards service methods.
 */

import { LessonCatalogService } from './service';
import { LessonCatalogRepo } from './repo';
import type {
  LessonSummary,
  LessonDetail,
  BrowseLessonsResponse,
  LessonFilters,
  CatalogStatistics,
  PaginationInfo,
} from './models';

// Public interface protocol
export interface LessonCatalogProvider {
  // Only expose what learning_session actually needs
  getLessonDetail(lessonId: string): Promise<LessonDetail | null>;

  // Internal methods for lesson_catalog's own screens (not cross-module)
  browseLessons(
    filters?: LessonFilters,
    pagination?: Omit<PaginationInfo, 'hasMore'>
  ): Promise<BrowseLessonsResponse>;
  searchLessons(
    query: string,
    filters?: LessonFilters,
    pagination?: Omit<PaginationInfo, 'hasMore'>
  ): Promise<BrowseLessonsResponse>;
  getPopularLessons(limit?: number): Promise<LessonSummary[]>;
  getCatalogStatistics(): Promise<CatalogStatistics>;
  refreshCatalog(): Promise<{
    refreshedLessons: number;
    totalLessons: number;
    timestamp: string;
  }>;
  checkHealth(): Promise<boolean>;
}

// Service instance (singleton)
let serviceInstance: LessonCatalogService | null = null;

function getServiceInstance(): LessonCatalogService {
  if (!serviceInstance) {
    const repo = new LessonCatalogRepo();
    serviceInstance = new LessonCatalogService(repo);
  }
  return serviceInstance;
}

// Public provider function
export function lessonCatalogProvider(): LessonCatalogProvider {
  const service = getServiceInstance();

  // Pure forwarder - no logic
  return {
    getLessonDetail: service.getLessonDetail.bind(service),
    browseLessons: service.browseLessons.bind(service),
    searchLessons: service.searchLessons.bind(service),
    getPopularLessons: service.getPopularLessons.bind(service),
    getCatalogStatistics: service.getCatalogStatistics.bind(service),
    refreshCatalog: service.refreshCatalog.bind(service),
    checkHealth: service.checkHealth.bind(service),
  };
}

// Export types for other modules
export type {
  LessonSummary,
  LessonDetail,
  BrowseLessonsResponse,
  LessonFilters,
  CatalogStatistics,
  PaginationInfo,
} from './models';
