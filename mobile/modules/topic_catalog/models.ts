/**
 * Topic Catalog Models
 *
 * DTOs and types for topic browsing and discovery.
 * Matches backend/modules/topic_catalog/service.py DTOs.
 */

// ================================
// Backend API Wire Types (Private)
// ================================

interface ApiTopicSummary {
  id: string;
  title: string;
  core_concept: string;
  user_level: string;
  learning_objectives: string[];
  key_concepts: string[];
  component_count: number;
}

interface ApiBrowseTopicsResponse {
  topics: ApiTopicSummary[];
  total: number;
}

interface ApiTopicDetail {
  id: string;
  title: string;
  core_concept: string;
  user_level: string;
  learning_objectives: string[];
  key_concepts: string[];
  components: any[];
  created_at: string;
  component_count: number;
}

// ================================
// Frontend DTOs (Public)
// ================================

export interface TopicSummary {
  readonly id: string;
  readonly title: string;
  readonly coreConcept: string;
  readonly userLevel: 'beginner' | 'intermediate' | 'advanced';
  readonly learningObjectives: string[];
  readonly keyConcepts: string[];
  readonly componentCount: number;
  readonly estimatedDuration: number; // Calculated from component count
  readonly isReadyForLearning: boolean; // Calculated from component count
  readonly createdAt?: string;
  readonly updatedAt?: string;
  readonly difficultyLevel: string; // Formatted user level
  readonly durationDisplay: string; // Formatted duration
  readonly readinessStatus: string; // Formatted readiness
  readonly tags: string[]; // Derived from key concepts
}

export interface TopicDetail {
  readonly id: string;
  readonly title: string;
  readonly coreConcept: string;
  readonly userLevel: 'beginner' | 'intermediate' | 'advanced';
  readonly learningObjectives: string[];
  readonly keyConcepts: string[];
  readonly components: any[];
  readonly componentCount: number;
  readonly createdAt: string;
  readonly estimatedDuration: number;
  readonly isReadyForLearning: boolean;
  readonly difficultyLevel: string;
  readonly durationDisplay: string;
  readonly readinessStatus: string;
  readonly tags: string[];
}

export interface BrowseTopicsResponse {
  readonly topics: TopicSummary[];
  readonly total: number;
  readonly query?: string;
  readonly filters: TopicFilters;
  readonly pagination: PaginationInfo;
}

// ================================
// Filter and Search Types
// ================================

export interface TopicFilters {
  readonly query?: string;
  readonly userLevel?: 'beginner' | 'intermediate' | 'advanced';
  readonly minDuration?: number;
  readonly maxDuration?: number;
  readonly readyOnly?: boolean;
}

export interface TopicSortOptions {
  readonly sortBy: 'relevance' | 'duration' | 'userLevel' | 'title';
  readonly sortOrder: 'asc' | 'desc';
}

export interface PaginationInfo {
  readonly limit: number;
  readonly offset: number;
  readonly hasMore: boolean;
}

// ================================
// Request/Response Types
// ================================

export interface SearchTopicsRequest {
  readonly query?: string;
  readonly userLevel?: 'beginner' | 'intermediate' | 'advanced';
  readonly minDuration?: number;
  readonly maxDuration?: number;
  readonly readyOnly?: boolean;
  readonly limit?: number;
  readonly offset?: number;
}

export interface CatalogStatistics {
  readonly totalTopics: number;
  readonly topicsByUserLevel: Record<string, number>;
  readonly topicsByReadiness: Record<string, number>;
  readonly averageDuration: number;
  readonly durationDistribution: Record<string, number>;
}

// ================================
// Error Types
// ================================

export interface TopicCatalogError {
  readonly message: string;
  readonly code?: string;
  readonly statusCode?: number;
  readonly details?: any;
}

// ================================
// Utility Functions for DTOs
// ================================

/**
 * Convert API TopicSummary to frontend DTO
 */
export function toTopicSummaryDTO(api: ApiTopicSummary): TopicSummary {
  const estimatedDuration = Math.max(5, api.component_count * 3); // 3 min per component, min 5 min
  const isReadyForLearning = api.component_count > 0;

  return {
    id: api.id,
    title: api.title,
    coreConcept: api.core_concept,
    userLevel: api.user_level as 'beginner' | 'intermediate' | 'advanced',
    learningObjectives: api.learning_objectives,
    keyConcepts: api.key_concepts,
    componentCount: api.component_count,
    estimatedDuration,
    isReadyForLearning,
    difficultyLevel: formatDifficultyLevel(api.user_level),
    durationDisplay: formatDuration(estimatedDuration),
    readinessStatus: formatReadinessStatus(
      isReadyForLearning,
      api.component_count
    ),
    tags: api.key_concepts.slice(0, 3), // Use first 3 key concepts as tags
  };
}

/**
 * Convert API TopicDetail to frontend DTO
 */
export function toTopicDetailDTO(api: ApiTopicDetail): TopicDetail {
  const estimatedDuration = Math.max(5, api.component_count * 3);
  const isReadyForLearning = api.component_count > 0;

  return {
    id: api.id,
    title: api.title,
    coreConcept: api.core_concept,
    userLevel: api.user_level as 'beginner' | 'intermediate' | 'advanced',
    learningObjectives: api.learning_objectives,
    keyConcepts: api.key_concepts,
    components: api.components,
    componentCount: api.component_count,
    createdAt: api.created_at,
    estimatedDuration,
    isReadyForLearning,
    difficultyLevel: formatDifficultyLevel(api.user_level),
    durationDisplay: formatDuration(estimatedDuration),
    readinessStatus: formatReadinessStatus(
      isReadyForLearning,
      api.component_count
    ),
    tags: api.key_concepts.slice(0, 3),
  };
}

/**
 * Convert API BrowseTopicsResponse to frontend DTO
 */
export function toBrowseTopicsResponseDTO(
  api: ApiBrowseTopicsResponse,
  filters: TopicFilters = {},
  pagination: Omit<PaginationInfo, 'hasMore'> = { limit: 100, offset: 0 }
): BrowseTopicsResponse {
  return {
    topics: api.topics.map(toTopicSummaryDTO),
    total: api.total,
    filters,
    pagination: {
      ...pagination,
      hasMore: pagination.offset + pagination.limit < api.total,
    },
  };
}

// ================================
// Helper Functions
// ================================

function formatDifficultyLevel(userLevel: string): string {
  const levelMap: Record<string, string> = {
    beginner: 'Beginner',
    intermediate: 'Intermediate',
    advanced: 'Advanced',
  };
  return levelMap[userLevel] || 'Unknown';
}

function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes} min`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  if (remainingMinutes === 0) {
    return `${hours} hr`;
  }

  return `${hours} hr ${remainingMinutes} min`;
}

function formatReadinessStatus(
  isReady: boolean,
  componentCount: number
): string {
  if (isReady) {
    return 'Ready';
  } else if (componentCount > 0) {
    return 'In Progress';
  } else {
    return 'Draft';
  }
}
