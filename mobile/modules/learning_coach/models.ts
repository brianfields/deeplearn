import type { ResourceSummary } from '../resource/public';

export type MessageRole = 'assistant' | 'user' | 'system';

export interface LearningCoachMessage {
  readonly id: string;
  readonly role: MessageRole;
  readonly content: string;
  readonly createdAt: string;
  readonly metadata: Record<string, any>;
}

export interface LearningCoachBrief {
  readonly title: string;
  readonly description: string;
  readonly objectives: string[];
  readonly notes?: string | null;
  readonly level?: string | null;
}

export interface LearningCoachLearningObjective {
  readonly id: string;
  readonly title: string;
  readonly description: string;
}

export interface LearningCoachSessionState {
  readonly conversationId: string;
  readonly messages: LearningCoachMessage[];
  readonly metadata: Record<string, any>;
  readonly finalizedTopic?: string | null;
  readonly unitTitle?: string | null;
  readonly learningObjectives?: LearningCoachLearningObjective[] | null;
  readonly suggestedLessonCount?: number | null;
  readonly proposedBrief?: LearningCoachBrief | null; // Deprecated
  readonly acceptedBrief?: LearningCoachBrief | null; // Deprecated
  readonly resources?: ResourceSummary[];
}

export interface StartSessionPayload {
  readonly topic?: string | null;
  readonly userId?: string | null;
}

export interface LearnerTurnPayload {
  readonly conversationId: string;
  readonly message: string;
  readonly userId?: string | null;
}

export interface AcceptBriefPayload {
  readonly conversationId: string;
  readonly brief: LearningCoachBrief;
  readonly userId?: string | null;
}

export interface AttachResourcePayload {
  readonly conversationId: string;
  readonly resourceId: string;
  readonly userId?: string | null;
}

export interface LearningCoachError {
  readonly message: string;
  readonly statusCode?: number;
  readonly code?: string;
  readonly details?: unknown;
}
