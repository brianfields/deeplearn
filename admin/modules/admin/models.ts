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

// ---- Lesson Types ----

export interface LessonSummary {
  id: string;
  title: string;
  learner_level: string;
  package_version: number;
  created_at: Date;
  updated_at: Date;
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
}

export interface LessonsListResponse {
  lessons: LessonSummary[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
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
  text: string;
  bloom_level: string | null;
}

export interface GlossaryTerm {
  term: string;
  definition: string;
  micro_check: string | null;
}

export interface MCQOption {
  id: string;
  label: string; // "A", "B", "C", "D"
  text: string;
  rationale_wrong: string | null;
}

export interface MCQAnswerKey {
  label: string;
  option_id: string | null;
  rationale_right?: string | null;
}

// Base Exercise interface
export interface Exercise {
  id: string;
  exercise_type: string; // "mcq", "short_answer", "coding", etc.
  lo_id: string;
  cognitive_level: string | null;
  estimated_difficulty: 'Easy' | 'Medium' | 'Hard' | null;
  misconceptions_used: string[];
}

// MCQ Exercise (extends Exercise)
export interface MCQExercise extends Exercise {
  exercise_type: 'mcq';
  stem: string;
  options: MCQOption[];
  answer_key: MCQAnswerKey;
}

export interface LessonPackage {
  meta: Meta;
  objectives: Objective[];
  glossary: Record<string, GlossaryTerm[]>;
  mini_lesson: string;
  exercises: Exercise[];
  misconceptions: Record<string, string>[];
  confusables: Record<string, string>[];
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
  difficulty: string;
  lesson_count: number;
  // New fields from backend
  target_lesson_count?: number | null;
  generated_from_topic?: boolean;
  flow_type?: 'standard' | 'fast';
}

export interface ApiUnitLessonSummary {
  id: string;
  title: string;
  core_concept: string;
  user_level: string;
  learning_objectives: string[];
  key_concepts: string[];
  exercise_count: number;
}

export interface ApiUnitDetail {
  id: string;
  title: string;
  description: string | null;
  difficulty: string;
  lesson_order: string[];
  lessons: ApiUnitLessonSummary[];
  // New fields from backend
  learning_objectives?: string[] | null;
  target_lesson_count?: number | null;
  source_material?: string | null;
  generated_from_topic?: boolean;
  flow_type?: 'standard' | 'fast';
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
  difficulty: string;
  lesson_count: number;
  // New fields for admin list UI
  target_lesson_count: number | null;
  generated_from_topic: boolean;
  flow_type: 'standard' | 'fast';
}

export interface UnitLessonSummary {
  id: string;
  title: string;
  user_level: string;
  exercise_count: number;
}

export interface UnitDetail {
  id: string;
  title: string;
  description: string | null;
  difficulty: string;
  lesson_order: string[];
  lessons: UnitLessonSummary[];
  // New fields for admin detail UI
  learning_objectives: string[] | null;
  target_lesson_count: number | null;
  source_material: string | null;
  generated_from_topic: boolean;
  flow_type: 'standard' | 'fast';
}

export type LessonToUnitMap = Record<string, { unit_id: string; unit_title: string }>;

// ---- API Wire Types (private to module) ----

export interface ApiFlowRun {
  id: string;
  flow_name: string;
  status: string;
  execution_mode: string;
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
  started_at: Date | null;
  completed_at: Date | null;
  retry_count: number;
  error_message: string | null;
  result: Record<string, any> | null;
  queue_name: string;
  priority: number;
  flow_name?: string;
  flow_run_id?: string;
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
  started_at: string | null;
  completed_at: string | null;
  retry_count: number;
  error_message: string | null;
  result: Record<string, any> | null;
  queue_name: string;
  priority: number;
  flow_name?: string;
  flow_run_id?: string;
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
