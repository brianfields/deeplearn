/**
 * Admin Module - Repository Layer
 *
 * HTTP client for all admin endpoints.
 * Handles API communication and returns raw API responses.
 */

import { apiClient } from '@/lib/api-client';
import type {
  ApiFlowRun,
  ApiFlowRunDetails,
  ApiFlowStepDetails,
  ApiLLMRequest,
  ApiSystemMetrics,
  FlowRunsQuery,
  LLMRequestsQuery,
  LessonsQuery,
  MetricsQuery,
  FlowRunsListResponse,
  LessonsListResponse,
  FlowMetrics,
  DailyMetrics,
} from './models';

const ADMIN_BASE = '/admin';

export const AdminRepo = {
  // ---- Flow Endpoints ----
  flows: {
    async list(params?: FlowRunsQuery): Promise<{ flows: ApiFlowRun[]; total_count: number; page: number; page_size: number; has_next: boolean }> {
      const queryParams = new URLSearchParams();

      if (params?.status) queryParams.append('status', params.status);
      if (params?.flow_name) queryParams.append('flow_name', params.flow_name);
      if (params?.user_id) queryParams.append('user_id', params.user_id);
      if (params?.start_date) queryParams.append('start_date', params.start_date.toISOString());
      if (params?.end_date) queryParams.append('end_date', params.end_date.toISOString());
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

      const url = `${ADMIN_BASE}/flows${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const { data } = await apiClient.get(url);
      return data;
    },

    async byId(id: string): Promise<ApiFlowRunDetails> {
      const { data } = await apiClient.get<ApiFlowRunDetails>(`${ADMIN_BASE}/flows/${id}`);
      return data;
    },

    async getStepDetails(flowId: string, stepId: string): Promise<ApiFlowStepDetails> {
      const { data } = await apiClient.get<ApiFlowStepDetails>(
        `${ADMIN_BASE}/flows/${flowId}/steps/${stepId}`
      );
      return data;
    },
  },

  // ---- LLM Request Endpoints ----
  llmRequests: {
    async list(params?: { page?: number; page_size?: number }): Promise<any> {
      const queryParams = new URLSearchParams();

      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

      const url = `${ADMIN_BASE}/llm-requests${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const { data } = await apiClient.get(url);
      return data;
    },

    async byId(id: string): Promise<any> {
      const { data } = await apiClient.get(`${ADMIN_BASE}/llm-requests/${id}`);
      return data;
    },
  },

  // ---- Lesson Endpoints ----
  lessons: {
    async list(params?: LessonsQuery): Promise<LessonsListResponse> {
      const queryParams = new URLSearchParams();

      if (params?.user_level) queryParams.append('user_level', params.user_level);
      if (params?.domain) queryParams.append('domain', params.domain);
      if (params?.search) queryParams.append('search', params.search);
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

      const url = `${ADMIN_BASE}/lessons${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const { data } = await apiClient.get<LessonsListResponse>(url);
      return data;
    },

    async byId(id: string): Promise<any> {
      const { data } = await apiClient.get(`${ADMIN_BASE}/lessons/${id}`);
      return data;
    },
  },

  // ---- Analytics Endpoints ----
  metrics: {
    async getSystemMetrics(params?: MetricsQuery): Promise<ApiSystemMetrics> {
      const queryParams = new URLSearchParams();

      if (params?.start_date) queryParams.append('start_date', params.start_date.toISOString());
      if (params?.end_date) queryParams.append('end_date', params.end_date.toISOString());

      const url = `${ADMIN_BASE}/metrics/system${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const { data } = await apiClient.get<ApiSystemMetrics>(url);
      return data;
    },

    async getFlowMetrics(params?: MetricsQuery): Promise<FlowMetrics[]> {
      const queryParams = new URLSearchParams();

      if (params?.start_date) queryParams.append('start_date', params.start_date.toISOString());
      if (params?.end_date) queryParams.append('end_date', params.end_date.toISOString());

      const url = `${ADMIN_BASE}/metrics/flows${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const { data } = await apiClient.get<FlowMetrics[]>(url);
      return data;
    },

    async getDailyMetrics(startDate: Date, endDate: Date): Promise<DailyMetrics[]> {
      const queryParams = new URLSearchParams({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      });

      const { data } = await apiClient.get<DailyMetrics[]>(
        `${ADMIN_BASE}/metrics/daily?${queryParams.toString()}`
      );
      return data;
    },
  },

  // ---- Health Check ----
  async healthCheck(): Promise<{ status: string; service: string }> {
    const { data } = await apiClient.get(`${ADMIN_BASE}/health`);
    return data;
  },
};
