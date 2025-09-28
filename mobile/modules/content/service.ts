import { ContentRepo } from './repo';
import type {
  Unit,
  UnitDetail,
  UserUnitCollections,
  ContentError,
  UpdateUnitSharingRequest,
} from './models';
import { toUnitDTO, toUnitDetailDTO } from './models';

interface ListUnitsParams {
  limit?: number;
  offset?: number;
  currentUserId?: number | null;
}

export class ContentService {
  constructor(private repo: ContentRepo) {}

  async listUnits(params?: ListUnitsParams): Promise<Unit[]> {
    try {
      const currentUserId = params?.currentUserId;
      const apiUnits = await this.repo.listUnits({
        limit: params?.limit,
        offset: params?.offset,
      });
      return apiUnits.map(api => toUnitDTO(api, currentUserId));
    } catch (error) {
      throw this.handleError(error, 'Failed to list units');
    }
  }

  async getUnitDetail(
    unitId: string,
    options?: { currentUserId?: number | null }
  ): Promise<UnitDetail | null> {
    if (!unitId?.trim()) {
      return null;
    }

    try {
      const api = await this.repo.getUnitDetail(unitId);
      return toUnitDetailDTO(api, options?.currentUserId);
    } catch (error: any) {
      if (error?.statusCode === 404) {
        return null;
      }
      throw this.handleError(error, `Failed to get unit ${unitId}`);
    }
  }

  async listPersonalUnits(
    userId: number,
    options?: { limit?: number; offset?: number; currentUserId?: number | null }
  ): Promise<Unit[]> {
    try {
      const apiUnits = await this.repo.listPersonalUnits(userId, {
        limit: options?.limit,
        offset: options?.offset,
      });
      return apiUnits.map(api =>
        toUnitDTO(api, options?.currentUserId ?? userId)
      );
    } catch (error) {
      throw this.handleError(error, 'Failed to load personal units');
    }
  }

  async listGlobalUnits(options?: {
    limit?: number;
    offset?: number;
    currentUserId?: number | null;
  }): Promise<Unit[]> {
    try {
      const apiUnits = await this.repo.listGlobalUnits({
        limit: options?.limit,
        offset: options?.offset,
      });
      return apiUnits.map(api => toUnitDTO(api, options?.currentUserId));
    } catch (error) {
      throw this.handleError(error, 'Failed to load global units');
    }
  }

  async getUserUnitCollections(
    userId: number,
    options?: { includeGlobal?: boolean; limit?: number; offset?: number }
  ): Promise<UserUnitCollections> {
    if (!Number.isFinite(userId) || userId <= 0) {
      return { personalUnits: [], globalUnits: [] };
    }

    const includeGlobal = options?.includeGlobal ?? true;
    const paging = { limit: options?.limit, offset: options?.offset };

    try {
      const personalPromise = this.repo.listPersonalUnits(userId, paging);
      const globalPromise = includeGlobal
        ? this.repo.listGlobalUnits(paging)
        : Promise.resolve([]);

      const [personalApi, globalApi] = await Promise.all([
        personalPromise,
        globalPromise,
      ]);

      const personalUnits = personalApi.map(api => toUnitDTO(api, userId));
      const personalIds = new Set(personalUnits.map(unit => unit.id));
      const globalUnits = globalApi
        .filter(api => !personalIds.has(api.id))
        .map(api => toUnitDTO(api, userId));

      return { personalUnits, globalUnits };
    } catch (error) {
      throw this.handleError(error, 'Failed to load user units');
    }
  }

  async updateUnitSharing(
    unitId: string,
    request: UpdateUnitSharingRequest,
    currentUserId?: number | null
  ): Promise<Unit> {
    if (!unitId?.trim()) {
      throw this.handleError(
        new Error('Unit ID is required'),
        'Unit ID is required'
      );
    }

    try {
      const updated = await this.repo.updateUnitSharing(unitId, request);
      return toUnitDTO(updated, currentUserId);
    } catch (error) {
      throw this.handleError(error, 'Failed to update unit sharing');
    }
  }

  private handleError(error: any, defaultMessage: string): ContentError {
    if (error && typeof error === 'object' && 'code' in error) {
      return error as ContentError;
    }

    return {
      message: (error as Error)?.message || defaultMessage,
      code: 'CONTENT_SERVICE_ERROR',
      details: error,
    };
  }
}
