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

export interface CatalogError {
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

function formatUnitStatusLabel(status: UnitStatus): string {
  const statusMap: Record<UnitStatus, string> = {
    draft: 'Draft',
    in_progress: 'Creating...',
    completed: 'Ready',
    failed: 'Failed',
  };
  return statusMap[status] ?? 'Unknown';
}

function formatUnitProgressMessage(
  status: UnitStatus,
  progress?: { stage: string; message: string } | null,
  errorMessage?: string | null
): string {
  switch (status) {
    case 'draft':
      return 'Unit is being prepared';
    case 'in_progress':
      return progress?.message ?? 'Creating unit content...';
    case 'completed':
      return 'Ready to learn';
    case 'failed':
      return errorMessage ?? 'Creation failed';
    default:
      return 'Unknown status';
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
  // New fields from backend
  target_lesson_count?: number | null;
  generated_from_topic?: boolean;
  // Status tracking fields
  status: string;
  creation_progress?: { stage: string; message: string } | null;
  error_message?: string | null;
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
  // New fields from backend
  learning_objectives?: string[] | null;
  target_lesson_count?: number | null;
  source_material?: string | null;
  generated_from_topic?: boolean;
}

export type UnitId = string;
export type Difficulty = 'beginner' | 'intermediate' | 'advanced';

// Unit status types for creation tracking
export type UnitStatus = 'draft' | 'in_progress' | 'completed' | 'failed';

export interface UnitCreationProgress {
  readonly stage: string;
  readonly message: string;
}

export interface UnitCreationRequest {
  readonly topic: string;
  readonly difficulty: Difficulty;
  readonly targetLessonCount?: number | null;
}

export interface UnitCreationResponse {
  readonly unitId: string;
  readonly status: UnitStatus;
  readonly title: string;
}

export interface Unit {
  readonly id: UnitId;
  readonly title: string;
  readonly description?: string | null;
  readonly difficulty: Difficulty;
  readonly lessonCount: number;
  readonly difficultyLabel: string;
  // New optional fields for richer summaries
  readonly targetLessonCount?: number | null;
  readonly generatedFromTopic?: boolean;
  // Optional LO list when available in summaries (not always provided)
  readonly learningObjectives?: string[] | null;
  // Status tracking fields
  readonly status: UnitStatus;
  readonly creationProgress?: UnitCreationProgress | null;
  readonly errorMessage?: string | null;
  // Computed status display fields
  readonly statusLabel: string;
  readonly isInteractive: boolean; // Can user open/interact with this unit
  readonly progressMessage: string; // User-friendly progress message
}

export interface UnitDetail {
  readonly id: UnitId;
  readonly title: string;
  readonly description?: string | null;
  readonly difficulty: Difficulty;
  readonly lessonIds: string[];
  readonly lessons: LessonSummary[];
  // New unit-level fields surfaced in details
  readonly learningObjectives?: string[] | null;
  readonly targetLessonCount?: number | null;
  readonly sourceMaterial?: string | null;
  readonly generatedFromTopic?: boolean;
}

export interface UnitProgress {
  readonly unitId: UnitId;
  readonly completedLessons: number;
  readonly totalLessons: number;
  readonly progressPercentage: number; // 0-100
}

export function toUnitDTO(api: ApiUnitSummary): Unit {
  const difficulty = (api.difficulty as Difficulty) ?? 'beginner';
  const status = (api.status as UnitStatus) ?? 'completed';

  return {
    id: api.id,
    title: api.title,
    description: api.description,
    difficulty,
    lessonCount: api.lesson_count,
    difficultyLabel: formatDifficultyLevel(difficulty),
    targetLessonCount: api.target_lesson_count ?? null,
    generatedFromTopic: !!api.generated_from_topic,
    status,
    creationProgress: api.creation_progress || null,
    errorMessage: api.error_message || null,
    statusLabel: formatUnitStatusLabel(status),
    isInteractive: status === 'completed',
    progressMessage: formatUnitProgressMessage(
      status,
      api.creation_progress,
      api.error_message
    ),
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
    learningObjectives: api.learning_objectives ?? null,
    targetLessonCount: api.target_lesson_count ?? null,
    sourceMaterial: api.source_material ?? null,
    generatedFromTopic: !!api.generated_from_topic,
  };
}
