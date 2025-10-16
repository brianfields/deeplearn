import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { learningCoachProvider } from './public';
import type {
  AcceptBriefPayload,
  LearnerTurnPayload,
  LearningCoachSessionState,
  StartSessionPayload,
} from './models';

const learningCoach = learningCoachProvider();

export const learningCoachKeys = {
  all: ['learningCoach'] as const,
  session(conversationId: string) {
    return [...this.all, 'session', conversationId] as const;
  },
};

export function useLearningCoachSession(
  conversationId: string | null | undefined
) {
  return useQuery<LearningCoachSessionState, Error>({
    queryKey: conversationId
      ? learningCoachKeys.session(conversationId)
      : ['learningCoach', 'session', 'empty'],
    queryFn: () => learningCoach.getSession(conversationId as string),
    enabled: Boolean(conversationId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useStartLearningCoachSession() {
  const queryClient = useQueryClient();
  return useMutation<LearningCoachSessionState, Error, StartSessionPayload>({
    mutationFn: payload => learningCoach.startSession(payload),
    onSuccess: state => {
      queryClient.setQueryData(
        learningCoachKeys.session(state.conversationId),
        state
      );
    },
  });
}

export function useLearnerTurnMutation() {
  const queryClient = useQueryClient();
  return useMutation<LearningCoachSessionState, Error, LearnerTurnPayload>({
    mutationFn: payload => learningCoach.sendLearnerTurn(payload),
    onSuccess: state => {
      queryClient.setQueryData(
        learningCoachKeys.session(state.conversationId),
        state
      );
    },
  });
}

export function useAcceptBriefMutation() {
  const queryClient = useQueryClient();
  return useMutation<LearningCoachSessionState, Error, AcceptBriefPayload>({
    mutationFn: payload => learningCoach.acceptBrief(payload),
    onSuccess: state => {
      queryClient.setQueryData(
        learningCoachKeys.session(state.conversationId),
        state
      );
    },
  });
}
