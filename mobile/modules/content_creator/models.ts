import type { UnitStatus } from '../content/public';

export interface UnitCreationRequest {
  readonly topic: string;
  readonly difficulty: 'beginner' | 'intermediate' | 'advanced';
  readonly unitTitle?: string | null;
  readonly targetLessonCount?: number | null;
  readonly shareGlobally?: boolean;
  readonly ownerUserId?: number | null;
  readonly conversationId?: string | null;
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
