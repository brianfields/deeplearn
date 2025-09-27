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
  UnitCreationRequest,
  UnitCreationResponse,
  UserUnitCollections,
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
    currentUserId?: number | null;
  }): Promise<import('./models').Unit[]>;
  getUnitDetail(
    unitId: string,
    currentUserId?: number | null
  ): Promise<import('./models').UnitDetail | null>;
  createUnit(request: UnitCreationRequest): Promise<UnitCreationResponse>;
  retryUnitCreation(unitId: string): Promise<UnitCreationResponse>;
  dismissUnit(unitId: string): Promise<void>;
  getUserUnitCollections(
    userId: number,
    options?: { includeGlobal?: boolean; limit?: number; offset?: number }
  ): Promise<UserUnitCollections>;
  toggleUnitSharing(
    unitId: string,
    request: { makeGlobal: boolean; actingUserId?: number | null }
  ): Promise<import('./models').Unit>;
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
    createUnit: service.createUnit.bind(service),
    retryUnitCreation: service.retryUnitCreation.bind(service),
    dismissUnit: service.dismissUnit.bind(service),
    getUserUnitCollections: service.getUserUnitCollections.bind(service),
    toggleUnitSharing: service.toggleUnitSharing.bind(service),
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
  UnitCreationRequest,
  UnitCreationResponse,
  UserUnitCollections,
} from './models';
export type { Unit, UnitDetail, UnitStatus, Difficulty } from './models';
