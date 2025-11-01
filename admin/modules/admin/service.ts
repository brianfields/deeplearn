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
  ApiConversationDetail,
  ApiConversationMessage,
  ApiConversationSummary,
  ApiConversationsListResponse,
  ApiLearningSession,
  ApiLearningSessionsListResponse,
  ApiLLMRequest,
  ApiSystemMetrics,
  ApiResourceSummary,
  ApiResourceDetail,
  ApiUserDetail,
  ApiUserOwnedUnitSummary,
  ApiUserListResponse,
  ApiUserSummary,
  ApiUserUpdateRequest,
  ApiUserConversationSummary,

  // DTO types
  ConversationDetail,
  ConversationMessage,
  ConversationSummary,
  ConversationsListResponse,
  DailyMetrics,
  FlowMetrics,
  FlowRunDetails,
  FlowRunSummary,
  FlowStepDetails,
  LearningSessionSummary,
  LLMRequestDetails,
  LLMRequestSummary,
  LessonDetails,
  LessonSummary,
  LessonPackage,
  LessonExercise,
  Objective,
  GlossaryTerm,
  ResourceSummary,
  ResourceDetail,
  ResourceUsageSummary,
  ResourceWithUsage,
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
  UserConversationSummary,

  // Query types
  ConversationListQuery,
  FlowRunsQuery,
  LearningSessionsQuery,
  LLMRequestsQuery,
  LessonsQuery,
  MetricsQuery,

  // Response types
  FlowRunsListResponse,
  LearningSessionsListResponse,
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
  submitted_at: new Date(apiTask.submitted_at ?? apiTask.created_at ?? new Date().toISOString()),
  created_at: new Date(apiTask.created_at ?? apiTask.submitted_at ?? new Date().toISOString()),
  started_at: parseDate(apiTask.started_at),
  completed_at: parseDate(apiTask.completed_at),
  retry_count: apiTask.retry_count ?? 0,
  error_message: apiTask.error_message ?? null,
  result: apiTask.result ?? null,
  queue_name: apiTask.queue_name,
  priority: apiTask.priority ?? 0,
  flow_name: apiTask.flow_name ?? null,
  task_type: apiTask.task_type ?? null,
  progress_percentage: apiTask.progress_percentage ?? null,
  current_step: apiTask.current_step ?? null,
  worker_id: apiTask.worker_id ?? null,
  user_id: apiTask.user_id ?? null,
  flow_run_id: apiTask.flow_run_id ?? null,
  unit_id: apiTask.unit_id ?? null,
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
  arq_task_id: apiFlow.arq_task_id ?? null,
  unit_id: (apiFlow as Record<string, any>).unit_id ?? null,
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
  arq_task_id: apiFlow.arq_task_id ?? null,
  unit_id: (apiFlow as Record<string, any>).unit_id ?? null,
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

const resourceSummaryToDTO = (apiResource: ApiResourceSummary): ResourceSummary => ({
  id: apiResource.id,
  resource_type: apiResource.resource_type,
  filename: apiResource.filename ?? null,
  source_url: apiResource.source_url ?? null,
  file_size: apiResource.file_size ?? null,
  created_at: new Date(apiResource.created_at),
  preview_text: apiResource.preview_text,
});

const resourceDetailToDTO = (apiResource: ApiResourceDetail): ResourceDetail => ({
  id: apiResource.id,
  user_id: apiResource.user_id,
  resource_type: apiResource.resource_type,
  filename: apiResource.filename ?? null,
  source_url: apiResource.source_url ?? null,
  extracted_text: apiResource.extracted_text,
  extraction_metadata: apiResource.extraction_metadata ?? {},
  file_size: apiResource.file_size ?? null,
  created_at: new Date(apiResource.created_at),
  updated_at: new Date(apiResource.updated_at),
});

const normalizeDifficulty = (value: unknown): 'Easy' | 'Medium' | 'Hard' | null => {
  if (typeof value !== 'string') {
    return null;
  }

  const normalized = value.trim().toLowerCase();
  if (normalized === 'easy') {
    return 'Easy';
  }
  if (normalized === 'medium') {
    return 'Medium';
  }
  if (normalized === 'hard') {
    return 'Hard';
  }
  return null;
};

const normalizeStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0);
};

const lessonExerciseToDTO = (exercise: any): LessonExercise => {
  if (!exercise || typeof exercise !== 'object') {
    return {
      id: '',
      exercise_type: 'mcq',
      lo_id: '',
      cognitive_level: null,
      estimated_difficulty: null,
      misconceptions_used: [],
      stem: '',
      options: [],
      answer_key: { label: '', option_id: null, rationale_right: null },
    };
  }

  const rawType = typeof exercise.exercise_type === 'string' ? exercise.exercise_type : 'mcq';
  const exerciseType = rawType === 'short_answer' ? 'short_answer' : 'mcq';
  const base = {
    id: typeof exercise.id === 'string' ? exercise.id : '',
    exercise_type: exerciseType,
    lo_id: typeof exercise.lo_id === 'string' ? exercise.lo_id : '',
    cognitive_level: typeof exercise.cognitive_level === 'string' ? exercise.cognitive_level : null,
    estimated_difficulty: normalizeDifficulty(exercise.estimated_difficulty),
    misconceptions_used: normalizeStringArray(exercise.misconceptions_used),
  };

  if (exerciseType === 'short_answer') {
    const acceptableAnswers = normalizeStringArray(exercise.acceptable_answers);
    const wrongAnswers = Array.isArray(exercise.wrong_answers)
      ? exercise.wrong_answers.map((wrong: any) => ({
          answer: typeof wrong?.answer === 'string' ? wrong.answer : '',
          explanation: typeof wrong?.explanation === 'string' ? wrong.explanation : '',
          misconception_ids: normalizeStringArray(wrong?.misconception_ids),
        }))
      : [];

    return {
      ...base,
      exercise_type: 'short_answer',
      stem: typeof exercise.stem === 'string' ? exercise.stem : '',
      canonical_answer: typeof exercise.canonical_answer === 'string' ? exercise.canonical_answer : '',
      acceptable_answers: acceptableAnswers,
      wrong_answers: wrongAnswers,
      explanation_correct: typeof exercise.explanation_correct === 'string' ? exercise.explanation_correct : '',
    };
  }

  const options = Array.isArray(exercise.options)
    ? exercise.options.map((option: any) => ({
        id: typeof option?.id === 'string' ? option.id : '',
        label: typeof option?.label === 'string' ? option.label : '',
        text: typeof option?.text === 'string' ? option.text : '',
        rationale: typeof option?.rationale === 'string' ? option.rationale : null,
        rationale_wrong: typeof option?.rationale_wrong === 'string' ? option.rationale_wrong : null,
      }))
    : [];

  const answerKey = exercise?.answer_key ?? {};

  return {
    ...base,
    exercise_type: 'mcq',
    stem: typeof exercise.stem === 'string' ? exercise.stem : '',
    options,
    answer_key: {
      label: typeof answerKey.label === 'string' ? answerKey.label : '',
      option_id: typeof answerKey.option_id === 'string' ? answerKey.option_id : null,
      rationale_right: typeof answerKey.rationale_right === 'string' ? answerKey.rationale_right : null,
    },
  };
};

const lessonPackageToDTO = (pkg: any): LessonPackage => {
  const exercises = Array.isArray(pkg?.exercises)
    ? pkg.exercises.map(lessonExerciseToDTO)
    : [];

  const meta = pkg?.meta ?? {};
  const objectives = Array.isArray(pkg?.objectives) ? pkg.objectives : [];
  const glossary =
    pkg && typeof pkg.glossary === 'object' && pkg.glossary !== null ? pkg.glossary : {};
  const misconceptions = Array.isArray(pkg?.misconceptions) ? pkg.misconceptions : [];
  const confusables = Array.isArray(pkg?.confusables) ? pkg.confusables : [];

  return {
    meta: {
      lesson_id: typeof meta.lesson_id === 'string' ? meta.lesson_id : '',
      title: typeof meta.title === 'string' ? meta.title : '',
      learner_level: typeof meta.learner_level === 'string' ? meta.learner_level : '',
      package_schema_version:
        typeof meta.package_schema_version === 'number' ? meta.package_schema_version : 1,
      content_version: typeof meta.content_version === 'number' ? meta.content_version : 1,
    },
    objectives: objectives as Objective[],
    glossary: glossary as Record<string, GlossaryTerm[]>,
    mini_lesson: typeof pkg?.mini_lesson === 'string' ? pkg.mini_lesson : '',
    exercises,
    misconceptions: misconceptions as Record<string, string>[],
    confusables: confusables as Record<string, string>[],
  };
};

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

const learningSessionToDTO = (apiSession: ApiLearningSession): LearningSessionSummary => ({
  id: apiSession.id,
  lesson_id: apiSession.lesson_id,
  unit_id: apiSession.unit_id,
  user_id: apiSession.user_id,
  status: apiSession.status,
  started_at: new Date(apiSession.started_at),
  completed_at: parseDate(apiSession.completed_at),
  current_exercise_index: apiSession.current_exercise_index,
  total_exercises: apiSession.total_exercises,
  progress_percentage: apiSession.progress_percentage,
  session_data: apiSession.session_data ?? {},
});

const normalizeMetadata = (metadata: Record<string, any> | null | undefined): Record<string, any> => {
  if (!metadata) {
    return {};
  }
  return { ...metadata };
};

const conversationMessageToDTO = (message: ApiConversationMessage): ConversationMessage => ({
  id: message.id,
  role: message.role,
  content: message.content,
  created_at: new Date(message.created_at),
  metadata: normalizeMetadata(message.metadata),
  tokens_used: message.tokens_used ?? null,
  cost_estimate: message.cost_estimate ?? null,
  llm_request_id: message.llm_request_id ?? null,
  message_order: message.message_order ?? null,
});

const conversationSummaryToDTO = (summary: ApiConversationSummary): ConversationSummary => ({
  id: summary.id,
  user_id: summary.user_id ?? null,
  title: summary.title ?? null,
  conversation_type: summary.conversation_type,
  status: summary.status,
  message_count: summary.message_count,
  created_at: new Date(summary.created_at),
  updated_at: new Date(summary.updated_at),
  last_message_at: summary.last_message_at ? new Date(summary.last_message_at) : null,
  metadata: normalizeMetadata(summary.metadata),
});

const conversationDetailToDTO = (detail: ApiConversationDetail): ConversationDetail => ({
  conversation_id: detail.conversation_id,
  conversation_type: detail.conversation_type,
  messages: detail.messages.map(conversationMessageToDTO),
  metadata: normalizeMetadata(detail.metadata),
  proposed_brief: detail.proposed_brief ?? null,
  accepted_brief: detail.accepted_brief ?? null,
  resources: (detail.resources ?? []).map(resourceSummaryToDTO),
});

const userConversationToDTO = (
  conversation: ApiUserConversationSummary
): UserConversationSummary => ({
  id: conversation.id,
  title: conversation.title ?? null,
  status: conversation.status,
  message_count: conversation.message_count,
  last_message_at: conversation.last_message_at
    ? new Date(conversation.last_message_at)
    : null,
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
  art_image_url: unit.art_image_url ?? null,
  art_image_description: unit.art_image_description ?? null,
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

const userDetailToDTO = (user: ApiUserDetail, resources: ResourceWithUsage[] = []): UserDetail => ({
  ...userSummaryToDTO(user),
  owned_units: user.owned_units.map(userOwnedUnitToDTO),
  recent_sessions: user.recent_sessions.map(userSessionToDTO),
  recent_llm_requests: user.recent_llm_requests.map(userRequestToDTO),
  recent_conversations: (user.recent_conversations ?? []).map(userConversationToDTO),
  resources,
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
      const resources = await this.buildUserResources(detail.id, detail.owned_units);
      return userDetailToDTO(detail, resources);
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
      const resources = await this.buildUserResources(updated.id, updated.owned_units);
      return userDetailToDTO(updated, resources);
    } catch (error) {
      console.error('Failed to update user:', error);
      return null;
    }
  }

  private async buildUserResources(
    userId: number | string,
    ownedUnits: ApiUserOwnedUnitSummary[]
  ): Promise<ResourceWithUsage[]> {
    const numericId = typeof userId === 'number' ? userId : Number(userId);
    if (!Number.isFinite(numericId)) {
      return [];
    }

    const listResourcesForUser = (
      AdminRepo.resources as { listByUser?: (userId: number) => Promise<ApiResourceSummary[]> }
    ).listByUser;
    const getUnitResources = (
      AdminRepo.units as { resources?: (unitId: string) => Promise<ApiResourceSummary[]> }
    ).resources;

    const [resources, unitResourceLookups] = await Promise.all([
      listResourcesForUser
        ? listResourcesForUser(numericId).catch(() => [] as ApiResourceSummary[])
        : Promise.resolve([] as ApiResourceSummary[]),
      Promise.all(
        ownedUnits.map(async (unit) => {
          if (!getUnitResources) {
            return { unitId: unit.id, unitTitle: unit.title, resources: [] as ApiResourceSummary[] };
          }
          try {
            const unitResources = await getUnitResources(unit.id);
            return { unitId: unit.id, unitTitle: unit.title, resources: unitResources };
          } catch (error) {
            console.error('Failed to fetch resources for unit', unit.id, error);
            return { unitId: unit.id, unitTitle: unit.title, resources: [] as ApiResourceSummary[] };
          }
        })
      ),
    ]);

    const usageByResource = new Map<string, ResourceUsageSummary[]>();
    for (const lookup of unitResourceLookups) {
      for (const resource of lookup.resources) {
        const existing = usageByResource.get(resource.id) ?? [];
        usageByResource.set(resource.id, [
          ...existing,
          { unit_id: lookup.unitId, unit_title: lookup.unitTitle },
        ]);
      }
    }

    return resources.map((resource) => ({
      ...resourceSummaryToDTO(resource),
      used_in_units: usageByResource.get(resource.id) ?? [],
    }));
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
      const apiFlow = await AdminRepo.flowEngine.byId(id);
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

  async getLLMRequests(
    params?: LLMRequestsQuery
  ): Promise<LLMRequestsListResponse> {
    try {
      const apiResponse = await AdminRepo.llmRequests.list(params);

      const rawRequests: ApiLLMRequest[] = Array.isArray(apiResponse)
        ? apiResponse
        : apiResponse.requests ?? [];

      const totalCount = Array.isArray(apiResponse)
        ? apiResponse.length
        : apiResponse?.total_count ?? rawRequests.length;

      const page = Array.isArray(apiResponse)
        ? params?.page ?? 1
        : apiResponse?.page ?? params?.page ?? 1;

      const defaultPageSize = rawRequests.length || 10;

      const pageSize = Array.isArray(apiResponse)
        ? params?.page_size ?? defaultPageSize
        : apiResponse?.page_size ?? params?.page_size ?? defaultPageSize;

      const hasNext = Array.isArray(apiResponse)
        ? false
        : apiResponse?.has_next ?? false;

      return {
        requests: rawRequests.map(llmRequestToDTO),
        total_count: totalCount,
        page,
        page_size: pageSize,
        has_next: hasNext,
      };
    } catch (error) {
      console.error('Failed to fetch LLM requests:', error);
      return {
        requests: [],
        total_count: 0,
        page: params?.page ?? 1,
        page_size: params?.page_size ?? 10,
        has_next: false,
      };
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

  // ---- Learning Sessions ----

  async getLearningSessions(
    params?: LearningSessionsQuery
  ): Promise<LearningSessionsListResponse> {
    try {
      const response: ApiLearningSessionsListResponse = await AdminRepo.learningSessions.list(params);

      return {
        sessions: response.sessions.map(learningSessionToDTO),
        total_count: response.total_count,
        page: response.page,
        page_size: response.page_size,
        has_next: response.has_next,
      };
    } catch (error) {
      console.error('Failed to fetch learning sessions:', error);
      const page = params?.page ?? 1;
      const pageSize = params?.page_size ?? 50;
      return {
        sessions: [],
        total_count: 0,
        page,
        page_size: pageSize,
        has_next: false,
      };
    }
  }

  async getLearningSession(sessionId: string): Promise<LearningSessionSummary | null> {
    if (!sessionId) {
      return null;
    }

    try {
      const session = await AdminRepo.learningSessions.byId(sessionId);
      return learningSessionToDTO(session);
    } catch (error) {
      console.error('Failed to fetch learning session detail:', error);
      return null;
    }
  }

  // ---- Learning Coach Conversations ----

  async getConversations(
    params?: ConversationListQuery
  ): Promise<ConversationsListResponse> {
    try {
      const response: ApiConversationsListResponse = await AdminRepo.conversations.list(params);

      return {
        conversations: response.conversations.map(conversationSummaryToDTO),
        total_count: response.total_count,
        page: response.page,
        page_size: response.page_size,
        has_next: response.has_next,
      };
    } catch (error) {
      console.error('Failed to fetch learning coach conversations:', error);
      const page = params?.page ?? 1;
      const pageSize = params?.page_size ?? 50;
      return {
        conversations: [],
        total_count: 0,
        page,
        page_size: pageSize,
        has_next: false,
      };
    }
  }

  async getConversation(conversationId: string): Promise<ConversationDetail | null> {
    if (!conversationId) {
      return null;
    }

    try {
      const detail = await AdminRepo.conversations.byId(conversationId);
      return conversationDetailToDTO(detail);
    } catch (error) {
      console.error('Failed to fetch learning coach conversation detail:', error);
      return null;
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
        has_podcast: Boolean(lesson.has_podcast),
        podcast_voice: lesson.podcast_voice ?? null,
        podcast_duration_seconds: lesson.podcast_duration_seconds ?? null,
        podcast_audio_url: lesson.podcast_audio_url ?? null,
        podcast_generated_at: lesson.podcast_generated_at
          ? new Date(lesson.podcast_generated_at)
          : null,
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
        package: lessonPackageToDTO(apiLesson.package),
        package_version: apiLesson.package_version,
        flow_run_id: apiLesson.flow_run_id || null,
        created_at: new Date(apiLesson.created_at),
        updated_at: new Date(apiLesson.updated_at),
        has_podcast: Boolean(apiLesson.has_podcast),
        podcast_transcript: apiLesson.podcast_transcript ?? null,
        podcast_voice: apiLesson.podcast_voice ?? null,
        podcast_audio_url: apiLesson.podcast_audio_url ?? null,
        podcast_duration_seconds: apiLesson.podcast_duration_seconds ?? null,
        podcast_generated_at: apiLesson.podcast_generated_at
          ? new Date(apiLesson.podcast_generated_at)
          : null,
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
      status: (u as Record<string, any>).status ?? null,
      creation_progress: (u as Record<string, any>).creation_progress ?? null,
      error_message: (u as Record<string, any>).error_message ?? null,
      arq_task_id: (u as Record<string, any>).arq_task_id ?? null,
      target_lesson_count: u.target_lesson_count ?? null,
      generated_from_topic: Boolean(u.generated_from_topic),
      flow_type: (u.flow_type as UnitSummary['flow_type']) ?? 'standard',
      user_id: u.user_id ?? null,
      is_global: Boolean(u.is_global),
      created_at: u.created_at ? new Date(u.created_at) : null,
      updated_at: u.updated_at ? new Date(u.updated_at) : null,
      has_podcast: Boolean((u as any).has_podcast ?? false),
      podcast_voice: u.podcast_voice ?? null,
      podcast_duration_seconds: u.podcast_duration_seconds ?? null,
      art_image_url: u.art_image_url ?? null,
      art_image_description: u.art_image_description ?? null,
    } satisfies UnitSummary));
  }

  async getUnitDetail(unitId: string): Promise<UnitDetail | null> {
    try {
      const loadUnitResources = (AdminRepo.units as {
        resources?: (unitId: string) => Promise<ApiResourceSummary[]>;
      }).resources;

      const [detail, flowRuns, resources] = await Promise.all([
        AdminRepo.units.detail(unitId),
        AdminRepo.units.flowRuns(unitId).catch(() => [] as ApiFlowRun[]),
        loadUnitResources
          ? loadUnitResources(unitId).catch(() => [] as ApiResourceSummary[])
          : Promise.resolve([] as ApiResourceSummary[]),
      ]);

      return {
        id: detail.id,
        title: detail.title,
        description: detail.description,
        learner_level: detail.learner_level,
        lesson_order: detail.lesson_order,
        lessons: detail.lessons.map((l) => ({
          id: l.id,
          title: l.title,
          learner_level: l.learner_level,
          learning_objectives: l.learning_objectives ?? [],
          key_concepts: l.key_concepts ?? [],
          exercise_count: l.exercise_count,
          has_podcast: Boolean(l.has_podcast),
          podcast_voice: l.podcast_voice ?? null,
          podcast_duration_seconds: l.podcast_duration_seconds ?? null,
          podcast_generated_at: l.podcast_generated_at
            ? new Date(l.podcast_generated_at)
            : null,
          podcast_audio_url: l.podcast_audio_url ?? null,
        })),
        learning_objectives:
          detail.learning_objectives?.map((lo) => ({
            id: lo.id,
            title: lo.title ?? (lo as Record<string, any>).text ?? lo.description ?? lo.id,
            description: lo.description ?? (lo as Record<string, any>).text ?? '',
            bloom_level: lo.bloom_level ?? null,
            evidence_of_mastery: lo.evidence_of_mastery ?? null,
          })) ?? null,
        target_lesson_count: detail.target_lesson_count ?? null,
        source_material: detail.source_material ?? null,
        generated_from_topic: Boolean(detail.generated_from_topic),
        flow_type: (detail.flow_type as UnitDetail['flow_type']) ?? 'standard',
        learning_objective_progress: detail.learning_objective_progress ?? null,
        has_podcast: Boolean(detail.has_podcast),
        podcast_voice: detail.podcast_voice ?? null,
        podcast_duration_seconds: detail.podcast_duration_seconds ?? null,
        podcast_transcript: detail.podcast_transcript ?? null,
        podcast_audio_url: detail.podcast_audio_url ?? null,
        art_image_url: detail.art_image_url ?? null,
        art_image_description: detail.art_image_description ?? null,
        status: (detail as Record<string, any>).status ?? null,
        creation_progress: (detail as Record<string, any>).creation_progress ?? null,
        error_message: (detail as Record<string, any>).error_message ?? null,
        arq_task_id: (detail as Record<string, any>).arq_task_id ?? null,
        flow_runs: flowRuns.map(flowRunToDTO),
        created_at: (detail as any).created_at ? new Date((detail as any).created_at) : null,
        updated_at: (detail as any).updated_at ? new Date((detail as any).updated_at) : null,
        resources: resources.map(resourceSummaryToDTO),
      };
    } catch (error) {
      console.error('Failed to fetch unit detail:', error);
      return null;
    }
  }

  async getResource(resourceId: string): Promise<ResourceDetail | null> {
    const loadResourceDetail = (AdminRepo.resources as {
      detail?: (resourceId: string) => Promise<ApiResourceDetail>;
    }).detail;

    if (!loadResourceDetail) {
      return null;
    }

    try {
      const resource = await loadResourceDetail(resourceId);
      return resourceDetailToDTO(resource);
    } catch (error) {
      const maybeAxiosError = error as { response?: { status?: number } };
      if (maybeAxiosError?.response?.status === 404) {
        return null;
      }
      console.error('Failed to fetch resource detail:', error);
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

  // ---- Task Queue & Background Tasks ----

  async getQueueStatus(queueName?: string): Promise<QueueStatus[]> {
    const data = await AdminRepo.taskQueue.status(queueName);
    if (!data) {
      return [];
    }

    const stats = data.stats ?? {};
    return [
      {
        queue_name: data.queue_name ?? queueName ?? 'default',
        status: (data.status ?? 'healthy') as QueueStatus['status'],
        pending_count: stats.pending_tasks ?? 0,
        running_count: stats.in_progress_tasks ?? 0,
        worker_count: data.workers?.total ?? 0,
        oldest_pending_minutes: stats.oldest_pending_minutes ?? null,
      },
    ];
  }

  async getQueueStats(queueName?: string): Promise<QueueStats[]> {
    const stats = await AdminRepo.taskQueue.stats(queueName);
    if (!stats) {
      return [];
    }

    return [
      {
        queue_name: stats.queue_name ?? queueName ?? 'default',
        pending_count: stats.pending_tasks ?? 0,
        running_count: stats.in_progress_tasks ?? 0,
        completed_count: stats.completed_tasks ?? 0,
        failed_count: stats.failed_tasks ?? 0,
        total_processed: (stats.completed_tasks ?? 0) + (stats.failed_tasks ?? 0),
        workers_count: stats.total_workers ?? 0,
        workers_busy: stats.in_progress_tasks ?? 0,
        oldest_pending_task: stats.last_updated ? new Date(stats.last_updated) : null,
        avg_processing_time_ms: stats.average_task_duration_ms ?? null,
      },
    ];
  }

  async getTasks(limit: number = 50, queueName?: string): Promise<TaskStatus[]> {
    const data = await AdminRepo.taskQueue.tasks(limit, queueName);
    return data.map(taskStatusToDTO);
  }

  async getTask(taskId: string): Promise<TaskStatus | null> {
    try {
      const data = await AdminRepo.taskQueue.taskById(taskId);
      return taskStatusToDTO(data);
    } catch (error) {
      console.error('Failed to fetch task:', error);
      return null;
    }
  }

  async getTaskFlowRuns(taskId: string): Promise<FlowRunSummary[]> {
    try {
      const runs = await AdminRepo.taskQueue.flowRuns(taskId);
      return runs.map(flowRunToDTO);
    } catch (error) {
      console.error('Failed to fetch task flow runs:', error);
      return [];
    }
  }

  async getUnitFlowRuns(unitId: string): Promise<FlowRunSummary[]> {
    try {
      const runs = await AdminRepo.units.flowRuns(unitId);
      return runs.map(flowRunToDTO);
    } catch (error) {
      console.error('Failed to fetch unit flow runs:', error);
      return [];
    }
  }

  async retryUnit(unitId: string): Promise<void> {
    await AdminRepo.contentCreator.retryUnit(unitId);
  }

  async getWorkers(): Promise<WorkerHealth[]> {
    const data = await AdminRepo.taskQueue.workers();
    return data.map(workerHealthToDTO);
  }

  async getQueueHealth(): Promise<{ status: string; details: Record<string, any> }> {
    return await AdminRepo.taskQueue.health();
  }
}
