import { infrastructureProvider } from '../infrastructure/public';
import type {
  ApiUnitSummary,
  ApiUnitDetail,
  UpdateUnitSharingRequest,
  ContentError,
  ApiUnitLearningObjective,
  AddToMyUnitsRequest,
  RemoveFromMyUnitsRequest,
} from './models';

const CONTENT_BASE = '/api/v1/content';

export interface ApiUnitRead extends ApiUnitSummary {
  lesson_order: string[];
  learning_objectives?: ApiUnitLearningObjective[] | null;
  source_material?: string | null;
  flow_type?: string;
  podcast_audio_url?: string | null;
  podcast_transcript?: string | null;
  schema_version?: number;
}

export interface ApiLessonRead {
  id: string;
  title: string;
  learner_level: string;
  unit_id?: string | null;
  package: unknown;
  package_version: number;
  created_at: string;
  updated_at: string;
  schema_version?: number;
}

export interface ApiUnitSyncAsset {
  id: string;
  unit_id: string;
  type: 'audio' | 'image';
  object_id?: string | null;
  remote_url?: string | null;
  presigned_url?: string | null;
  updated_at?: string | null;
  schema_version?: number;
}

export interface ApiUnitSyncEntry {
  unit: ApiUnitRead;
  lessons: ApiLessonRead[];
  assets: ApiUnitSyncAsset[];
}

export interface ApiUnitSyncResponse {
  units: ApiUnitSyncEntry[];
  deleted_unit_ids: string[];
  deleted_lesson_ids: string[];
  cursor: string;
}

export interface ApiMyUnitMutationResponse {
  unit: ApiUnitRead;
  is_in_my_units: boolean;
}

export class ContentRepo {
  private infrastructure = infrastructureProvider();

  async listUnits(params?: {
    limit?: number;
    offset?: number;
  }): Promise<ApiUnitSummary[]> {
    const limit = params?.limit ?? 100;
    const offset = params?.offset ?? 0;
    const url = `${CONTENT_BASE}/units?limit=${encodeURIComponent(String(limit))}&offset=${encodeURIComponent(String(offset))}`;

    try {
      return await this.infrastructure.request<ApiUnitSummary[]>(url, {
        method: 'GET',
      });
    } catch (error) {
      throw this.handleError(error, 'Failed to list units');
    }
  }

  async getUnitDetail(unitId: string): Promise<ApiUnitDetail> {
    const url = `${CONTENT_BASE}/units/${encodeURIComponent(unitId)}`;
    try {
      return await this.infrastructure.request<ApiUnitDetail>(url, {
        method: 'GET',
      });
    } catch (error) {
      throw this.handleError(error, `Failed to get unit ${unitId}`);
    }
  }

  async updateUnitSharing(
    unitId: string,
    request: UpdateUnitSharingRequest
  ): Promise<ApiUnitSummary> {
    const url = `${CONTENT_BASE}/units/${encodeURIComponent(unitId)}/sharing`;

    try {
      return await this.infrastructure.request<ApiUnitSummary>(url, {
        method: 'PATCH',
        body: JSON.stringify({
          is_global: request.isGlobal,
          acting_user_id: request.actingUserId,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      throw this.handleError(error, 'Failed to update unit sharing');
    }
  }

  async addUnitToMyUnits(
    request: AddToMyUnitsRequest
  ): Promise<ApiMyUnitMutationResponse> {
    const url = `${CONTENT_BASE}/units/my-units/add`;

    try {
      return await this.infrastructure.request<ApiMyUnitMutationResponse>(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: request.userId,
          unit_id: request.unitId,
        }),
      });
    } catch (error) {
      throw this.handleError(error, 'Failed to add unit to My Units');
    }
  }

  async removeUnitFromMyUnits(
    request: RemoveFromMyUnitsRequest
  ): Promise<ApiMyUnitMutationResponse> {
    const url = `${CONTENT_BASE}/units/my-units/remove`;

    try {
      return await this.infrastructure.request<ApiMyUnitMutationResponse>(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: request.userId,
          unit_id: request.unitId,
        }),
      });
    } catch (error) {
      throw this.handleError(error, 'Failed to remove unit from My Units');
    }
  }

  async listPersonalUnits(params: {
    userId: number;
    limit?: number;
    offset?: number;
  }): Promise<ApiUnitSummary[]> {
    const limit = params.limit ?? 100;
    const offset = params.offset ?? 0;
    const url = `${CONTENT_BASE}/units/personal?user_id=${encodeURIComponent(String(params.userId))}&limit=${encodeURIComponent(String(limit))}&offset=${encodeURIComponent(String(offset))}`;

    try {
      return await this.infrastructure.request<ApiUnitSummary[]>(url, {
        method: 'GET',
      });
    } catch (error) {
      throw this.handleError(error, 'Failed to list personal units');
    }
  }

  private handleError(error: any, defaultMessage: string): ContentError {
    console.error('[ContentRepo]', defaultMessage, error);

    if (error && typeof error === 'object') {
      return {
        message: error.message || defaultMessage,
        code: error.code || 'CONTENT_ERROR',
        statusCode: error.status || error.statusCode,
        details: error.details || error,
      };
    }

    return {
      message: defaultMessage,
      code: 'CONTENT_ERROR',
      details: error,
    };
  }

  async syncUnits(params: {
    userId: number;
    since?: string | null;
    limit?: number;
    includeDeleted?: boolean;
    payload: 'minimal' | 'full';
  }): Promise<ApiUnitSyncResponse> {
    const search = new URLSearchParams();
    search.append('user_id', String(params.userId));
    if (params.since) {
      search.append('since', params.since);
    }
    if (typeof params.limit === 'number') {
      search.append('limit', String(params.limit));
    }
    if (params.includeDeleted) {
      search.append('include_deleted', 'true');
    }
    search.append('payload', params.payload);

    const url = `${CONTENT_BASE}/units/sync?${search.toString()}`;

    try {
      return await this.infrastructure.request<ApiUnitSyncResponse>(url, {
        method: 'GET',
      });
    } catch (error) {
      throw this.handleError(error, 'Failed to sync units');
    }
  }
}
