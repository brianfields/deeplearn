// Content Creation Types

export interface CreateRefinedMaterialRequest {
  topic: string
  source_material: string
  domain?: string
  level: 'beginner' | 'intermediate' | 'advanced'
  model?: string
}

export interface CreateMCQRequest {
  session_id: string
  topic: string
  learning_objective: string
  key_facts: string[]
  common_misconceptions: Array<{
    misconception: string
    correct_concept: string
  }>
  assessment_angles: string[]
  level: 'beginner' | 'intermediate' | 'advanced'
  model?: string
}

export interface RefinedMaterialTopic {
  topic: string
  learning_objectives: string[]
  key_facts: string[]
  common_misconceptions: Array<{
    misconception: string
    correct_concept: string
  }>
  assessment_angles: string[]
}

export interface RefinedMaterial {
  topics: RefinedMaterialTopic[]
}

export interface MCQData {
  stem: string
  options: string[]
  correct_answer: string
  correct_answer_index: number
  rationale: string
}

export interface MCQEvaluation {
  alignment: string
  stem_quality: string
  options_quality: string
  cognitive_challenge: string
  clarity_fairness: string
  overall: string
}

export interface MCQ {
  mcq_id: string
  topic: string
  learning_objective: string
  mcq: MCQData
  evaluation: MCQEvaluation
  created_at: string
}

export interface ContentSession {
  session_id: string
  topic: string
  domain: string
  level: string
  refined_material: RefinedMaterial | null
  mcqs: MCQ[]
  created_at: string
  updated_at: string
}

export interface RefinedMaterialResponse {
  session_id: string
  topic: string
  domain: string
  level: string
  source_material_length: number
  refined_material: RefinedMaterial
  created_at: string
}

export interface MCQResponse {
  session_id: string
  mcq_id: string
  topic: string
  learning_objective: string
  mcq: MCQData
  evaluation: MCQEvaluation
  created_at: string
}

export interface ApiError {
  detail: string
}