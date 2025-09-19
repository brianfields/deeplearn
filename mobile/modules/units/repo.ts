/**
 * Units Module - Repository
 *
 * HTTP client for unit endpoints exposed via lesson_catalog routes.
 */

import { infrastructureProvider } from '../infrastructure/public';
import type { ApiUnitSummary, ApiUnitDetail } from './models';

const BASE = '/api/v1/lesson_catalog';

export class UnitsRepo {
  private infrastructure = infrastructureProvider();

  async list(params?: {
    limit?: number;
    offset?: number;
  }): Promise<ApiUnitSummary[]> {
    const limit = params?.limit ?? 100;
    const offset = params?.offset ?? 0;
    const url = `${BASE}/units?limit=${encodeURIComponent(String(limit))}&offset=${encodeURIComponent(String(offset))}`;
    return this.infrastructure.request<ApiUnitSummary[]>(url, {
      method: 'GET',
    });
  }

  async detail(unitId: string): Promise<ApiUnitDetail> {
    const url = `${BASE}/units/${encodeURIComponent(unitId)}`;
    return this.infrastructure.request<ApiUnitDetail>(url, { method: 'GET' });
  }
}
