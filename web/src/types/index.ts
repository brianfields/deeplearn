/**
 * Core TypeScript types and interfaces for the Learning Platform
 *
 * This file contains all the shared types used throughout the application.
 * When adding new types, ensure they are:
 * 1. Well-documented with JSDoc comments
 * 2. Exported for use in other modules
 * 3. Follow naming conventions (PascalCase for types/interfaces)
 */

// ================================
// Core Domain Types
// ================================

/**
 * Learning path represents a structured course on a specific topic
 */
export interface LearningPath {
  id: string
  topic_name: string
  description: string
  topics: Topic[]
  current_topic_index: number
  estimated_total_hours: number
  created_at?: string
}

/**
 * Summary version of learning path for list views
 */
export interface LearningPathSummary {
  id: string
  topic_name: string
  description: string
  total_topics: number
  progress_count: number
  created_at: string
  estimated_total_hours: number
}

/**
 * Individual topic within a learning path
 */
export interface Topic {
  id: string
  title: string
  description: string
  learning_objectives: string[]
  estimated_duration: number
  difficulty_level: number
  position: number
  status: TopicStatus
}

/**
 * Status of a topic's completion
 */
export type TopicStatus = 'not_started' | 'in_progress' | 'completed' | 'mastery'

/**
 * User's skill level options
 */
export type UserLevel = 'beginner' | 'intermediate' | 'advanced'

// ================================
// Conversation Types
// ================================

/**
 * A conversation session with the AI tutor
 */
export interface ConversationSession {
  session_id: string
  ai_message: string
  conversation_state: ConversationState
  topic_title: string
  message_history?: ChatMessage[]
}

/**
 * States of a conversation session
 */
export type ConversationState = 'introduction' | 'exploration' | 'practice' | 'assessment' | 'completed'

/**
 * Individual message in a conversation
 */
export interface ChatMessage {
  role: MessageRole
  content: string
  timestamp: string
}

/**
 * Message sender role
 */
export type MessageRole = 'user' | 'assistant' | 'system'

/**
 * Real-time WebSocket message types
 */
export interface WebSocketMessage {
  type: WebSocketMessageType
  message?: ChatMessage
  progress?: ProgressUpdate
  state?: SessionState
  error?: string
}

/**
 * WebSocket message type discriminator
 */
export type WebSocketMessageType = 'chat_message' | 'progress_update' | 'session_state' | 'error'

// ================================
// Progress & Analytics Types
// ================================

/**
 * Overall learning progress across all paths
 */
export interface Progress {
  learning_paths: LearningPathProgress[]
  overall_progress: OverallProgress
  total_paths: number
  completed_paths: number
}

/**
 * Progress for a specific learning path
 */
export interface LearningPathProgress {
  id: string
  topic_name: string
  progress: number
  current_topic: string | null
}

/**
 * Overall learning statistics
 */
export interface OverallProgress {
  understanding_level: number
  engagement_score: number
  concepts_covered: number
  concepts_mastered: number
}

/**
 * Real-time progress updates from WebSocket
 */
export interface ProgressUpdate {
  understanding_level: number
  engagement_score: number
  objectives_covered: string[]
  topic_title?: string
  learning_objectives: LearningObjective[]
  key_concepts: KeyConcept[]
  sub_topics: SubTopic[]
}

/**
 * Learning objective with completion status
 */
export interface LearningObjective {
  text: string
  status: ObjectiveStatus
}

/**
 * Status of learning objective completion
 */
export type ObjectiveStatus = 'not_started' | 'introduced' | 'mastered'

/**
 * Key concept with understanding status
 */
export interface KeyConcept {
  name: string
  status: ConceptStatus
  definition?: string
}

/**
 * Status of concept understanding
 */
export type ConceptStatus = 'not_covered' | 'introduced' | 'mastered'

/**
 * Sub-topic with progress tracking
 */
export interface SubTopic {
  name: string
  status: SubTopicStatus
  progress_percentage: number
}

/**
 * Status of sub-topic completion
 */
export type SubTopicStatus = 'upcoming' | 'current' | 'completed'

/**
 * Session state information for debugging and transparency
 */
export interface SessionState {
  phase: ConversationState
  last_strategy: TeachingStrategy | null
  session_duration_minutes: number
  confusion_level: number
  learning_velocity: number
  needs_encouragement: boolean
  strategy_confidence: number
  strategy_reasoning: string
  available_strategies: TeachingStrategy[]
  performance_history: PerformanceEntry[]
}

/**
 * AI tutor teaching strategies
 */
export type TeachingStrategy =
  | 'direct_instruction'
  | 'socratic_inquiry'
  | 'guided_practice'
  | 'assessment'
  | 'encouragement'

/**
 * Performance tracking entry
 */
export interface PerformanceEntry {
  timestamp: string
  metric: string
  value: number
}

// ================================
// API & Error Types
// ================================

/**
 * Standard API response wrapper
 */
export interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
}

/**
 * API error response
 */
export interface ApiError {
  message: string
  status: number
  code?: string
  details?: unknown
}

/**
 * Request to create a new learning path
 */
export interface CreateLearningPathRequest {
  topic: string
  user_level: UserLevel
}

/**
 * Health check response
 */
export interface HealthCheck {
  status: string
  timestamp: string
  services: Record<string, boolean>
}

// ================================
// UI & Component Types
// ================================

/**
 * Generic loading state
 */
export interface LoadingState {
  isLoading: boolean
  error: string | null
}

/**
 * Async operation result
 */
export interface AsyncResult<T> extends LoadingState {
  data: T | null
}

/**
 * Form validation error
 */
export interface ValidationError {
  field: string
  message: string
}

/**
 * Modal props interface
 */
export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
}

/**
 * Search and filter options
 */
export interface SearchFilters {
  searchTerm: string
  status?: TopicStatus
  difficulty?: number
  sortBy?: SortOption
}

/**
 * Sorting options for lists
 */
export type SortOption = 'name' | 'created_date' | 'progress' | 'difficulty'

// ================================
// Utility Types
// ================================

/**
 * Make all properties of T optional
 */
export type Partial<T> = {
  [P in keyof T]?: T[P]
}

/**
 * Pick specific properties from T
 */
export type Pick<T, K extends keyof T> = {
  [P in K]: T[P]
}

/**
 * Omit specific properties from T
 */
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>

/**
 * Function that returns void
 */
export type VoidFunction = () => void

/**
 * Function that takes a parameter and returns void
 */
export type Callback<T> = (value: T) => void

/**
 * Async function type
 */
export type AsyncFunction<T = void> = () => Promise<T>

// ================================
// Configuration Types
// ================================

/**
 * Application configuration
 */
export interface AppConfig {
  apiUrl: string
  wsUrl: string
  enableDebug: boolean
  defaultUserLevel: UserLevel
}

/**
 * Feature flags for conditional functionality
 */
export interface FeatureFlags {
  enableProgressAnalytics: boolean
  enableVoiceInterface: boolean
  enableCollaborativeLearning: boolean
}