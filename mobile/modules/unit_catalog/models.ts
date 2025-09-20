/**
 * Lesson Catalog Models
 *
 * DTOs and types for lesson browsing and discovery.
 * Matches backend/modules/lesson_catalog/service.py DTOs.
 */

// ================================
// Backend API Wire Types (Private)
// ================================

interface ApiLessonSummary {
  id: string;
  title: string;
  core_concept: string;
  user_level: string;
  learning_objectives: string[];
  key_concepts: string[];
  exercise_count: number;
}

interface ApiBrowseLessonsResponse {
  lessons: ApiLessonSummary[];
  total: number;
}

interface ApiLessonDetail {
  id: string;
  title: string;
  core_concept: string;
  user_level: string;
  learning_objectives: string[];
  key_concepts: string[];
  didactic_snippet: any;
  exercises: any[];
  glossary_terms: any[];
  created_at: string;
  exercise_count: number;
}

// ================================
// Frontend DTOs (Public)
// ================================

export interface LessonSummary {
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

export interface LessonDetail {
  readonly id: string;
  readonly title: string;
  readonly coreConcept: string;
  readonly userLevel: 'beginner' | 'intermediate' | 'advanced';
  readonly learningObjectives: string[];
  readonly keyConcepts: string[];
  readonly didacticSnippet: any;
  readonly exercises: any[];
  readonly glossaryTerms: any[];
  readonly exerciseCount: number;
  readonly createdAt: string;
  readonly estimatedDuration: number;
  readonly isReadyForLearning: boolean;
  readonly difficultyLevel: string;
  readonly durationDisplay: string;
  readonly readinessStatus: string;
  readonly tags: string[];
}

export interface BrowseLessonsResponse {
  readonly lessons: LessonSummary[];
  readonly total: number;
  readonly query?: string;
  readonly filters: LessonFilters;
  readonly pagination: PaginationInfo;
}

// ================================
// Filter and Search Types
// ================================

export interface LessonFilters {
  readonly query?: string;
  readonly userLevel?: 'beginner' | 'intermediate' | 'advanced';
  readonly minDuration?: number;
  readonly maxDuration?: number;
  readonly readyOnly?: boolean;
}

export interface LessonSortOptions {
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

export interface SearchLessonsRequest {
  readonly query?: string;
  readonly userLevel?: 'beginner' | 'intermediate' | 'advanced';
  readonly minDuration?: number;
  readonly maxDuration?: number;
  readonly readyOnly?: boolean;
  readonly limit?: number;
  readonly offset?: number;
}

export interface CatalogStatistics {
  readonly totalLessons: number;
  readonly lessonsByUserLevel: Record<string, number>;
  readonly lessonsByReadiness: Record<string, number>;
  readonly averageDuration: number;
  readonly durationDistribution: Record<string, number>;
}

// ================================
// Error Types
// ================================

export interface LessonCatalogError {
  readonly message: string;
  readonly code?: string;
  readonly statusCode?: number;
  readonly details?: any;
}

// ================================
// Utility Functions for DTOs
// ================================

/**
 * Convert API LessonSummary to frontend DTO
 */
export function toLessonSummaryDTO(api: ApiLessonSummary): LessonSummary {
  const estimatedDuration = Math.max(5, api.exercise_count * 3); // 3 min per exercise, min 5 min
  const isReadyForLearning = api.exercise_count > 0;

  return {
    id: api.id,
    title: api.title,
    coreConcept: api.core_concept,
    userLevel: api.user_level as 'beginner' | 'intermediate' | 'advanced',
    learningObjectives: api.learning_objectives,
    keyConcepts: api.key_concepts,
    componentCount: api.exercise_count, // kept for compatibility; represents exercises
    estimatedDuration,
    isReadyForLearning,
    difficultyLevel: formatDifficultyLevel(api.user_level),
    durationDisplay: formatDuration(estimatedDuration),
    readinessStatus: formatReadinessStatus(
      isReadyForLearning,
      api.exercise_count
    ),
    tags: api.key_concepts.slice(0, 3), // Use first 3 key concepts as tags
  };
}

/**
 * Convert API LessonDetail to frontend DTO
 */
export function toLessonDetailDTO(api: ApiLessonDetail): LessonDetail {
  const estimatedDuration = Math.max(5, api.exercise_count * 3);
  const isReadyForLearning = api.exercise_count > 0;

  return {
    id: api.id,
    title: api.title,
    coreConcept: api.core_concept,
    userLevel: api.user_level as 'beginner' | 'intermediate' | 'advanced',
    learningObjectives: api.learning_objectives,
    keyConcepts: api.key_concepts,
    didacticSnippet: api.didactic_snippet,
    exercises: api.exercises,
    glossaryTerms: api.glossary_terms,
    exerciseCount: api.exercise_count,
    createdAt: api.created_at,
    estimatedDuration,
    isReadyForLearning,
    difficultyLevel: formatDifficultyLevel(api.user_level),
    durationDisplay: formatDuration(estimatedDuration),
    readinessStatus: formatReadinessStatus(
      isReadyForLearning,
      api.exercise_count
    ),
    tags: api.key_concepts.slice(0, 3),
  };
}

/**
 * Convert API BrowseLessonsResponse to frontend DTO
 */
export function toBrowseLessonsResponseDTO(
  api: ApiBrowseLessonsResponse,
  filters: LessonFilters = {},
  pagination: Omit<PaginationInfo, 'hasMore'> = { limit: 100, offset: 0 }
): BrowseLessonsResponse {
  return {
    lessons: api.lessons.map(toLessonSummaryDTO),
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

// ================================
// Units (DTOs and Wire Types)
// ================================

// Backend API Wire Types (private to module)
export interface ApiUnitSummary {
  id: string;
  title: string;
  description: string | null;
  difficulty: string;
  lesson_count: number;
}

export interface ApiUnitDetail {
  id: string;
  title: string;
  description: string | null;
  difficulty: string;
  lesson_order: string[];
  lessons: Array<{
    id: string;
    title: string;
    core_concept: string;
    user_level: string;
    learning_objectives: string[];
    key_concepts: string[];
    exercise_count: number;
  }>;
}

export type UnitId = string;
export type Difficulty = 'beginner' | 'intermediate' | 'advanced';

export interface Unit {
  readonly id: UnitId;
  readonly title: string;
  readonly description?: string | null;
  readonly difficulty: Difficulty;
  readonly lessonCount: number;
  readonly difficultyLabel: string;
}

export interface UnitDetail {
  readonly id: UnitId;
  readonly title: string;
  readonly description?: string | null;
  readonly difficulty: Difficulty;
  readonly lessonIds: string[];
  readonly lessons: LessonSummary[];
}

export interface UnitProgress {
  readonly unitId: UnitId;
  readonly completedLessons: number;
  readonly totalLessons: number;
  readonly progressPercentage: number; // 0-100
}

export function toUnitDTO(api: ApiUnitSummary): Unit {
  const difficulty = (api.difficulty as Difficulty) ?? 'beginner';
  return {
    id: api.id,
    title: api.title,
    description: api.description,
    difficulty,
    lessonCount: api.lesson_count,
    difficultyLabel: formatDifficultyLevel(difficulty),
  };
}

export function toUnitDetailDTO(api: ApiUnitDetail): UnitDetail {
  const difficulty = (api.difficulty as Difficulty) ?? 'beginner';
  return {
    id: api.id,
    title: api.title,
    description: api.description,
    difficulty,
    lessonIds: [...(api.lesson_order ?? [])],
    lessons: api.lessons.map(l =>
      toLessonSummaryDTO({
        id: l.id,
        title: l.title,
        core_concept: l.core_concept,
        user_level: l.user_level,
        learning_objectives: l.learning_objectives,
        key_concepts: l.key_concepts,
        exercise_count: l.exercise_count,
      })
    ),
  };
}
