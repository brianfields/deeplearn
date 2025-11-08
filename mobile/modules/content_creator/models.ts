import type { UnitStatus } from '../content/public';
import type { LearningCoachLearningObjective } from '../learning_conversations/models';

/**
 * UnitCreationRequest: Coach-driven unit creation from learning coach conversation.
 * All fields are required because the coach must finalize them before unit creation.
 */
export interface UnitCreationRequest {
  readonly learnerDesires: string; // Unified learner context (topic, difficulty, preferences, etc.)
  readonly unitTitle: string; // From learning coach
  readonly learningObjectives: readonly LearningCoachLearningObjective[]; // From learning coach (required)
  readonly targetLessonCount: number; // From learning coach
  readonly conversationId: string; // For traceability and resource lookup
  readonly ownerUserId?: number | null;
}

export interface UnitCreationResponse {
  readonly unitId: string;
  readonly status: UnitStatus;
  readonly title: string;
}

export interface ContentCreatorError {
  readonly message: string;
  readonly code: string;
  readonly statusCode?: number;
  readonly details?: unknown;
}
