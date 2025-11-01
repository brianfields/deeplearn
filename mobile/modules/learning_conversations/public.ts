import { LearningCoachService } from './service';

export interface LearningConversationsProvider {
  startSession: LearningCoachService['startSession'];
  sendLearnerTurn: LearningCoachService['sendLearnerTurn'];
  acceptBrief: LearningCoachService['acceptBrief'];
  getSession: LearningCoachService['getSession'];
  attachResource: LearningCoachService['attachResource'];
  startTeachingAssistantSession: LearningCoachService['startTeachingAssistantSession'];
  submitTeachingAssistantQuestion: LearningCoachService['submitTeachingAssistantQuestion'];
  getTeachingAssistantSessionState: LearningCoachService['getTeachingAssistantSessionState'];
}

let serviceInstance: LearningCoachService | null = null;

function getService(): LearningCoachService {
  if (!serviceInstance) {
    serviceInstance = new LearningCoachService();
  }
  return serviceInstance;
}

export function learningConversationsProvider(): LearningConversationsProvider {
  const service = getService();
  return {
    startSession: service.startSession.bind(service),
    sendLearnerTurn: service.sendLearnerTurn.bind(service),
    acceptBrief: service.acceptBrief.bind(service),
    getSession: service.getSession.bind(service),
    attachResource: service.attachResource.bind(service),
    startTeachingAssistantSession:
      service.startTeachingAssistantSession.bind(service),
    submitTeachingAssistantQuestion:
      service.submitTeachingAssistantQuestion.bind(service),
    getTeachingAssistantSessionState:
      service.getTeachingAssistantSessionState.bind(service),
  };
}

export type {
  LearningCoachBrief,
  LearningCoachMessage,
  LearningCoachSessionState,
  AttachResourcePayload,
} from './models';
export type {
  TeachingAssistantMessage,
  TeachingAssistantSessionState,
  TeachingAssistantContext,
  TeachingAssistantStartPayload,
  TeachingAssistantQuestionPayload,
  TeachingAssistantStateRequest,
} from './models';
