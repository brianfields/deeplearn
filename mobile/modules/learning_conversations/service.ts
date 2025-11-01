import { LearningCoachRepo } from './repo';
import type {
  AcceptBriefPayload,
  LearnerTurnPayload,
  LearningCoachSessionState,
  AttachResourcePayload,
  StartSessionPayload,
  TeachingAssistantStartPayload,
  TeachingAssistantSessionState,
  TeachingAssistantQuestionPayload,
  TeachingAssistantStateRequest,
} from './models';

function createDefaultRepo(): LearningCoachRepo {
  return new LearningCoachRepo();
}

export class LearningCoachService {
  constructor(private repo: LearningCoachRepo = createDefaultRepo()) {}

  async startSession(
    payload: StartSessionPayload
  ): Promise<LearningCoachSessionState> {
    return this.repo.startSession(payload);
  }

  async sendLearnerTurn(
    payload: LearnerTurnPayload
  ): Promise<LearningCoachSessionState> {
    return this.repo.sendLearnerTurn(payload);
  }

  async acceptBrief(
    payload: AcceptBriefPayload
  ): Promise<LearningCoachSessionState> {
    return this.repo.acceptBrief(payload);
  }

  async getSession(conversationId: string): Promise<LearningCoachSessionState> {
    return this.repo.getSession(conversationId);
  }

  async attachResource(
    payload: AttachResourcePayload
  ): Promise<LearningCoachSessionState> {
    return this.repo.attachResource(payload);
  }

  async startTeachingAssistantSession(
    payload: TeachingAssistantStartPayload
  ): Promise<TeachingAssistantSessionState> {
    return this.repo.startTeachingAssistantSession(payload);
  }

  async submitTeachingAssistantQuestion(
    payload: TeachingAssistantQuestionPayload
  ): Promise<TeachingAssistantSessionState> {
    return this.repo.submitTeachingAssistantQuestion(payload);
  }

  async getTeachingAssistantSessionState(
    payload: TeachingAssistantStateRequest
  ): Promise<TeachingAssistantSessionState> {
    return this.repo.getTeachingAssistantSessionState(payload);
  }
}
