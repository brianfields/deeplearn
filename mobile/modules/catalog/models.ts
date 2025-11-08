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
  learner_level: string;
  learning_objectives: string[];
  key_concepts: string[];
  exercise_count: number;
  has_podcast?: boolean;
  podcast_duration_seconds?: number | null;
  podcast_voice?: string | null;
}

interface ApiBrowseLessonsResponse {
  lessons: ApiLessonSummary[];
  total: number;
}

interface ApiLessonDetail {
  id: string;
  title: string;
  learner_level: string;
  learning_objectives: string[];
  key_concepts: string[];
  mini_lesson: string;
  exercises: any[];
  glossary_terms: any[];
  created_at: string;
  exercise_count: number;
  unit_id?: string | null;
  podcast_transcript?: string | null;
  podcast_audio_url?: string | null;
  podcast_duration_seconds?: number | null;
  podcast_voice?: string | null;
  podcast_generated_at?: string | null;
  has_podcast?: boolean;
}

// ================================
// Frontend DTOs (Public)
// ================================

export interface LessonSummary {
  readonly id: string;
  readonly title: string;
  readonly learnerLevel: 'beginner' | 'intermediate' | 'advanced';
  readonly learningObjectives: string[];
  readonly keyConcepts: string[];
  readonly componentCount: number;
  readonly estimatedDuration: number; // Calculated from component count
  readonly isReadyForLearning: boolean; // Calculated from component count
  readonly createdAt?: string;
  readonly updatedAt?: string;
  readonly learnerLevelLabel: string; // Formatted learner level
  readonly durationDisplay: string; // Formatted duration
  readonly readinessStatus: string; // Formatted readiness
  readonly tags: string[]; // Derived from key concepts
  readonly hasPodcast: boolean;
  readonly podcastDurationSeconds: number | null;
  readonly podcastVoice: string | null;
}

export interface LessonDetail {
  readonly id: string;
  readonly title: string;
  readonly learnerLevel: 'beginner' | 'intermediate' | 'advanced';
  readonly learningObjectives: string[];
  readonly keyConcepts: string[];
  readonly miniLesson: string;
  readonly exercises: LessonExercise[];
  readonly glossaryTerms: any[];
  readonly exerciseCount: number;
  readonly createdAt: string;
  readonly estimatedDuration: number;
  readonly isReadyForLearning: boolean;
  readonly learnerLevelLabel: string;
  readonly durationDisplay: string;
  readonly readinessStatus: string;
  readonly tags: string[];
  readonly unitId?: string | null;
  readonly podcastTranscript?: string | null;
  readonly podcastAudioUrl?: string | null;
  readonly podcastDurationSeconds?: number | null;
  readonly podcastVoice?: string | null;
  readonly podcastGeneratedAt?: string | null;
  readonly hasPodcast: boolean;
}

export interface LessonMCQOption {
  readonly label: string;
  readonly text: string;
  readonly rationale_right?: string;
  readonly rationale_wrong?: string;
  readonly option_id?: string;
}

export interface LessonMCQAnswerKey {
  readonly label: string;
  readonly option_id?: string;
  readonly rationale_right?: string;
}

export interface LessonMCQExercise {
  readonly exercise_type: 'mcq';
  readonly id: string;
  readonly stem: string;
  readonly options: LessonMCQOption[];
  readonly answer_key: LessonMCQAnswerKey;
  readonly lo_id?: string;
  readonly title?: string;
  readonly difficulty?: string;
}

export interface LessonWrongAnswer {
  readonly answer: string;
  readonly explanation: string;
  readonly misconception_ids: string[];
}

export interface LessonShortAnswerExercise {
  readonly exercise_type: 'short_answer';
  readonly id: string;
  readonly stem: string;
  readonly canonical_answer: string;
  readonly acceptable_answers: string[];
  readonly wrong_answers: LessonWrongAnswer[];
  readonly explanation_correct: string;
  readonly lo_id?: string;
  readonly title?: string;
  readonly difficulty?: string;
}

export type LessonExercise = LessonMCQExercise | LessonShortAnswerExercise;

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
  readonly learnerLevel?: 'beginner' | 'intermediate' | 'advanced';
  readonly minDuration?: number;
  readonly maxDuration?: number;
  readonly readyOnly?: boolean;
}

export interface LessonSortOptions {
  readonly sortBy: 'relevance' | 'duration' | 'learnerLevel' | 'title';
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
  readonly learnerLevel?: 'beginner' | 'intermediate' | 'advanced';
  readonly minDuration?: number;
  readonly maxDuration?: number;
  readonly readyOnly?: boolean;
  readonly limit?: number;
  readonly offset?: number;
}

export interface CatalogStatistics {
  readonly totalLessons: number;
  readonly lessonsByLearnerLevel: Record<string, number>;
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
    learnerLevel: api.learner_level as 'beginner' | 'intermediate' | 'advanced',
    learningObjectives: api.learning_objectives,
    keyConcepts: api.key_concepts,
    componentCount: api.exercise_count, // kept for compatibility; represents exercises
    estimatedDuration,
    isReadyForLearning,
    learnerLevelLabel: formatLearnerLevel(api.learner_level),
    durationDisplay: formatDuration(estimatedDuration),
    readinessStatus: formatReadinessStatus(
      isReadyForLearning,
      api.exercise_count
    ),
    tags: api.key_concepts.slice(0, 3), // Use first 3 key concepts as tags
    hasPodcast: Boolean(api.has_podcast),
    podcastDurationSeconds: api.podcast_duration_seconds ?? null,
    podcastVoice: api.podcast_voice ?? null,
  };
}

/**
 * Convert API LessonDetail to frontend DTO
 */
export function toLessonDetailDTO(api: ApiLessonDetail): LessonDetail {
  const estimatedDuration = Math.max(5, api.exercise_count * 3);
  const isReadyForLearning = api.exercise_count > 0;

  // Debug logging
  console.log('[toLessonDetailDTO] API response:', {
    lessonId: api.id,
    title: api.title,
    exerciseCount: api.exercise_count,
    exercisesArrayLength: api.exercises?.length ?? 0,
    hasExercises: Array.isArray(api.exercises),
    firstExercise: api.exercises?.[0],
  });

  const exercises = Array.isArray(api.exercises)
    ? api.exercises
        .map((exercise, index) => mapLessonExercise(exercise, index))
        .filter((exercise): exercise is LessonExercise => exercise !== null)
    : [];

  // Debug logging after mapping
  console.log('[toLessonDetailDTO] After mapping:', {
    mappedCount: exercises.length,
    types: exercises.map(e => e.exercise_type),
  });

  return {
    id: api.id,
    title: api.title,
    learnerLevel: api.learner_level as 'beginner' | 'intermediate' | 'advanced',
    learningObjectives: api.learning_objectives,
    keyConcepts: api.key_concepts,
    miniLesson: api.mini_lesson,
    exercises,
    glossaryTerms: api.glossary_terms,
    exerciseCount: api.exercise_count,
    createdAt: api.created_at,
    estimatedDuration,
    isReadyForLearning,
    learnerLevelLabel: formatLearnerLevel(api.learner_level),
    durationDisplay: formatDuration(estimatedDuration),
    readinessStatus: formatReadinessStatus(
      isReadyForLearning,
      api.exercise_count
    ),
    tags: api.key_concepts.slice(0, 3),
    unitId: api.unit_id ?? null,
    podcastTranscript: api.podcast_transcript ?? null,
    podcastAudioUrl: api.podcast_audio_url ?? null,
    podcastDurationSeconds: api.podcast_duration_seconds ?? null,
    podcastVoice: api.podcast_voice ?? null,
    podcastGeneratedAt: api.podcast_generated_at ?? null,
    hasPodcast: Boolean(api.has_podcast),
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

function formatLearnerLevel(learnerLevel: string): string {
  const levelMap: Record<string, string> = {
    beginner: 'Beginner',
    intermediate: 'Intermediate',
    advanced: 'Advanced',
  };
  return levelMap[learnerLevel] || 'Unknown';
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

// Units live in the content module; types are re-exported via catalog/public.ts.

function mapLessonExercise(
  exercise: any,
  index: number
): LessonExercise | null {
  if (!exercise || typeof exercise !== 'object') {
    return null;
  }

  const id =
    typeof exercise.id === 'string' && exercise.id.trim().length > 0
      ? exercise.id
      : `exercise-${index}`;
  const loId =
    typeof exercise.lo_id === 'string' && exercise.lo_id.trim().length > 0
      ? exercise.lo_id
      : undefined;
  const title =
    typeof exercise.title === 'string' && exercise.title.trim().length > 0
      ? exercise.title
      : undefined;
  const difficulty =
    typeof exercise.difficulty === 'string' &&
    exercise.difficulty.trim().length > 0
      ? exercise.difficulty
      : undefined;

  if (exercise.exercise_type === 'mcq') {
    const options = Array.isArray(exercise.options)
      ? exercise.options.map(
          (option: any): LessonMCQOption => ({
            label: typeof option?.label === 'string' ? option.label : '',
            text: typeof option?.text === 'string' ? option.text : '',
            rationale_right:
              typeof option?.rationale_right === 'string'
                ? option.rationale_right
                : undefined,
            rationale_wrong:
              typeof option?.rationale_wrong === 'string'
                ? option.rationale_wrong
                : undefined,
            option_id:
              typeof option?.option_id === 'string'
                ? option.option_id
                : undefined,
          })
        )
      : [];

    const answerKeyRaw = exercise.answer_key ?? {};
    const answerKey: LessonMCQAnswerKey = {
      label:
        typeof answerKeyRaw.label === 'string' && answerKeyRaw.label
          ? answerKeyRaw.label
          : 'A',
      option_id:
        typeof answerKeyRaw.option_id === 'string'
          ? answerKeyRaw.option_id
          : undefined,
      rationale_right:
        typeof answerKeyRaw.rationale_right === 'string'
          ? answerKeyRaw.rationale_right
          : undefined,
    };

    return {
      exercise_type: 'mcq',
      id,
      stem: typeof exercise.stem === 'string' ? exercise.stem : '',
      options,
      answer_key: answerKey,
      lo_id: loId,
      title,
      difficulty,
    };
  }

  if (exercise.exercise_type === 'short_answer') {
    const wrongAnswers = Array.isArray(exercise.wrong_answers)
      ? exercise.wrong_answers.map(
          (wrong: any): LessonWrongAnswer => ({
            answer: typeof wrong?.answer === 'string' ? wrong.answer : '',
            explanation:
              typeof wrong?.rationale_wrong === 'string'
                ? wrong.rationale_wrong
                : typeof wrong?.explanation === 'string'
                  ? wrong.explanation
                  : '',
            misconception_ids: Array.isArray(wrong?.misconception_ids)
              ? wrong.misconception_ids.map((idValue: any) => String(idValue))
              : [],
          })
        )
      : [];

    return {
      exercise_type: 'short_answer',
      id,
      stem: typeof exercise.stem === 'string' ? exercise.stem : '',
      canonical_answer:
        typeof exercise.canonical_answer === 'string'
          ? exercise.canonical_answer
          : '',
      acceptable_answers: Array.isArray(exercise.acceptable_answers)
        ? exercise.acceptable_answers.map((answer: any) => String(answer))
        : [],
      wrong_answers: wrongAnswers,
      explanation_correct:
        typeof exercise.explanation_correct === 'string'
          ? exercise.explanation_correct
          : '',
      lo_id: loId,
      title,
      difficulty,
    };
  }

  return null;
}
