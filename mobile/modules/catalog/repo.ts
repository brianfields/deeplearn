/**
 * Lesson Catalog Repository
 *
 * HTTP client for lesson catalog API endpoints.
 * Uses infrastructure module for HTTP requests.
 */

import { infrastructureProvider } from '../infrastructure/public';
import { offlineCacheProvider } from '../offline_cache/public';
import type {
  SearchLessonsRequest,
  CatalogStatistics,
  CatalogError,
  LessonDetail,
} from './models';
import { toLessonDetailDTO } from './models';

// Backend API endpoints
const LESSON_CATALOG_BASE = '/api/v1/catalog';

// API response types (private to repo)
interface ApiBrowseLessonsResponse {
  lessons: Array<{
    id: string;
    title: string;
    learner_level: string;
    learning_objectives: string[];
    key_concepts: string[];
    exercise_count: number;
    has_podcast?: boolean;
    podcast_duration_seconds?: number | null;
    podcast_voice?: string | null;
  }>;
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

export class CatalogRepo {
  private infrastructure = infrastructureProvider();
  private offlineCache = offlineCacheProvider();

  /**
   * Browse lessons with optional filters
   */
  async browseLessons(
    request: SearchLessonsRequest = {}
  ): Promise<ApiBrowseLessonsResponse> {
    try {
      const params = new URLSearchParams();

      if (request.learnerLevel) {
        params.append('learner_level', request.learnerLevel);
      }
      if (request.limit !== undefined) {
        params.append('limit', request.limit.toString());
      }

      const endpoint = `${LESSON_CATALOG_BASE}/?${params.toString()}`;

      const response =
        await this.infrastructure.request<ApiBrowseLessonsResponse>(endpoint, {
          method: 'GET',
        });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to browse lessons');
    }
  }

  /**
   * Get lesson details by ID
   */
  async getLessonDetail(lessonId: string): Promise<ApiLessonDetail> {
    try {
      const endpoint = `${LESSON_CATALOG_BASE}/${lessonId}`;

      const response = await this.infrastructure.request<ApiLessonDetail>(
        endpoint,
        { method: 'GET' }
      );

      return response;
    } catch (error) {
      throw this.handleError(error, `Failed to get lesson ${lessonId}`);
    }
  }

  /**
   * Get lesson detail with offline-first behavior
   */
  async getLesson(lessonId: string): Promise<LessonDetail | null> {
    if (!lessonId?.trim()) {
      return null;
    }

    const cachedLesson = await this.findLessonInOfflineCache(lessonId);
    if (cachedLesson) {
      console.info(`[CatalogRepo] Found lesson ${lessonId} in offline cache`);
      return cachedLesson;
    }

    try {
      const apiResponse = await this.getLessonDetail(lessonId);
      return toLessonDetailDTO(apiResponse);
    } catch (error: any) {
      if (error && typeof error === 'object' && 'statusCode' in error) {
        const statusCode = (error as CatalogError).statusCode;
        if (statusCode === 404) {
          return null;
        }
      }

      throw error;
    }
  }

  /**
   * Search lessons with query and filters
   */
  async searchLessons(
    request: SearchLessonsRequest
  ): Promise<ApiBrowseLessonsResponse> {
    try {
      const params = new URLSearchParams();

      if (request.query) {
        params.append('query', request.query);
      }
      if (request.learnerLevel) {
        params.append('learner_level', request.learnerLevel);
      }
      if (request.minDuration !== undefined) {
        params.append('min_duration', request.minDuration.toString());
      }
      if (request.maxDuration !== undefined) {
        params.append('max_duration', request.maxDuration.toString());
      }
      if (request.readyOnly !== undefined) {
        params.append('ready_only', request.readyOnly.toString());
      }
      if (request.limit !== undefined) {
        params.append('limit', request.limit.toString());
      }
      if (request.offset !== undefined) {
        params.append('offset', request.offset.toString());
      }

      // Use the new search endpoint
      const endpoint = `${LESSON_CATALOG_BASE}/search?${params.toString()}`;

      const response =
        await this.infrastructure.request<ApiBrowseLessonsResponse>(endpoint, {
          method: 'GET',
        });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to search lessons');
    }
  }

  /**
   * Get popular lessons
   */
  async getPopularLessons(
    limit: number = 10
  ): Promise<ApiBrowseLessonsResponse> {
    try {
      const params = new URLSearchParams();
      params.append('limit', limit.toString());

      // Use the new popular endpoint
      const endpoint = `${LESSON_CATALOG_BASE}/popular?${params.toString()}`;

      const lessons = await this.infrastructure.request<
        Array<{
          id: string;
          title: string;
          learner_level: string;
          learning_objectives: string[];
          key_concepts: string[];
          exercise_count: number;
        }>
      >(endpoint, {
        method: 'GET',
      });

      // Convert to browse response format
      return {
        lessons,
        total: lessons.length,
      };
    } catch (error) {
      throw this.handleError(error, 'Failed to get popular lessons');
    }
  }

  /**
   * Get catalog statistics
   */
  async getCatalogStatistics(): Promise<CatalogStatistics> {
    try {
      const endpoint = `${LESSON_CATALOG_BASE}/statistics`;

      const response = await this.infrastructure.request<{
        total_lessons: number;
        lessons_by_learner_level: Record<string, number>;
        lessons_by_readiness: Record<string, number>;
        average_duration: number;
        duration_distribution: Record<string, number>;
      }>(endpoint, {
        method: 'GET',
      });

      // Convert snake_case to camelCase
      return {
        totalLessons: response.total_lessons,
        lessonsByLearnerLevel: response.lessons_by_learner_level,
        lessonsByReadiness: response.lessons_by_readiness,
        averageDuration: response.average_duration,
        durationDistribution: response.duration_distribution,
      };
    } catch (error) {
      throw this.handleError(error, 'Failed to get catalog statistics');
    }
  }

  /**
   * Refresh catalog
   */
  async refreshCatalog(): Promise<{
    refreshedLessons: number;
    totalLessons: number;
    timestamp: string;
  }> {
    try {
      const endpoint = `${LESSON_CATALOG_BASE}/refresh`;

      const response = await this.infrastructure.request<{
        refreshed_lessons: number;
        total_lessons: number;
        timestamp: string;
      }>(endpoint, {
        method: 'POST',
      });

      // Convert snake_case to camelCase
      return {
        refreshedLessons: response.refreshed_lessons,
        totalLessons: response.total_lessons,
        timestamp: response.timestamp,
      };
    } catch (error) {
      throw this.handleError(error, 'Failed to refresh catalog');
    }
  }

  /**
   * Check health
   */
  async checkHealth(): Promise<boolean> {
    try {
      const networkStatus = this.infrastructure.getNetworkStatus();
      return networkStatus.isConnected;
    } catch (error) {
      console.warn('[CatalogRepo] Health check failed:', error);
      return false;
    }
  }

  private async findLessonInOfflineCache(
    lessonId: string
  ): Promise<LessonDetail | null> {
    try {
      const units = await this.offlineCache.listUnits();

      for (const unit of units) {
        const unitDetail = await this.offlineCache.getUnitDetail(unit.id);
        if (!unitDetail) {
          continue;
        }

        const canonicalObjectivesRaw =
          unitDetail.unitPayload?.learning_objectives ?? null;
        const canonicalObjectives = Array.isArray(canonicalObjectivesRaw)
          ? canonicalObjectivesRaw
              .map(item => {
                if (typeof item === 'string') {
                  return { id: item, text: item };
                }
                if (item && typeof item === 'object') {
                  const id =
                    typeof (item as { id?: unknown }).id === 'string'
                      ? ((item as { id?: string }).id as string)
                      : typeof (item as { lo_id?: unknown }).lo_id === 'string'
                        ? ((item as { lo_id?: string }).lo_id as string)
                        : null;
                  const title =
                    typeof (item as { title?: unknown }).title === 'string'
                      ? ((item as { title?: string }).title as string)
                      : typeof (item as { text?: unknown }).text === 'string'
                        ? ((item as { text?: string }).text as string)
                        : null;
                  const description =
                    typeof (item as { description?: unknown }).description ===
                    'string'
                      ? ((item as { description?: string })
                          .description as string)
                      : typeof (item as { text?: unknown }).text === 'string'
                        ? ((item as { text?: string }).text as string)
                        : typeof (item as { objective?: unknown }).objective ===
                            'string'
                          ? ((item as { objective?: string })
                              .objective as string)
                          : null;
                  if (id && (title || description)) {
                    const normalizedDescription = (
                      description ??
                      title ??
                      ''
                    ).trim();
                    if (normalizedDescription) {
                      return {
                        id,
                        title:
                          (title ?? normalizedDescription).trim() ||
                          normalizedDescription,
                        description: normalizedDescription,
                      };
                    }
                  }
                }
                return null;
              })
              .filter(
                (
                  value
                ): value is {
                  id: string;
                  title: string;
                  description: string;
                } => value !== null
              )
          : [];
        const loDescriptionById = new Map<
          string,
          { title: string; description: string }
        >();
        for (const objective of canonicalObjectives) {
          loDescriptionById.set(objective.id, {
            title: objective.title,
            description: objective.description,
          });
        }

        const cachedLesson = unitDetail.lessons.find(
          lesson => lesson.id === lessonId
        );

        if (cachedLesson && (cachedLesson as { payload?: unknown }).payload) {
          const payload = (cachedLesson as { payload?: any }).payload || {};
          const lessonPackage = payload.package || {};
          const unitLearningObjectiveIds = Array.isArray(
            lessonPackage.unit_learning_objective_ids
          )
            ? lessonPackage.unit_learning_objective_ids.filter(
                (value: unknown): value is string => typeof value === 'string'
              )
            : [];
          const fallbackObjectives = Array.isArray(
            lessonPackage.learning_objectives
          )
            ? lessonPackage.learning_objectives.filter(
                (value: unknown): value is string => typeof value === 'string'
              )
            : [];
          const learningObjectives =
            unitLearningObjectiveIds.length > 0
              ? unitLearningObjectiveIds.map((id: string) => {
                  const objective = loDescriptionById.get(id);
                  if (!objective) {
                    return id;
                  }
                  return objective.description || objective.title;
                })
              : fallbackObjectives;

          const podcastTranscript =
            typeof payload.podcast_transcript === 'string'
              ? payload.podcast_transcript
              : null;
          const podcastAudioUrl =
            typeof payload.podcast_audio_url === 'string'
              ? payload.podcast_audio_url
              : null;
          const rawPodcastDuration = payload.podcast_duration_seconds;
          const podcastDurationSeconds =
            typeof rawPodcastDuration === 'number'
              ? rawPodcastDuration
              : typeof rawPodcastDuration === 'string'
                ? Number.parseInt(rawPodcastDuration, 10)
                : null;
          const podcastVoice =
            typeof payload.podcast_voice === 'string'
              ? payload.podcast_voice
              : null;
          const rawGeneratedAt = payload.podcast_generated_at;
          const podcastGeneratedAt =
            typeof rawGeneratedAt === 'string'
              ? rawGeneratedAt
              : rawGeneratedAt instanceof Date
                ? rawGeneratedAt.toISOString()
                : null;
          const hasPodcast =
            typeof payload.has_podcast === 'boolean'
              ? payload.has_podcast
              : Boolean(
                  podcastAudioUrl ||
                    podcastTranscript ||
                    podcastDurationSeconds ||
                    podcastVoice
                );

          return {
            id: cachedLesson.id,
            title: cachedLesson.title,
            learnerLevel: (payload.learner_level || 'beginner') as
              | 'beginner'
              | 'intermediate'
              | 'advanced',
            learningObjectives,
            keyConcepts: lessonPackage.key_concepts || [],
            miniLesson: lessonPackage.mini_lesson || '',
            exercises: lessonPackage.exercises || [],
            glossaryTerms: lessonPackage.glossary || {},
            exerciseCount: lessonPackage.exercises?.length || 0,
            createdAt: new Date(cachedLesson.updatedAt).toISOString(),
            estimatedDuration: payload.duration_minutes || 0,
            isReadyForLearning: true,
            learnerLevelLabel:
              payload.learner_level === 'intermediate'
                ? 'Intermediate'
                : payload.learner_level === 'advanced'
                  ? 'Advanced'
                  : 'Beginner',
            durationDisplay: `${payload.duration_minutes || 0} min`,
            readinessStatus: 'ready',
            tags: payload.tags || [],
            unitId: cachedLesson.unitId,
            podcastTranscript,
            podcastAudioUrl,
            podcastDurationSeconds:
              typeof podcastDurationSeconds === 'number' &&
              Number.isFinite(podcastDurationSeconds)
                ? podcastDurationSeconds
                : null,
            podcastVoice,
            podcastGeneratedAt,
            hasPodcast,
          };
        }
      }

      return null;
    } catch (error) {
      console.warn('[CatalogRepo] Error searching offline cache:', error);
      return null;
    }
  }

  /**
   * Handle and transform errors
   */
  private handleError(error: any, defaultMessage: string): CatalogError {
    console.error('[CatalogRepo]', defaultMessage, error);

    // If it's already a structured error from infrastructure
    if (error && typeof error === 'object') {
      return {
        message: error.message || defaultMessage,
        code: error.code || 'LESSON_CATALOG_ERROR',
        statusCode: error.status || error.statusCode,
        details: error.details || error,
      };
    }

    // Generic error
    return {
      message: defaultMessage,
      code: 'LESSON_CATALOG_ERROR',
      details: error,
    };
  }
}
