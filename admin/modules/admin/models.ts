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
  execution_mode: 'sync' | 'async' | 'background';
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
  execution_mode: 'sync' | 'async' | 'background';
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
  core_concept: string;
  user_level: string;
  source_domain: string | null;
  source_level: string | null;
  package_version: number;
  created_at: Date;
  updated_at: Date;
}

export interface LessonDetails {
  id: string;
  title: string;
  core_concept: string;
  user_level: string;
  source_material: string | null;
  source_domain: string | null;
  source_level: string | null;
  refined_material: Record<string, any> | null;
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

export interface LengthBudgets {
  stem_max_words: number;
  vignette_max_words: number;
  option_max_words: number;
}

export interface Meta {
  lesson_id: string;
  title: string;
  core_concept: string;
  user_level: string;
  domain: string;
  package_schema_version: number;
  content_version: number;
  length_budgets: LengthBudgets;
}

export interface Objective {
  id: string;
  text: string;
  bloom_level: string | null;
}

export interface GlossaryTerm {
  id: string;
  term: string;
  definition: string;
  relation_to_core: string | null;
  common_confusion: string | null;
  micro_check: string | null;
}

export interface DidacticSnippet {
  id: string;
  mini_vignette: string | null;
  plain_explanation: string;
  key_takeaways: string[];
  worked_example: string | null;
  near_miss_example: string | null;
  discriminator_hint: string | null;
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
  didactic_snippet: DidacticSnippet; // Single lesson-wide explanation
  exercises: Exercise[]; // Generalized from MCQs to support multiple exercise types
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
  user_level?: string;
  domain?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface MetricsQuery {
  start_date?: Date;
  end_date?: Date;
}
