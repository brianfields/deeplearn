import { ContentService } from './service';
import { ContentRepo } from './repo';
import type { Unit, UnitDetail, UserUnitCollections } from './models';
import type { UpdateUnitSharingRequest } from './models';
import type { CachedAsset, SyncStatus } from '../offline_cache/public';

export interface ContentProvider {
  listUnits(params?: {
    limit?: number;
    offset?: number;
    currentUserId?: number | null;
  }): Promise<Unit[]>;
  getUnitDetail(
    unitId: string,
    options?: { currentUserId?: number | null }
  ): Promise<UnitDetail | null>;
  getUserUnitCollections(
    userId: number,
    options?: { includeGlobal?: boolean; limit?: number; offset?: number }
  ): Promise<UserUnitCollections>;
  updateUnitSharing(
    unitId: string,
    request: UpdateUnitSharingRequest,
    currentUserId?: number | null
  ): Promise<Unit>;
  requestUnitDownload(unitId: string): Promise<void>;
  removeUnitDownload(unitId: string): Promise<void>;
  resolveAsset(assetId: string): Promise<CachedAsset | null>;
  syncNow(): Promise<SyncStatus>;
  getSyncStatus(): Promise<SyncStatus>;
}

let serviceInstance: ContentService | null = null;

function getServiceInstance(): ContentService {
  if (!serviceInstance) {
    const repo = new ContentRepo();
    serviceInstance = new ContentService(repo);
  }
  return serviceInstance;
}

export function contentProvider(): ContentProvider {
  const service = getServiceInstance();
  return {
    listUnits: service.listUnits.bind(service),
    getUnitDetail: service.getUnitDetail.bind(service),
    getUserUnitCollections: service.getUserUnitCollections.bind(service),
    updateUnitSharing: service.updateUnitSharing.bind(service),
    requestUnitDownload: service.requestUnitDownload.bind(service),
    removeUnitDownload: service.removeUnitDownload.bind(service),
    resolveAsset: service.resolveAsset.bind(service),
    syncNow: service.syncNow.bind(service),
    getSyncStatus: service.getSyncStatus.bind(service),
  };
}

export type {
  Unit,
  UnitDetail,
  UnitStatus,
  Difficulty,
  UnitLessonSummary,
  UnitCreationProgress,
  UnitProgress,
  UserUnitCollections,
  ContentError,
  UpdateUnitSharingRequest,
} from './models';
