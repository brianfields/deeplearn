/**
 * Lesson Catalog Public Interface
 *
 * The only interface other modules should import from.
 * Pure forwarder - no logic, just selects/forwards service methods.
 */

import { CatalogService } from './service';
import { CatalogRepo } from './repo';
import type {
  LessonSummary,
  LessonDetail,
  BrowseLessonsResponse,
  LessonFilters,
  CatalogStatistics,
  PaginationInfo,
} from './models';

// Public interface protocol
export interface CatalogProvider {
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
  // Units
  browseUnits(params?: {
    limit?: number;
    offset?: number;
  }): Promise<import('./models').Unit[]>;
  getUnitDetail(unitId: string): Promise<import('./models').UnitDetail | null>;
}

// Service instance (singleton)
let serviceInstance: CatalogService | null = null;

function getServiceInstance(): CatalogService {
  if (!serviceInstance) {
    const repo = new CatalogRepo();
    serviceInstance = new CatalogService(repo);
  }
  return serviceInstance;
}

// Public provider function
export function catalogProvider(): CatalogProvider {
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
    browseUnits: service.browseUnits.bind(service),
    getUnitDetail: service.getUnitDetail.bind(service),
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
export type { Unit, UnitDetail } from './models';
