import { infrastructureProvider } from '../infrastructure/public';
import type {
  StartSessionPayload,
  LearnerTurnPayload,
  AcceptBriefPayload,
  LearningCoachSessionState,
  LearningCoachMessage,
  LearningCoachBrief,
  LearningCoachLearningObjective,
  LearningCoachError,
  AttachResourcePayload,
} from './models';
import type { ResourceSummary, ResourceType } from '../resource/public';

const LEARNING_COACH_BASE = '/api/v1/learning_coach';

interface ApiMessage {
  readonly id: string;
  readonly role: 'assistant' | 'user' | 'system';
  readonly content: string;
  readonly created_at: string;
  readonly metadata: Record<string, any>;
}

interface ApiSessionState {
  readonly conversation_id: string;
  readonly messages: ApiMessage[];
  readonly metadata: Record<string, any>;
  readonly finalized_topic?: string | null;
  readonly unit_title?: string | null;
  readonly learning_objectives?: ApiLearningObjective[] | null;
  readonly suggested_lesson_count?: number | null;
  readonly proposed_brief?: Record<string, any> | null;
  readonly accepted_brief?: Record<string, any> | null;
  readonly resources?: ApiResourceSummary[] | null;
}

interface ApiLearningObjective {
  readonly id?: string;
  readonly title?: string;
  readonly description?: string;
  readonly text?: string;
}

interface ApiResourceSummary {
  readonly id: string;
  readonly resource_type: string;
  readonly filename?: string | null;
  readonly source_url?: string | null;
  readonly file_size?: number | null;
  readonly created_at: string;
  readonly preview_text?: string | null;
}

function toMessage(dto: ApiMessage): LearningCoachMessage {
  return {
    id: dto.id,
    role: dto.role,
    content: dto.content,
    createdAt: dto.created_at,
    metadata: dto.metadata ?? {},
  };
}

function normalizeBrief(
  brief: Record<string, any> | null | undefined
): LearningCoachBrief | null {
  if (!brief || typeof brief !== 'object') {
    return null;
  }
  const objectives = Array.isArray(brief.objectives)
    ? brief.objectives.map(value => String(value))
    : [];
  return {
    title: String(brief.title ?? ''),
    description: String(brief.description ?? ''),
    objectives,
    notes: brief.notes ? String(brief.notes) : null,
    level: brief.level ? String(brief.level) : null,
  };
}

function toSessionState(dto: ApiSessionState): LearningCoachSessionState {
  return {
    conversationId: dto.conversation_id,
    messages: dto.messages.map(toMessage),
    metadata: dto.metadata ?? {},
    finalizedTopic: dto.finalized_topic ?? null,
    unitTitle: dto.unit_title ?? null,
    learningObjectives: normalizeLearningObjectives(dto.learning_objectives),
    suggestedLessonCount: dto.suggested_lesson_count ?? null,
    proposedBrief: normalizeBrief(dto.proposed_brief),
    acceptedBrief: normalizeBrief(dto.accepted_brief),
    resources: normalizeResources(dto.resources),
  };
}

function normalizeLearningObjectives(
  objectives: ApiSessionState['learning_objectives']
): LearningCoachLearningObjective[] | null {
  if (!Array.isArray(objectives)) {
    return null;
  }

  const normalized = objectives
    .map(objective => {
      if (!objective || typeof objective !== 'object') {
        return null;
      }

      const id = typeof objective.id === 'string' ? objective.id : null;
      const rawTitle =
        typeof objective.title === 'string'
          ? objective.title
          : typeof objective.text === 'string'
            ? objective.text
            : null;
      const rawDescription =
        typeof objective.description === 'string'
          ? objective.description
          : typeof objective.text === 'string'
            ? objective.text
            : null;

      if (!id || (!rawTitle && !rawDescription)) {
        return null;
      }

      const title = (rawTitle ?? rawDescription ?? '').trim();
      const description = (rawDescription ?? rawTitle ?? '').trim();

      if (!title || !description) {
        return null;
      }

      return {
        id,
        title,
        description,
      } satisfies LearningCoachLearningObjective;
    })
    .filter(
      (objective): objective is LearningCoachLearningObjective =>
        objective !== null
    );

  return normalized.length > 0 ? normalized : null;
}

function normalizeResources(
  resources: ApiResourceSummary[] | null | undefined
): ResourceSummary[] | undefined {
  if (!Array.isArray(resources)) {
    return undefined;
  }
  return resources.map(resource => ({
    id: resource.id,
    resourceType: resource.resource_type as ResourceType,
    filename: resource.filename ?? null,
    sourceUrl: resource.source_url ?? null,
    fileSize: resource.file_size ?? null,
    createdAt: resource.created_at,
    previewText: resource.preview_text ?? '',
  }));
}

export class LearningCoachRepo {
  private infrastructure = infrastructureProvider();

  async startSession(
    payload: StartSessionPayload
  ): Promise<LearningCoachSessionState> {
    try {
      const response = await this.infrastructure.request<ApiSessionState>(
        `${LEARNING_COACH_BASE}/session/start`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: payload.topic ?? null,
            user_id: payload.userId ?? null,
          }),
        }
      );
      return toSessionState(response);
    } catch (error) {
      throw this.handleError(error, 'Failed to start learning coach session');
    }
  }

  async sendLearnerTurn(
    payload: LearnerTurnPayload
  ): Promise<LearningCoachSessionState> {
    try {
      const response = await this.infrastructure.request<ApiSessionState>(
        `${LEARNING_COACH_BASE}/session/message`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: payload.conversationId,
            message: payload.message,
            user_id: payload.userId ?? null,
          }),
        }
      );
      return toSessionState(response);
    } catch (error) {
      throw this.handleError(error, 'Failed to send learner response');
    }
  }

  async acceptBrief(
    payload: AcceptBriefPayload
  ): Promise<LearningCoachSessionState> {
    try {
      const response = await this.infrastructure.request<ApiSessionState>(
        `${LEARNING_COACH_BASE}/session/accept`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conversation_id: payload.conversationId,
            brief: payload.brief,
            user_id: payload.userId ?? null,
          }),
        }
      );
      return toSessionState(response);
    } catch (error) {
      throw this.handleError(error, 'Failed to accept unit brief');
    }
  }

  async getSession(conversationId: string): Promise<LearningCoachSessionState> {
    try {
      const response = await this.infrastructure.request<ApiSessionState>(
        `${LEARNING_COACH_BASE}/session/${encodeURIComponent(conversationId)}`,
        {
          method: 'GET',
        }
      );
      return toSessionState(response);
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch session state');
    }
  }

  async attachResource(
    payload: AttachResourcePayload
  ): Promise<LearningCoachSessionState> {
    try {
      const response = await this.infrastructure.request<ApiSessionState>(
        `${LEARNING_COACH_BASE}/conversations/${encodeURIComponent(payload.conversationId)}/resources`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            resource_id: payload.resourceId,
            user_id: payload.userId ?? null,
          }),
        }
      );
      return toSessionState(response);
    } catch (error) {
      throw this.handleError(error, 'Failed to attach resource');
    }
  }

  private handleError(error: any, message: string): LearningCoachError {
    console.error('[LearningCoachRepo]', message, error);
    if (error && typeof error === 'object') {
      return {
        message: (error as any).message ?? message,
        statusCode: (error as any).status ?? (error as any).statusCode,
        code: (error as any).code ?? 'LEARNING_COACH_ERROR',
        details: error,
      };
    }
    return {
      message,
      code: 'LEARNING_COACH_ERROR',
      details: error,
    };
  }
}
