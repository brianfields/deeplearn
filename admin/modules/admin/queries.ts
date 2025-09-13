/**
 * Admin Module - React Query Hooks
 *
 * React Query hooks for all admin data fetching.
 * Provides caching, error handling, and loading states.
 */

import { useQuery } from '@tanstack/react-query';
import { AdminService } from './service';
import type {
  FlowRunsQuery,
  LLMRequestsQuery,
  LessonsQuery,
  MetricsQuery,
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
  metrics: () => [...adminKeys.all, 'metrics'] as const,
  systemMetrics: (params?: MetricsQuery) => [...adminKeys.metrics(), 'system', params] as const,
  flowMetrics: (params?: MetricsQuery) => [...adminKeys.metrics(), 'flows', params] as const,
  dailyMetrics: (startDate: Date, endDate: Date) => [...adminKeys.metrics(), 'daily', startDate.toISOString(), endDate.toISOString()] as const,
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
