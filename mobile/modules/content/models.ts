/**
 * Content Module Models
 *
 * DTOs and mappings for unit content surfaces.
 */

import type { CacheMode, DownloadStatus } from '../offline_cache/public';
import type { ResourceSummary } from '../resource/public';

// Backend API wire types (private to module)
export interface ApiUnitLearningObjective {
  id: string;
  title: string;
  description: string;
}

export interface ApiUnitSummary {
  id: string;
  title: string;
  description: string | null;
  learner_level: string;
  lesson_count: number;
  target_lesson_count?: number | null;
  generated_from_topic?: boolean;
  status: string;
  creation_progress?: { stage: string; message: string } | null;
  error_message?: string | null;
  user_id?: number | null;
  is_global?: boolean;
  created_at?: string;
  updated_at?: string;
  has_podcast?: boolean;
  podcast_voice?: string | null;
  podcast_duration_seconds?: number | null;
  podcast_audio_url?: string | null;
  podcast_transcript?: string | null;
  art_image_url?: string | null;
  art_image_description?: string | null;
  learning_objectives?: ApiUnitLearningObjective[] | null;
}

export interface ApiUnitDetail {
  id: string;
  title: string;
  description: string | null;
  learner_level: string;
  lesson_order: string[];
  lessons: Array<{
    id: string;
    title: string;
    learner_level: string;
    learning_objective_ids: string[];
    learning_objectives: string[];
    key_concepts: string[];
    exercise_count: number;
    has_podcast?: boolean;
    podcast_voice?: string | null;
    podcast_duration_seconds?: number | null;
    podcast_generated_at?: string | null;
    podcast_audio_url?: string | null;
    podcast_transcript?: string | null;
  }>;
  learning_objectives?: ApiUnitLearningObjective[] | null;
  target_lesson_count?: number | null;
  source_material?: string | null;
  generated_from_topic?: boolean;
  user_id?: number | null;
  is_global?: boolean;
  learning_objective_progress?: Array<{
    objective: string;
    exercises_total: number;
    exercises_correct: number;
    progress_percentage: number;
  }> | null;
  has_podcast?: boolean;
  podcast_voice?: string | null;
  podcast_duration_seconds?: number | null;
  podcast_transcript?: string | null;
  podcast_audio_url?: string | null;
  art_image_url?: string | null;
  art_image_description?: string | null;
}

export type UnitId = string;
export type Difficulty = 'beginner' | 'intermediate' | 'advanced';
export type UnitStatus = 'draft' | 'in_progress' | 'completed' | 'partial' | 'failed';

export interface UnitCreationProgress {
  readonly stage: string;
  readonly message: string;
}

export interface UnitLessonSummary {
  readonly id: string;
  readonly title: string;
  readonly learnerLevel: Difficulty;
  readonly learningObjectiveIds: string[];
  readonly learningObjectives: string[];
  readonly keyConcepts: string[];
  readonly exerciseCount: number;
  readonly componentCount: number;
  readonly isReadyForLearning: boolean;
  readonly estimatedDuration: number;
  readonly learnerLevelLabel: string;
  readonly hasPodcast: boolean;
  readonly podcastVoice: string | null;
  readonly podcastDurationSeconds: number | null;
  readonly podcastGeneratedAt: string | null;
  readonly podcastAudioUrl: string | null;
}

export interface Lesson {
  readonly id: string;
  readonly title: string;
  readonly learnerLevel: Difficulty;
  readonly learningObjectives: string[];
  readonly keyConcepts: string[];
  readonly exerciseCount: number;
  readonly podcastTranscript?: string | null;
  readonly podcastAudioUrl?: string | null;
  readonly podcastDurationSeconds?: number | null;
  readonly podcastVoice?: string | null;
  readonly podcastGeneratedAt?: string | null;
  readonly hasPodcast: boolean;
}

export interface UnitLearningObjective {
  readonly id: string;
  readonly title: string;
  readonly description: string;
}

export interface Unit {
  readonly id: UnitId;
  readonly title: string;
  readonly description?: string | null;
  readonly difficulty: Difficulty;
  readonly lessonCount: number;
  readonly difficultyLabel: string;
  readonly targetLessonCount?: number | null;
  readonly generatedFromTopic?: boolean;
  readonly learningObjectives?: UnitLearningObjective[] | null;
  readonly status: UnitStatus;
  readonly creationProgress?: UnitCreationProgress | null;
  readonly errorMessage?: string | null;
  readonly statusLabel: string;
  readonly isInteractive: boolean;
  readonly progressMessage: string;
  readonly ownerUserId: number | null;
  readonly isGlobal: boolean;
  readonly ownershipLabel: string;
  readonly isOwnedByCurrentUser: boolean;
  readonly hasPodcast: boolean;
  readonly podcastVoice: string | null;
  readonly podcastDurationSeconds: number | null;
  readonly artImageUrl: string | null;
  readonly artImageDescription: string | null;
  readonly cacheMode?: CacheMode;
  readonly downloadStatus?: DownloadStatus;
  readonly downloadedAt?: number | null;
  readonly syncedAt?: number | null;
  readonly createdAt?: string | null;
  readonly updatedAt?: string | null;
}

export interface UnitDetail {
  readonly id: UnitId;
  readonly title: string;
  readonly description?: string | null;
  readonly difficulty: Difficulty;
  readonly lessonIds: string[];
  readonly lessons: UnitLessonSummary[];
  readonly learningObjectives?: UnitLearningObjective[] | null;
  readonly targetLessonCount?: number | null;
  readonly sourceMaterial?: string | null;
  readonly generatedFromTopic?: boolean;
  readonly ownerUserId: number | null;
  readonly isGlobal: boolean;
  readonly ownershipLabel: string;
  readonly isOwnedByCurrentUser: boolean;
  readonly learningObjectiveProgress?: LearningObjectiveProgress[] | null;
  readonly hasPodcast: boolean;
  readonly podcastVoice: string | null;
  readonly podcastDurationSeconds: number | null;
  readonly podcastTranscript: string | null;
  readonly podcastAudioUrl: string | null;
  readonly artImageUrl: string | null;
  readonly artImageDescription: string | null;
  readonly cacheMode?: CacheMode;
  readonly downloadStatus?: DownloadStatus;
  readonly downloadedAt?: number | null;
  readonly syncedAt?: number | null;
  readonly resources: ResourceSummary[];
}

export interface LearningObjectiveProgress {
  readonly objective: string;
  readonly exercisesTotal: number;
  readonly exercisesCorrect: number;
  readonly progressPercentage: number;
}

export interface UnitProgress {
  readonly unitId: UnitId;
  readonly completedLessons: number;
  readonly totalLessons: number;
  readonly progressPercentage: number;
}

export interface UserUnitCollections {
  readonly units: Unit[];
  readonly ownedUnitIds: string[];
}

export interface UpdateUnitSharingRequest {
  readonly isGlobal: boolean;
  readonly actingUserId?: number;
}

export interface AddToMyUnitsRequest {
  readonly userId: number;
  readonly unitId: string;
}

export interface RemoveFromMyUnitsRequest {
  readonly userId: number;
  readonly unitId: string;
}

export interface ContentError {
  readonly message: string;
  readonly code: string;
  readonly statusCode?: number;
  readonly details?: unknown;
}

export function toUnitDTO(
  api: ApiUnitSummary,
  currentUserId?: number | null
): Unit {
  const difficulty = (api.learner_level as Difficulty) ?? 'beginner';
  const status = (api.status as UnitStatus) ?? 'completed';
  const ownerUserId = api.user_id ?? null;
  const isGlobal = Boolean(api.is_global);
  const isOwnedByCurrentUser = Boolean(
    ownerUserId && currentUserId && ownerUserId === currentUserId
  );

  const learningObjectives = mapApiLearningObjectives(api.learning_objectives);

  return {
    id: api.id,
    title: api.title,
    description: api.description,
    difficulty,
    lessonCount: api.lesson_count,
    difficultyLabel: formatLearnerLevel(difficulty),
    targetLessonCount: api.target_lesson_count ?? null,
    generatedFromTopic: !!api.generated_from_topic,
    learningObjectives,
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
    ownerUserId,
    isGlobal,
    ownershipLabel: formatOwnershipLabel(isGlobal, isOwnedByCurrentUser),
    isOwnedByCurrentUser,
    hasPodcast: Boolean(api.has_podcast),
    podcastVoice: api.podcast_voice ?? null,
    podcastDurationSeconds: api.podcast_duration_seconds ?? null,
    artImageUrl: api.art_image_url ?? null,
    artImageDescription: api.art_image_description ?? null,
    createdAt: api.created_at ?? null,
    updatedAt: api.updated_at ?? null,
  };
}

export function toUnitDetailDTO(
  api: ApiUnitDetail,
  currentUserId?: number | null,
  resources: ResourceSummary[] = []
): UnitDetail {
  const difficulty = (api.learner_level as Difficulty) ?? 'beginner';
  const ownerUserId = api.user_id ?? null;
  const isGlobal = Boolean(api.is_global);
  const isOwnedByCurrentUser = Boolean(
    ownerUserId && currentUserId && ownerUserId === currentUserId
  );

  const lessons = Array.isArray(api.lessons) ? api.lessons : [];
  const lessonOrder = Array.isArray(api.lesson_order) ? api.lesson_order : [];
  const lessonIds = lessonOrder.length
    ? [...lessonOrder]
    : lessons.map(lesson => lesson.id);

  const learningObjectives = mapApiLearningObjectives(api.learning_objectives);

  return {
    id: api.id,
    title: api.title,
    description: api.description,
    difficulty,
    lessonIds,
    lessons: lessons.map(toUnitLessonSummaryDTO),
    learningObjectives,
    targetLessonCount: api.target_lesson_count ?? null,
    sourceMaterial: api.source_material ?? null,
    generatedFromTopic: !!api.generated_from_topic,
    ownerUserId,
    isGlobal,
    ownershipLabel: formatOwnershipLabel(isGlobal, isOwnedByCurrentUser),
    isOwnedByCurrentUser,
    learningObjectiveProgress: api.learning_objective_progress
      ? api.learning_objective_progress.map(progress => ({
          objective: progress.objective,
          exercisesTotal: progress.exercises_total,
          exercisesCorrect: progress.exercises_correct,
          progressPercentage: progress.progress_percentage,
        }))
      : null,
    hasPodcast: Boolean(api.has_podcast),
    podcastVoice: api.podcast_voice ?? null,
    podcastDurationSeconds: api.podcast_duration_seconds ?? null,
    podcastTranscript: api.podcast_transcript ?? null,
    podcastAudioUrl: api.podcast_audio_url ?? null,
    artImageUrl: api.art_image_url ?? null,
    artImageDescription: api.art_image_description ?? null,
    resources,
  };
}

function toUnitLessonSummaryDTO(
  lesson: ApiUnitDetail['lessons'][number]
): UnitLessonSummary {
  const learnerLevel = (lesson.learner_level as Difficulty) ?? 'beginner';
  const componentCount = lesson.exercise_count;
  const isReadyForLearning = componentCount > 0;
  const estimatedDuration = Math.max(5, componentCount * 3);
  const hasPodcast =
    typeof lesson.has_podcast === 'boolean'
      ? lesson.has_podcast
      : Boolean(
          lesson.podcast_audio_url ||
            lesson.podcast_duration_seconds ||
            lesson.podcast_voice
        );
  return {
    id: lesson.id,
    title: lesson.title,
    learnerLevel,
    learningObjectiveIds: lesson.learning_objective_ids ?? [],
    learningObjectives: lesson.learning_objectives ?? [],
    keyConcepts: lesson.key_concepts ?? [],
    exerciseCount: componentCount,
    componentCount,
    isReadyForLearning,
    estimatedDuration,
    learnerLevelLabel: formatLearnerLevel(learnerLevel),
    hasPodcast,
    podcastVoice: lesson.podcast_voice ?? null,
    podcastDurationSeconds: lesson.podcast_duration_seconds ?? null,
    podcastGeneratedAt: lesson.podcast_generated_at ?? null,
    podcastAudioUrl: lesson.podcast_audio_url ?? null,
  };
}

function formatLearnerLevel(level: string): string {
  const map: Record<string, string> = {
    beginner: 'Beginner',
    intermediate: 'Intermediate',
    advanced: 'Advanced',
  };
  return map[level] ?? 'Unknown';
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

function formatOwnershipLabel(
  isGlobal: boolean,
  isOwnedByCurrentUser: boolean
): string {
  if (isGlobal) {
    return 'Shared Globally';
  }
  if (isOwnedByCurrentUser) {
    return 'My Unit';
  }
  return 'Personal';
}

function mapApiLearningObjectives(
  raw: ApiUnitLearningObjective[] | null | undefined
): UnitLearningObjective[] | null {
  if (!Array.isArray(raw)) {
    return null;
  }

  const objectives = raw
    .map(objective => normalizeLearningObjective(objective as unknown))
    .filter((value): value is UnitLearningObjective => value !== null);

  return objectives.length > 0 ? objectives : null;
}

function normalizeLearningObjective(
  objective: unknown
): UnitLearningObjective | null {
  if (!objective || typeof objective !== 'object') {
    return null;
  }

  const candidate = objective as Record<string, unknown>;
  const id = typeof candidate.id === 'string' ? candidate.id : null;
  const rawTitle = candidate.title;
  const rawDescription = candidate.description;
  const fallbackText = candidate.text;

  const description =
    typeof rawDescription === 'string' && rawDescription.trim().length > 0
      ? rawDescription
      : typeof fallbackText === 'string' && fallbackText.trim().length > 0
        ? fallbackText
        : null;

  if (!id || !description) {
    return null;
  }

  const title =
    typeof rawTitle === 'string' && rawTitle.trim().length > 0
      ? rawTitle
      : description;

  return {
    id,
    title,
    description,
  };
}
