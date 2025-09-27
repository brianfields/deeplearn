import { ContentService } from './service';
import { ContentRepo } from './repo';
import type {
  Unit,
  UnitDetail,
  UnitStatus,
  Difficulty,
  UnitLessonSummary,
  UserUnitCollections,
  ContentError,
} from './models';
import type { UpdateUnitSharingRequest } from './models';

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
  listPersonalUnits(
    userId: number,
    options?: { limit?: number; offset?: number; currentUserId?: number | null }
  ): Promise<Unit[]>;
  listGlobalUnits(
    options?: { limit?: number; offset?: number; currentUserId?: number | null }
  ): Promise<Unit[]>;
  getUserUnitCollections(
    userId: number,
    options?: { includeGlobal?: boolean; limit?: number; offset?: number }
  ): Promise<UserUnitCollections>;
  updateUnitSharing(
    unitId: string,
    request: UpdateUnitSharingRequest,
    currentUserId?: number | null
  ): Promise<Unit>;
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
    listPersonalUnits: service.listPersonalUnits.bind(service),
    listGlobalUnits: service.listGlobalUnits.bind(service),
    getUserUnitCollections: service.getUserUnitCollections.bind(service),
    updateUnitSharing: service.updateUnitSharing.bind(service),
  };
}

export type {
  Unit,
  UnitDetail,
  UnitStatus,
  Difficulty,
  UnitLessonSummary,
  UserUnitCollections,
  ContentError,
  UpdateUnitSharingRequest,
} from './models';
