/**
 * Shared Navigation Types for React Native Learning App
 *
 * Centralized navigation type definitions used across the application.
 */

import type { LessonDetail } from './modules/catalog/models';
import type { SessionResults } from './modules/learning_session/models';

// ================================
// Navigation Types
// ================================

export type RootStackParamList = {
  Dashboard: undefined;
  Learning: { lessonId: string };
  LessonDetail: { lessonId: string; lesson: LessonDetail };
};

export type LearningStackParamList = {
  LessonList: undefined;
  CreateUnit: undefined;
  LearningFlow: { lessonId: string; lesson: LessonDetail };
  UnitDetail: { unitId: string };
  Results: {
    results: SessionResults;
  };
};
