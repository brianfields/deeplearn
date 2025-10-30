/**
 * Admin Module - React Query Hooks
 *
 * React Query hooks for all admin data fetching.
 * Provides caching, error handling, and loading states.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AdminService } from './service';
import type {
  ConversationDetail,
  ConversationListQuery,
  ConversationsListResponse,
  FlowRunsQuery,
  LearningSessionsListResponse,
  LearningSessionsQuery,
  LLMRequestsQuery,
  LessonsQuery,
  MetricsQuery,
  UnitDetail,
  ResourceDetail,
  UserDetail,
  UserListQuery,
  UserUpdatePayload,
  LLMRequestsListResponse,
} from './models';

const service = new AdminService();

// ---- Query Keys ----

export const adminKeys = {
  all: ['admin'] as const,
  flows: () => [...adminKeys.all, 'flows'] as const,
  flowsList: (params?: FlowRunsQuery) => [...adminKeys.flows(), 'list', params] as const,
  flowDetail: (id: string) => [...adminKeys.flows(), 'detail', id] as const,
  flowStepDetail: (flowId: string, stepId: string) => [...adminKeys.flows(), 'step', flowId, stepId] as const,
  conversations: () => [...adminKeys.all, 'conversations'] as const,
  conversationsList: (params?: ConversationListQuery) =>
    [...adminKeys.conversations(), 'list', params ?? {}] as const,
  conversationDetail: (id: string) => [...adminKeys.conversations(), 'detail', id] as const,
  learningSessions: () => [...adminKeys.all, 'learning-sessions'] as const,
  learningSessionsList: (params?: LearningSessionsQuery) =>
    [...adminKeys.learningSessions(), 'list', params ?? {}] as const,
  learningSessionDetail: (id: string) => [...adminKeys.learningSessions(), 'detail', id] as const,
  llmRequests: () => [...adminKeys.all, 'llm-requests'] as const,
  llmRequestsList: (params?: LLMRequestsQuery) => [...adminKeys.llmRequests(), 'list', params] as const,
  llmRequestDetail: (id: string) => [...adminKeys.llmRequests(), 'detail', id] as const,
  lessons: () => [...adminKeys.all, 'lessons'] as const,
  lessonsList: (params?: LessonsQuery) => [...adminKeys.lessons(), 'list', params] as const,
  lessonDetail: (id: string) => [...adminKeys.lessons(), 'detail', id] as const,
  units: () => [...adminKeys.all, 'units'] as const,
  unitsList: () => [...adminKeys.units(), 'list'] as const,
  unitDetail: (id: string) => [...adminKeys.units(), 'detail', id] as const,
  resources: () => [...adminKeys.all, 'resources'] as const,
  resourceDetail: (id: string) => [...adminKeys.resources(), 'detail', id] as const,
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
  workers: () => [...adminKeys.taskQueue(), 'workers'] as const,
  queueHealth: () => [...adminKeys.taskQueue(), 'health'] as const,
  tasks: () => [...adminKeys.all, 'tasks'] as const,
  taskList: (limit?: number, queueName?: string) => [...adminKeys.tasks(), 'list', limit, queueName] as const,
  taskDetail: (taskId: string) => [...adminKeys.tasks(), 'detail', taskId] as const,
  taskFlowRuns: (taskId: string) => [...adminKeys.tasks(), 'flow-runs', taskId] as const,
  unitFlowRuns: (unitId: string) => [...adminKeys.units(), 'flow-runs', unitId] as const,
};

// ---- Flow Hooks ----

export function useFlowRuns(params?: FlowRunsQuery) {
  return useQuery({
    queryKey: adminKeys.flowsList(params),
    queryFn: () => service.getFlowRuns(params),
    staleTime: 2 * 1000, // 2 seconds - keep data fresh for real-time visibility
    refetchInterval: 3 * 1000, // Poll every 3 seconds for running flows
  });
}

export function useFlowRun(id: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: adminKeys.flowDetail(id),
    queryFn: () => service.getFlowRun(id),
    enabled: !!id && (options?.enabled ?? true),
    staleTime: 2 * 1000, // 2 seconds - keep fresh for step-by-step monitoring
    refetchInterval: 3 * 1000, // Poll every 3 seconds to see steps completing
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

// ---- Conversation Hooks ----

export function useConversations(params?: ConversationListQuery) {
  return useQuery<ConversationsListResponse>({
    queryKey: adminKeys.conversationsList(params),
    queryFn: () => service.getConversations(params),
    staleTime: 30 * 1000, // manual reload preferred but keep cache warm briefly
    refetchOnWindowFocus: false,
  });
}

export function useLearningSessions(params?: LearningSessionsQuery) {
  return useQuery<LearningSessionsListResponse>({
    queryKey: adminKeys.learningSessionsList(params),
    queryFn: () => service.getLearningSessions(params),
    staleTime: 30 * 1000,
    refetchOnWindowFocus: false,
  });
}

export function useLearningSession(sessionId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: adminKeys.learningSessionDetail(sessionId),
    queryFn: () => service.getLearningSession(sessionId),
    enabled: !!sessionId && (options?.enabled ?? true),
    staleTime: 30 * 1000,
    refetchOnWindowFocus: false,
  });
}

export function useConversation(conversationId: string, options?: { enabled?: boolean }) {
  return useQuery<ConversationDetail | null>({
    queryKey: adminKeys.conversationDetail(conversationId),
    queryFn: () => service.getConversation(conversationId),
    enabled: !!conversationId && (options?.enabled ?? true),
    staleTime: 30 * 1000,
    refetchOnWindowFocus: false,
  });
}

// ---- LLM Request Hooks ----

export function useLLMRequests(params?: LLMRequestsQuery) {
  return useQuery<LLMRequestsListResponse>({
    queryKey: adminKeys.llmRequestsList(params),
    queryFn: () => service.getLLMRequests(params),
    staleTime: 2 * 1000, // 2 seconds - keep fresh for real-time visibility
    refetchInterval: 3 * 1000, // Poll every 3 seconds during active flows
  });
}

export function useLLMRequest(id: string) {
  return useQuery({
    queryKey: adminKeys.llmRequestDetail(id),
    queryFn: () => service.getLLMRequest(id),
    enabled: !!id,
    staleTime: 5 * 1000, // 5 seconds - completed requests don't change
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

export function useUnit(unitId: string, options?: { enabled?: boolean }) {
  return useQuery<UnitDetail | null>({
    queryKey: adminKeys.unitDetail(unitId),
    queryFn: () => service.getUnitDetail(unitId),
    enabled: !!unitId && (options?.enabled ?? true),
    staleTime: 60 * 1000,
  });
}

// ---- Resource Hooks ----

export function useResource(resourceId: string | null, options?: { enabled?: boolean }) {
  return useQuery<ResourceDetail | null>({
    queryKey: adminKeys.resourceDetail(resourceId ?? 'unknown'),
    queryFn: () => (resourceId ? service.getResource(resourceId) : Promise.resolve(null)),
    enabled: !!resourceId && (options?.enabled ?? true),
    staleTime: 5 * 60 * 1000,
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

// ---- Background Task Hooks ----

export function useTasks(limit: number = 50, queueName?: string) {
  return useQuery({
    queryKey: adminKeys.taskList(limit, queueName),
    queryFn: () => service.getTasks(limit, queueName),
    staleTime: 5 * 1000,
    refetchInterval: 10 * 1000,
  });
}

export function useTask(taskId: string | null) {
  return useQuery({
    queryKey: adminKeys.taskDetail(taskId ?? 'unknown'),
    queryFn: () => (taskId ? service.getTask(taskId) : Promise.resolve(null)),
    enabled: !!taskId,
    staleTime: 5 * 1000,
    refetchInterval: 10 * 1000,
  });
}

export function useTaskFlowRuns(taskId: string | null) {
  return useQuery({
    queryKey: adminKeys.taskFlowRuns(taskId ?? 'unknown'),
    queryFn: () => (taskId ? service.getTaskFlowRuns(taskId) : Promise.resolve([])),
    enabled: !!taskId,
    staleTime: 10 * 1000,
    refetchInterval: 15 * 1000,
  });
}

export function useUnitFlowRuns(unitId: string | null) {
  return useQuery({
    queryKey: adminKeys.unitFlowRuns(unitId ?? 'unknown'),
    queryFn: () => (unitId ? service.getUnitFlowRuns(unitId) : Promise.resolve([])),
    enabled: !!unitId,
    staleTime: 10 * 1000,
  });
}

export function useRetryUnit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (unitId: string) => service.retryUnit(unitId),
    onSuccess: (_data, unitId) => {
      queryClient.invalidateQueries({ queryKey: adminKeys.unitDetail(unitId) });
      queryClient.invalidateQueries({ queryKey: adminKeys.unitFlowRuns(unitId) });
    },
  });
}
