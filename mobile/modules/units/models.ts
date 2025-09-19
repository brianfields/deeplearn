/**
 * Units Module - Models
 *
 * DTOs and types for unit browsing, details, and progress.
 * Mirrors backend lesson_catalog unit DTOs and maps snake_case → camelCase.
 */

import type { LessonSummary as CatalogLessonSummary } from '../unit_catalog/models';

// ================================
// Backend API Wire Types (Private)
// ================================

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
  // Lessons come back as lesson_catalog LessonSummary wire shape (snake_case)
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

// ================================
// Frontend DTOs (Public)
// ================================

export type UnitId = string;
export type Difficulty = 'beginner' | 'intermediate' | 'advanced';

export interface Unit {
  readonly id: UnitId;
  readonly title: string;
  readonly description?: string | null;
  readonly difficulty: Difficulty;
  readonly lessonCount: number;
  readonly difficultyLabel: string; // Derived label for display
}

export interface UnitDetail {
  readonly id: UnitId;
  readonly title: string;
  readonly description?: string | null;
  readonly difficulty: Difficulty;
  readonly lessonIds: string[];
  readonly lessons: CatalogLessonSummary[]; // Reuse lesson DTO from lesson_catalog
}

export interface UnitProgress {
  readonly unitId: UnitId;
  readonly completedLessons: number;
  readonly totalLessons: number;
  readonly progressPercentage: number; // 0-100
}

// ================================
// DTO Conversion Helpers
// ================================

export function toUnitDTO(api: ApiUnitSummary): Unit {
  const difficulty = (api.difficulty as Difficulty) ?? 'beginner';
  return {
    id: api.id,
    title: api.title,
    description: api.description,
    difficulty,
    lessonCount: api.lesson_count,
    difficultyLabel: formatDifficulty(difficulty),
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
    lessons: api.lessons.map(
      l =>
        ({
          id: l.id,
          title: l.title,
          coreConcept: l.core_concept,
          userLevel: l.user_level as CatalogLessonSummary['userLevel'],
          learningObjectives: l.learning_objectives,
          keyConcepts: l.key_concepts,
          componentCount: l.exercise_count,
          estimatedDuration: Math.max(5, l.exercise_count * 3),
          isReadyForLearning: l.exercise_count > 0,
          difficultyLevel: formatDifficulty(l.user_level as Difficulty),
          durationDisplay: formatDuration(Math.max(5, l.exercise_count * 3)),
          readinessStatus: l.exercise_count > 0 ? 'Ready' : 'Draft',
          tags: (l.key_concepts ?? []).slice(0, 3),
        }) as unknown as CatalogLessonSummary
    ),
  };
}

function formatDifficulty(d: Difficulty | string): string {
  const map: Record<string, string> = {
    beginner: 'Beginner',
    intermediate: 'Intermediate',
    advanced: 'Advanced',
  };
  return map[d] ?? 'Unknown';
}

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  return remaining === 0 ? `${hours} hr` : `${hours} hr ${remaining} min`;
}
