import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { learningConversationsProvider } from './public';
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

const learningConversations = learningConversationsProvider();

export const learningConversationsKeys = {
  coach: ['learningConversations', 'coach'] as const,
  coachSession(conversationId: string) {
    return [...this.coach, 'session', conversationId] as const;
  },
  assistant: ['learningConversations', 'teachingAssistant'] as const,
  assistantSession(conversationId: string) {
    return [...this.assistant, 'session', conversationId] as const;
  },
};

export function useLearningCoachSession(
  conversationId: string | null | undefined
) {
  return useQuery<LearningCoachSessionState, Error>({
    queryKey: conversationId
      ? learningConversationsKeys.coachSession(conversationId)
      : ['learningConversations', 'coach', 'session', 'empty'],
    queryFn: () => learningConversations.getSession(conversationId as string),
    enabled: Boolean(conversationId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useStartLearningCoachSession() {
  const queryClient = useQueryClient();
  return useMutation<LearningCoachSessionState, Error, StartSessionPayload>({
    mutationFn: payload => learningConversations.startSession(payload),
    onSuccess: state => {
      queryClient.setQueryData(
        learningConversationsKeys.coachSession(state.conversationId),
        state
      );
    },
  });
}

export function useLearnerTurnMutation() {
  const queryClient = useQueryClient();
  return useMutation<LearningCoachSessionState, Error, LearnerTurnPayload>({
    mutationFn: payload => learningConversations.sendLearnerTurn(payload),
    onSuccess: state => {
      queryClient.setQueryData(
        learningConversationsKeys.coachSession(state.conversationId),
        state
      );
    },
  });
}

export function useAcceptBriefMutation() {
  const queryClient = useQueryClient();
  return useMutation<LearningCoachSessionState, Error, AcceptBriefPayload>({
    mutationFn: payload => learningConversations.acceptBrief(payload),
    onSuccess: state => {
      queryClient.setQueryData(
        learningConversationsKeys.coachSession(state.conversationId),
        state
      );
    },
  });
}

export function useAttachResourceMutation() {
  const queryClient = useQueryClient();
  return useMutation<LearningCoachSessionState, Error, AttachResourcePayload>({
    mutationFn: payload => learningConversations.attachResource(payload),
    onSuccess: state => {
      queryClient.setQueryData(
        learningConversationsKeys.coachSession(state.conversationId),
        state
      );
    },
  });
}

export function useStartTeachingAssistant() {
  const queryClient = useQueryClient();
  return useMutation<
    TeachingAssistantSessionState,
    Error,
    TeachingAssistantStartPayload
  >({
    mutationFn: payload =>
      learningConversations.startTeachingAssistantSession(payload),
    onSuccess: state => {
      queryClient.setQueryData(
        learningConversationsKeys.assistantSession(state.conversationId),
        state
      );
    },
  });
}

export function useSubmitTeachingAssistantQuestion() {
  const queryClient = useQueryClient();
  return useMutation<
    TeachingAssistantSessionState,
    Error,
    TeachingAssistantQuestionPayload
  >({
    mutationFn: payload =>
      learningConversations.submitTeachingAssistantQuestion(payload),
    onSuccess: state => {
      queryClient.setQueryData(
        learningConversationsKeys.assistantSession(state.conversationId),
        state
      );
    },
  });
}

export function useTeachingAssistantSessionState(
  request: TeachingAssistantStateRequest | null | undefined
) {
  return useQuery<TeachingAssistantSessionState, Error>({
    queryKey: request
      ? learningConversationsKeys.assistantSession(request.conversationId)
      : ['learningConversations', 'teachingAssistant', 'session', 'empty'],
    queryFn: () =>
      learningConversations.getTeachingAssistantSessionState(
        request as TeachingAssistantStateRequest
      ),
    enabled: Boolean(
      request &&
        request.conversationId &&
        request.unitId &&
        request.conversationId.length > 0
    ),
    staleTime: 60 * 1000,
  });
}
