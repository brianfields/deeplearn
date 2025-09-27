import { infrastructureProvider } from '../infrastructure/public';
import type {
  ApiUnitSummary,
  ApiUnitDetail,
  UpdateUnitSharingRequest,
  ContentError,
} from './models';

const CONTENT_BASE = '/api/v1/content';

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

  async listPersonalUnits(
    userId: number,
    params?: { limit?: number; offset?: number }
  ): Promise<ApiUnitSummary[]> {
    const limit = params?.limit ?? 100;
    const offset = params?.offset ?? 0;
    const search = new URLSearchParams();
    search.append('user_id', String(userId));
    search.append('limit', String(limit));
    search.append('offset', String(offset));
    const url = `${CONTENT_BASE}/units/personal?${search.toString()}`;

    try {
      return await this.infrastructure.request<ApiUnitSummary[]>(url, {
        method: 'GET',
      });
    } catch (error) {
      throw this.handleError(error, 'Failed to load personal units');
    }
  }

  async listGlobalUnits(params?: {
    limit?: number;
    offset?: number;
  }): Promise<ApiUnitSummary[]> {
    const limit = params?.limit ?? 100;
    const offset = params?.offset ?? 0;
    const search = new URLSearchParams();
    search.append('limit', String(limit));
    search.append('offset', String(offset));
    const url = `${CONTENT_BASE}/units/global?${search.toString()}`;

    try {
      return await this.infrastructure.request<ApiUnitSummary[]>(url, {
        method: 'GET',
      });
    } catch (error) {
      throw this.handleError(error, 'Failed to load global units');
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
}
