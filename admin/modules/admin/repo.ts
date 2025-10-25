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
  ApiUnitBasic,
  ApiUnitDetail,
  ApiUnitSummary,
  ApiUserDetail,
  ApiUserListResponse,
  ApiUserUpdateRequest,
  DailyMetrics,
  FlowMetrics,
  FlowRunsListResponse,
  FlowRunsQuery,
  LLMRequestsQuery,
  LessonsListResponse,
  LessonsQuery,
  MetricsQuery,
  UserListQuery,
} from './models';

const ADMIN_BASE = '/admin';
const FLOW_ENGINE_BASE = '/flow-engine';
const TASK_QUEUE_BASE = '/task-queue';
const CONTENT_BASE = '/content';
const CONTENT_CREATOR_BASE = '/content-creator';

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

      if (params?.learner_level) queryParams.append('learner_level', params.learner_level);
      if (params?.search) queryParams.append('search', params.search);
      if (params?.domain) queryParams.append('domain', params.domain);
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

  // ---- Units (via catalog and units modules) ----
  units: {
    async list(params?: { limit?: number; offset?: number }): Promise<ApiUnitSummary[]> {
      const query = new URLSearchParams();
      if (params?.limit) query.append('limit', params.limit.toString());
      if (params?.offset) query.append('offset', params.offset.toString());
      const suffix = query.toString() ? `?${query.toString()}` : '';
      const { data } = await apiClient.get<ApiUnitSummary[]>(`${CONTENT_BASE}/units${suffix}`);
      return data;
    },
    async detail(unitId: string): Promise<ApiUnitDetail> {
      const { data } = await apiClient.get<ApiUnitDetail>(`${CONTENT_BASE}/units/${unitId}`);
      return data;
    },
    async basics(): Promise<ApiUnitBasic[]> {
      const { data } = await apiClient.get<ApiUnitBasic[]>(`/units`);
      return data;
    },
    async flowRuns(unitId: string): Promise<ApiFlowRun[]> {
      const { data } = await apiClient.get<ApiFlowRun[]>(`${CONTENT_BASE}/units/${unitId}/flow-runs`);
      return data;
    },
  },

  // ---- User Management ----
  users: {
    async list(params?: UserListQuery): Promise<ApiUserListResponse> {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
      if (params?.search) queryParams.append('search', params.search);
      const suffix = queryParams.toString() ? `?${queryParams.toString()}` : '';
      const { data } = await apiClient.get<ApiUserListResponse>(`${ADMIN_BASE}/users${suffix}`);
      return data;
    },

    async detail(userId: number | string): Promise<ApiUserDetail> {
      const { data } = await apiClient.get<ApiUserDetail>(`${ADMIN_BASE}/users/${userId}`);
      return data;
    },

    async update(userId: number | string, payload: ApiUserUpdateRequest): Promise<ApiUserDetail> {
      const { data } = await apiClient.put<ApiUserDetail>(`${ADMIN_BASE}/users/${userId}`, payload);
      return data;
    },
  },

  // ---- Task Queue Endpoints ----
  taskQueue: {
    async status(queueName?: string): Promise<any> {
      const query = queueName ? `?queue_name=${encodeURIComponent(queueName)}` : '';
      const { data } = await apiClient.get(`${TASK_QUEUE_BASE}/status${query}`);
      return data;
    },

    async stats(queueName?: string): Promise<any> {
      const query = queueName ? `?queue_name=${encodeURIComponent(queueName)}` : '';
      const { data } = await apiClient.get(`${TASK_QUEUE_BASE}/stats${query}`);
      return data;
    },

    async tasks(limit: number = 50, queueName?: string): Promise<any[]> {
      const params = new URLSearchParams({ limit: limit.toString() });
      if (queueName) {
        params.append('queue_name', queueName);
      }
      const suffix = params.toString() ? `?${params.toString()}` : '';
      const { data } = await apiClient.get(`${TASK_QUEUE_BASE}/tasks${suffix}`);
      return data;
    },

    async taskById(taskId: string): Promise<any> {
      const { data } = await apiClient.get(`${TASK_QUEUE_BASE}/tasks/${taskId}`);
      return data;
    },

    async workers(): Promise<any[]> {
      const { data } = await apiClient.get(`${TASK_QUEUE_BASE}/workers`);
      return data;
    },

    async health(): Promise<{ status: string; details: Record<string, any> }> {
      const { data } = await apiClient.get(`${TASK_QUEUE_BASE}/health`);
      return data;
    },

    async flowRuns(taskId: string): Promise<ApiFlowRun[]> {
      const { data } = await apiClient.get<ApiFlowRun[]>(`${TASK_QUEUE_BASE}/tasks/${taskId}/flow-runs`);
      return data;
    },
  },

  flowEngine: {
    async list(params?: { arq_task_id?: string; unit_id?: string; limit?: number; offset?: number }): Promise<ApiFlowRun[]> {
      const query = new URLSearchParams();
      if (params?.arq_task_id) query.append('arq_task_id', params.arq_task_id);
      if (params?.unit_id) query.append('unit_id', params.unit_id);
      if (params?.limit) query.append('limit', params.limit.toString());
      if (params?.offset) query.append('offset', params.offset.toString());
      const suffix = query.toString() ? `?${query.toString()}` : '';
      const { data } = await apiClient.get<ApiFlowRun[]>(`${FLOW_ENGINE_BASE}/runs${suffix}`);
      return data;
    },

    async byId(flowRunId: string): Promise<ApiFlowRunDetails> {
      const { data } = await apiClient.get<ApiFlowRunDetails>(`${FLOW_ENGINE_BASE}/runs/${flowRunId}`);
      return data;
    },
  },

  contentCreator: {
    async retryUnit(unitId: string): Promise<void> {
      await apiClient.post(`${CONTENT_CREATOR_BASE}/units/${unitId}/retry`);
    },
  },
};
