/**
 * Admin Module - Service Layer
 *
 * Business logic and data transformation for admin dashboard.
 * Handles API→DTO mapping and provides clean interfaces for components.
 */

import { AdminRepo } from './repo';
import type {
  // API types
  ApiFlowRun,
  ApiFlowRunDetails,
  ApiFlowStepDetails,
  ApiLLMRequest,
  ApiSystemMetrics,
  ApiUnitSummary,
  ApiUserDetail,
  ApiUserListResponse,
  ApiUserSummary,
  ApiUserUpdateRequest,

  // DTO types
  DailyMetrics,
  FlowMetrics,
  FlowRunDetails,
  FlowRunSummary,
  FlowStepDetails,
  LLMRequestDetails,
  LLMRequestSummary,
  LessonDetails,
  LessonSummary,
  SystemMetrics,
  UnitDetail,
  UnitSummary,
  UserAssociationSummary,
  UserDetail,
  UserListQuery,
  UserListResponse,
  UserOwnedUnitSummary,
  UserSessionSummary,
  UserSummary,
  UserUpdatePayload,
  UserLLMRequestSummary,

  // Query types
  FlowRunsQuery,
  LLMRequestsQuery,
  LessonsQuery,
  MetricsQuery,

  // Response types
  FlowRunsListResponse,
  LLMRequestsListResponse,
  LessonsListResponse,

  // Task Queue types
  ApiTaskStatus,
  ApiWorkerHealth,
  QueueStats,
  QueueStatus,
  TaskStatus,
  WorkerHealth,
} from './models';

// ---- Data Transformation Functions ----

const parseDate = (dateString: string | null): Date | null => {
  return dateString ? new Date(dateString) : null;
};

const taskStatusToDTO = (apiTask: ApiTaskStatus): TaskStatus => ({
  task_id: apiTask.task_id,
  status: apiTask.status as 'pending' | 'running' | 'completed' | 'failed' | 'cancelled',
  submitted_at: new Date(apiTask.submitted_at),
  started_at: parseDate(apiTask.started_at),
  completed_at: parseDate(apiTask.completed_at),
  retry_count: apiTask.retry_count,
  error_message: apiTask.error_message,
  result: apiTask.result,
  queue_name: apiTask.queue_name,
  priority: apiTask.priority,
  flow_name: apiTask.flow_name,
  flow_run_id: apiTask.flow_run_id,
});

const workerHealthToDTO = (apiWorker: ApiWorkerHealth): WorkerHealth => ({
  worker_id: apiWorker.worker_id,
  status: apiWorker.status as 'healthy' | 'busy' | 'unhealthy' | 'offline',
  last_heartbeat: new Date(apiWorker.last_heartbeat),
  current_task_id: apiWorker.current_task_id,
  tasks_completed: apiWorker.tasks_completed,
  queue_name: apiWorker.queue_name,
  started_at: new Date(apiWorker.started_at),
  version: apiWorker.version,
});

const flowRunToDTO = (apiFlow: ApiFlowRun): FlowRunSummary => ({
  id: apiFlow.id,
  flow_name: apiFlow.flow_name,
  status: apiFlow.status as FlowRunSummary['status'],
  execution_mode: apiFlow.execution_mode as FlowRunSummary['execution_mode'],
  user_id: apiFlow.user_id,
  created_at: new Date(apiFlow.created_at),
  started_at: parseDate(apiFlow.started_at),
  completed_at: parseDate(apiFlow.completed_at),
  execution_time_ms: apiFlow.execution_time_ms,
  total_tokens: apiFlow.total_tokens,
  total_cost: apiFlow.total_cost,
  step_count: apiFlow.step_count,
  error_message: apiFlow.error_message,
});

const flowRunDetailsToDTO = (apiFlow: ApiFlowRunDetails): FlowRunDetails => ({
  id: apiFlow.id,
  flow_name: apiFlow.flow_name,
  status: apiFlow.status as FlowRunDetails['status'],
  execution_mode: apiFlow.execution_mode as FlowRunDetails['execution_mode'],
  user_id: apiFlow.user_id,
  current_step: apiFlow.current_step,
  step_progress: apiFlow.step_progress,
  total_steps: apiFlow.total_steps,
  progress_percentage: apiFlow.progress_percentage,
  created_at: new Date(apiFlow.created_at),
  started_at: parseDate(apiFlow.started_at),
  completed_at: parseDate(apiFlow.completed_at),
  last_heartbeat: parseDate(apiFlow.last_heartbeat),
  execution_time_ms: apiFlow.execution_time_ms,
  total_tokens: apiFlow.total_tokens,
  total_cost: apiFlow.total_cost,
  inputs: apiFlow.inputs,
  outputs: apiFlow.outputs,
  flow_metadata: apiFlow.flow_metadata,
  error_message: apiFlow.error_message,
  steps: apiFlow.steps.map(stepToDTO),
});

const stepToDTO = (apiStep: ApiFlowStepDetails): FlowStepDetails => ({
  id: apiStep.id,
  flow_run_id: apiStep.flow_run_id,
  llm_request_id: apiStep.llm_request_id,
  step_name: apiStep.step_name,
  step_order: apiStep.step_order,
  status: apiStep.status as FlowStepDetails['status'],
  inputs: apiStep.inputs,
  outputs: apiStep.outputs,
  tokens_used: apiStep.tokens_used,
  cost_estimate: apiStep.cost_estimate,
  execution_time_ms: apiStep.execution_time_ms,
  error_message: apiStep.error_message,
  step_metadata: apiStep.step_metadata,
  created_at: new Date(apiStep.created_at),
  completed_at: parseDate(apiStep.completed_at),
});

const llmRequestToDTO = (apiRequest: ApiLLMRequest): LLMRequestSummary => ({
  id: apiRequest.id,
  user_id: apiRequest.user_id,
  api_variant: apiRequest.api_variant,
  provider: apiRequest.provider,
  model: apiRequest.model,
  status: apiRequest.status as LLMRequestSummary['status'],
  tokens_used: apiRequest.tokens_used,
  input_tokens: apiRequest.input_tokens,
  output_tokens: apiRequest.output_tokens,
  cost_estimate: apiRequest.cost_estimate,
  execution_time_ms: apiRequest.execution_time_ms,
  cached: apiRequest.cached,
  created_at: new Date(apiRequest.created_at),
  error_message: apiRequest.error_message,
});

const systemMetricsToDTO = (apiMetrics: ApiSystemMetrics): SystemMetrics => ({
  total_flows: apiMetrics.total_flows,
  active_flows: apiMetrics.active_flows,
  completed_flows: apiMetrics.completed_flows,
  failed_flows: apiMetrics.failed_flows,
  total_steps: apiMetrics.total_steps,
  total_llm_requests: apiMetrics.total_llm_requests,
  total_tokens_used: apiMetrics.total_tokens_used,
  total_cost: apiMetrics.total_cost,
  total_lessons: apiMetrics.total_lessons,
  active_sessions: apiMetrics.active_sessions,
});

const userAssociationsToDTO = (api: ApiUserSummary['associations']): UserAssociationSummary => ({
  owned_unit_count: api.owned_unit_count,
  owned_global_unit_count: api.owned_global_unit_count,
  learning_session_count: api.learning_session_count,
  llm_request_count: api.llm_request_count,
});

const userOwnedUnitToDTO = (unit: ApiUserDetail['owned_units'][number]): UserOwnedUnitSummary => ({
  id: unit.id,
  title: unit.title,
  is_global: unit.is_global,
  updated_at: new Date(unit.updated_at),
});

const userSessionToDTO = (session: ApiUserDetail['recent_sessions'][number]): UserSessionSummary => ({
  id: session.id,
  lesson_id: session.lesson_id,
  status: session.status,
  started_at: new Date(session.started_at),
  completed_at: session.completed_at ? new Date(session.completed_at) : null,
  progress_percentage: session.progress_percentage,
});

const userRequestToDTO = (request: ApiUserDetail['recent_llm_requests'][number]): UserLLMRequestSummary => ({
  id: request.id,
  model: request.model,
  status: request.status,
  created_at: new Date(request.created_at),
  tokens_used: request.tokens_used,
});

const userSummaryToDTO = (user: ApiUserSummary): UserSummary => ({
  id: user.id,
  email: user.email,
  name: user.name,
  role: user.role,
  is_active: user.is_active,
  created_at: new Date(user.created_at),
  updated_at: new Date(user.updated_at),
  associations: userAssociationsToDTO(user.associations),
});

const userDetailToDTO = (user: ApiUserDetail): UserDetail => ({
  ...userSummaryToDTO(user),
  owned_units: user.owned_units.map(userOwnedUnitToDTO),
  recent_sessions: user.recent_sessions.map(userSessionToDTO),
  recent_llm_requests: user.recent_llm_requests.map(userRequestToDTO),
});

// ---- Service Implementation ----

export class AdminService {
  // ---- User Management ----

  async getUsers(params?: UserListQuery): Promise<UserListResponse> {
    try {
      const response: ApiUserListResponse = await AdminRepo.users.list(params);
      return {
        users: response.users.map(userSummaryToDTO),
        total_count: response.total_count,
        page: response.page,
        page_size: response.page_size,
        has_next: response.has_next,
      };
    } catch (error) {
      console.error('Failed to fetch users:', error);
      const page = params?.page ?? 1;
      const pageSize = params?.page_size ?? 50;
      return {
        users: [],
        total_count: 0,
        page,
        page_size: pageSize,
        has_next: false,
      };
    }
  }

  async getUser(userId: number | string): Promise<UserDetail | null> {
    try {
      const detail = await AdminRepo.users.detail(userId);
      return userDetailToDTO(detail);
    } catch (error) {
      console.error('Failed to fetch user detail:', error);
      return null;
    }
  }

  async updateUser(userId: number | string, payload: UserUpdatePayload): Promise<UserDetail | null> {
    try {
      const updateRequest: ApiUserUpdateRequest = {};
      if (payload.name !== undefined) updateRequest.name = payload.name;
      if (payload.role !== undefined) updateRequest.role = payload.role;
      if (payload.is_active !== undefined) updateRequest.is_active = payload.is_active;

      const updated = await AdminRepo.users.update(userId, updateRequest);
      return userDetailToDTO(updated);
    } catch (error) {
      console.error('Failed to update user:', error);
      return null;
    }
  }

  // ---- Flow Management ----

  async getFlowRuns(params?: FlowRunsQuery): Promise<FlowRunsListResponse> {
    const response = await AdminRepo.flows.list(params);

    return {
      flows: response.flows.map((flow: ApiFlowRun) => flowRunToDTO(flow)),
      total_count: response.total_count,
      page: response.page,
      page_size: response.page_size,
      has_next: response.has_next,
    };
  }

  async getFlowRun(id: string): Promise<FlowRunDetails | null> {
    try {
      const apiFlow = await AdminRepo.flows.byId(id);
      return flowRunDetailsToDTO(apiFlow);
    } catch (error) {
      console.error('Failed to fetch flow run:', error);
      return null;
    }
  }

  async getFlowStepDetails(flowId: string, stepId: string): Promise<FlowStepDetails | null> {
    try {
      const apiStep = await AdminRepo.flows.getStepDetails(flowId, stepId);
      return stepToDTO(apiStep);
    } catch (error) {
      console.error('Failed to fetch flow step:', error);
      return null;
    }
  }

  // ---- LLM Request Management ----

  async getLLMRequests(params?: LLMRequestsQuery): Promise<LLMRequestSummary[]> {
    try {
      const apiRequests = await AdminRepo.llmRequests.list(params);
      return apiRequests.map(llmRequestToDTO);
    } catch (error) {
      console.error('Failed to fetch LLM requests:', error);
      return [];
    }
  }

  async getLLMRequest(id: string): Promise<LLMRequestDetails | null> {
    try {
      const apiRequest = await AdminRepo.llmRequests.byId(id);

      // Transform the detailed LLM request
      return {
        id: apiRequest.id,
        user_id: apiRequest.user_id,
        api_variant: apiRequest.api_variant,
        provider: apiRequest.provider,
        model: apiRequest.model,
        provider_response_id: apiRequest.provider_response_id,
        system_fingerprint: apiRequest.system_fingerprint,
        temperature: apiRequest.temperature,
        max_output_tokens: apiRequest.max_output_tokens,
        messages: apiRequest.messages || [],
        additional_params: apiRequest.additional_params,
        request_payload: apiRequest.request_payload,
        response_content: apiRequest.response_content,
        response_raw: apiRequest.response_raw,
        response_output: apiRequest.response_output,
        tokens_used: apiRequest.tokens_used,
        input_tokens: apiRequest.input_tokens,
        output_tokens: apiRequest.output_tokens,
        cost_estimate: apiRequest.cost_estimate,
        response_created_at: parseDate(apiRequest.response_created_at),
        status: apiRequest.status as LLMRequestDetails['status'],
        execution_time_ms: apiRequest.execution_time_ms,
        error_message: apiRequest.error_message,
        error_type: apiRequest.error_type,
        retry_attempt: apiRequest.retry_attempt,
        cached: apiRequest.cached,
        created_at: new Date(apiRequest.created_at),
      };
    } catch (error) {
      console.error('Failed to fetch LLM request:', error);
      return null;
    }
  }

  async getLLMRequestsList(params?: { page?: number; page_size?: number }): Promise<LLMRequestsListResponse> {
    try {
      const response = await AdminRepo.llmRequests.list(params);

      // Transform LLM request summaries
      const requests: LLMRequestSummary[] = response.requests.map((request: any) => ({
        id: request.id,
        user_id: request.user_id,
        api_variant: request.api_variant,
        provider: request.provider,
        model: request.model,
        status: request.status as LLMRequestSummary['status'],
        tokens_used: request.tokens_used,
        input_tokens: request.input_tokens,
        output_tokens: request.output_tokens,
        cost_estimate: request.cost_estimate,
        execution_time_ms: request.execution_time_ms,
        cached: request.cached,
        created_at: new Date(request.created_at),
        error_message: request.error_message,
      }));

      return {
        requests,
        total_count: response.total_count,
        page: response.page,
        page_size: response.page_size,
        has_next: response.has_next,
      };
    } catch (error) {
      console.error('Failed to fetch LLM requests:', error);
      return {
        requests: [],
        total_count: 0,
        page: 1,
        page_size: 50,
        has_next: false,
      };
    }
  }

  // ---- Lesson Management ----

  async getLessons(params?: LessonsQuery): Promise<LessonsListResponse> {
    try {
      const response = await AdminRepo.lessons.list(params);

      // Transform lesson summaries
      const lessons: LessonSummary[] = response.lessons.map((lesson: any) => ({
        id: lesson.id,
        title: lesson.title,
        learner_level: lesson.learner_level,
        package_version: lesson.package_version,
        created_at: new Date(lesson.created_at),
        updated_at: new Date(lesson.updated_at),
      }));

      return {
        lessons,
        total_count: response.total_count,
        page: response.page,
        page_size: response.page_size,
        has_next: response.has_next,
      };
    } catch (error) {
      console.error('Failed to fetch lessons:', error);
      return {
        lessons: [],
        total_count: 0,
        page: 1,
        page_size: 50,
        has_next: false,
      };
    }
  }

  async getLesson(id: string): Promise<LessonDetails | null> {
    try {
      const apiLesson = await AdminRepo.lessons.byId(id);

      return {
        id: apiLesson.id,
        title: apiLesson.title,
        learner_level: apiLesson.learner_level,
        source_material: apiLesson.source_material,
        package: apiLesson.package, // Already structured as LessonPackage
        package_version: apiLesson.package_version,
        flow_run_id: apiLesson.flow_run_id || null,
        created_at: new Date(apiLesson.created_at),
        updated_at: new Date(apiLesson.updated_at),
      };
    } catch (error) {
      console.error('Failed to fetch lesson:', error);
      return null;
    }
  }

  // ---- Analytics and Metrics ----

  async getSystemMetrics(params?: MetricsQuery): Promise<SystemMetrics> {
    try {
      const apiMetrics = await AdminRepo.metrics.getSystemMetrics(params);
      return systemMetricsToDTO(apiMetrics);
    } catch (error) {
      console.error('Failed to fetch system metrics:', error);
      // Return default metrics on error
      return {
        total_flows: 0,
        active_flows: 0,
        completed_flows: 0,
        failed_flows: 0,
        total_steps: 0,
        total_llm_requests: 0,
        total_tokens_used: 0,
        total_cost: 0,
        total_lessons: 0,
        active_sessions: 0,
      };
    }
  }

  async getFlowMetrics(params?: MetricsQuery): Promise<FlowMetrics[]> {
    try {
      const metrics = await AdminRepo.metrics.getFlowMetrics(params);

      // Transform flow metrics (they should already be in the right format from backend)
      return metrics.map((metric: any) => ({
        flow_name: metric.flow_name,
        total_runs: metric.total_runs,
        success_rate: metric.success_rate,
        avg_execution_time_ms: metric.avg_execution_time_ms,
        avg_tokens: metric.avg_tokens,
        avg_cost: metric.avg_cost,
        last_run: metric.last_run ? new Date(metric.last_run) : null,
      }));
    } catch (error) {
      console.error('Failed to fetch flow metrics:', error);
      return [];
    }
  }

  async getDailyMetrics(startDate: Date, endDate: Date): Promise<DailyMetrics[]> {
    try {
      const metrics = await AdminRepo.metrics.getDailyMetrics(startDate, endDate);

      // Transform daily metrics
      return metrics.map((metric: any) => ({
        date: metric.date,
        flow_runs: metric.flow_runs,
        llm_requests: metric.llm_requests,
        tokens_used: metric.tokens_used,
        cost: metric.cost,
        unique_users: metric.unique_users,
      }));
    } catch (error) {
      console.error('Failed to fetch daily metrics:', error);
      return [];
    }
  }

  // ---- Health Check ----

  async healthCheck(): Promise<{ status: string; service: string }> {
    try {
      return await AdminRepo.healthCheck();
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'unhealthy', service: 'admin' };
    }
  }

  // ---- Units ----

  async getUnits(): Promise<UnitSummary[]> {
    const arr = await AdminRepo.units.list();
    return arr.map((u) => ({
      id: u.id,
      title: u.title,
      description: u.description,
      learner_level: u.learner_level,
      lesson_count: u.lesson_count ?? (u.lesson_order ? u.lesson_order.length : 0),
      target_lesson_count: u.target_lesson_count ?? null,
      generated_from_topic: Boolean(u.generated_from_topic),
      flow_type: (u.flow_type as UnitSummary['flow_type']) ?? 'standard',
      user_id: u.user_id ?? null,
      is_global: Boolean(u.is_global),
      created_at: u.created_at ? new Date(u.created_at) : null,
      updated_at: u.updated_at ? new Date(u.updated_at) : null,
    } satisfies UnitSummary));
  }

  async getUnitDetail(unitId: string): Promise<UnitDetail | null> {
    try {
      const d = await AdminRepo.units.detail(unitId);
      return {
        id: d.id,
        title: d.title,
        description: d.description,
        learner_level: d.learner_level,
        lesson_order: d.lesson_order,
        lessons: d.lessons.map((l) => ({ id: l.id, title: l.title, learner_level: l.learner_level, exercise_count: l.exercise_count })),
        learning_objectives: d.learning_objectives ?? null,
        target_lesson_count: d.target_lesson_count ?? null,
        source_material: d.source_material ?? null,
        generated_from_topic: Boolean(d.generated_from_topic),
        flow_type: (d.flow_type as UnitDetail['flow_type']) ?? 'standard',
      };
    } catch {
      return null;
    }
  }

  async getLessonToUnitMap(): Promise<Record<string, { unit_id: string; unit_title: string }>> {
    try {
      const basics = await AdminRepo.units.basics();
      const map: Record<string, { unit_id: string; unit_title: string }> = {};
      for (const u of basics) {
        for (const lessonId of u.lesson_order || []) {
          if (!map[lessonId]) {
            map[lessonId] = { unit_id: u.id, unit_title: u.title };
          }
        }
      }
      return map;
    } catch {
      return {};
    }
  }

  // ---- Task Queue Methods ----

  async getQueueStatus(): Promise<QueueStatus[]> {
    const data = await AdminRepo.taskQueue.status();
    return data.map((queue: any) => ({
      queue_name: queue.queue_name,
      status: queue.status as 'healthy' | 'degraded' | 'down',
      pending_count: queue.pending_count,
      running_count: queue.running_count,
      worker_count: queue.worker_count,
      oldest_pending_minutes: queue.oldest_pending_minutes,
    }));
  }

  async getQueueStats(): Promise<QueueStats[]> {
    const data = await AdminRepo.taskQueue.stats();
    return data.map((stats: any) => ({
      queue_name: stats.queue_name,
      pending_count: stats.pending_count,
      running_count: stats.running_count,
      completed_count: stats.completed_count,
      failed_count: stats.failed_count,
      total_processed: stats.total_processed,
      workers_count: stats.workers_count,
      workers_busy: stats.workers_busy,
      oldest_pending_task: stats.oldest_pending_task ? new Date(stats.oldest_pending_task) : null,
      avg_processing_time_ms: stats.avg_processing_time_ms,
    }));
  }

  async getQueueTasks(limit: number = 50): Promise<TaskStatus[]> {
    const data = await AdminRepo.taskQueue.tasks(limit);
    return data.map(taskStatusToDTO);
  }

  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    const data = await AdminRepo.taskQueue.taskById(taskId);
    return taskStatusToDTO(data);
  }

  async getWorkers(): Promise<WorkerHealth[]> {
    const data = await AdminRepo.taskQueue.workers();
    return data.map(workerHealthToDTO);
  }

  async getQueueHealth(): Promise<{ status: string; details: Record<string, any> }> {
    return await AdminRepo.taskQueue.health();
  }

  // ---- Flow-Task Integration Methods ----

  async getFlowTaskStatus(flowId: string): Promise<TaskStatus | null> {
    try {
      // This would query tasks by flow_run_id
      const tasks = await AdminRepo.taskQueue.tasks(100);
      const flowTask = tasks.find((task: any) => task.flow_run_id === flowId);
      return flowTask ? taskStatusToDTO(flowTask) : null;
    } catch (error) {
      console.warn('Failed to get flow task status:', error);
      return null;
    }
  }
}
