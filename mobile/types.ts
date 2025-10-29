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
  AuthLanding: undefined;
  Login: undefined;
  Register: undefined;
  Dashboard: undefined;
  Learning: { lessonId: string; unitId: string };
  LessonDetail: { lessonId: string; lesson: LessonDetail; unitId: string };
};

export type LearningStackParamList = {
  LessonList: undefined;
  LearningCoach:
    | {
        topic?: string;
        conversationId?: string;
        attachResourceId?: string;
      }
    | undefined;
  AddResource:
    | { attachToConversation?: boolean; conversationId?: string | null }
    | undefined;
  LearningFlow: { lessonId: string; lesson: LessonDetail; unitId: string };
  UnitDetail: { unitId: string };
  UnitLODetail: { unitId: string; unitTitle?: string | null };
  Results: {
    results: SessionResults;
    unitId: string;
  };
  CatalogBrowser: undefined;
  ManageCache: undefined;
  SQLiteDetail: undefined;
  AsyncStorageDetail: undefined;
  FileSystemDetail: undefined;
};
