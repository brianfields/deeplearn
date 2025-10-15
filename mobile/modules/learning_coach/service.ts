import { LearningCoachRepo } from './repo';
import type {
  AcceptBriefPayload,
  LearnerTurnPayload,
  LearningCoachSessionState,
  StartSessionPayload,
} from './models';

function createDefaultRepo(): LearningCoachRepo {
  return new LearningCoachRepo();
}

export class LearningCoachService {
  constructor(private repo: LearningCoachRepo = createDefaultRepo()) {}

  async startSession(payload: StartSessionPayload): Promise<LearningCoachSessionState> {
    return this.repo.startSession(payload);
  }

  async sendLearnerTurn(payload: LearnerTurnPayload): Promise<LearningCoachSessionState> {
    return this.repo.sendLearnerTurn(payload);
  }

  async acceptBrief(payload: AcceptBriefPayload): Promise<LearningCoachSessionState> {
    return this.repo.acceptBrief(payload);
  }

  async getSession(conversationId: string): Promise<LearningCoachSessionState> {
    return this.repo.getSession(conversationId);
  }
}
