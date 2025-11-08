/**
 * Admin Module - Type Definitions
 *
 * All admin-related types and DTOs for the frontend.
 * Mirrors the backend DTOs but adapted for frontend use.
 */

// ---- Flow Management Types ----

export interface FlowRunSummary {
  id: string;
  flow_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  execution_mode: 'sync' | 'async' | 'background' | 'arq';
  arq_task_id: string | null;
  unit_id?: string | null;
  user_id: string | null;
  created_at: Date;
  started_at: Date | null;
  completed_at: Date | null;
  execution_time_ms: number | null;
  total_tokens: number;
  total_cost: number;
  step_count: number;
  error_message: string | null;
}

export interface FlowStepDetails {
  id: string;
  flow_run_id: string;
  llm_request_id: string | null;
  step_name: string;
  step_order: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  inputs: Record<string, any>;
  outputs: Record<string, any> | null;
  tokens_used: number;
  cost_estimate: number;
  execution_time_ms: number | null;
  error_message: string | null;
  step_metadata: Record<string, any> | null;
  created_at: Date;
  completed_at: Date | null;
}

export interface FlowRunDetails {
  id: string;
  flow_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  execution_mode: 'sync' | 'async' | 'background' | 'arq';
  arq_task_id: string | null;
  unit_id?: string | null;
  user_id: string | null;
  current_step: string | null;
  step_progress: number;
  total_steps: number | null;
  progress_percentage: number;
  created_at: Date;
  started_at: Date | null;
  completed_at: Date | null;
  last_heartbeat: Date | null;
  execution_time_ms: number | null;
  total_tokens: number;
  total_cost: number;
  inputs: Record<string, any>;
  outputs: Record<string, any> | null;
  flow_metadata: Record<string, any> | null;
  error_message: string | null;
  steps: FlowStepDetails[];
}

export interface FlowRunsListResponse {
  flows: FlowRunSummary[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface LearningSessionSummary {
  id: string;
  lesson_id: string;
  unit_id: string | null;
  user_id: string | null;
  status: string;
  started_at: Date;
  completed_at: Date | null;
  current_exercise_index: number;
  total_exercises: number;
  progress_percentage: number;
  session_data: Record<string, any>;
}

export interface LearningSessionsListResponse {
  sessions: LearningSessionSummary[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// ---- LLM Request Types ----

export interface LLMRequestSummary {
  id: string;
  user_id: string | null;
  api_variant: string;
  provider: string;
  model: string;
  status: 'pending' | 'completed' | 'failed';
  tokens_used: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_estimate: number | null;
  execution_time_ms: number | null;
  cached: boolean;
  created_at: Date;
  error_message: string | null;
}

export interface LLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface LLMRequestDetails {
  id: string;
  user_id: string | null;
  api_variant: string;
  provider: string;
  model: string;
  provider_response_id: string | null;
  system_fingerprint: string | null;
  temperature: number;
  max_output_tokens: number | null;
  messages: LLMMessage[];
  additional_params: Record<string, any> | null;
  request_payload: Record<string, any> | null;
  response_content: string | null;
  response_raw: Record<string, any> | null;
  response_output: Record<string, any> | Record<string, any>[] | null;
  tokens_used: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_estimate: number | null;
  response_created_at: Date | null;
  status: 'pending' | 'completed' | 'failed';
  execution_time_ms: number | null;
  error_message: string | null;
  error_type: string | null;
  retry_attempt: number;
  cached: boolean;
  created_at: Date;
}

export interface LLMRequestsListResponse {
  requests: LLMRequestSummary[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// ---- Learning Coach Conversation Types ----

export interface ConversationMessage {
  id: string;
  role: 'system' | 'user' | 'assistant';
  content: string;
  created_at: Date;
  metadata: Record<string, any>;
  tokens_used: number | null;
  cost_estimate: number | null;
  llm_request_id: string | null;
  message_order: number | null;
}

export interface ConversationDetail {
  conversation_id: string;
  conversation_type: string; // "learning_coach" or "teaching_assistant"
  messages: ConversationMessage[];
  metadata: Record<string, any>;
  proposed_brief: Record<string, any> | null;
  accepted_brief: Record<string, any> | null;
  resources: ResourceSummary[];
  total_cost: number;
}

export interface ConversationSummary {
  id: string;
  user_id: number | string | null;
  title: string | null;
  conversation_type: string; // "learning_coach" or "teaching_assistant"
  status: string;
  message_count: number;
  created_at: Date;
  updated_at: Date;
  last_message_at: Date | null;
  metadata: Record<string, any>;
  total_cost: number;
}

export interface ConversationsListResponse {
  conversations: ConversationSummary[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// ---- Lesson Types ----

export interface LessonSummary {
  id: string;
  title: string;
  learner_level: string;
  package_version: number;
  created_at: Date;
  updated_at: Date;
  has_podcast: boolean;
  podcast_voice: string | null;
  podcast_duration_seconds: number | null;
  podcast_audio_url: string | null;
  podcast_generated_at?: Date | null;
}

export interface LessonDetails {
  id: string;
  title: string;
  learner_level: string;
  source_material: string | null;
  package: LessonPackage;
  package_version: number;
  flow_run_id: string | null;
  created_at: Date;
  updated_at: Date;
  has_podcast: boolean;
  podcast_transcript: string | null;
  podcast_voice: string | null;
  podcast_audio_url: string | null;
  podcast_duration_seconds: number | null;
  podcast_generated_at: Date | null;
}

export interface LessonsListResponse {
  lessons: LessonSummary[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// ---- User Management DTOs ----

export interface ApiUserAssociationSummary {
  owned_unit_count: number;
  owned_global_unit_count: number;
  learning_session_count: number;
  llm_request_count: number;
}

export interface ApiUserOwnedUnitSummary {
  id: string;
  title: string;
  is_global: boolean;
  updated_at: string;
  art_image_url?: string | null;
  art_image_description?: string | null;
}

export interface ApiUserSessionSummary {
  id: string;
  lesson_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  progress_percentage: number;
}

export interface ApiUserLLMRequestSummary {
  id: string;
  model: string;
  status: string;
  created_at: string;
  tokens_used: number | null;
}

export interface ApiUserConversationSummary {
  id: string;
  title: string | null;
  conversation_type: string; // "learning_coach" or "teaching_assistant"
  status: string;
  message_count: number;
  last_message_at: string | null;
}

export interface ApiUserSummary {
  id: number | string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  associations: ApiUserAssociationSummary;
}

export interface ApiUserDetail extends ApiUserSummary {
  owned_units: ApiUserOwnedUnitSummary[];
  recent_sessions: ApiUserSessionSummary[];
  recent_llm_requests: ApiUserLLMRequestSummary[];
  recent_conversations: ApiUserConversationSummary[];
}

export interface ApiUserListResponse {
  users: ApiUserSummary[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface ApiUserUpdateRequest {
  name?: string | null;
  role?: string | null;
  is_active?: boolean | null;
}

export interface UserAssociationSummary {
  owned_unit_count: number;
  owned_global_unit_count: number;
  learning_session_count: number;
  llm_request_count: number;
}

export interface UserOwnedUnitSummary {
  id: string;
  title: string;
  is_global: boolean;
  updated_at: Date;
  art_image_url: string | null;
  art_image_description: string | null;
}

export interface UserSessionSummary {
  id: string;
  lesson_id: string;
  status: string;
  started_at: Date;
  completed_at: Date | null;
  progress_percentage: number;
}

export interface UserLLMRequestSummary {
  id: string;
  model: string;
  status: string;
  created_at: Date;
  tokens_used: number | null;
}

export interface UserConversationSummary {
  id: string;
  title: string | null;
  conversation_type: string; // "learning_coach" or "teaching_assistant"
  status: string;
  message_count: number;
  last_message_at: Date | null;
}

export interface UserSummary {
  id: number | string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
  associations: UserAssociationSummary;
}

export interface UserDetail extends UserSummary {
  owned_units: UserOwnedUnitSummary[];
  recent_sessions: UserSessionSummary[];
  recent_llm_requests: UserLLMRequestSummary[];
  recent_conversations: UserConversationSummary[];
  resources: ResourceWithUsage[];
}

export interface UserListResponse {
  users: UserSummary[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface UserListQuery {
  page?: number;
  page_size?: number;
  search?: string;
}

export interface UserUpdatePayload {
  name?: string | null;
  role?: string | null;
  is_active?: boolean | null;
}

// ---- Lesson Package Types (from backend package_models.py) ----

export interface Meta {
  lesson_id: string;
  title: string;
  learner_level: string;
  package_schema_version: number;
  content_version: number;
}

export interface Objective {
  id: string;
  title: string;
  description: string;
  bloom_level: string | null;
  text?: string; // legacy support while cached data updates
}

export interface UnitLearningObjective {
  id: string;
  title: string;
  description: string;
  bloom_level?: string | null;
  evidence_of_mastery?: string | null;
}

export interface ExerciseOption {
  id: string;
  label: string;
  text: string;
  rationale_wrong: string | null;
}

export interface ExerciseAnswerKey {
  label: string;
  option_id: string | null;
  rationale_right: string | null;
}

export interface WrongAnswerWithRationale {
  answer: string;
  rationale_wrong: string;
  explanation?: string; // alias for rationale_wrong
  misconception_ids: string[];
}

interface LessonExerciseBase {
  id: string;
  exercise_type: 'mcq' | 'short_answer';
  exercise_category: 'comprehension' | 'transfer';
  aligned_learning_objective: string;
  lo_id?: string; // alias for aligned_learning_objective
  cognitive_level: 'Recall' | 'Comprehension' | 'Application' | 'Transfer';
  difficulty: 'easy' | 'medium' | 'hard';
  estimated_difficulty?: string; // alias for difficulty
  stem: string;
}

export interface MCQExercise extends LessonExerciseBase {
  exercise_type: 'mcq';
  options: ExerciseOption[];
  answer_key: ExerciseAnswerKey;
  misconceptions_used?: string[]; // derived from wrong_answers
}

export interface ShortAnswerExercise extends LessonExerciseBase {
  exercise_type: 'short_answer';
  canonical_answer: string;
  acceptable_answers: string[];
  wrong_answers: WrongAnswerWithRationale[];
  explanation_correct: string;
  misconceptions_used?: string[]; // derived from wrong_answers
}

export type LessonExercise = MCQExercise | ShortAnswerExercise;

export interface QuizCoverageByLO {
  exercise_ids: string[];
  concepts: string[];
}

export interface QuizCoverageByConcept {
  exercise_ids: string[];
  types: Array<'mcq' | 'short_answer'>;
}

export interface QuizMetadata {
  quiz_type: string;
  total_items: number;
  difficulty_distribution_target: Record<string, number>;
  difficulty_distribution_actual: Record<string, number>;
  cognitive_mix_target: Record<string, number>;
  cognitive_mix_actual: Record<string, number>;
  coverage_by_LO: Record<string, QuizCoverageByLO>;
  coverage_by_concept: Record<string, QuizCoverageByConcept>;
  normalizations_applied: string[];
  selection_rationale: string[];
  gaps_identified: string[];
}

export interface LessonPackage {
  meta: Meta;
  unit_learning_objective_ids: string[];
  exercise_bank: LessonExercise[];
  exercises?: LessonExercise[]; // alias for exercise_bank
  quiz: string[];
  quiz_metadata: QuizMetadata;
}

// ---- Analytics Types ----

export interface SystemMetrics {
  total_flows: number;
  active_flows: number;
  completed_flows: number;
  failed_flows: number;
  total_steps: number;
  total_llm_requests: number;
  total_tokens_used: number;
  total_cost: number;
  total_lessons: number;
  active_sessions: number;
}

export interface FlowMetrics {
  flow_name: string;
  total_runs: number;
  success_rate: number;
  avg_execution_time_ms: number;
  avg_tokens: number;
  avg_cost: number;
  last_run: Date | null;
}

export interface DailyMetrics {
  date: string; // ISO date string
  flow_runs: number;
  llm_requests: number;
  tokens_used: number;
  cost: number;
  unique_users: number;
}

// ---- Units Types ----

// API wire formats
export interface ApiUnitSummary {
  id: string;
  title: string;
  description: string | null;
  learner_level: string;
  lesson_order: string[];
  lesson_count: number;
  user_id?: number | string | null;
  is_global?: boolean;
  target_lesson_count?: number | null;
  generated_from_topic?: boolean;
  flow_type?: 'standard' | 'fast';
  created_at?: string;
  updated_at?: string;
  has_podcast?: boolean;
  podcast_voice?: string | null;
  podcast_duration_seconds?: number | null;
  podcast_transcript?: string | null;
  podcast_audio_url?: string | null;
  art_image_url?: string | null;
  art_image_description?: string | null;
}

export interface ApiUnitLessonSummary {
  id: string;
  title: string;
  learner_level: string;
  learning_objectives: string[];
  key_concepts: string[];
  exercise_count: number;
  has_podcast?: boolean;
  podcast_voice?: string | null;
  podcast_duration_seconds?: number | null;
  podcast_generated_at?: string | null;
  podcast_audio_url?: string | null;
}

export interface ApiUnitDetail {
  id: string;
  title: string;
  description: string | null;
  learner_level: string;
  lesson_order: string[];
  lessons: ApiUnitLessonSummary[];
  // New fields from backend
  learning_objectives?: UnitLearningObjective[] | null;
  target_lesson_count?: number | null;
  source_material?: string | null;
  generated_from_topic?: boolean;
  flow_type?: 'standard' | 'fast';
  learning_objective_progress?: LearningObjectiveProgress[] | null;
  has_podcast?: boolean;
  podcast_voice?: string | null;
  podcast_duration_seconds?: number | null;
  podcast_transcript?: string | null;
  podcast_audio_url?: string | null;
  art_image_url?: string | null;
  art_image_description?: string | null;
}

// Basic unit from /api/v1/units
export interface ApiUnitBasic {
  id: string;
  title: string;
  description: string | null;
  difficulty: string;
  lesson_order: string[];
  created_at: string;
  updated_at: string;
}

// DTOs used by admin UI
export interface UnitSummary {
  id: string;
  title: string;
  description: string | null;
  learner_level: string;
  lesson_count: number;
  status?: string | null;
  creation_progress?: Record<string, any> | null;
  error_message?: string | null;
  arq_task_id?: string | null;
  target_lesson_count: number | null;
  generated_from_topic: boolean;
  flow_type: 'standard' | 'fast';
  user_id: number | string | null;
  is_global: boolean;
  created_at: Date | null;
  updated_at: Date | null;
  has_podcast: boolean;
  podcast_voice: string | null;
  podcast_duration_seconds: number | null;
  art_image_url: string | null;
  art_image_description: string | null;
}

export interface UnitLessonSummary {
  id: string;
  title: string;
  learner_level: string;
  learning_objectives: string[];
  key_concepts: string[];
  exercise_count: number;
  has_podcast: boolean;
  podcast_voice: string | null;
  podcast_duration_seconds: number | null;
  podcast_generated_at: Date | null;
  podcast_audio_url: string | null;
}

export interface LearningObjectiveProgress {
  objective: string;
  exercises_total: number;
  exercises_correct: number;
  progress_percentage: number;
}

export interface UnitDetail {
  id: string;
  title: string;
  description: string | null;
  learner_level: string;
  lesson_order: string[];
  lessons: UnitLessonSummary[];
  // New fields for admin detail UI
  learning_objectives: UnitLearningObjective[] | null;
  target_lesson_count: number | null;
  source_material: string | null;
  generated_from_topic: boolean;
  flow_type: 'standard' | 'fast';
  learning_objective_progress: LearningObjectiveProgress[] | null;
  has_podcast: boolean;
  podcast_voice: string | null;
  podcast_duration_seconds: number | null;
  podcast_transcript: string | null;
  podcast_audio_url: string | null;
  art_image_url: string | null;
  art_image_description: string | null;
  status: string | null;
  creation_progress: Record<string, any> | null;
  error_message: string | null;
  arq_task_id: string | null;
  flow_runs: FlowRunSummary[];
  created_at: Date | null;
  updated_at: Date | null;
  resources: ResourceSummary[];
}

export type LessonToUnitMap = Record<string, { unit_id: string; unit_title: string }>;

// ---- Resource Types ----

export interface ApiResourceSummary {
  id: string;
  resource_type: string;
  filename: string | null;
  source_url: string | null;
  file_size: number | null;
  created_at: string;
  preview_text: string;
}

export interface ApiResourceDetail {
  id: string;
  user_id: number;
  resource_type: string;
  filename: string | null;
  source_url: string | null;
  extracted_text: string;
  extraction_metadata: Record<string, unknown>;
  file_size: number | null;
  created_at: string;
  updated_at: string;
}

export interface ResourceSummary {
  id: string;
  resource_type: string;
  filename: string | null;
  source_url: string | null;
  file_size: number | null;
  created_at: Date;
  preview_text: string;
}

export interface ResourceDetail {
  id: string;
  user_id: number;
  resource_type: string;
  filename: string | null;
  source_url: string | null;
  extracted_text: string;
  extraction_metadata: Record<string, unknown>;
  file_size: number | null;
  created_at: Date;
  updated_at: Date;
}

export interface ResourceUsageSummary {
  unit_id: string;
  unit_title: string;
}

export interface ResourceWithUsage extends ResourceSummary {
  used_in_units: ResourceUsageSummary[];
}

// ---- API Wire Types (private to module) ----

export interface ApiFlowRun {
  id: string;
  flow_name: string;
  status: string;
  execution_mode: string;
  arq_task_id?: string | null;
  unit_id?: string | null;
  user_id: string | null;
  created_at: string; // ISO string
  started_at: string | null;
  completed_at: string | null;
  execution_time_ms: number | null;
  total_tokens: number;
  total_cost: number;
  step_count: number;
  error_message: string | null;
}

export interface ApiFlowRunDetails {
  id: string;
  flow_name: string;
  status: string;
  execution_mode: string;
  arq_task_id?: string | null;
  unit_id?: string | null;
  user_id: string | null;
  current_step: string | null;
  step_progress: number;
  total_steps: number | null;
  progress_percentage: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  last_heartbeat: string | null;
  execution_time_ms: number | null;
  total_tokens: number;
  total_cost: number;
  inputs: Record<string, any>;
  outputs: Record<string, any> | null;
  flow_metadata: Record<string, any> | null;
  error_message: string | null;
  steps: ApiFlowStepDetails[];
}

export interface ApiFlowStepDetails {
  id: string;
  flow_run_id: string;
  llm_request_id: string | null;
  step_name: string;
  step_order: number;
  status: string;
  inputs: Record<string, any>;
  outputs: Record<string, any> | null;
  tokens_used: number;
  cost_estimate: number;
  execution_time_ms: number | null;
  error_message: string | null;
  step_metadata: Record<string, any> | null;
  created_at: string;
  completed_at: string | null;
}

export interface ApiLLMRequest {
  id: string;
  user_id: string | null;
  api_variant: string;
  provider: string;
  model: string;
  status: string;
  tokens_used: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_estimate: number | null;
  execution_time_ms: number | null;
  cached: boolean;
  created_at: string;
  error_message: string | null;
}

export interface ApiConversationMessage {
  id: string;
  role: 'system' | 'user' | 'assistant';
  content: string;
  created_at: string;
  metadata: Record<string, any> | null;
  tokens_used: number | null;
  cost_estimate: number | null;
  llm_request_id: string | null;
  message_order: number | null;
}

export interface ApiConversationDetail {
  conversation_id: string;
  conversation_type: string; // "learning_coach" or "teaching_assistant"
  messages: ApiConversationMessage[];
  metadata: Record<string, any> | null;
  proposed_brief?: Record<string, any> | null;
  accepted_brief?: Record<string, any> | null;
  resources?: ApiResourceSummary[];
  total_cost: number;
}

export interface ApiConversationSummary {
  id: string;
  user_id: number | string | null;
  title: string | null;
  conversation_type: string; // "learning_coach" or "teaching_assistant"
  status: string;
  message_count: number;
  created_at: string;
  updated_at: string;
  last_message_at: string | null;
  metadata: Record<string, any> | null;
  total_cost: number;
}

export interface ApiConversationsListResponse {
  conversations: ApiConversationSummary[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface ApiLearningSession {
  id: string;
  lesson_id: string;
  unit_id: string | null;
  user_id: string | null;
  status: string;
  started_at: string;
  completed_at: string | null;
  current_exercise_index: number;
  total_exercises: number;
  progress_percentage: number;
  session_data: Record<string, any>;
}

export interface ApiLearningSessionsListResponse {
  sessions: ApiLearningSession[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface ApiSystemMetrics {
  total_flows: number;
  active_flows: number;
  completed_flows: number;
  failed_flows: number;
  total_steps: number;
  total_llm_requests: number;
  total_tokens_used: number;
  total_cost: number;
  total_lessons: number;
  active_sessions: number;
}

// ---- Query Parameter Types ----

export interface FlowRunsQuery {
  status?: string;
  flow_name?: string;
  user_id?: string;
  start_date?: Date;
  end_date?: Date;
  page?: number;
  page_size?: number;
}

export interface ConversationListQuery {
  status?: string;
  user_id?: string | number;
  page?: number;
  page_size?: number;
}

export interface LearningSessionsQuery {
  status?: string;
  user_id?: string;
  lesson_id?: string;
  page?: number;
  page_size?: number;
}

export interface LLMRequestsQuery {
  status?: string;
  provider?: string;
  model?: string;
  user_id?: string;
  start_date?: Date;
  end_date?: Date;
  page?: number;
  page_size?: number;
}

export interface LessonsQuery {
  learner_level?: string;
  search?: string;
  domain?: string;
  page?: number;
  page_size?: number;
}

export interface MetricsQuery {
  start_date?: Date;
  end_date?: Date;
}

// ---- Task Queue Types ----

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  submitted_at: Date;
  created_at: Date;
  started_at: Date | null;
  completed_at: Date | null;
  retry_count: number;
  error_message: string | null;
  result: Record<string, any> | null;
  queue_name: string;
  priority: number;
  flow_name?: string | null;
  task_type?: string | null;
  progress_percentage?: number | null;
  current_step?: string | null;
  worker_id?: string | null;
  user_id?: string | null;
  flow_run_id?: string | null;
  unit_id?: string | null;
}

export interface WorkerHealth {
  worker_id: string;
  status: 'healthy' | 'busy' | 'unhealthy' | 'offline';
  last_heartbeat: Date;
  current_task_id: string | null;
  tasks_completed: number;
  queue_name: string;
  started_at: Date;
  version: string | null;
}

export interface QueueStats {
  queue_name: string;
  pending_count: number;
  running_count: number;
  completed_count: number;
  failed_count: number;
  total_processed: number;
  workers_count: number;
  workers_busy: number;
  oldest_pending_task: Date | null;
  avg_processing_time_ms: number | null;
}

export interface QueueStatus {
  queue_name: string;
  status: 'healthy' | 'degraded' | 'down';
  pending_count: number;
  running_count: number;
  worker_count: number;
  oldest_pending_minutes: number | null;
}

// API wire formats for task queue
export interface ApiTaskStatus {
  task_id: string;
  status: string;
  submitted_at: string;
  created_at?: string;
  started_at: string | null;
  completed_at: string | null;
  retry_count: number;
  error_message: string | null;
  result: Record<string, any> | null;
  queue_name: string;
  priority: number;
  flow_name?: string | null;
  task_type?: string | null;
  progress_percentage?: number | null;
  current_step?: string | null;
  worker_id?: string | null;
  user_id?: string | null;
  flow_run_id?: string | null;
  unit_id?: string | null;
}

export interface ApiWorkerHealth {
  worker_id: string;
  status: string;
  last_heartbeat: string;
  current_task_id: string | null;
  tasks_completed: number;
  queue_name: string;
  started_at: string;
  version: string | null;
}
