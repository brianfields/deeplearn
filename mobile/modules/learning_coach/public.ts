import { LearningCoachService } from './service';

export interface LearningCoachProvider {
  startSession: LearningCoachService['startSession'];
  sendLearnerTurn: LearningCoachService['sendLearnerTurn'];
  acceptBrief: LearningCoachService['acceptBrief'];
  getSession: LearningCoachService['getSession'];
}

let serviceInstance: LearningCoachService | null = null;

function getService(): LearningCoachService {
  if (!serviceInstance) {
    serviceInstance = new LearningCoachService();
  }
  return serviceInstance;
}

export function learningCoachProvider(): LearningCoachProvider {
  const service = getService();
  return {
    startSession: service.startSession.bind(service),
    sendLearnerTurn: service.sendLearnerTurn.bind(service),
    acceptBrief: service.acceptBrief.bind(service),
    getSession: service.getSession.bind(service),
  };
}

export type {
  LearningCoachBrief,
  LearningCoachMessage,
  LearningCoachSessionState,
} from './models';
