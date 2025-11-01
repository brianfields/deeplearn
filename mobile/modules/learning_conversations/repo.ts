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
  TeachingAssistantStartPayload,
  TeachingAssistantSessionState,
  TeachingAssistantQuestionPayload,
  TeachingAssistantStateRequest,
  TeachingAssistantMessage,
  TeachingAssistantContext,
} from './models';
import type { ResourceSummary, ResourceType } from '../resource/public';

const LEARNING_CONVERSATIONS_BASE = '/api/v1/learning_conversations';

const COACH_PREFIX = `${LEARNING_CONVERSATIONS_BASE}/coach`;
const TEACHING_ASSISTANT_PREFIX = `${LEARNING_CONVERSATIONS_BASE}/teaching_assistant`;

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
  readonly uncovered_learning_objective_ids?: string[] | null;
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

interface ApiTeachingAssistantMessage extends ApiMessage {
  readonly suggested_quick_replies?: string[] | null;
}

interface ApiTeachingAssistantContext {
  readonly unit_id: string;
  readonly lesson_id: string | null;
  readonly session_id: string | null;
  readonly session?: Record<string, any> | null;
  readonly exercise_attempt_history?: Record<string, any>[] | null;
  readonly lesson?: Record<string, any> | null;
  readonly unit?: Record<string, any> | null;
  readonly unit_session?: Record<string, any> | null;
  readonly unit_resources?: Record<string, any>[] | null;
}

interface ApiTeachingAssistantState {
  readonly conversation_id: string;
  readonly unit_id: string;
  readonly lesson_id: string | null;
  readonly session_id: string | null;
  readonly messages: ApiTeachingAssistantMessage[];
  readonly suggested_quick_replies?: string[] | null;
  readonly metadata: Record<string, any>;
  readonly context: ApiTeachingAssistantContext;
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

function toTeachingAssistantMessage(
  dto: ApiTeachingAssistantMessage
): TeachingAssistantMessage {
  return {
    ...toMessage(dto),
    suggestedQuickReplies: Array.isArray(dto.suggested_quick_replies)
      ? dto.suggested_quick_replies.filter(isNonEmptyString)
      : [],
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
    uncoveredLearningObjectiveIds: normalizeUncoveredLearningObjectiveIds(
      dto.uncovered_learning_objective_ids
    ),
  };
}

function toTeachingAssistantContext(
  dto: ApiTeachingAssistantContext
): TeachingAssistantContext {
  return {
    unitId: dto.unit_id,
    lessonId: dto.lesson_id,
    sessionId: dto.session_id,
    session: dto.session ?? null,
    exerciseAttemptHistory:
      dto.exercise_attempt_history?.map(entry => ({ ...entry })) ?? [],
    lesson: dto.lesson ?? null,
    unit: dto.unit ?? null,
    unitSession: dto.unit_session ?? null,
    unitResources: dto.unit_resources ?? [],
  };
}

function toTeachingAssistantState(
  dto: ApiTeachingAssistantState
): TeachingAssistantSessionState {
  return {
    conversationId: dto.conversation_id,
    unitId: dto.unit_id,
    lessonId: dto.lesson_id,
    sessionId: dto.session_id,
    messages: dto.messages.map(toTeachingAssistantMessage),
    suggestedQuickReplies: Array.isArray(dto.suggested_quick_replies)
      ? dto.suggested_quick_replies.filter(isNonEmptyString)
      : [],
    metadata: dto.metadata ?? {},
    context: toTeachingAssistantContext(dto.context),
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

function normalizeUncoveredLearningObjectiveIds(
  ids: ApiSessionState['uncovered_learning_objective_ids']
): string[] | null | undefined {
  if (ids === undefined) {
    return undefined;
  }
  if (ids === null) {
    return null;
  }
  if (!Array.isArray(ids)) {
    return undefined;
  }

  const normalized = ids
    .map(id => (typeof id === 'string' ? id : null))
    .filter((id): id is string => Boolean(id));

  return normalized;
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

export class LearningCoachRepo {
  private infrastructure = infrastructureProvider();

  async startSession(
    payload: StartSessionPayload
  ): Promise<LearningCoachSessionState> {
    try {
      const response = await this.infrastructure.request<ApiSessionState>(
        `${COACH_PREFIX}/session/start`,
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
        `${COACH_PREFIX}/session/message`,
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
        `${COACH_PREFIX}/session/accept`,
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
        `${COACH_PREFIX}/session/${encodeURIComponent(conversationId)}`,
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
        `${COACH_PREFIX}/conversations/${encodeURIComponent(payload.conversationId)}/resources`,
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

  async startTeachingAssistantSession(
    payload: TeachingAssistantStartPayload
  ): Promise<TeachingAssistantSessionState> {
    try {
      const response =
        await this.infrastructure.request<ApiTeachingAssistantState>(
          `${TEACHING_ASSISTANT_PREFIX}/start`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              unit_id: payload.unitId,
              lesson_id: payload.lessonId ?? null,
              session_id: payload.sessionId ?? null,
              user_id: payload.userId ?? null,
            }),
          }
        );
      return toTeachingAssistantState(response);
    } catch (error) {
      throw this.handleError(
        error,
        'Failed to start teaching assistant session'
      );
    }
  }

  async submitTeachingAssistantQuestion(
    payload: TeachingAssistantQuestionPayload
  ): Promise<TeachingAssistantSessionState> {
    try {
      const response =
        await this.infrastructure.request<ApiTeachingAssistantState>(
          `${TEACHING_ASSISTANT_PREFIX}/ask`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              conversation_id: payload.conversationId,
              message: payload.message,
              unit_id: payload.unitId,
              lesson_id: payload.lessonId ?? null,
              session_id: payload.sessionId ?? null,
              user_id: payload.userId ?? null,
            }),
          }
        );
      return toTeachingAssistantState(response);
    } catch (error) {
      throw this.handleError(
        error,
        'Failed to submit teaching assistant question'
      );
    }
  }

  async getTeachingAssistantSessionState(
    payload: TeachingAssistantStateRequest
  ): Promise<TeachingAssistantSessionState> {
    try {
      const query = new URLSearchParams({
        unit_id: payload.unitId,
      });
      if (payload.lessonId) {
        query.set('lesson_id', payload.lessonId);
      }
      if (payload.sessionId) {
        query.set('session_id', payload.sessionId);
      }
      if (payload.userId) {
        query.set('user_id', String(payload.userId));
      }

      const response =
        await this.infrastructure.request<ApiTeachingAssistantState>(
          `${TEACHING_ASSISTANT_PREFIX}/${encodeURIComponent(payload.conversationId)}?${query.toString()}`,
          {
            method: 'GET',
          }
        );
      return toTeachingAssistantState(response);
    } catch (error) {
      throw this.handleError(
        error,
        'Failed to fetch teaching assistant session state'
      );
    }
  }

  private handleError(error: any, message: string): LearningCoachError {
    console.error('[LearningConversationsRepo]', message, error);
    if (error && typeof error === 'object') {
      return {
        message: (error as any).message ?? message,
        statusCode: (error as any).status ?? (error as any).statusCode,
        code: (error as any).code ?? 'LEARNING_CONVERSATIONS_ERROR',
        details: error,
      };
    }
    return {
      message,
      code: 'LEARNING_CONVERSATIONS_ERROR',
      details: error,
    };
  }
}
