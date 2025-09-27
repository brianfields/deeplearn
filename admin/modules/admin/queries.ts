/**
 * Admin Module - React Query Hooks
 *
 * React Query hooks for all admin data fetching.
 * Provides caching, error handling, and loading states.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AdminService } from './service';
import type {
  FlowRunsQuery,
  LLMRequestsQuery,
  LessonsQuery,
  MetricsQuery,
  UnitDetail,
  UserDetail,
  UserListQuery,
  UserUpdatePayload,
} from './models';

const service = new AdminService();

// ---- Query Keys ----

export const adminKeys = {
  all: ['admin'] as const,
  flows: () => [...adminKeys.all, 'flows'] as const,
  flowsList: (params?: FlowRunsQuery) => [...adminKeys.flows(), 'list', params] as const,
  flowDetail: (id: string) => [...adminKeys.flows(), 'detail', id] as const,
  flowStepDetail: (flowId: string, stepId: string) => [...adminKeys.flows(), 'step', flowId, stepId] as const,
  llmRequests: () => [...adminKeys.all, 'llm-requests'] as const,
  llmRequestsList: (params?: LLMRequestsQuery) => [...adminKeys.llmRequests(), 'list', params] as const,
  llmRequestDetail: (id: string) => [...adminKeys.llmRequests(), 'detail', id] as const,
  lessons: () => [...adminKeys.all, 'lessons'] as const,
  lessonsList: (params?: LessonsQuery) => [...adminKeys.lessons(), 'list', params] as const,
  lessonDetail: (id: string) => [...adminKeys.lessons(), 'detail', id] as const,
  units: () => [...adminKeys.all, 'units'] as const,
  unitsList: () => [...adminKeys.units(), 'list'] as const,
  unitDetail: (id: string) => [...adminKeys.units(), 'detail', id] as const,
  users: () => [...adminKeys.all, 'users'] as const,
  usersList: (params?: UserListQuery) => [...adminKeys.users(), 'list', params ?? {}] as const,
  userDetail: (id: number | string) => [...adminKeys.users(), 'detail', id] as const,
  metrics: () => [...adminKeys.all, 'metrics'] as const,
  systemMetrics: (params?: MetricsQuery) => [...adminKeys.metrics(), 'system', params] as const,
  flowMetrics: (params?: MetricsQuery) => [...adminKeys.metrics(), 'flows', params] as const,
  dailyMetrics: (startDate: Date, endDate: Date) => [...adminKeys.metrics(), 'daily', startDate.toISOString(), endDate.toISOString()] as const,
  taskQueue: () => [...adminKeys.all, 'task-queue'] as const,
  queueStatus: () => [...adminKeys.taskQueue(), 'status'] as const,
  queueStats: () => [...adminKeys.taskQueue(), 'stats'] as const,
  queueTasks: (limit?: number) => [...adminKeys.taskQueue(), 'tasks', limit] as const,
  taskDetail: (taskId: string) => [...adminKeys.taskQueue(), 'task', taskId] as const,
  workers: () => [...adminKeys.taskQueue(), 'workers'] as const,
  queueHealth: () => [...adminKeys.taskQueue(), 'health'] as const,
};

// ---- Flow Hooks ----

export function useFlowRuns(params?: FlowRunsQuery) {
  return useQuery({
    queryKey: adminKeys.flowsList(params),
    queryFn: () => service.getFlowRuns(params),
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useFlowRun(id: string) {
  return useQuery({
    queryKey: adminKeys.flowDetail(id),
    queryFn: () => service.getFlowRun(id),
    enabled: !!id,
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useFlowStepDetails(flowId: string, stepId: string) {
  return useQuery({
    queryKey: adminKeys.flowStepDetail(flowId, stepId),
    queryFn: () => service.getFlowStepDetails(flowId, stepId),
    enabled: !!flowId && !!stepId,
    staleTime: 60 * 1000, // 1 minute
  });
}

// ---- LLM Request Hooks ----

export function useLLMRequests(params?: LLMRequestsQuery) {
  return useQuery({
    queryKey: adminKeys.llmRequestsList(params),
    queryFn: () => service.getLLMRequests(params),
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useLLMRequest(id: string) {
  return useQuery({
    queryKey: adminKeys.llmRequestDetail(id),
    queryFn: () => service.getLLMRequest(id),
    enabled: !!id,
    staleTime: 60 * 1000, // 1 minute
  });
}

// ---- Lesson Hooks ----

export function useLessons(params?: LessonsQuery) {
  return useQuery({
    queryKey: adminKeys.lessonsList(params),
    queryFn: () => service.getLessons(params),
    staleTime: 5 * 60 * 1000, // 5 minutes (lessons change less frequently)
  });
}

export function useLesson(id: string) {
  return useQuery({
    queryKey: adminKeys.lessonDetail(id),
    queryFn: () => service.getLesson(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ---- Analytics Hooks ----

export function useSystemMetrics(params?: MetricsQuery) {
  return useQuery({
    queryKey: adminKeys.systemMetrics(params),
    queryFn: () => service.getSystemMetrics(params),
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useFlowMetrics(params?: MetricsQuery) {
  return useQuery({
    queryKey: adminKeys.flowMetrics(params),
    queryFn: () => service.getFlowMetrics(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useDailyMetrics(startDate: Date, endDate: Date) {
  return useQuery({
    queryKey: adminKeys.dailyMetrics(startDate, endDate),
    queryFn: () => service.getDailyMetrics(startDate, endDate),
    enabled: !!startDate && !!endDate,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ---- Health Check Hook ----

export function useHealthCheck() {
  return useQuery({
    queryKey: [...adminKeys.all, 'health'],
    queryFn: () => service.healthCheck(),
    staleTime: 30 * 1000, // 30 seconds
    retry: 3,
  });
}

// ---- Units Hooks ----

export function useUnits() {
  return useQuery({
    queryKey: adminKeys.unitsList(),
    queryFn: () => service.getUnits(),
    staleTime: 60 * 1000,
  });
}

export function useUnit(unitId: string) {
  return useQuery<UnitDetail | null>({
    queryKey: adminKeys.unitDetail(unitId),
    queryFn: () => service.getUnitDetail(unitId),
    enabled: !!unitId,
    staleTime: 60 * 1000,
  });
}

// ---- User Hooks ----

export function useAdminUsers(params?: UserListQuery) {
  return useQuery({
    queryKey: adminKeys.usersList(params),
    queryFn: () => service.getUsers(params),
    staleTime: 30 * 1000,
  });
}

export function useAdminUser(userId: number | string | null) {
  return useQuery<UserDetail | null>({
    queryKey: adminKeys.userDetail(userId ?? 'unknown'),
    queryFn: () => (userId ? service.getUser(userId) : Promise.resolve(null)),
    enabled: !!userId,
    staleTime: 30 * 1000,
  });
}

export function useUpdateAdminUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, payload }: { userId: number | string; payload: UserUpdatePayload }) => {
      return service.updateUser(userId, payload);
    },
    onSuccess: (data, variables) => {
      if (data) {
        queryClient.setQueryData(adminKeys.userDetail(variables.userId), data);
      }
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
    },
  });
}

// ---- Task Queue Hooks ----

export function useQueueStatus() {
  return useQuery({
    queryKey: adminKeys.queueStatus(),
    queryFn: () => service.getQueueStatus(),
    staleTime: 5 * 1000, // 5 seconds - queue status changes frequently
    refetchInterval: 10 * 1000, // Auto-refresh every 10 seconds
  });
}

export function useQueueStats() {
  return useQuery({
    queryKey: adminKeys.queueStats(),
    queryFn: () => service.getQueueStats(),
    staleTime: 10 * 1000, // 10 seconds
    refetchInterval: 15 * 1000, // Auto-refresh every 15 seconds
  });
}

export function useQueueTasks(limit: number = 50) {
  return useQuery({
    queryKey: adminKeys.queueTasks(limit),
    queryFn: () => service.getQueueTasks(limit),
    staleTime: 5 * 1000, // 5 seconds
    refetchInterval: 10 * 1000, // Auto-refresh every 10 seconds
  });
}

export function useTaskStatus(taskId: string) {
  return useQuery({
    queryKey: adminKeys.taskDetail(taskId),
    queryFn: () => service.getTaskStatus(taskId),
    enabled: !!taskId,
    staleTime: 5 * 1000, // 5 seconds
    refetchInterval: 10 * 1000, // Auto-refresh every 10 seconds
  });
}

export function useWorkers() {
  return useQuery({
    queryKey: adminKeys.workers(),
    queryFn: () => service.getWorkers(),
    staleTime: 10 * 1000, // 10 seconds
    refetchInterval: 15 * 1000, // Auto-refresh every 15 seconds
  });
}

export function useQueueHealth() {
  return useQuery({
    queryKey: adminKeys.queueHealth(),
    queryFn: () => service.getQueueHealth(),
    staleTime: 10 * 1000, // 10 seconds
    refetchInterval: 30 * 1000, // Auto-refresh every 30 seconds
  });
}

// ---- Flow-Task Integration Hooks ----

export function useFlowTaskStatus(flowId: string) {
  return useQuery({
    queryKey: [...adminKeys.flows(), 'task-status', flowId],
    queryFn: () => service.getFlowTaskStatus(flowId),
    enabled: !!flowId,
    staleTime: 10 * 1000, // 10 seconds
    refetchInterval: 15 * 1000, // Auto-refresh every 15 seconds
  });
}
