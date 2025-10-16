import React, { useEffect, useMemo, useState } from 'react';
import { View, ActivityIndicator, Text, StyleSheet, Alert } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useAuth } from '../../user/public';
import { uiSystemProvider } from '../../ui_system/public';
import { ConversationList } from '../components/ConversationList';
import { QuickReplies } from '../components/QuickReplies';
import { Composer } from '../components/Composer';
import { BriefCard } from '../components/BriefCard';
import {
  useAcceptBriefMutation,
  useLearnerTurnMutation,
  useLearningCoachSession,
  useStartLearningCoachSession,
} from '../queries';
import type { LearningStackParamList } from '../../../types';
import { useCreateUnit } from '../../catalog/queries';

const uiSystem = uiSystemProvider();
const theme = uiSystem.getCurrentTheme();

type ScreenProps = NativeStackScreenProps<
  LearningStackParamList,
  'LearningCoach'
>;

export function LearningCoachScreen({
  navigation,
  route,
}: ScreenProps): React.ReactElement {
  const { user } = useAuth();
  const [conversationId, setConversationId] = useState<string | null>(
    route.params?.conversationId ?? null
  );
  const startSession = useStartLearningCoachSession();
  const learnerTurn = useLearnerTurnMutation();
  const acceptBrief = useAcceptBriefMutation();
  const createUnit = useCreateUnit();
  const sessionQuery = useLearningCoachSession(conversationId);

  useEffect(() => {
    if (!conversationId && !startSession.isPending && !startSession.isSuccess) {
      startSession.mutate(
        {
          topic: route.params?.topic ?? null,
          userId: user ? String(user.id) : null,
        },
        {
          onSuccess: state => {
            setConversationId(state.conversationId);
          },
        }
      );
    }
  }, [conversationId, route.params?.topic, startSession, user]);

  useEffect(() => {
    if (!conversationId && startSession.isSuccess) {
      setConversationId(startSession.data.conversationId);
    }
  }, [conversationId, startSession.data, startSession.isSuccess]);

  const sessionState = sessionQuery.data ?? startSession.data ?? null;

  const isCoachLoading = useMemo(() => {
    return (
      startSession.isPending || learnerTurn.isPending || sessionQuery.isFetching
    );
  }, [startSession.isPending, learnerTurn.isPending, sessionQuery.isFetching]);

  const handleSend = (message: string) => {
    if (!conversationId) {
      return;
    }
    learnerTurn.mutate({
      conversationId,
      message,
      userId: user ? String(user.id) : null,
    });
  };

  const handleQuickReply = (reply: string) => {
    handleSend(reply);
  };

  const normalizeDifficulty = (
    level: string | null | undefined
  ): 'beginner' | 'intermediate' | 'advanced' => {
    if (!level) {
      return 'intermediate';
    }
    const normalized = level.toLowerCase();
    if (normalized.includes('beginner')) {
      return 'beginner';
    }
    if (normalized.includes('advanced')) {
      return 'advanced';
    }
    return 'intermediate';
  };

  const handleAccept = () => {
    if (!conversationId || !sessionState?.proposedBrief) {
      return;
    }

    const brief = sessionState.proposedBrief;

    acceptBrief.mutate(
      {
        conversationId,
        brief,
        userId: user ? String(user.id) : null,
      },
      {
        onSuccess: state => {
          const accepted = state.acceptedBrief ?? state.proposedBrief;
          if (!accepted) {
            return;
          }

          const difficulty = normalizeDifficulty(accepted.level ?? null);
          createUnit.mutate(
            {
              topic: accepted.title,
              difficulty,
              targetLessonCount:
                (state.metadata?.target_lesson_count as number | undefined) ??
                undefined,
              ownerUserId: user?.id ?? undefined,
            },
            {
              onSuccess: () => {
                Alert.alert(
                  'Unit creation started',
                  'We will notify you when your unit is ready.'
                );
                navigation.navigate('LessonList');
              },
              onError: error => {
                console.error(
                  'Failed to create unit from learning coach brief',
                  error
                );
              },
            }
          );
        },
        onError: error => {
          console.error('Failed to accept learning coach brief', error);
        },
      }
    );
  };

  const isAccepting = acceptBrief.isPending || createUnit.isPending;

  if (!sessionState) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator color={theme.colors.primary} size="large" />
        <Text style={styles.loadingText}>Connecting you with the coach…</Text>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <ConversationList messages={sessionState.messages} />
      {sessionState.proposedBrief ? (
        <BriefCard
          brief={sessionState.proposedBrief}
          onAccept={handleAccept}
          onIterate={() =>
            handleQuickReply('Can we try a different direction?')
          }
          isAccepting={isAccepting}
        />
      ) : null}
      <QuickReplies onSelect={handleQuickReply} disabled={isCoachLoading} />
      <Composer onSend={handleSend} disabled={isCoachLoading || isAccepting} />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.background,
    gap: 16,
  },
  loadingText: {
    color: theme.colors.text,
    fontSize: 16,
  },
});
