import type { ResourceSummary } from '../resource/public';

export type MessageRole = 'assistant' | 'user' | 'system';

export interface LearningCoachMessage {
  readonly id: string;
  readonly role: MessageRole;
  readonly content: string;
  readonly createdAt: string;
  readonly metadata: Record<string, any>;
}

export interface TeachingAssistantMessage extends LearningCoachMessage {
  readonly suggestedQuickReplies: string[];
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
  readonly learnerDesires?: string | null; // Unified learner context (topic, difficulty, preferences, etc.)
  readonly proposedBrief?: LearningCoachBrief | null; // Deprecated
  readonly acceptedBrief?: LearningCoachBrief | null; // Deprecated
  readonly resources?: ResourceSummary[];
  readonly uncoveredLearningObjectiveIds?: string[] | null;
}

export interface TeachingAssistantContext {
  readonly unitId: string;
  readonly lessonId: string | null;
  readonly sessionId: string | null;
  readonly session: Record<string, any> | null;
  readonly exerciseAttemptHistory: ReadonlyArray<Record<string, any>>;
  readonly lesson: Record<string, any> | null;
  readonly unit: Record<string, any> | null;
  readonly unitSession: Record<string, any> | null;
  readonly unitResources: ReadonlyArray<Record<string, any>>;
}

export interface TeachingAssistantSessionState {
  readonly conversationId: string;
  readonly unitId: string;
  readonly lessonId: string | null;
  readonly sessionId: string | null;
  readonly messages: TeachingAssistantMessage[];
  readonly suggestedQuickReplies: string[];
  readonly metadata: Record<string, any>;
  readonly context: TeachingAssistantContext;
}

export interface StartSessionPayload {
  readonly topic?: string | null;
  readonly userId?: string | null;
}

export interface TeachingAssistantStartPayload {
  readonly unitId: string;
  readonly lessonId?: string | null;
  readonly sessionId?: string | null;
  readonly userId?: string | null;
}

export interface LearnerTurnPayload {
  readonly conversationId: string;
  readonly message: string;
  readonly userId?: string | null;
}

export interface TeachingAssistantQuestionPayload {
  readonly conversationId: string;
  readonly message: string;
  readonly unitId: string;
  readonly lessonId?: string | null;
  readonly sessionId?: string | null;
  readonly userId?: string | null;
}

export interface TeachingAssistantStateRequest {
  readonly conversationId: string;
  readonly unitId: string;
  readonly lessonId?: string | null;
  readonly sessionId?: string | null;
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
